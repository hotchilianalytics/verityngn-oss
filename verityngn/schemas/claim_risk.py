"""Unified claim / evidence / action record for video and disclosure packs.

Schema 2.0 (verityngn-mcp v2) adds anchors, coverage, severity, review and
provenance. Every new field is optional so 1.x records still load; the MCP v2
server always fills them. There is deliberately no computed likelihood field:
``confidence`` is evidence confidence, and likelihood exists only as a
human-entered ``judgment``.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

SCHEMA_VERSION = "2.0"

VERDICTS = ("SUPPORTED", "CONTESTED", "UNRESOLVED")
ACTIONS = ("REWRITE", "KEEP", "MOVE", "REMOVE", "ADD")

_LEGACY_VERDICTS = {
    "TRUE": "SUPPORTED",
    "LIKELY_TRUE": "SUPPORTED",
    "MOSTLY_TRUE": "SUPPORTED",
    "HIGHLY_LIKELY_TO_BE_TRUE": "SUPPORTED",
    "SUPPORTED": "SUPPORTED",
    "FALSE": "CONTESTED",
    "LIKELY_FALSE": "CONTESTED",
    "MOSTLY_FALSE": "CONTESTED",
    "HIGHLY_LIKELY_TO_BE_FALSE": "CONTESTED",
    "CONTESTED": "CONTESTED",
    "MOVE TO GENERAL RISK FACTORS": "MOVE",
    "MOVE_TO_GENERAL": "MOVE",
    "REMOVE AS STALE": "REMOVE",
    "REMOVE_AS_STALE": "REMOVE",
}


class EvidenceItem(BaseModel):
    source: str = ""
    quote: str = ""
    date: Optional[str] = None
    url: Optional[str] = None
    source_id: Optional[str] = None
    source_class: Optional[str] = None
    stance: Optional[str] = None
    visibility: Optional[str] = None
    anchor: Optional[dict[str, Any]] = None
    match_mode: Optional[str] = None
    quote_sha256: Optional[str] = None
    allegation: bool = False
    licence: Optional[dict[str, Any]] = None
    retrieved_at: Optional[str] = None


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

    schema_version: Optional[str] = None
    doc_id: Optional[str] = None
    target: Optional[dict[str, Any]] = None
    entity_id: Optional[str] = None
    category: Optional[str] = None
    item_1a_heading: Optional[str] = None
    severity: Optional[dict[str, Any]] = None
    coverage: Optional[dict[str, Any]] = None
    visibility: Optional[str] = None
    role_view: Optional[list[str]] = None
    allegation: bool = False
    junior_obvious: Optional[dict[str, Any]] = None
    lag_clock: Optional[dict[str, Any]] = None
    illustrative_rewrite: Optional[str] = None
    review: Optional[dict[str, Any]] = None
    judgment: Optional[dict[str, Any]] = None
    no_promote: bool = False
    disclaimers: Optional[list[str]] = None
    provenance: Optional[dict[str, Any]] = None

    def to_wire(self) -> dict[str, Any]:
        """JSON shape for MCP v2 (``urn:splitrisk:schema:v1#/$defs/ClaimRiskRecord``)."""
        return self.model_dump(mode="json", exclude_none=True)


def neutral_verdict(raw: Any, *, claim_kind: str) -> str:
    """Map legacy truthfulness labels onto Supported / Contested / Unresolved.

    Supported and Contested are only allowed on ``source_backed_fact``.
    """
    key = str(raw or "").strip().upper().replace("-", "_")
    mapped = _LEGACY_VERDICTS.get(key) or _LEGACY_VERDICTS.get(key.replace("_", " "))
    if mapped is None:
        mapped = key if key in VERDICTS + ACTIONS else "UNRESOLVED"
    if mapped in ("SUPPORTED", "CONTESTED") and claim_kind != "source_backed_fact":
        return "UNRESOLVED"
    return mapped


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
