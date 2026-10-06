"""Gaze and blink metrics.

Validity notes (research, not product claims):
- Blink amplitude / rate correlate with state anxiety (r ~ 0.42–0.56), comparable
  to skin conductance in film-clip paradigms.
- Gaze aversion does NOT reliably predict veracity — treat as cognitive-load
  proxy only. Never map gaze aversion → "lying."
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional
import hashlib
import math


GAZE_VALIDITY_NOTE = (
    "Blink amplitude/rate are cognitive-load / anxiety proxies. "
    "Gaze aversion does not predict veracity — never use as a lie signal."
)


@dataclass
class GazeBlinkSummary:
    video_id: str
    blink_rate_per_min: float
    blink_amplitude_mean: float
    blink_amplitude_std: float
    fixation_count: float
    gaze_yaw_mean: float
    gaze_pitch_mean: float
    gaze_aversion_ratio: float  # fraction of frames looking away — cognitive load only
    backend: str = "synthetic"
    validity_note: str = GAZE_VALIDITY_NOTE
    gated: bool = False
    not_for_employment_use: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _seed(key: str) -> float:
    h = int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)
    return (h % 10000) / 10000.0


def extract_gaze_blink(
    video_id: str,
    *,
    duration_sec: float = 60.0,
    backend: Optional[str] = None,
) -> GazeBlinkSummary:
    used = backend or "synthetic"
    if used == "openface3" and backend:
        try:
            from verityngn.services.vision.adapters.openface3 import try_gaze_blink

            out = try_gaze_blink(video_id, duration_sec=duration_sec)
            if out is not None:
                return out
        except Exception:  # noqa: BLE001
            used = "synthetic"

    # Deterministic synthetic summary
    br = 12.0 + 10.0 * _seed(f"{video_id}:br")
    ba = 0.4 + 0.4 * _seed(f"{video_id}:ba")
    return GazeBlinkSummary(
        video_id=video_id,
        blink_rate_per_min=round(br, 2),
        blink_amplitude_mean=round(ba, 3),
        blink_amplitude_std=round(0.05 + 0.15 * _seed(f"{video_id}:bas"), 3),
        fixation_count=round(duration_sec * (0.5 + _seed(f"{video_id}:fix")), 1),
        gaze_yaw_mean=round((_seed(f"{video_id}:yaw") - 0.5) * 20.0, 2),
        gaze_pitch_mean=round((_seed(f"{video_id}:pitch") - 0.5) * 10.0, 2),
        gaze_aversion_ratio=round(0.1 + 0.3 * _seed(f"{video_id}:av"), 3),
        backend=used,
    )


def cognitive_load_proxy(summary: GazeBlinkSummary) -> float:
    """Map blink rate + amplitude into [0,1] cognitive-load proxy — not veracity."""
    # Normalize roughly around 15 blinks/min and amplitude 0.5
    br_z = (summary.blink_rate_per_min - 15.0) / 10.0
    ba_z = (summary.blink_amplitude_mean - 0.5) / 0.3
    raw = 0.5 + 0.25 * math.tanh(br_z) + 0.25 * math.tanh(ba_z)
    return float(max(0.0, min(1.0, raw)))
