"""Story-arc / continuity summaries for risk-aligned vision cues.

Thin stub: face-coverage continuity when MediaPipe is available; otherwise
returns a skipped schema. Not a lie detector. Not for employment use.
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

NOT_FOR_EMPLOYMENT = (
    "Story-arc / continuity features are optional risk cues only. "
    "Not for employment, HR, or education screening."
)


@dataclass
class ContinuitySummary:
    video_id: str
    status: str = "skipped"
    schema_version: str = "0.1"
    face_coverage_mean: Optional[float] = None
    face_coverage_std: Optional[float] = None
    n_frames_sampled: int = 0
    talking_head_proxy: Optional[float] = None
    notes: str = ""
    disclaimer: str = NOT_FOR_EMPLOYMENT
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d

    def write_json(self, path: Path | str) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return path


def summarize_continuity(
    video_id: str,
    *,
    video_path: Optional[str | Path] = None,
    max_frames: int = 24,
) -> ContinuitySummary:
    """
    Sample frames and estimate face-coverage continuity via MediaPipe when present.

    Returns status=skipped if mediapipe/opencv unavailable or video unreadable.
    """
    summary = ContinuitySummary(video_id=video_id)
    if not video_path:
        summary.notes = "No video_path provided"
        return summary
    path = Path(video_path)
    if not path.is_file():
        summary.notes = f"Missing file: {path}"
        return summary

    try:
        from verityngn.services.vision.adapters.mediapipe import MediaPipeAdapter
    except Exception as exc:  # noqa: BLE001
        summary.notes = f"MediaPipe adapter import failed: {exc}"
        return summary

    adapter = MediaPipeAdapter()
    if not adapter.available():
        summary.notes = "mediapipe not installed (pip install 'verityngn[vision]')"
        return summary

    try:
        import cv2  # type: ignore
        import numpy as np
    except ImportError:
        summary.notes = "opencv not installed"
        return summary

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        summary.notes = "cv2 could not open video"
        return summary

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if frame_count <= 0:
        frame_count = max_frames * 10
    indices = np.linspace(0, max(frame_count - 1, 0), num=min(max_frames, max(frame_count, 1)))
    coverages: list[float] = []

    # Prefer adapter.analyze_frame / analyze if present; else skip measured path
    analyze = getattr(adapter, "analyze_image", None) or getattr(adapter, "analyze", None)

    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ok, frame = cap.read()
        if not ok or frame is None:
            continue
        cov = None
        if callable(analyze):
            try:
                # Many adapters expect RGB path or ndarray — try ndarray
                result = analyze(frame)
                if isinstance(result, dict):
                    cov = (
                        result.get("face_coverage")
                        or result.get("coverage")
                        or (result.get("summary") or {}).get("face_coverage")
                    )
            except Exception:  # noqa: BLE001
                cov = None
        if cov is None:
            # Heuristic fallback: skin-ish pixel fraction in center crop (weak proxy)
            h, w = frame.shape[:2]
            crop = frame[h // 4 : 3 * h // 4, w // 4 : 3 * w // 4]
            ycrcb = cv2.cvtColor(crop, cv2.COLOR_BGR2YCrCb)
            cr, cb = ycrcb[:, :, 1], ycrcb[:, :, 2]
            mask = (cr > 130) & (cr < 175) & (cb > 75) & (cb < 135)
            cov = float(mask.mean())
        try:
            coverages.append(float(cov))
        except (TypeError, ValueError):
            continue

    cap.release()
    summary.n_frames_sampled = len(coverages)
    if not coverages:
        summary.status = "skipped"
        summary.notes = "No frames sampled"
        return summary

    arr = np.asarray(coverages, dtype=float)
    summary.face_coverage_mean = float(arr.mean())
    summary.face_coverage_std = float(arr.std())
    # High mean + low std ⇒ talking-head-ish continuity
    summary.talking_head_proxy = float(
        max(0.0, min(1.0, summary.face_coverage_mean * (1.0 - min(1.0, summary.face_coverage_std * 2))))
    )
    summary.status = "ok"
    summary.notes = "continuity summary (heuristic + optional MediaPipe)"
    summary.extras = {"use_case": "V1_talking_head_vs_broll"}
    return summary
