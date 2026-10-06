"""Change-point story-arc segmentation over fused affect series."""
from __future__ import annotations

from typing import Any
import statistics

from verityngn.services.fusion.plutchik import map_affect_to_segments


def _series_value(row: dict[str, Any]) -> float:
    ex = row.get("exuberance")
    ar = row.get("sympathetic_arousal")
    try:
        ex_f = float(ex) if ex == ex and ex is not None else None
    except (TypeError, ValueError):
        ex_f = None
    try:
        ar_f = float(ar) if ar == ar and ar is not None else None
    except (TypeError, ValueError):
        ar_f = None
    if ex_f is not None and ar_f is not None:
        return 0.6 * ex_f + 0.4 * ar_f
    if ex_f is not None:
        return ex_f
    if ar_f is not None:
        return ar_f
    return 0.5


def segment_story_arcs(
    fused_rows: list[dict[str, Any]],
    *,
    min_arc_sec: float = 15.0,
    z_thresh: float = 1.25,
) -> list[dict[str, Any]]:
    """
    Simple change-point arcs: split when |Δ series| exceeds rolling std * z_thresh
    and the resulting span is at least min_arc_sec.
    """
    if not fused_rows:
        return []
    ordered = sorted(fused_rows, key=lambda r: float(r.get("t_sec") or 0.0))
    values = [_series_value(r) for r in ordered]
    times = [float(r.get("t_sec") or 0.0) for r in ordered]

    if len(ordered) == 1:
        return [_arc_from_slice(ordered, 0, 1, arc_idx=1)]

    breaks = [0]
    window = max(3, len(values) // 8)
    for i in range(1, len(values)):
        lo = max(0, i - window)
        hist = values[lo:i]
        if len(hist) < 2:
            continue
        mu = statistics.fmean(hist)
        sd = statistics.pstdev(hist) or 0.05
        if abs(values[i] - mu) / sd >= z_thresh and (times[i] - times[breaks[-1]]) >= min_arc_sec:
            breaks.append(i)
    breaks.append(len(ordered))

    arcs = []
    for ai, (a, b) in enumerate(zip(breaks[:-1], breaks[1:]), start=1):
        if b <= a:
            continue
        arcs.append(_arc_from_slice(ordered, a, b, arc_idx=ai))
    return arcs


def _arc_from_slice(rows: list[dict[str, Any]], a: int, b: int, *, arc_idx: int) -> dict[str, Any]:
    sl = rows[a:b]
    t0 = float(sl[0].get("t_sec") or 0.0)
    t1 = float(sl[-1].get("t_sec") or t0)
    ex_vals = [
        float(r["exuberance"])
        for r in sl
        if isinstance(r.get("exuberance"), (int, float)) and r["exuberance"] == r["exuberance"]
    ]
    mean_ex = statistics.fmean(ex_vals or [0.5])
    mean_sent = statistics.fmean([float(r.get("text_sentiment") or 0.0) for r in sl])
    ar_vals = [
        float(r["sympathetic_arousal"])
        for r in sl
        if isinstance(r.get("sympathetic_arousal"), (int, float))
        and r["sympathetic_arousal"] == r["sympathetic_arousal"]
    ]
    mean_ar = statistics.fmean(ar_vals or [0.5])
    segs = map_affect_to_segments(mean_sent, mean_ex, mean_ar)
    claims = [r.get("claim_id") for r in sl if r.get("claim_id") is not None]
    dominant = segs[0]["segment_id"] if segs else "sr_anticipation_interest_curiosity"
    return {
        "arc": f"Arc {arc_idx}: {dominant}",
        "start_time": t0,
        "end_time": t1,
        "summary": (
            f"Fused delivery window [{t0:.0f}s–{t1:.0f}s]; "
            f"exuberance≈{mean_ex:.2f}, arousal≈{mean_ar:.2f}, sentiment≈{mean_sent:.2f}."
        ),
        "dominant_sr_segments": segs,
        "claims": claims,
        "n_points": len(sl),
    }
