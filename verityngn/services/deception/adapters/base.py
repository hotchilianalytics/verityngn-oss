"""Vendor adapters for licensed deception-adjacent constructs (stubs)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class DeceptionVendorAdapter(ABC):
    name: str

    @abstractmethod
    def analyze(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class NemesyscoAdapter(DeceptionVendorAdapter):
    """Nemesysco LVA — licensed; stub only until contract + API keys."""

    name = "nemesysco_lva"

    def analyze(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "source": f"vendor:{self.name}",
            "construct_type": "interpreted",
            "status": "stub",
            "note": "Licensed LVA construct; not enabled. Do not treat as veracity.",
            "input_keys": sorted(payload.keys()),
        }


class RevealenseAdapter(DeceptionVendorAdapter):
    """Revealense Illuminator — licensed facial/micro signals; stub."""

    name = "revealense_illuminator"

    def analyze(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "source": f"vendor:{self.name}",
            "construct_type": "interpreted",
            "status": "stub",
            "note": "Licensed Illuminator construct; not enabled.",
            "input_keys": sorted(payload.keys()),
        }
