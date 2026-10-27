"""Unified claim / evidence / action record for video and disclosure packs."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    source: str = ""
    quote: str = ""
    date: Optional[str] = None
    url: Optional[str] = None


class ClaimRiskRecord(BaseModel):
    """One object an evidence registry can store for any domain pack."""

    claim_id: str
    domain_pack: str
    claim_text: str
    claim_kind: str = "source_backed_fact"
    evidence: list[EvidenceItem] = Field(default_factory=list)
    verdict_or_action: str = "UNRESOLVED"
    confidence: Optional[float] = None
    residual_reliance_risk: Optional[str] = None
    source_lane: str = "video"


def from_video_claim(claim: Any, *, domain_pack: str = "consumer_craap") -> ClaimRiskRecord:
    """Map a VerityNgn Claim (or dict) onto the shared registry shape."""
    if hasattr(claim, "model_dump"):
        data = claim.model_dump()
    elif isinstance(claim, dict):
        data = claim
    else:
        data = {"claim_text": str(claim)}

    evidence: list[EvidenceItem] = []
    for item in data.get("evidence") or []:
        if isinstance(item, dict):
            evidence.append(
                EvidenceItem(
                    source=str(item.get("source_name") or item.get("source") or ""),
                    quote=str(item.get("text") or item.get("quote") or "")[:400],
                    date=item.get("date"),
                    url=item.get("url"),
                )
            )

    verdict = data.get("verdict_or_action")
    if not verdict:
        vr = data.get("verification_result")
        if isinstance(vr, dict):
            verdict = str(vr.get("result") or "UNRESOLVED")
        else:
            verdict = str(data.get("initial_assessment") or "UNRESOLVED")

    return ClaimRiskRecord(
        claim_id=str(data.get("claim_id") or "0"),
        domain_pack=domain_pack,
        claim_text=str(data.get("claim_text") or ""),
        claim_kind=str(data.get("claim_kind") or "source_backed_fact"),
        evidence=evidence,
        verdict_or_action=verdict.upper(),
        residual_reliance_risk=data.get("residual_reliance_risk"),
        source_lane="video",
    )


def from_disclosure(finding: dict[str, Any], *, domain_pack: str = "securities_disclosure") -> ClaimRiskRecord:
    """Map an rfkit finding onto the shared registry shape."""
    evidence = [
        EvidenceItem(
            source=str(finding.get("item1a_source") or "Item 1A"),
            quote=str(finding.get("item1a_quote") or finding.get("hedged") or "")[:400],
            date=finding.get("item1a_date"),
            url=finding.get("item1a_url"),
        ),
        EvidenceItem(
            source=str(finding.get("record_source") or "own record"),
            quote=str(finding.get("record_quote") or finding.get("materialized") or "")[:400],
            date=finding.get("record_date"),
            url=finding.get("record_url"),
        ),
    ]
    action = str(finding.get("action") or finding.get("verdict_or_action") or "KEEP")
    return ClaimRiskRecord(
        claim_id=str(finding.get("claim_id") or finding.get("pair_id") or "disclosure"),
        domain_pack=domain_pack,
        claim_text=str(finding.get("claim_text") or finding.get("hedged") or ""),
        claim_kind="disclosure_pair",
        evidence=evidence,
        verdict_or_action=action.upper(),
        confidence=finding.get("confidence") or finding.get("score"),
        residual_reliance_risk=finding.get("residual_reliance_risk"),
        source_lane="disclosure",
    )
