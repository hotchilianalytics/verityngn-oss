"""Claim-kind taxonomy for author-proof / opinion lanes (OSS v3 post-sb1507).

Separates sourceable factual claims from author-proof candidates and
interpretive / synthesized statements so report histograms stay factual
while still surfacing deeper-research and opinion sleeves.
"""
from __future__ import annotations

import logging
import re
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ClaimKind(str, Enum):
    FACTUAL_SOURCEABLE = "factual_sourceable"
    AUTHOR_PROOF_CANDIDATE = "author_proof_candidate"
    OPINION_OR_SYNTHESIS = "opinion_or_synthesis"
    NEW_REPORT_CONCLUSION = "new_report_conclusion"


# Excluded from core truthfulness histogram / overall headline denominators.
NON_CORE_KINDS = {
    ClaimKind.OPINION_OR_SYNTHESIS.value,
    ClaimKind.NEW_REPORT_CONCLUSION.value,
}

OPINION_MARKERS = (
    "should ",
    "must ",
    "ought ",
    "i believe",
    "we believe",
    "in my view",
    "in our view",
    "seems to",
    "appears that",
    "arguably",
    "suggests that",
    "implies that",
    "likely means",
    "the takeaway",
    "bottom line",
    "my conclusion",
    "our conclusion",
    "forecast",
    "will probably",
    "going to be",
)

AUTHOR_LOGIC_MARKERS = (
    "because ",
    "therefore",
    "which means",
    "this means",
    "as a result",
    "chain of",
    "implies",
    "thus ",
    "hence ",
    "so that",
    "conditioned on",
    "gut and stuff",
    "placeholder",
    "legislative concept",
    "rolling conformity",
    "decoupl",
)

FACTUAL_ANCHORS = (
    r"\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}\b",
    r"\b(?:19|20)\d{2}\b",
    r"\b(?:sb|hb|hr|s\.?\s*b\.?)\s*\d{2,5}\b",
    r"\bors\s+\d+",
    r"\barticle\s+[ivxlcdm]+\b",
    r"\b\d{1,3}(?:-\d{1,3})?\s+(?:vote|passed|voted)\b",
    r"\b\d+(?:,\d{3})*(?:\.\d+)?%",
    r"\b\$\d",
)


def classify_claim_kind(
    claim_text: str,
    *,
    source_type: Optional[str] = None,
    report_generated: bool = False,
) -> str:
    """Rule-based claim_kind classifier (no LLM)."""
    text = (claim_text or "").strip()
    if not text:
        return ClaimKind.FACTUAL_SOURCEABLE.value

    if report_generated or (source_type or "").lower() in {
        "report_synthesis",
        "report_generated",
        "verityngn_summary",
    }:
        return ClaimKind.NEW_REPORT_CONCLUSION.value

    lower = text.lower()
    opinion_hits = sum(1 for m in OPINION_MARKERS if m in lower)
    if opinion_hits >= 1 and not re.search(r"\b(?:act|bill|statute|ors|signed|passed|vote)\b", lower):
        return ClaimKind.OPINION_OR_SYNTHESIS.value
    if opinion_hits >= 2:
        return ClaimKind.OPINION_OR_SYNTHESIS.value

    factual_hits = sum(1 for pat in FACTUAL_ANCHORS if re.search(pat, text, re.IGNORECASE))
    logic_hits = sum(1 for m in AUTHOR_LOGIC_MARKERS if m in lower)

    # Chained legislative / causal logic with sparse hard anchors → author proof path.
    if logic_hits >= 2 and factual_hits <= 1:
        return ClaimKind.AUTHOR_PROOF_CANDIDATE.value
    if logic_hits >= 1 and factual_hits == 0 and len(text) > 120:
        return ClaimKind.AUTHOR_PROOF_CANDIDATE.value

    return ClaimKind.FACTUAL_SOURCEABLE.value


def annotate_claim_kind(claim: Dict[str, Any]) -> Dict[str, Any]:
    """Stamp claim_kind, verification_lane, and initial deeper-research flag."""
    if not isinstance(claim, dict):
        return claim
    text = claim.get("claim_text") or claim.get("claim") or ""
    kind = classify_claim_kind(
        text,
        source_type=claim.get("source_type"),
        report_generated=bool(claim.get("report_generated_inference")),
    )
    claim["claim_kind"] = kind
    if kind == ClaimKind.FACTUAL_SOURCEABLE.value:
        claim["verification_lane"] = "factual"
        claim.setdefault("needs_deeper_research", False)
        claim["source_path_status"] = claim.get("source_path_status") or "pending"
    elif kind == ClaimKind.AUTHOR_PROOF_CANDIDATE.value:
        claim["verification_lane"] = "author_proof"
        claim["needs_deeper_research"] = True
        claim["source_path_status"] = "incomplete"
        claim["author_logic_detected"] = True
    elif kind == ClaimKind.OPINION_OR_SYNTHESIS.value:
        claim["verification_lane"] = "opinion"
        claim["needs_deeper_research"] = False
        claim["source_path_status"] = "not_applicable"
    else:
        claim["verification_lane"] = "report_inference"
        claim["needs_deeper_research"] = True
        claim["source_path_status"] = "report_generated"
        claim["report_generated_inference"] = True
    return claim


def annotate_claims_kind(claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for c in claims or []:
        if isinstance(c, dict):
            out.append(annotate_claim_kind(c))
        else:
            out.append(c)
    kinds = {}
    for c in out:
        if isinstance(c, dict):
            k = c.get("claim_kind", "unknown")
            kinds[k] = kinds.get(k, 0) + 1
    logger.info("claim_kind distribution: %s", kinds)
    return out


def get_claim_kind(claim: Any) -> str:
    if isinstance(claim, dict):
        return (claim.get("claim_kind") or ClaimKind.FACTUAL_SOURCEABLE.value).lower()
    kind = getattr(claim, "claim_kind", None)
    if kind:
        return str(kind).lower()
    vr = getattr(claim, "verification_result", None)
    if isinstance(vr, dict) and vr.get("claim_kind"):
        return str(vr.get("claim_kind")).lower()
    return ClaimKind.FACTUAL_SOURCEABLE.value


def is_core_factual_claim(claim: Any) -> bool:
    return get_claim_kind(claim) not in NON_CORE_KINDS


def needs_deeper_research(claim: Any) -> bool:
    if isinstance(claim, dict):
        if claim.get("needs_deeper_research"):
            return True
        vr = claim.get("verification_result") or {}
        if isinstance(vr, dict) and vr.get("needs_deeper_research"):
            return True
        return get_claim_kind(claim) in {
            ClaimKind.AUTHOR_PROOF_CANDIDATE.value,
            ClaimKind.NEW_REPORT_CONCLUSION.value,
        }
    if getattr(claim, "needs_deeper_research", False):
        return True
    vr = getattr(claim, "verification_result", None)
    if isinstance(vr, dict) and vr.get("needs_deeper_research"):
        return True
    return get_claim_kind(claim) in {
        ClaimKind.AUTHOR_PROOF_CANDIDATE.value,
        ClaimKind.NEW_REPORT_CONCLUSION.value,
    }
