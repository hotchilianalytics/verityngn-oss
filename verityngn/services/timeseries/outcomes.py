"""Outcome adapters behind one interface: equity CAR, FOMC rate moves."""
from __future__ import annotations

from typing import Any, Optional

from verityngn.services.timeseries.returns import car as equity_car, raw_h1


def equity_outcomes(ticker: str, event_date: str) -> dict[str, Any]:
    mm = equity_car(ticker, event_date)
    return {
        "kind": "equity_car",
        "ticker": ticker,
        "event_date": event_date,
        **mm,
        "raw_h1": mm.get("raw_h1") or raw_h1(ticker, event_date),
    }


def fomc_outcomes(event_date: str, *, futures_ticker: str = "ZF=F") -> dict[str, Any]:
    """Nearest-session move in 5-year futures (proxy). None if yfinance misses."""
    mm = equity_car(futures_ticker, event_date, horizons=(1, 5))
    spy = equity_car("SPY", event_date, horizons=(1, 5))
    return {
        "kind": "fomc_rates",
        "event_date": event_date,
        "zf_raw_h1": mm.get("raw_h1"),
        "spy_raw_h1": spy.get("raw_h1"),
        "zf_car_h1": mm.get("car_h1"),
        "spy_car_h1": spy.get("car_h1"),
    }


def outcome_for(kind: str, event_date: str, *, ticker: str = "") -> dict[str, Any]:
    if kind in {"equity", "equity_car", "earnings"}:
        if not ticker:
            raise ValueError("equity outcomes need ticker")
        return equity_outcomes(ticker, event_date)
    if kind in {"fomc", "fomc_rates"}:
        return fomc_outcomes(event_date)
    raise ValueError(f"unknown outcome kind {kind}")
