"""Earnings calendar / surprise ground truth (yfinance optional; fixtures default)."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional
import json


@dataclass
class EarningsEvent:
    ticker: str
    event_date: str
    eps_actual: float
    eps_estimate: float
    surprise_pct: float
    source: str = "fixture"

    @property
    def surprise_direction(self) -> int:
        """+1 beat, -1 miss, 0 inline (|surprise| < 1%)."""
        if abs(self.surprise_pct) < 1.0:
            return 0
        return 1 if self.surprise_pct > 0 else -1

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["surprise_direction"] = self.surprise_direction
        return d


# Offline fixtures for pilot tickers (illustrative; not for live trading)
DEFAULT_FIXTURES: list[dict[str, Any]] = [
    {"ticker": "AAPL", "event_date": "2025-01-30", "eps_actual": 2.40, "eps_estimate": 2.35, "surprise_pct": 2.13},
    {"ticker": "AAPL", "event_date": "2025-05-01", "eps_actual": 1.65, "eps_estimate": 1.62, "surprise_pct": 1.85},
    {"ticker": "AAPL", "event_date": "2025-07-31", "eps_actual": 1.57, "eps_estimate": 1.55, "surprise_pct": 1.29},
    {"ticker": "MSFT", "event_date": "2025-01-29", "eps_actual": 3.23, "eps_estimate": 3.10, "surprise_pct": 4.19},
    {"ticker": "MSFT", "event_date": "2025-04-30", "eps_actual": 3.46, "eps_estimate": 3.35, "surprise_pct": 3.28},
    {"ticker": "MSFT", "event_date": "2025-07-30", "eps_actual": 3.65, "eps_estimate": 3.55, "surprise_pct": 2.82},
    {"ticker": "NVDA", "event_date": "2025-02-26", "eps_actual": 0.89, "eps_estimate": 0.84, "surprise_pct": 5.95},
    {"ticker": "NVDA", "event_date": "2025-05-28", "eps_actual": 0.76, "eps_estimate": 0.74, "surprise_pct": 2.70},
    {"ticker": "NVDA", "event_date": "2025-08-27", "eps_actual": 0.95, "eps_estimate": 0.90, "surprise_pct": 5.56},
    {"ticker": "PLTR", "event_date": "2025-02-03", "eps_actual": 0.09, "eps_estimate": 0.08, "surprise_pct": 12.50},
    {"ticker": "PLTR", "event_date": "2025-05-05", "eps_actual": 0.13, "eps_estimate": 0.11, "surprise_pct": 18.18},
    {"ticker": "PLTR", "event_date": "2025-08-04", "eps_actual": 0.16, "eps_estimate": 0.14, "surprise_pct": 14.29},
    {"ticker": "TSLA", "event_date": "2025-01-29", "eps_actual": 0.73, "eps_estimate": 0.75, "surprise_pct": -2.67},
    {"ticker": "TSLA", "event_date": "2025-04-22", "eps_actual": 0.27, "eps_estimate": 0.43, "surprise_pct": -37.21},
    {"ticker": "TSLA", "event_date": "2025-07-23", "eps_actual": 0.40, "eps_estimate": 0.42, "surprise_pct": -4.76},
]


def load_earnings_fixtures(path: Optional[Path] = None) -> list[EarningsEvent]:
    if path and Path(path).exists():
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        rows = raw if isinstance(raw, list) else raw.get("events") or []
    else:
        rows = DEFAULT_FIXTURES
    return [
        EarningsEvent(
            ticker=r["ticker"],
            event_date=r["event_date"],
            eps_actual=float(r["eps_actual"]),
            eps_estimate=float(r["eps_estimate"]),
            surprise_pct=float(r["surprise_pct"]),
            source=r.get("source", "fixture"),
        )
        for r in rows
    ]


def fetch_earnings_yfinance(ticker: str) -> list[EarningsEvent]:
    """Optional live pull; returns [] if yfinance unavailable."""
    try:
        import yfinance as yf  # type: ignore
    except ImportError:
        return []
    t = yf.Ticker(ticker)
    cal = getattr(t, "earnings_dates", None)
    if cal is None:
        return []
    # Best-effort parse; structure varies by yfinance version
    events: list[EarningsEvent] = []
    try:
        df = cal if hasattr(cal, "iterrows") else None
        if df is None:
            return []
        for idx, row in df.head(8).iterrows():
            actual = row.get("Reported EPS") or row.get("EPS Actual")
            est = row.get("EPS Estimate")
            if actual is None or est is None:
                continue
            actual_f = float(actual)
            est_f = float(est)
            surprise = ((actual_f - est_f) / abs(est_f) * 100.0) if est_f else 0.0
            events.append(
                EarningsEvent(
                    ticker=ticker.upper(),
                    event_date=str(idx.date()) if hasattr(idx, "date") else str(idx)[:10],
                    eps_actual=actual_f,
                    eps_estimate=est_f,
                    surprise_pct=surprise,
                    source="yfinance",
                )
            )
    except Exception:  # noqa: BLE001
        return []
    return events


def write_fixtures(path: Path, events: Optional[list[EarningsEvent]] = None) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ev = events or load_earnings_fixtures()
    path.write_text(json.dumps([e.to_dict() for e in ev], indent=2), encoding="utf-8")
    return path
