"""Optional vision sleeve — MediaPipe Face Landmarker and related cues.

Congruence / delivery-risk / authenticity cues only — not a lie detector.
Not for employment, HR, or education screening.
"""
from __future__ import annotations

from verityngn.services.vision.adapters.mediapipe import MediaPipeAdapter, NOT_FOR_EMPLOYMENT
from verityngn.services.vision.story_arc import ContinuitySummary, summarize_continuity
from verityngn.services.vision.adaptive_sampler import SceneProbeResult, effective_segment_fps, probe_and_recommend
from verityngn.services.vision.exhibit_tracker import ExhibitMap, build_exhibit_map, persist_exhibit_map

__all__ = [
    "MediaPipeAdapter",
    "NOT_FOR_EMPLOYMENT",
    "ContinuitySummary",
    "summarize_continuity",
    "SceneProbeResult",
    "effective_segment_fps",
    "probe_and_recommend",
    "ExhibitMap",
    "build_exhibit_map",
    "persist_exhibit_map",
]
