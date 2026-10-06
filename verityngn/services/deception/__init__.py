"""
Deception-risk sleeve — congruence / delivery-risk only.

Never emits a \"lying\" verdict. Output is ``deception_risk`` band + evidence.
"""
from __future__ import annotations

from verityngn.services.deception.risk import DeceptionRiskResult, assess_deception_risk

__all__ = ["DeceptionRiskResult", "assess_deception_risk"]
