"""FACS Action Unit intensities — OpenFace 3.0 / Py-Feat adapters.

Documented AU F1 reality check: ~0.60 on DISFA (OpenFace 3.0 MTL). Features are
congruence / arousal inputs — never veracity labels.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional
import hashlib


# Common AUs used in delivery / cognitive-load analysis
AU_NAMES = [
    "AU01",  # Inner brow raiser
    "AU02",  # Outer brow raiser
    "AU04",  # Brow lowerer
    "AU05",  # Upper lid raiser
    "AU06",  # Cheek raiser
    "AU07",  # Lid tightener
    "AU12",  # Lip corner puller
    "AU15",  # Lip corner depressor
    "AU17",  # Chin raiser
    "AU20",  # Lip stretcher
    "AU23",  # Lip tightener
    "AU25",  # Lips part
    "AU26",  # Jaw drop
    "AU45",  # Blink
]


@dataclass
class AUFrame:
    t_sec: float
    intensities: dict[str, float]
    source: str = "synthetic"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ActionUnitTrack:
    video_id: str
    frames: list[AUFrame] = field(default_factory=list)
    backend: str = "synthetic"
    au_f1_benchmark_note: str = "OpenFace 3.0 MTL AU F1 ~0.60 on DISFA — not clinical grade"
    gated: bool = False
    not_for_employment_use: bool = True

    def mean_intensities(self) -> dict[str, float]:
        if not self.frames:
            return {au: float("nan") for au in AU_NAMES}
        out = {}
        for au in AU_NAMES:
            vals = [f.intensities.get(au, 0.0) for f in self.frames]
            out[au] = float(sum(vals) / len(vals))
        return out

    def to_dict(self) -> dict[str, Any]:
        return {
            "video_id": self.video_id,
            "backend": self.backend,
            "gated": self.gated,
            "not_for_employment_use": self.not_for_employment_use,
            "au_f1_benchmark_note": self.au_f1_benchmark_note,
            "mean_intensities": self.mean_intensities(),
            "n_frames": len(self.frames),
            "frames_sample": [f.to_dict() for f in self.frames[:: max(1, len(self.frames) // 10)][:10]],
        }


def _seed(key: str) -> float:
    h = int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)
    return (h % 10000) / 10000.0


def extract_action_units(
    video_id: str,
    *,
    duration_sec: float = 60.0,
    fps: float = 5.0,
    backend: Optional[str] = None,
) -> ActionUnitTrack:
    used = backend or "synthetic"
    if used in {"openface3", "pyfeat"} and backend:
        try:
            if used == "openface3":
                from verityngn.services.vision.adapters.openface3 import try_action_units

                track = try_action_units(video_id, duration_sec=duration_sec, fps=fps)
                if track is not None:
                    return track
            if used == "pyfeat":
                from verityngn.services.vision.adapters.pyfeat import try_action_units

                track = try_action_units(video_id, duration_sec=duration_sec, fps=fps)
                if track is not None:
                    return track
        except Exception:  # noqa: BLE001
            used = "synthetic"

    n = max(1, int(duration_sec * fps))
    frames = []
    for i in range(n):
        t = i / fps
        intensities = {au: round(0.1 + 0.8 * _seed(f"{video_id}:{i}:{au}"), 4) for au in AU_NAMES}
        # Mild temporal structure: blinks cluster
        if i % 25 == 0:
            intensities["AU45"] = 2.5 + _seed(f"{video_id}:{i}:blink")
        frames.append(AUFrame(t_sec=t, intensities=intensities, source="synthetic"))
    return ActionUnitTrack(video_id=video_id, frames=frames, backend=used)
