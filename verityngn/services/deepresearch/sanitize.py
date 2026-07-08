"""
Counter-intelligence sanitizer for report JSON (OSS).

Strips self-referential evidence and unsafe citation URLs.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from verityngn.services.reputation.url_safety import (
    sanitize_report_dict_urls,
    sanitize_url_list_in_text,
)

logger = logging.getLogger(__name__)


def sanitize_report_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
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
        "counter-intel sanitize: kept=%d dropped=%d self-referential evidence items",
        kept,
        dropped,
    )
    return sanitized


def count_claims(raw_data: Dict[str, Any]) -> int:
    claims = (raw_data or {}).get("claims_breakdown", [])
    return len(claims) if isinstance(claims, list) else 0
