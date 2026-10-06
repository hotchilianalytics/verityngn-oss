"""Market-model abnormal returns. Honest names: raw_h1 vs car.

raw_h1 — single-session close-to-close (what T010 reported as "CAR" through 2026-08-14).
car(H) — sum of daily abnormal returns r_i - (alpha + beta * r_m) over H sessions
         after the event, beta estimated vs SPY on [-250, -30] trading days.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional

CAR_HORIZONS = (1, 5, 10, 21)


def _flatten_close(hist: Any) -> Optional[Any]:
    if hist is None or getattr(hist, "empty", True):
        return None
    cols = hist.columns
    if getattr(cols, "nlevels", 1) > 1:
        for key in ("Close", "close"):
            try:
                sub = hist[key]
                if hasattr(sub, "columns"):
                    sub = sub.iloc[:, 0]
                return sub
            except Exception:  # noqa: BLE001
                pass
        try:
            return hist.xs("Close", axis=1, level=-1).iloc[:, 0]
        except Exception:  # noqa: BLE001
            return None
    if "Close" not in hist.columns:
        return None
    return hist["Close"]


def _history(ticker: str, start: datetime, end: datetime) -> Optional[Any]:
    try:
        import yfinance as yf  # type: ignore
    except ImportError:
        return None
    hist = None
    try:
        hist = yf.Ticker(ticker).history(
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            auto_adjust=True,
        )
    except Exception:  # noqa: BLE001
        hist = None
    if hist is None or getattr(hist, "empty", True):
        try:
            hist = yf.download(
                ticker,
                start=start.strftime("%Y-%m-%d"),
                end=end.strftime("%Y-%m-%d"),
                progress=False,
                auto_adjust=True,
            )
        except Exception:  # noqa: BLE001
            return None
    return hist


def _event_loc(closes, event_date: str) -> Optional[int]:
    if closes is None or getattr(closes, "empty", True):
        return None
    target = datetime.strptime(event_date[:10], "%Y-%m-%d").date()
    idx = None
    for ts in closes.index:
        d = ts.date() if hasattr(ts, "date") else ts
        if d >= target:
            idx = ts
            break
    if idx is None:
        return None
    return list(closes.index).index(idx)


def raw_h1(ticker: str, event_date: str) -> Optional[float]:
    """Single-session close-to-close on first trade on/after event_date. Not a CAR."""
    start = datetime.strptime(event_date[:10], "%Y-%m-%d") - timedelta(days=15)
    end = datetime.strptime(event_date[:10], "%Y-%m-%d") + timedelta(days=10)
    hist = _history(ticker, start, end)
    closes = _flatten_close(hist)
    loc = _event_loc(closes, event_date)
    if loc is None or loc == 0:
        return None
    prev, now = float(closes.iloc[loc - 1]), float(closes.iloc[loc])
    if prev == 0:
        return None
    return round((now - prev) / prev, 6)


def _simple_returns(closes) -> list[float]:
    out = []
    for i in range(1, len(closes)):
        prev = float(closes.iloc[i - 1])
        now = float(closes.iloc[i])
        out.append((now - prev) / prev if prev else 0.0)
    return out


def car(
    ticker: str,
    event_date: str,
    *,
    horizons: tuple[int, ...] = CAR_HORIZONS,
    benchmark: str = "SPY",
    est_start_offset: int = -250,
    est_end_offset: int = -30,
) -> dict[str, Optional[float]]:
    """Market-model CAR at each horizon. Missing → None (never fill 0)."""
    evt = datetime.strptime(event_date[:10], "%Y-%m-%d")
    start = evt - timedelta(days=420)  # ~250 trading days + buffer
    end = evt + timedelta(days=max(horizons) * 3 + 14)
    stk = _history(ticker, start, end)
    mkt = _history(benchmark, start, end)
    s = _flatten_close(stk)
    m = _flatten_close(mkt)
    out: dict[str, Optional[float]] = {f"car_h{h}": None for h in horizons}
    out["raw_h1"] = raw_h1(ticker, event_date)
    out["beta"] = None
    out["alpha"] = None
    if s is None or m is None:
        return out
    # Align on dates
    s_map = { (ts.date() if hasattr(ts, "date") else ts): float(v) for ts, v in zip(s.index, s.values) }
    m_map = { (ts.date() if hasattr(ts, "date") else ts): float(v) for ts, v in zip(m.index, m.values) }
    common = sorted(set(s_map) & set(m_map))
    if len(common) < 40:
        return out
    # daily returns on common calendar
    dates = common
    rs, rm = [], []
    for i in range(1, len(dates)):
        ps, pm = s_map[dates[i - 1]], m_map[dates[i - 1]]
        if not ps or not pm:
            continue
        rs.append(((s_map[dates[i]] - ps) / ps, dates[i]))
        rm.append(((m_map[dates[i]] - pm) / pm, dates[i]))
    target = evt.date()
    # event index = first common return date >= event
    ev_i = None
    for i, (rv, d) in enumerate(rs):
        if d >= target:
            ev_i = i
            break
    if ev_i is None:
        return out
    est_hi = ev_i + est_end_offset  # -30
    est_lo = ev_i + est_start_offset  # -250
    if est_hi <= 1:
        est_hi = max(1, ev_i - 20)
    if est_lo < 0:
        est_lo = 0
    ys = [rs[i][0] for i in range(est_lo, max(est_lo + 1, est_hi))]
    xs = [rm[i][0] for i in range(est_lo, max(est_lo + 1, est_hi))]
    if len(ys) < 20:
        return out
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    varx = sum((x - mx) ** 2 for x in xs)
    if varx < 1e-12:
        return out
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    beta = cov / varx
    alpha = my - beta * mx
    out["beta"] = round(beta, 6)
    out["alpha"] = round(alpha, 6)
    # accumulate abnormal from event session through H
    ar = []
    for i in range(ev_i, min(ev_i + max(horizons), len(rs))):
        ar.append(rs[i][0] - (alpha + beta * rm[i][0]))
    cum = 0.0
    for h in range(1, max(horizons) + 1):
        if h - 1 < len(ar):
            cum += ar[h - 1]
        if h in horizons:
            out[f"car_h{h}"] = round(cum, 6) if h - 1 < len(ar) else None
    return out
