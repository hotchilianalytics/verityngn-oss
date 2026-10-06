"""
Fusion sleeve — align modalities, Plutchik taxonomy, story arcs, cross-modal congruence,
Gemini multi-sense interpreted track.
"""
from __future__ import annotations

from verityngn.services.fusion.derailment import score_derailment
from verityngn.services.fusion.gemini_multisense import run_gemini_multisense
from verityngn.services.fusion.plutchik import closure, write_taxonomy_csv
from verityngn.services.fusion.run_multisense import run_multisense
from verityngn.services.fusion.schema import build_fused_index, write_fused_index

__all__ = [
    "build_fused_index",
    "write_fused_index",
    "closure",
    "write_taxonomy_csv",
    "run_gemini_multisense",
    "run_multisense",
    "score_derailment",
]
