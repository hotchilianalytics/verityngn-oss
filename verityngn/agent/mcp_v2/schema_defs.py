"""Shared JSON Schema definitions: ``urn:splitrisk:schema:v1``.

Tool schemas reference these as ``urn:splitrisk:schema:v1#/$defs/<Name>``.
MCP 2026-07-28 tells clients to reject schemas whose ``$ref`` they cannot
resolve and never to fetch remote ones, so :func:`bundle` rewrites every such
reference to a local ``#/$defs/<Name>`` and copies the definitions it needs
into the published schema.
"""

from __future__ import annotations

import copy
from typing import Any

SCHEMA_ID = "urn:splitrisk:schema:v1"
_PREFIX = SCHEMA_ID + "#/$defs/"

SOURCE_CLASSES = ["own", "staff", "docket", "short", "spoken"]
CATEGORIES = [
    "operational",
    "financial_liquidity",
    "legal_regulatory_litigation",
    "cybersecurity",
    "reputational_media",
    "sanctions_aml",
    "governance",
    "macro_market",
    "general",
]
TOOL_ERROR_CODES = [
    "LOCK_WINDOW",
    "LOCK_CHANNEL_NOT_OWNED",
    "LOCK_NO_LICENCE",
    "LOCK_ROLE",
    "NEEDS_CONFIRMATION",
    "NOT_FOUND",
    "QUOTA",
    "UPSTREAM",
    "ANCHOR_UNRESOLVED",
    "INVALID",
    "ENGINE_NOT_INSTALLED",
]
JUDGMENT_LABEL = "Reviewer judgment, not computed"


def _ref(name: str) -> dict[str, str]:
    return {"$ref": _PREFIX + name}


DEFS: dict[str, Any] = {
    "DocId": {"type": "string", "pattern": "^sr:doc:[a-z0-9-]+/[a-f0-9]{16,64}$"},
    "RecordId": {"type": "string", "pattern": "^sr:rec:[a-z0-9-]+/[A-Za-z0-9_-]+$"},
    "ReportId": {"type": "string", "pattern": "^sr:rep:[a-z0-9-]+/[A-Za-z0-9_-]+$"},
    "EntityId": {"type": "string", "pattern": "^sr:ent:[A-Za-z0-9_-]+$"},
    "IsoDate": {"type": "string", "format": "date"},
    "Window": {
        "type": "object",
        "required": ["from", "to"],
        "properties": {"from": _ref("IsoDate"), "to": _ref("IsoDate")},
        "description": "Closed range. Rejected if longer than 366 days or if 'to' is in the future.",
    },
    "DomainPack": {"enum": ["securities_disclosure", "analyst_sift", "legal_deposition"]},
    "SourceClass": {"enum": SOURCE_CLASSES},
    "Stance": {"enum": ["supports_exposure", "contradicts_disclosure", "context"]},
    "Visibility": {"enum": ["public", "internal", "private"]},
    "Category": {"enum": CATEGORIES},
    "Severity": {
        "type": "object",
        "required": ["level", "basis"],
        "properties": {
            "level": {"enum": ["low", "medium", "high"]},
            "basis": {"enum": ["engine", "reviewer"]},
            "rule": {"type": "string", "description": "Engine rule ID that set the level, e.g. SEV-OWN-PAIR"},
            "rationale": {"type": "string", "maxLength": 500},
        },
    },
    "ToolError": {
        "type": "object",
        "required": ["code", "message"],
        "properties": {
            "code": {"enum": TOOL_ERROR_CODES},
            "message": {"type": "string"},
            "alternative": {"type": "string", "description": "Allowed action to offer the user instead"},
            "details": {"type": "object"},
        },
    },
    "Target": {
        "type": "object",
        "required": ["source", "scope"],
        "properties": {
            "source": {
                "type": "string",
                "description": "doc_id; or urn:splitrisk:video:youtube:{video_id}; or a canonical URL",
            },
            "scope": {"enum": ["span", "section", "document", "time_range"]},
            "selector": {"type": "array", "items": _ref("Selector")},
            "section": {
                "type": "object",
                "properties": {
                    "item": {"type": "string"},
                    "heading_path": {"type": "array", "items": {"type": "string"}},
                },
            },
            "source_hash": {"type": "string"},
            "anchor_status": {"enum": ["exact", "fuzzy", "approximate", "orphaned"], "description": "Output only"},
        },
    },
    "Selector": {
        "oneOf": [
            {
                "type": "object",
                "required": ["type", "exact"],
                "properties": {
                    "type": {"const": "TextQuoteSelector"},
                    "exact": {"type": "string"},
                    "prefix": {"type": "string", "maxLength": 64},
                    "suffix": {"type": "string", "maxLength": 64},
                },
            },
            {
                "type": "object",
                "required": ["type", "start", "end"],
                "properties": {
                    "type": {"const": "TextPositionSelector"},
                    "start": {"type": "integer", "minimum": 0},
                    "end": {"type": "integer", "minimum": 0},
                },
            },
            {
                "type": "object",
                "required": ["type", "conformsTo", "value"],
                "properties": {
                    "type": {"const": "FragmentSelector"},
                    "conformsTo": {"enum": ["http://tools.ietf.org/rfc/rfc3778", "http://www.w3.org/TR/media-frags/"]},
                    "value": {"type": "string"},
                    "refinedBy": {"type": "object"},
                },
            },
            {
                "type": "object",
                "required": ["type", "startSelector", "endSelector"],
                "properties": {
                    "type": {"const": "RangeSelector"},
                    "startSelector": {"type": "object"},
                    "endSelector": {"type": "object"},
                },
            },
        ]
    },
    "CoverageCell": {
        "type": "object",
        "required": ["state"],
        "properties": {
            "state": {"enum": ["none", "hit", "junior_obvious"]},
            "quote": {"type": "string", "maxLength": 400},
            "date": {"type": "string", "format": "date"},
            "url": {"type": "string"},
            "record_id": _ref("RecordId"),
            "allegation": {"type": "boolean"},
        },
    },
    "CoverageMatrix": {
        "type": "object",
        "required": ["columns", "rows"],
        "properties": {
            "columns": {"const": SOURCE_CLASSES},
            "rows": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["heading", "cells", "severity"],
                    "properties": {
                        "heading": {"type": "string"},
                        "category": _ref("Category"),
                        "severity": _ref("Severity"),
                        "cells": {
                            "type": "object",
                            "propertyNames": _ref("SourceClass"),
                            "additionalProperties": _ref("CoverageCell"),
                        },
                    },
                },
            },
            "uncovered_spoken": {"type": "array", "items": _ref("RecordId")},
            "context_records": {"type": "array", "items": _ref("RecordId")},
        },
    },
    "EvidenceItem": {
        "type": "object",
        "required": ["source", "quote", "date", "url"],
        "properties": {
            "source": {"type": "string", "description": "Human label, e.g. 'MSFT 8-K Item 1.05'"},
            "quote": {"type": "string", "maxLength": 400},
            "date": {"type": "string", "format": "date"},
            "url": {"type": "string"},
            "source_id": {
                "type": "string",
                "description": "accession+item | video_id+t | article URI | OpenSanctions id | docket id",
            },
            "source_class": _ref("SourceClass"),
            "stance": _ref("Stance"),
            "visibility": _ref("Visibility"),
            "anchor": _ref("Target"),
            "match_mode": {"enum": ["exact", "fuzzy", "failed"]},
            "quote_sha256": {"type": "string"},
            "allegation": {"type": "boolean", "default": False},
            "licence": {
                "type": "object",
                "properties": {
                    "provider": {"type": "string"},
                    "display_limit": {"type": "string", "description": "e.g. 'excerpt <=400 chars', 'live only'"},
                },
            },
            "retrieved_at": {"type": "string", "format": "date-time"},
        },
    },
    "ClaimRiskRecord": {
        "type": "object",
        "required": ["claim_id", "domain_pack", "claim_text", "claim_kind", "evidence", "verdict_or_action"],
        "properties": {
            "schema_version": {"const": "2.0"},
            "claim_id": _ref("RecordId"),
            "domain_pack": _ref("DomainPack"),
            "claim_text": {"type": "string"},
            "claim_kind": {
                "enum": [
                    "source_backed_fact",
                    "data_derived_inference",
                    "causal_analytical",
                    "reasoned_opinion",
                    "prediction",
                    "unverified_assertion",
                    "disclosure_pair",
                    "uncovered_spoken",
                    "softening",
                ]
            },
            "evidence": {"type": "array", "items": _ref("EvidenceItem")},
            "verdict_or_action": {
                "enum": ["SUPPORTED", "CONTESTED", "UNRESOLVED", "REWRITE", "KEEP", "MOVE", "REMOVE", "ADD"]
            },
            "confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
                "description": "Evidence confidence; not likelihood",
            },
            "residual_reliance_risk": {"type": "string"},
            "source_lane": {"enum": ["video", "disclosure", "news", "filing", "sanctions"]},
            "doc_id": _ref("DocId"),
            "target": _ref("Target"),
            "entity_id": _ref("EntityId"),
            "category": _ref("Category"),
            "item_1a_heading": {"type": "string"},
            "severity": _ref("Severity"),
            "coverage": {
                "type": "object",
                "propertyNames": _ref("SourceClass"),
                "additionalProperties": _ref("CoverageCell"),
            },
            "visibility": _ref("Visibility"),
            "role_view": {
                "type": "array",
                "items": {"enum": ["analyst", "gc", "junior"]},
                "description": "Views that show this record by default; a hint, not access control",
            },
            "allegation": {"type": "boolean", "default": False},
            "junior_obvious": {
                "type": "object",
                "properties": {"flag": {"type": "boolean"}, "reason": {"type": "string"}},
            },
            "lag_clock": {
                "type": "object",
                "properties": {
                    "event_date": {"type": "string", "format": "date"},
                    "filing_date": {"type": "string", "format": "date"},
                    "days": {"type": "integer"},
                },
            },
            "illustrative_rewrite": {"type": "string", "description": "For counsel to edit; never a final draft"},
            "review": {
                "type": "object",
                "properties": {
                    "state": {"enum": ["proposed", "accepted", "edited", "rejected"]},
                    "version": {"type": "integer"},
                    "history": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "action": {"type": "string"},
                                "by": {"type": "string"},
                                "role": {"type": "string"},
                                "at": {"type": "string", "format": "date-time"},
                                "note": {"type": "string"},
                                "evidence_hash": {"type": "string"},
                            },
                        },
                    },
                },
            },
            "judgment": {
                "type": "object",
                "required": ["likelihood", "label", "entered_by", "entered_at"],
                "properties": {
                    "likelihood": {"enum": ["remote", "possible", "likely"]},
                    "label": {"const": JUDGMENT_LABEL},
                    "entered_by": {"type": "string"},
                    "entered_at": {"type": "string", "format": "date-time"},
                },
            },
            "no_promote": {"type": "boolean", "default": False},
            "disclaimers": {
                "type": "array",
                "items": {"enum": ["not_legal_advice", "allegation_only", "llm_editorial", "youtube_editorial"]},
            },
            "provenance": {
                "type": "object",
                "properties": {
                    "tool": {"type": "string"},
                    "engine": {"enum": ["rfkit", "verityngn"]},
                    "engine_version": {"type": "string"},
                    "engine_commit": {"type": "string"},
                    "model": {"type": "string"},
                    "generated_at": {"type": "string", "format": "date-time"},
                },
            },
        },
        "allOf": [
            {
                "if": {
                    "properties": {"verdict_or_action": {"enum": ["SUPPORTED", "CONTESTED"]}},
                    "required": ["verdict_or_action"],
                },
                "then": {"properties": {"claim_kind": {"const": "source_backed_fact"}}},
            },
            {
                "if": {"properties": {"allegation": {"const": True}}, "required": ["allegation"]},
                "then": {"properties": {"visibility": {"const": "internal"}}, "required": ["visibility"]},
            },
        ],
    },
}


def definitions_document() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": SCHEMA_ID,
        "$defs": copy.deepcopy(DEFS),
    }


def ref(name: str) -> dict[str, str]:
    """Reference a shared definition from a tool schema."""
    if name not in DEFS:
        raise KeyError(name)
    return _ref(name)


def _localize(node: Any, needed: set[str]) -> Any:
    if isinstance(node, dict):
        out = {}
        for key, value in node.items():
            if key == "$ref" and isinstance(value, str) and value.startswith(_PREFIX):
                name = value[len(_PREFIX):]
                needed.add(name)
                out[key] = "#/$defs/" + name
            else:
                out[key] = _localize(value, needed)
        return out
    if isinstance(node, list):
        return [_localize(v, needed) for v in node]
    return node


def bundle(schema: dict[str, Any]) -> dict[str, Any]:
    """Return a self-contained copy of ``schema`` with local ``$defs``."""
    needed: set[str] = set()
    body = _localize(copy.deepcopy(schema), needed)
    defs: dict[str, Any] = {}
    pending = list(needed)
    while pending:
        name = pending.pop()
        if name in defs:
            continue
        inner: set[str] = set()
        defs[name] = _localize(copy.deepcopy(DEFS[name]), inner)
        pending.extend(n for n in inner if n not in defs)
    if defs:
        body.setdefault("$defs", {}).update(dict(sorted(defs.items())))
    return body
