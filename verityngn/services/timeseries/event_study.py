"""Leakage-safe event study with CAR windows H=1/5/10/21/30."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
import hashlib

from verityngn.services.timeseries.earnings import EarningsEvent, load_earnings_fixtures
from verityngn.services.timeseries.leakage import assert_causal, time_ordered_split
from verityngn.services.timeseries.models import fit_baseline_logit

CAR_HORIZONS = (1, 5, 10, 21, 30)


@dataclass
class EventStudyResult:
    trial_id: str
    n_events: int
    train_acc: Optional[float]
    val_acc: Optional[float]
    test_acc: Optional[float]
    rows: list[dict[str, Any]] = field(default_factory=list)
    car_summary: dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "trial_id": self.trial_id,
            "n_events": self.n_events,
            "train_acc": self.train_acc,
            "val_acc": self.val_acc,
            "test_acc": self.test_acc,
            "car_horizons": list(CAR_HORIZONS),
            "car_summary": self.car_summary,
            "rows": self.rows,
            "notes": self.notes,
            "limits": (
                "Fixture/smoke metrics only until registered trial with live features. "
                "Do not present as tradable alpha. See docs/trials_ledger.md."
            ),
        }


def _feature_asof_for_event(event_date: str) -> str:
    y, m, d = [int(x) for x in event_date[:10].split("-")]
    d -= 1
    if d == 0:
        m -= 1
        if m == 0:
            y -= 1
            m = 12
        dim = [31, 29 if y % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]
        d = dim
    return f"{y:04d}-{m:02d}-{d:02d}"


def _synthetic_pre_event_features(ticker: str, event: EarningsEvent) -> dict[str, float]:
    seed = sum(ord(c) for c in ticker + event.event_date)
    return {
        "exuberance_mean": ((seed % 100) / 100.0) * 0.5 + 0.25,
        "mediasphere_velocity": ((seed // 7) % 50) / 50.0 - 0.25,
        "delivery_risk": ((seed // 13) % 100) / 100.0,
        "congruence": 0.4 + ((seed // 3) % 50) / 100.0,
        "sympathetic_arousal": 0.3 + ((seed // 11) % 40) / 100.0,
    }


def _synthetic_car(ticker: str, event_date: str, horizon: int, *, allow_synthetic: bool = False) -> float:
    """Deterministic synthetic CAR — NOT measured returns.

    Raises unless allow_synthetic=True. Fixture smoke tests must pass the flag
    explicitly so user-facing paths cannot silently emit hash noise.
    """
    if not allow_synthetic:
        raise RuntimeError(
            "event_study._synthetic_car refused: pass allow_synthetic=True for fixture "
            "smoke only. Real CARs live in verityngn.services.timeseries.returns.car"
        )
    h = hashlib.sha256(f"{ticker}:{event_date}:H{horizon}".encode()).hexdigest()
    raw = int(h[:8], 16) / 0xFFFFFFFF
    return (raw - 0.5) * 0.06  # ±3% band


def run_event_study(
    *,
    trial_id: str = "T000",
    ticker_to_player: Optional[dict[str, str]] = None,
    feature_lookup: Optional[dict[tuple[str, str], dict[str, float]]] = None,
    events: Optional[list[EarningsEvent]] = None,
    car_horizons: tuple[int, ...] = CAR_HORIZONS,
    allow_synthetic: bool = False,
    use_market_model: bool = False,
) -> EventStudyResult:
    events = events or load_earnings_fixtures()
    ticker_to_player = ticker_to_player or {
        "AAPL": "ceo_aapl_cook",
        "MSFT": "ceo_msft_nadella",
        "NVDA": "ceo_nvda_huang",
        "PLTR": "ceo_pltr_karp",
        "TSLA": "ceo_tsla_musk",
    }

    rows: list[dict[str, Any]] = []
    for ev in events:
        player_id = ticker_to_player.get(ev.ticker, ev.ticker)
        asof = _feature_asof_for_event(ev.event_date)
        assert_causal(asof, ev.event_date, label="pre_event_features")
        feats = None
        if feature_lookup:
            feats = feature_lookup.get((player_id, asof))
        if feats is None:
            feats = _synthetic_pre_event_features(ev.ticker, ev)
        y = 1 if ev.surprise_direction >= 0 else 0
        if use_market_model:
            from verityngn.services.timeseries.returns import car as market_car
            mm = market_car(ev.ticker, ev.event_date, horizons=tuple(car_horizons))
            cars = {f"car_h{h}": mm.get(f"car_h{h}") for h in car_horizons}
            cars["raw_h1"] = mm.get("raw_h1")
            cars["beta"] = mm.get("beta")
        else:
            cars = {
                f"car_h{h}": _synthetic_car(ev.ticker, ev.event_date, h, allow_synthetic=allow_synthetic)
                for h in car_horizons
            }
        rows.append(
            {
                "player_id": player_id,
                "ticker": ev.ticker,
                "ts": ev.event_date,
                "date": ev.event_date,
                "asof_available": asof,
                "y_beat": y,
                "surprise_pct": ev.surprise_pct,
                **feats,
                **cars,
            }
        )

    train, val, test = time_ordered_split(rows)
    feature_keys = [
        "exuberance_mean",
        "mediasphere_velocity",
        "delivery_risk",
        "congruence",
        "sympathetic_arousal",
    ]

    def _acc(split: list[dict[str, Any]], model: Any) -> Optional[float]:
        if not split or model is None:
            return None
        correct = 0
        for r in split:
            x = [float(r.get(k) or 0.0) for k in feature_keys]
            pred = model.predict(x)
            correct += int(pred == int(r["y_beat"]))
        return correct / len(split)

    model = fit_baseline_logit(train, feature_keys=feature_keys, label_key="y_beat")

    car_summary = {}
    for h in car_horizons:
        key = f"car_h{h}"
        vals = [float(r[key]) for r in rows]
        car_summary[key] = {
            "mean": sum(vals) / len(vals) if vals else None,
            "n": len(vals),
            "note": (
                "Market-model CAR" if use_market_model
                else "Synthetic CAR — fixture only; refuse without allow_synthetic"
            ),
        }

    return EventStudyResult(
        trial_id=trial_id,
        n_events=len(rows),
        train_acc=_acc(train, model),
        val_acc=_acc(val, model),
        test_acc=_acc(test, model),
        rows=rows,
        car_summary=car_summary,
        notes=(
            f"splits train/val/test={len(train)}/{len(val)}/{len(test)}; "
            f"CAR horizons={list(car_horizons)}; model={'logit' if model else 'none'}"
        ),
    )
