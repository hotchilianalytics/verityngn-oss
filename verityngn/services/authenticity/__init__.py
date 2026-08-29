"""Authenticity sleeve — deepfake / provenance gate before affect scoring."""
from __future__ import annotations

from verityngn.services.authenticity.gate import AuthenticityResult, run_authenticity_gate

__all__ = ["AuthenticityResult", "run_authenticity_gate"]
