"""Authenticity vendor / open adapters."""
from __future__ import annotations

from typing import Any


class CorsoundAdapter:
    """Corsound AI voice deepfake check — stub until API key."""

    name = "corsound"

    def analyze(self, audio_path: str, **kwargs: Any) -> dict[str, Any]:
        return {
            "source": f"vendor:{self.name}",
            "construct_type": "interpreted",
            "status": "stub",
            "score": 1.0,
            "audio_path": audio_path,
            "note": "Stub pass; set CORSOUND_API_KEY to enable live checks.",
        }


class OpenVisualDeepfakeAdapter:
    """Placeholder for open-source visual deepfake detector."""

    name = "open_visual_deepfake"

    def analyze(self, video_path: str, **kwargs: Any) -> dict[str, Any]:
        return {
            "source": f"open:{self.name}",
            "construct_type": "measured",
            "status": "stub",
            "score": 1.0,
            "video_path": video_path,
        }


class C2PAAdapter:
    """C2PA provenance check stub."""

    name = "c2pa"

    def analyze(self, asset_path: str, **kwargs: Any) -> dict[str, Any]:
        return {
            "source": f"open:{self.name}",
            "construct_type": "measured",
            "status": "stub",
            "score": 1.0,
            "asset_path": asset_path,
            "note": "No C2PA manifest parsed in MVP.",
        }
