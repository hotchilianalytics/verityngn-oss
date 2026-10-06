"""Spearman RankIC / ICIR — hca-qngn qa_ic_baseline equivalent for JSON panels."""
from __future__ import annotations

from typing import Any, Optional
import math


def _rank(xs: list[float]) -> list[float]:
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def spearman(x: list[float], y: list[float]) -> float:
    if len(x) < 3 or len(x) != len(y):
        return float("nan")
    rx, ry = _rank(x), _rank(y)
    mx = sum(rx) / len(rx)
    my = sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    denx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    deny = math.sqrt(sum((b - my) ** 2 for b in ry))
    if denx < 1e-12 or deny < 1e-12:
        return float("nan")
    return num / (denx * deny)


def daily_rank_ic(rows: list[dict[str, Any]], *, pred_key: str = "prediction", y_key: str = "y") -> list[float]:
    """Group by date, compute Spearman RankIC each day."""
    by_date: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        d = str(r.get("date") or r.get("ts") or "")
        by_date.setdefault(d, []).append(r)
    ics = []
    for d in sorted(by_date):
        g = by_date[d]
        xs = [float(r[pred_key]) for r in g if pred_key in r and y_key in r]
        ys = [float(r[y_key]) for r in g if pred_key in r and y_key in r]
        if len(xs) >= 3:
            ics.append(spearman(xs, ys))
    return [ic for ic in ics if ic == ic]


def ic_summary(ics: list[float]) -> dict[str, Any]:
    if not ics:
        return {"n": 0, "mean_ic": None, "std_ic": None, "icir": None, "frac_pos": None}
    mean = sum(ics) / len(ics)
    var = sum((x - mean) ** 2 for x in ics) / len(ics)
    std = math.sqrt(var)
    icir = mean / std if std > 1e-12 else None
    frac = sum(1 for x in ics if x > 0) / len(ics)
    return {
        "n": len(ics),
        "mean_ic": mean,
        "std_ic": std,
        "icir": icir,
        "frac_pos": frac,
    }



def event_time_ic(
    rows: list[dict[str, Any]],
    *,
    pred_key: str = "prediction",
    y_key: str = "y",
    min_n: int = 3,
) -> float:
    """Pooled Spearman across *events* — defined on staggered earnings (n>=3).

    Calendar daily_rank_ic requires >=3 names on the same date and yields n=0
    on a typical earnings calendar. That is an evaluation-design bug, not a
    missing factor. Use this (or event_week_ics) instead.
    """
    xs: list[float] = []
    ys: list[float] = []
    for r in rows:
        if pred_key not in r or y_key not in r:
            continue
        try:
            x = float(r[pred_key])
            y = float(r[y_key])
        except (TypeError, ValueError):
            continue
        if x == x and y == y:
            xs.append(x)
            ys.append(y)
    if len(xs) < min_n:
        return float("nan")
    return spearman(xs, ys)


def event_week_ics(
    rows: list[dict[str, Any]],
    *,
    pred_key: str = "prediction",
    y_key: str = "y",
    date_key: str = "event_date",
    min_names: int = 3,
) -> list[float]:
    """RankIC inside ISO-week buckets when a week has >= min_names events."""
    from datetime import datetime

    buckets: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        ds = str(r.get(date_key) or r.get("date") or r.get("ts") or "")[:10]
        if len(ds) < 10:
            continue
        try:
            d = datetime.strptime(ds, "%Y-%m-%d")
        except ValueError:
            continue
        iso = f"{d.isocalendar()[0]}-W{d.isocalendar()[1]:02d}"
        buckets.setdefault(iso, []).append(r)
    ics = []
    for week in sorted(buckets):
        g = buckets[week]
        xs, ys = [], []
        for r in g:
            if pred_key not in r or y_key not in r:
                continue
            try:
                x, y = float(r[pred_key]), float(r[y_key])
            except (TypeError, ValueError):
                continue
            if x == x and y == y:
                xs.append(x)
                ys.append(y)
        if len(xs) >= min_names:
            ic = spearman(xs, ys)
            if ic == ic:
                ics.append(ic)
    return ics
