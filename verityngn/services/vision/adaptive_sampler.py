"""Adaptive video sampling policy — fps and media_resolution by scene class.

Cheap OpenCV probe (optional) estimates cut density and face presence to pick
lecture-rate vs flash-OCR vs montage sampling. Not a lie detector.
"""
from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

SCENE_LECTURE = "lecture_vsl"
SCENE_MONTAGE = "montage_motion"
SCENE_FLASH_OCR = "flash_ocr"
SCENE_EXHIBIT = "exhibit_slide"

DEFAULT_POLICY = {
    SCENE_LECTURE: {"fps": 1.0, "media_resolution": "MEDIA_RESOLUTION_LOW"},
    SCENE_MONTAGE: {"fps": 3.0, "media_resolution": "MEDIA_RESOLUTION_MEDIUM"},
    SCENE_FLASH_OCR: {"fps": 6.0, "media_resolution": "MEDIA_RESOLUTION_HIGH"},
    SCENE_EXHIBIT: {"fps": 4.0, "media_resolution": "MEDIA_RESOLUTION_HIGH"},
}


@dataclass
class SceneProbeResult:
    video_id: str
    status: str = "skipped"
    duration_sec: float = 0.0
    frames_sampled: int = 0
    cut_density_per_min: float = 0.0
    face_coverage_mean: Optional[float] = None
    dominant_scene: str = SCENE_LECTURE
    recommended_fps: float = 1.0
    recommended_media_resolution: str = "MEDIA_RESOLUTION_LOW"
    notes: str = ""
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _probe_opencv(video_path: Path, *, max_frames: int = 48) -> dict[str, Any]:
    """Sample frames; estimate cut density via mean absolute diff."""
    import cv2  # type: ignore
    import numpy as np

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return {"error": "unreadable", "frames": 0}

    native_fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
    n_total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = n_total / native_fps if native_fps > 0 and n_total > 0 else 0.0
    step = max(1, int(round(native_fps)))  # ~1 native frame/sec for probe

    prev_gray = None
    diffs: list[float] = []
    face_hits = 0
    sampled = 0
    idx = 0

    while sampled < max_frames:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if prev_gray is not None:
            diff = float(np.mean(cv2.absdiff(prev_gray, gray)))
            diffs.append(diff)
        prev_gray = gray
        sampled += 1
        idx += step

    cap.release()

    cut_density = 0.0
    if diffs and duration > 0:
        # Heuristic: large diffs ≈ cuts; normalize per minute
        threshold = max(8.0, float(np.percentile(diffs, 75)) if diffs else 8.0)
        cuts = sum(1 for d in diffs if d >= threshold)
        cut_density = (cuts / max(duration / 60.0, 1e-6))

    return {
        "duration_sec": duration,
        "frames_sampled": sampled,
        "cut_density_per_min": round(cut_density, 3),
        "face_coverage_mean": (face_hits / sampled) if sampled else None,
    }


def classify_scene(
    *,
    cut_density_per_min: float = 0.0,
    face_coverage_mean: Optional[float] = None,
    genre_hint: Optional[str] = None,
) -> str:
    """Map probe metrics (+ optional genre) to a scene class."""
    gh = (genre_hint or "").strip().lower()
    if gh in ("ad", "ugc", "short"):
        return SCENE_FLASH_OCR
    if gh in ("deposition", "hearing", "legal"):
        return SCENE_EXHIBIT
    if gh in ("earnings", "webcast", "ir"):
        return SCENE_EXHIBIT
    if cut_density_per_min >= 12:
        return SCENE_MONTAGE
    if cut_density_per_min >= 6:
        return SCENE_FLASH_OCR
    if face_coverage_mean is not None and face_coverage_mean < 0.25:
        return SCENE_EXHIBIT
    return SCENE_LECTURE


def resolve_sampling_policy(
    scene_class: str,
    *,
    overrides: Optional[dict[str, Any]] = None,
) -> tuple[float, str]:
    """Return (fps, media_resolution) for a scene class."""
    base = dict(DEFAULT_POLICY.get(scene_class, DEFAULT_POLICY[SCENE_LECTURE]))
    if overrides:
        base.update({k: v for k, v in overrides.items() if v is not None})
    return float(base["fps"]), str(base["media_resolution"])


def probe_and_recommend(
    video_id: str,
    *,
    video_path: Optional[str | Path] = None,
    genre_hint: Optional[str] = None,
    max_probe_frames: int = 48,
) -> SceneProbeResult:
    """
    Probe local video (if readable) and return recommended fps/resolution.

    Without video_path or OpenCV, returns lecture defaults with status=skipped.
    """
    result = SceneProbeResult(video_id=video_id)
    if not video_path:
        result.notes = "No video_path; using lecture defaults"
        result.recommended_fps, result.recommended_media_resolution = resolve_sampling_policy(
            SCENE_LECTURE
        )
        return result

    path = Path(video_path)
    if not path.is_file():
        result.notes = f"Missing file: {path}"
        result.recommended_fps, result.recommended_media_resolution = resolve_sampling_policy(
            SCENE_LECTURE
        )
        return result

    try:
        metrics = _probe_opencv(path, max_frames=max_probe_frames)
    except ImportError:
        result.notes = "opencv not available; using genre hint or lecture defaults"
        scene = classify_scene(genre_hint=genre_hint)
        result.dominant_scene = scene
        result.recommended_fps, result.recommended_media_resolution = resolve_sampling_policy(scene)
        result.status = "skipped"
        return result
    except Exception as exc:  # noqa: BLE001
        result.notes = f"probe failed: {exc}"
        result.recommended_fps, result.recommended_media_resolution = resolve_sampling_policy(
            SCENE_LECTURE
        )
        return result

    if metrics.get("error"):
        result.notes = str(metrics["error"])
        result.recommended_fps, result.recommended_media_resolution = resolve_sampling_policy(
            SCENE_LECTURE
        )
        return result

    result.status = "ok"
    result.duration_sec = float(metrics.get("duration_sec") or 0.0)
    result.frames_sampled = int(metrics.get("frames_sampled") or 0)
    result.cut_density_per_min = float(metrics.get("cut_density_per_min") or 0.0)
    result.face_coverage_mean = metrics.get("face_coverage_mean")

    scene = classify_scene(
        cut_density_per_min=result.cut_density_per_min,
        face_coverage_mean=result.face_coverage_mean,
        genre_hint=genre_hint,
    )
    result.dominant_scene = scene
    result.recommended_fps, result.recommended_media_resolution = resolve_sampling_policy(scene)
    return result


def effective_segment_fps(
    video_id: str,
    *,
    video_path: Optional[str | Path] = None,
    genre_hint: Optional[str] = None,
    env_fps: Optional[float] = None,
    adaptive_enabled: bool = True,
) -> tuple[float, str, SceneProbeResult]:
    """
    Choose fps for Gemini videoMetadata.

    Priority: explicit env_fps override > adaptive probe > 1.0 default.
    Returns (fps, media_resolution, probe_result).
    """
    if env_fps is not None and env_fps > 0:
        probe = SceneProbeResult(
            video_id=video_id,
            status="env_override",
            recommended_fps=float(env_fps),
            recommended_media_resolution="MEDIA_RESOLUTION_LOW",
            notes=f"SEGMENT_FPS env override={env_fps}",
        )
        return float(env_fps), probe.recommended_media_resolution, probe

    if not adaptive_enabled:
        probe = SceneProbeResult(
            video_id=video_id,
            status="disabled",
            recommended_fps=1.0,
            recommended_media_resolution="MEDIA_RESOLUTION_LOW",
            notes="ADAPTIVE_SAMPLING disabled",
        )
        return 1.0, probe.recommended_media_resolution, probe

    probe = probe_and_recommend(video_id, video_path=video_path, genre_hint=genre_hint)
    return probe.recommended_fps, probe.recommended_media_resolution, probe
