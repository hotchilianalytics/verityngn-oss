"""
Affect sleeve — prosody, disfluency, text sentiment, exuberance.

Tier-1 open measured features only in the core path. Vendor emotion APIs
live under ``adapters/`` and must be labeled ``construct_type: interpreted``.
"""
from __future__ import annotations

from verityngn.services.affect.extract import AffectResult, extract_affect_for_report

__all__ = ["AffectResult", "extract_affect_for_report"]
