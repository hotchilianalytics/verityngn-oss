"""millionways.ai Thorsten-4 adapter (first partner).

API calls are opt-in via MILLIONWAYS_API_KEY + MILLIONWAYS_API_URL.
Without credentials, returns a structured stub suitable for demos.
"""
from __future__ import annotations

import os
from typing import Any

from verityngn.services.affect.adapters.base import AffectVendorAdapter, VendorAffectResult


class MillionwaysAdapter(AffectVendorAdapter):
    name = "millionways"

    def __init__(self, api_url: str | None = None, api_key: str | None = None) -> None:
        self.api_url = api_url or os.environ.get("MILLIONWAYS_API_URL", "https://api.millionways.ai/v1/thorsten4")
        self.api_key = api_key or os.environ.get("MILLIONWAYS_API_KEY")

    def analyze_audio(self, audio_path: str, **kwargs: Any) -> VendorAffectResult:
        if not self.api_key:
            return VendorAffectResult(
                vendor=self.name,
                vectors={"valence": 0.0, "arousal": 0.0, "dominance": 0.0},
                raw={"status": "stub", "audio_path": audio_path, "note": "Set MILLIONWAYS_API_KEY to enable"},
                error=None,
            )
        try:
            import httpx  # optional at runtime

            with open(audio_path, "rb") as f:
                files = {"file": (os.path.basename(audio_path), f, "audio/wav")}
                headers = {"Authorization": f"Bearer {self.api_key}"}
                resp = httpx.post(self.api_url, headers=headers, files=files, timeout=60.0)
                resp.raise_for_status()
                data = resp.json()
            vectors = {
                "valence": float(data.get("valence", 0.0)),
                "arousal": float(data.get("arousal", 0.0)),
                "dominance": float(data.get("dominance", 0.0)),
            }
            return VendorAffectResult(vendor=self.name, vectors=vectors, raw=data)
        except Exception as exc:  # noqa: BLE001 — surface as vendor error, don't crash sleeve
            return VendorAffectResult(vendor=self.name, vectors={}, error=str(exc))
