"""
Counter-intelligence sanitizer for the Deep Research pass.

Ported faithfully from the vetted ``platinum_pipeline.py`` ``sanitize_data``:
strip self-referential evidence so the model never cites the subject's own
PR/marketing as independent "proof". Operates on a deep copy; the original
``{video_id}_report.json`` is never mutated.

Also strips unsafe citation URLs so the grounded model cannot re-cite them.
"""
from __future__ import annotations

import copy
import logging
from typing import Any, Dict

from verityngn.services.reputation.url_safety import (
    sanitize_report_dict_urls,
    sanitize_url_list_in_text,
)
from verityngn.services.report.display_labels import is_visual_only_claim

logger = logging.getLogger(__name__)


def sanitize_report_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply the counter-intelligence filter and URL safety filter.

    For every claim in ``claims_breakdown``, keep only evidence items whose
    ``self_referential`` flag is explicitly ``False``. Items missing the flag,
    or with a truthy/self-referential flag, are dropped.

    Unsafe citation URLs are removed from sources lists and prose fields.

    Returns a sanitized deep copy suitable for ``1_sanitized_input.json``.
    """
    if not isinstance(raw_data, dict):
        raise TypeError(f"sanitize_report_data expects a dict, got {type(raw_data)!r}")

    sanitized = sanitize_report_dict_urls(raw_data)
    claims = sanitized.get("claims_breakdown", [])
    if not isinstance(claims, list):
        return sanitized

    dropped = 0
    kept = 0
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        verification = claim.get("verification_result", {})
        if not isinstance(verification, dict):
            continue
        evidence_list = verification.get("evidence", [])
        if isinstance(evidence_list, list):
            clean_evidence = [
                ev for ev in evidence_list
                if isinstance(ev, dict) and ev.get("self_referential") is False
            ]
            dropped += len(evidence_list) - len(clean_evidence)
            kept += len(clean_evidence)
            verification["evidence"] = clean_evidence
        elif isinstance(evidence_list, str):
            verification["evidence"] = sanitize_url_list_in_text(evidence_list)

    logger.info(
        "[deep-research] counter-intel sanitize: kept=%d dropped=%d self-referential evidence items",
        kept,
        dropped,
    )

    visual_only: list[dict[str, Any]] = []
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        st = claim.get("source_type")
        if is_visual_only_claim(st):
            visual_only.append(
                {
                    "claim_text": claim.get("claim_text"),
                    "source_type": st,
                    "timestamp": claim.get("timestamp"),
                    "speaker": claim.get("speaker"),
                }
            )
    if visual_only:
        sanitized["visual_only_claims"] = visual_only
        sanitized["visual_only_claim_count"] = len(visual_only)

    # Author-proof / opinion sleeves for Deep Research to prioritize (report.html §6.3/6.4).
    deeper_research_claims = []
    interpretive_claims = []
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        kind = (claim.get("claim_kind")
                or (claim.get("verification_result") or {}).get("claim_kind")
                or "")
        needs = bool(
            claim.get("needs_deeper_research")
            or (claim.get("verification_result") or {}).get("needs_deeper_research")
        )
        entry = {
            "claim_text": claim.get("claim_text"),
            "claim_kind": kind or None,
            "timestamp": claim.get("timestamp"),
            "needs_deeper_research": needs,
        }
        if kind in {"opinion_or_synthesis", "new_report_conclusion"}:
            interpretive_claims.append(entry)
        elif needs or kind == "author_proof_candidate":
            deeper_research_claims.append(entry)
    if deeper_research_claims:
        sanitized["deeper_research_claims"] = deeper_research_claims
        sanitized["deeper_research_claim_count"] = len(deeper_research_claims)
    if interpretive_claims:
        sanitized["interpretive_claims"] = interpretive_claims
        sanitized["interpretive_claim_count"] = len(interpretive_claims)

    return sanitized


def count_claims(raw_data: Dict[str, Any]) -> int:
    """Number of claims in the report (used by the min-claims cost guard)."""
    claims = (raw_data or {}).get("claims_breakdown", [])
    return len(claims) if isinstance(claims, list) else 0
