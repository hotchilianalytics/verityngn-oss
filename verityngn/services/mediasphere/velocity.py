"""Velocity = Δ appearance frequency over a lookback."""
from __future__ import annotations

from typing import Any, Sequence


def compute_velocity(series: Sequence[dict[str, Any]], *, field: str = "youtube_hit_estimate") -> dict[str, Any]:
    if not series:
        return {"velocity": 0.0, "n": 0, "field": field}
    vals = [float(r.get(field) or 0.0) for r in series]
    if len(vals) == 1:
        return {"velocity": 0.0, "n": 1, "field": field, "latest": vals[-1]}
    # simple end-minus-start / days
    velocity = (vals[-1] - vals[0]) / max(1, len(vals) - 1)
    return {
        "velocity": velocity,
        "n": len(vals),
        "field": field,
        "latest": vals[-1],
        "start": vals[0],
    }
