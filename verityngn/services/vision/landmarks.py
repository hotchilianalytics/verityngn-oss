"""Face landmarks — adapter interface + synthetic offline fallback."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional
import hashlib


@dataclass
class LandmarkFrame:
    t_sec: float
    n_points: int
    bbox: list[float]  # x, y, w, h normalized
    confidence: float
    source: str = "synthetic"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LandmarkTrack:
    video_id: str
    fps: float
    frames: list[LandmarkFrame] = field(default_factory=list)
    backend: str = "synthetic"
    gated: bool = False
    not_for_employment_use: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "video_id": self.video_id,
            "fps": self.fps,
            "backend": self.backend,
            "gated": self.gated,
            "not_for_employment_use": self.not_for_employment_use,
            "n_frames": len(self.frames),
            "frames": [f.to_dict() for f in self.frames[:50]],  # cap for JSON size
            "frames_truncated": len(self.frames) > 50,
        }


def _seed_float(key: str, lo: float, hi: float) -> float:
    h = int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)
    return lo + (h % 10000) / 10000.0 * (hi - lo)


def extract_landmarks(
    video_id: str,
    *,
    duration_sec: float = 60.0,
    fps: float = 5.0,
    backend: Optional[str] = None,
) -> LandmarkTrack:
    """
    Extract face landmark track.

    Without a CV backend, emits a deterministic synthetic track suitable for
    pipeline smoke tests (face present, mild motion).
    """
    used = backend or "synthetic"
    # Optional backends are tried only if explicitly requested
    if used in {"mediapipe", "openface3"} and backend:
        try:
            if used == "mediapipe":
                from verityngn.services.vision.adapters.mediapipe import try_landmarks

                track = try_landmarks(video_id, duration_sec=duration_sec, fps=fps)
                if track is not None:
                    return track
            if used == "openface3":
                from verityngn.services.vision.adapters.openface3 import try_landmarks

                track = try_landmarks(video_id, duration_sec=duration_sec, fps=fps)
                if track is not None:
                    return track
        except Exception:  # noqa: BLE001
            used = "synthetic"

    n = max(1, int(duration_sec * fps))
    frames = []
    for i in range(n):
        t = i / fps
        frames.append(
            LandmarkFrame(
                t_sec=t,
                n_points=68,
                bbox=[
                    0.35 + 0.02 * _seed_float(f"{video_id}:{i}:x", -1, 1),
                    0.25 + 0.02 * _seed_float(f"{video_id}:{i}:y", -1, 1),
                    0.30,
                    0.40,
                ],
                confidence=0.85 + 0.1 * _seed_float(f"{video_id}:{i}:c", 0, 1),
                source="synthetic",
            )
        )
    return LandmarkTrack(video_id=video_id, fps=fps, frames=frames, backend=used)
