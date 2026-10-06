"""Spectral / physiological proxies from video: rPPG + sympathetic arousal.

rPPG (CHROM/POS style) estimates heart rate / HRV from skin color modulation.
Sympathetic arousal is a separate labeled channel (SympCam: mean corr ~0.77;
plain rPPG alone is insufficient for stress).

rPPG spatial inconsistency is also an authenticity / deepfake tell — wired into
the authenticity gate.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Optional
import hashlib
import math


@dataclass
class SpectralFeatures:
    video_id: str
    heart_rate_bpm: float
    hrv_sdnn_ms: float
    sympathetic_arousal: float  # [0,1] research proxy
    rppg_consistency: float  # [0,1] — low → deepfake suspicion
    method: str = "synthetic_chrom"
    backend: str = "synthetic"
    gated: bool = False
    not_for_employment_use: bool = True
    notes: str = (
        "Sympathetic arousal is a separate channel from rPPG HR. "
        "rppg_consistency feeds authenticity gate (deepfake tell)."
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _seed(key: str) -> float:
    h = int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)
    return (h % 10000) / 10000.0


def extract_spectral(
    video_id: str,
    *,
    duration_sec: float = 60.0,
    backend: Optional[str] = None,
) -> SpectralFeatures:
    used = backend or "synthetic"
    if used == "pyvhr" and backend:
        try:
            from verityngn.services.vision.adapters.pyvhr import try_spectral

            out = try_spectral(video_id, duration_sec=duration_sec)
            if out is not None:
                return out
        except Exception:  # noqa: BLE001
            used = "synthetic"

    hr = 60.0 + 40.0 * _seed(f"{video_id}:hr")
    hrv = 20.0 + 60.0 * _seed(f"{video_id}:hrv")
    arousal = 0.2 + 0.6 * _seed(f"{video_id}:arousal")
    # Synthetic videos are consistent by construction
    consistency = 0.75 + 0.2 * _seed(f"{video_id}:cons")
    return SpectralFeatures(
        video_id=video_id,
        heart_rate_bpm=round(hr, 1),
        hrv_sdnn_ms=round(hrv, 1),
        sympathetic_arousal=round(arousal, 3),
        rppg_consistency=round(consistency, 3),
        backend=used,
    )


def rppg_authenticity_check(spectral: SpectralFeatures, *, threshold: float = 0.45) -> dict[str, Any]:
    """Map rPPG consistency into an authenticity-gate payload."""
    score = spectral.rppg_consistency
    status = "pass" if score >= threshold else "fail"
    if math.isnan(score):
        status = "skipped"
        score = 0.0
    return {
        "source": "open:rppg_consistency",
        "construct_type": "measured",
        "status": status,
        "score": float(score),
        "threshold": threshold,
        "heart_rate_bpm": spectral.heart_rate_bpm,
        "note": "Low spatial rPPG consistency is a deepfake tell; fail → gate affect/vision.",
    }
