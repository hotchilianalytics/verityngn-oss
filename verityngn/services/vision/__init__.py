"""Optional vision sleeve — MediaPipe Face Landmarker and related cues.

Congruence / delivery-risk / authenticity cues only — not a lie detector.
Not for employment, HR, or education screening.
"""
from __future__ import annotations

from verityngn.services.vision.adapters.mediapipe import MediaPipeAdapter, NOT_FOR_EMPLOYMENT

__all__ = ["MediaPipeAdapter", "NOT_FOR_EMPLOYMENT"]
