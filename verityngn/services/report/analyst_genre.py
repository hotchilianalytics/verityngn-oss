"""Analyst-video report genre: SIFT / method review in place of CRAAP.

Consumer factual videos keep CRAAP. When the claim mix is dominated by
data-derived, causal, and predictive statements, reports use a method-and-
reliance review (SIFT + ICD dual metrics) instead of library-source CRAAP.
"""
from __future__ import annotations

from typing import Any, Dict, List

from verityngn.workflows.claim_kind import (
    ClaimKind,
    claim_kind_display_label,
    get_claim_kind,
)

ANALYST_KINDS = {
    ClaimKind.DATA_DERIVED_INFERENCE.value,
    ClaimKind.CAUSAL_ANALYTICAL.value,
    ClaimKind.PREDICTION.value,
}


def infer_report_genre(claims: List[Any]) -> str:
    """Return ``analyst`` or ``consumer_factual`` from the claim-kind mix."""
    if not claims:
        return "consumer_factual"
    n = 0
    analystish = 0
    for c in claims:
        n += 1
        if get_claim_kind(c) in ANALYST_KINDS:
            analystish += 1
    if n and analystish / n >= 0.25:
        return "analyst"
    return "consumer_factual"


def _vr(claim: Any) -> Dict[str, Any]:
    vr = getattr(claim, "verification_result", None)
    if vr is None and isinstance(claim, dict):
        vr = claim.get("verification_result")
    return vr if isinstance(vr, dict) else {}


def build_sift_method_section(claims: List[Any]) -> List[str]:
    """Section 9 replacement for analyst videos (SIFT + residual reliance)."""
    lines: List[str] = [
        "## 9. Method & Reliance Review (SIFT)",
        "",
        "This video reads as **analyst / deep-data** work. Library CRAAP "
        "(Currency, Relevance, Authority, Accuracy, Purpose) is the wrong primary "
        "bar: method-backed dollar and percent claims are not journal articles. "
        "This section uses **SIFT** (Stop, Investigate, Find better coverage, Trace) "
        "plus dual metrics: likelihood, evidence confidence, and residual reliance risk.",
        "",
        "| Move | What we ask for this genre |",
        "|:-----|:---------------------------|",
        "| **Stop** | Do not score a modeled figure as a newspaper fact, and do not call it false only because no academic paper cites it. |",
        "| **Investigate the source** | Who produced the number (author workbook, LRO sheet, on-screen graphic, statute)? Is the method named? |",
        "| **Find better coverage** | Lateral check against the primary posting (revenue impact statement, bill text, hearing record), not a peer-review search. |",
        "| **Trace** | Can the on-screen $ or % be traced to a dated artifact the viewer could open? |",
        "",
    ]

    kind_counts: Dict[str, int] = {}
    high_residual = 0
    for c in claims or []:
        k = get_claim_kind(c)
        kind_counts[k] = kind_counts.get(k, 0) + 1
        residual = (
            getattr(c, "residual_reliance_risk", None)
            or _vr(c).get("residual_reliance_risk")
            or ""
        )
        if str(residual).lower() == "high":
            high_residual += 1

    lines.append("### Claim-type mix")
    lines.append("")
    lines.append("| Type | Count |")
    lines.append("|:-----|:-----:|")
    for k, n in sorted(kind_counts.items(), key=lambda x: -x[1]):
        lines.append(f"| {claim_kind_display_label(k)} | {n} |")
    lines.append("")
    if high_residual:
        lines.append(
            f"**Residual reliance headline:** {high_residual} claim(s) still **high** "
            "after this pass. Those are the ones a viewer should not treat as settled."
        )
    else:
        lines.append(
            "**Residual reliance headline:** no claim remains at high residual reliance risk."
        )
    lines.append("")
    lines.append(
        "Evidence confidence here means backing for the *judgment* (method named, "
        "sources agree), not how many peer-reviewed papers mention the topic."
    )
    lines.append("")
    return lines
