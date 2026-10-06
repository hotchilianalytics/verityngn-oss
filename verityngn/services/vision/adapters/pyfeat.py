"""Py-Feat adapter — prefer Detectorv2 multitask (AU + valence/arousal + gaze + pose).

Optional import; returns None when py-feat is not installed so offline pipelines stay green.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


def _run_detector_v2(video_path: Path, **kwargs: Any) -> Optional[dict[str, Any]]:
    try:
        from feat import Detector  # type: ignore
    except ImportError:
        try:
            from pyfeat import Detector  # type: ignore
        except ImportError:
            return None

    try:
        # Detectorv2 API (py-feat ≥0.7): single multitask network
        detector = Detector(device=kwargs.get("device", "cpu"))
        # Some versions expose Detectorv2 explicitly
        if hasattr(detector, "__class__") and "v1" in detector.__class__.__name__.lower():
            try:
                from feat import Detectorv2  # type: ignore

                detector = Detectorv2(device=kwargs.get("device", "cpu"))
            except Exception:  # noqa: BLE001
                pass

        result = detector.detect_video(str(video_path))
        # Fex dataframe → summary dict
        summary: dict[str, Any] = {"backend": "pyfeat", "n_frames": int(getattr(result, "shape", [0])[0])}
        cols = list(getattr(result, "columns", []))
        au_cols = [c for c in cols if str(c).startswith("AU")]
        if au_cols:
            means = {c: float(result[c].mean()) for c in au_cols[:20]}
            summary["action_units_mean"] = means
        for key in ("valence", "arousal", "happiness", "sadness", "anger", "fear", "surprise", "disgust", "neutral"):
            if key in cols:
                summary[key] = float(result[key].mean())
        # Gaze / pose if present
        for key in ("gaze_0_x", "gaze_0_y", "pitch", "yaw", "roll"):
            if key in cols:
                summary[key] = float(result[key].mean())
        summary["construct_type"] = "measured"
        return summary
    except Exception as exc:  # noqa: BLE001
        logger.info("[pyfeat] detect_video failed: %s", exc)
        return None


def try_action_units(video_id: str, **kwargs: Any) -> Optional[Any]:
    """
    Attempt Py-Feat Detectorv2 on a local video path.

    kwargs may include ``video_path``. Returns None when backend unavailable.
    """
    path = kwargs.pop("video_path", None) or kwargs.pop("path", None)
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        return None
    return _run_detector_v2(p, **kwargs)


def try_full_fex(video_path: str | Path, **kwargs: Any) -> Optional[dict[str, Any]]:
    """Public helper for vision/extract.py orchestration."""
    return try_action_units("local", video_path=str(video_path), **kwargs)
