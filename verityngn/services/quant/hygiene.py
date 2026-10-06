"""Factor hygiene gates — thresholds mirrored from hca-qngn."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
import json
from pathlib import Path

from verityngn.services.quant.ic import daily_rank_ic, event_time_ic, event_week_ics, ic_summary
from verityngn.services.quant.deflated_sharpe import dsr_gate

ICIR_FLOOR = 0.40
FRAC_IC_POS = 0.55
WEEKLY_JACCARD_MAX = 0.25
NEUTRALIZATION_RATIO = 0.5
COST_BPS_HYGIENE = 10
COST_BPS_PROMOTE = 20


@dataclass
class HygieneResult:
    factor_hygiene_pass: bool
    promote_ready: bool
    gates: dict[str, bool] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "factor_hygiene_pass": self.factor_hygiene_pass,
            "promote_ready": self.promote_ready,
            "gates": self.gates,
            "metrics": self.metrics,
            "notes": self.notes,
            "thresholds": {
                "icir_floor": ICIR_FLOOR,
                "frac_ic_pos": FRAC_IC_POS,
                "weekly_jaccard_max": WEEKLY_JACCARD_MAX,
                "neutralization_ratio": NEUTRALIZATION_RATIO,
                "cost_bps_hygiene": COST_BPS_HYGIENE,
                "cost_bps_promote": COST_BPS_PROMOTE,
            },
        }


def jaccard_turnover(sets: list[set[str]]) -> float:
    if len(sets) < 2:
        return 0.0
    turns = []
    for a, b in zip(sets[:-1], sets[1:]):
        inter = len(a & b)
        union = len(a | b) or 1
        turns.append(1.0 - inter / union)
    return sum(turns) / len(turns)


def run_factor_hygiene(
    rows: list[dict[str, Any]],
    *,
    pred_key: str = "prediction",
    y_key: str = "y",
    weekly_memberships: Optional[list[set[str]]] = None,
    resid_icir: Optional[float] = None,
    q5_q1_ann: Optional[float] = None,
    weekly_turnover: float = 0.2,
    n_trials: int = 1,
    observed_sharpe: Optional[float] = None,
    use_event_time_ic: bool = True,
) -> HygieneResult:
    ics = daily_rank_ic(rows, pred_key=pred_key, y_key=y_key)
    if not ics and use_event_time_ic:
        week_ics = event_week_ics(rows, pred_key=pred_key, y_key=y_key)
        if week_ics:
            ics = week_ics
        else:
            pooled = event_time_ic(rows, pred_key=pred_key, y_key=y_key)
            if pooled == pooled:
                ics = [pooled]
    summary = ic_summary(ics)
    icir = summary.get("icir")
    frac = summary.get("frac_pos")

    churn = jaccard_turnover(weekly_memberships or [])
    raw_icir = icir if icir is not None else 0.0
    if resid_icir is None:
        # Fail-closed: missing neutralization input is NOT a pass.
        neut_ok = False
        resid_used = None
    else:
        resid_used = resid_icir
        neut_ok = resid_used >= NEUTRALIZATION_RATIO * max(raw_icir, 1e-9)

    def _cost_ok(bps: float) -> bool:
        if q5_q1_ann is None:
            return False  # fail-closed until panel has returns
        drag = weekly_turnover * (bps / 1e4) * 52
        return q5_q1_ann > drag

    dsr = dsr_gate(
        float(observed_sharpe or 0.0),
        n_obs=max(len(ics), 2),
        n_trials=max(n_trials, 1),
    )

    gates = {
        "icir_floor": (icir is not None and icir >= ICIR_FLOOR),
        "frac_ic_pos": (frac is not None and frac >= FRAC_IC_POS),
        "churn_lt_max": churn < WEEKLY_JACCARD_MAX,
        "neutralization_ok": neut_ok,
        "cost_edge_10bps": _cost_ok(COST_BPS_HYGIENE),
        "cost_edge_20bps": _cost_ok(COST_BPS_PROMOTE),
        "dsr": bool(dsr.get("pass")),
    }
    hygiene = all(
        [
            gates["icir_floor"],
            gates["frac_ic_pos"],
            gates["churn_lt_max"],
            gates["neutralization_ok"],
            gates["cost_edge_10bps"],
            gates["dsr"],
        ]
    )
    promote = hygiene and gates["cost_edge_20bps"]
    return HygieneResult(
        factor_hygiene_pass=hygiene,
        promote_ready=promote,
        gates=gates,
        metrics={
            "ic_summary": summary,
            "weekly_jaccard_turnover": churn,
            "resid_icir": resid_used,
            "q5_q1_ann": q5_q1_ann,
            "dsr": dsr,
            "event_time_ic_used": use_event_time_ic,
        },
        notes=(
            "Factor PASS ≠ portfolio PROMOTE. Never live-demean by sector; "
            "never fillna(0) on sparse alt-data; horizon must match rebalance."
        ),
    )


def write_hygiene(result: HygieneResult, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
    return path
