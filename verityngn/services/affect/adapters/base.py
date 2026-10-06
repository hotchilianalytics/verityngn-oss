"""Vendor adapter base for affect / emotion APIs."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class VendorAffectResult:
    vendor: str
    construct_type: str = "interpreted"
    vectors: dict[str, float] = field(default_factory=dict)
    raw: Optional[dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": f"vendor:{self.vendor}",
            "construct_type": self.construct_type,
            "vectors": self.vectors,
            "raw": self.raw,
            "error": self.error,
        }


class AffectVendorAdapter(ABC):
    name: str

    @abstractmethod
    def analyze_audio(self, audio_path: str, **kwargs: Any) -> VendorAffectResult:
        raise NotImplementedError
