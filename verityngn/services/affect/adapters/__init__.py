"""Affect vendor adapters."""
from __future__ import annotations

from verityngn.services.affect.adapters.audeering_vad import (
    AudEeringVADAdapter,
    extract_dimensional_affect,
)
from verityngn.services.affect.adapters.base import AffectVendorAdapter, VendorAffectResult
from verityngn.services.affect.adapters.millionways import MillionwaysAdapter

__all__ = [
    "AffectVendorAdapter",
    "VendorAffectResult",
    "MillionwaysAdapter",
    "AudEeringVADAdapter",
    "extract_dimensional_affect",
]
