"""Seed official legislature / agency URLs into Deep Research sanitize input.

Deprecated always-on Oregon static pack — delegates to domain-class
``primary_pack.py``. Kept for import back-compat.
"""
from __future__ import annotations

from typing import Any, Dict, List

from verityngn.services.deepresearch.primary_pack import (
    build_primary_pack,
    extract_bill_ids,
    inject_primary_pack,
)

__all__ = [
    "extract_bill_ids",
    "build_legislature_primary_pack",
    "inject_legislature_primaries",
]


def build_legislature_primary_pack(report: Dict[str, Any]) -> List[Dict[str, str]]:
    pack, _ = build_primary_pack(report)
    return pack


def inject_legislature_primaries(sanitized: Dict[str, Any]) -> Dict[str, Any]:
    return inject_primary_pack(sanitized)
