"""Tool contracts for verityngn-mcp v2 (SplitRisk concept, Round 2 section 2.4).

Each entry keeps the concept doc's input schema, output schema, annotations and
MCP Apps link. Published schemas are bundled (see ``schema_defs.bundle``).
"""

from __future__ import annotations

from typing import Any

from verityngn.agent.mcp_v2.schema_defs import bundle, ref

UI_MIME = "text/html;profile=mcp-app"

SCOPES = {
    "read": "splitrisk.read",
    "assess": "splitrisk.assess",
    "search": "splitrisk.search",
    "video": "splitrisk.video",
    "propose": "splitrisk.review.propose",
    "decide": "splitrisk.review.decide",
    "export": "splitrisk.export",
}
ALL_SCOPES = list(SCOPES.values())

ROLE_DEFAULT_SCOPES = {
    "analyst": ["read", "assess", "search", "video", "propose", "export"],
    "gc": ["read", "assess", "search", "video", "decide", "export"],
    "junior": ["read", "assess", "search", "propose", "export"],
    "admin": list(SCOPES),
}

_PENDING = {
    "type": "object",
    "required": ["report_id", "status"],
    "properties": {
        "report_id": ref("ReportId"),
        "status": {"const": "running"},
        "records_ready": {"type": "integer"},
    },
}

_RECORDS = {"type": "array", "items": ref("ClaimRiskRecord")}

_TOOLS: list[dict[str, Any]] = [
    {
        "name": "register_document",
        "title": "Register a document",
        "description": (
            "Make a document addressable. Pass its text, a public URL (EDGAR, issuer site or article) "
            "or an app upload reference, plus a rights attestation. Returns a doc_id, the sha256 of the "
            "normalized text that every position refers to, and an outline. Registering the same bytes "
            "twice returns the same doc_id."
        ),
        "scope": "assess",
        "inputSchema": {
            "type": "object",
            "oneOf": [{"required": ["text"]}, {"required": ["url"]}, {"required": ["upload_ref"]}],
            "required": ["media_type", "rights"],
            "additionalProperties": False,
            "properties": {
                "text": {"type": "string", "maxLength": 2000000},
                "url": {"type": "string", "format": "uri", "description": "EDGAR, issuer site or article URL"},
                "upload_ref": {"type": "string", "description": "Signed object-store reference from the app"},
                "media_type": {
                    "enum": [
                        "application/pdf",
                        "text/html",
                        "text/plain",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        "text/vtt",
                    ]
                },
                "title": {"type": "string"},
                "rights": {
                    "enum": ["public_source", "own_or_client_document", "licensed_ai_use_permitted"],
                    "description": "User attestation. There is deliberately no value for licensed content without AI rights.",
                },
            },
        },
        "outputSchema": {
            "type": "object",
            "required": ["doc_id", "source_hash", "outline"],
            "properties": {
                "doc_id": ref("DocId"),
                "document_uri": {"type": "string", "description": "splitrisk://documents/{doc_id}: normalized text, outline and offset tables"},
                "source_hash": {"type": "string", "description": "sha256 of the normalized text that all positions refer to"},
                "normalizer": {"type": "string", "description": "e.g. docling-2.x+sr-norm-1"},
                "length": {"type": "integer"},
                "outline": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "heading_path": {"type": "array", "items": {"type": "string"}},
                            "item": {"type": "string", "description": "SEC Item, e.g. 1A"},
                            "start": {"type": "integer"},
                            "end": {"type": "integer"},
                        },
                    },
                },
            },
        },
        "annotations": {"readOnlyHint": False, "idempotentHint": True, "openWorldHint": False},
    },
    {
        "name": "assess_selection",
        "title": "Assess a selection",
        "description": (
            "Assess a span, a section or a time range of a registered document for disclosure and delivery "
            "risk. Returns claim-risk records anchored to the passage, with coverage and a severity tag. "
            "Never computes likelihood."
        ),
        "scope": "assess",
        "task": "optional",
        "inputSchema": {
            "type": "object",
            "required": ["target", "domain_pack"],
            "additionalProperties": False,
            "properties": {
                "target": ref("Target"),
                "domain_pack": ref("DomainPack"),
                "context_chars": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 4000,
                    "default": 1200,
                    "description": "Text on each side passed to the engine for context; findings stay inside the target",
                },
                "entity_id": {**ref("EntityId"), "description": "Issuer whose own record is searched for same-incident pairs"},
            },
        },
        "outputSchema": {
            "oneOf": [
                {
                    "type": "object",
                    "required": ["records", "target"],
                    "properties": {
                        "target": {**ref("Target"), "description": "Echoed with anchor_status set"},
                        "records": _RECORDS,
                        "report_id": ref("ReportId"),
                    },
                },
                _PENDING,
            ]
        },
        "annotations": {"readOnlyHint": True, "openWorldHint": True},
        "ui": "ui://splitrisk/assessment",
    },
    {
        "name": "assess_document",
        "title": "Assess a whole document",
        "description": (
            "Assess a whole registered document. Long-running: returned as a task when the client supports "
            "the Tasks extension, otherwise as a report_id to poll with get_report. Output adds a coverage "
            "matrix across the five source classes."
        ),
        "scope": "assess",
        "task": "required",
        "inputSchema": {
            "type": "object",
            "required": ["doc_id", "domain_pack"],
            "additionalProperties": False,
            "properties": {
                "doc_id": ref("DocId"),
                "domain_pack": ref("DomainPack"),
                "entity_id": ref("EntityId"),
                "prior_doc_id": {**ref("DocId"), "description": "Last year's filing, or the previous version of a registration statement (DRS/A or S-1 against S-1/A), for softening and change detection"},
            },
        },
        "outputSchema": {
            "oneOf": [
                {
                    "type": "object",
                    "required": ["report_id", "records", "coverage"],
                    "properties": {
                        "report_id": ref("ReportId"),
                        "records": _RECORDS,
                        "coverage": ref("CoverageMatrix"),
                    },
                },
                _PENDING,
            ]
        },
        "annotations": {"readOnlyHint": True, "openWorldHint": True},
        "ui": "ui://splitrisk/coverage",
    },
    {
        "name": "verify_quote",
        "title": "Verify a quote",
        "description": (
            "Check that a quote appears in a source (a doc_id, an EDGAR URL or a registered URL). "
            "Returns exact, fuzzy or failed, with a score, the matched text, a character diff and an anchor."
        ),
        "scope": "assess",
        "inputSchema": {
            "type": "object",
            "required": ["quote", "source"],
            "additionalProperties": False,
            "properties": {
                "quote": {"type": "string", "maxLength": 4000},
                "source": {"type": "string", "description": "doc_id, EDGAR URL or registered URL"},
                "fuzzy_threshold": {"type": "number", "minimum": 0.5, "maximum": 1, "default": 0.9},
            },
        },
        "outputSchema": {
            "type": "object",
            "required": ["match_mode"],
            "properties": {
                "match_mode": {"enum": ["exact", "fuzzy", "failed"]},
                "score": {"type": "number"},
                "matched_text": {"type": "string"},
                "diff": {"type": "string", "description": "Character-level difference when fuzzy"},
                "quote_sha256": {"type": "string"},
                "target": ref("Target"),
            },
        },
        "annotations": {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": True},
    },
    {
        "name": "resolve_entity",
        "title": "Resolve an issuer",
        "description": (
            "Resolve a company name, ticker or SEC CIK to an entity ID before any directed query. "
            "Returns candidates with CIK, tickers and verified owned YouTube channels."
        ),
        "scope": "search",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "name": {"type": "string"},
                "ticker": {"type": "string"},
                "cik": {"type": "string", "pattern": "^[0-9]{1,10}$"},
            },
            "minProperties": 1,
        },
        "outputSchema": {
            "type": "object",
            "required": ["candidates"],
            "properties": {
                "candidates": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["entity_id", "name"],
                        "properties": {
                            "entity_id": ref("EntityId"),
                            "name": {"type": "string"},
                            "cik": {"type": "string"},
                            "tickers": {"type": "array", "items": {"type": "string"}},
                            "aliases": {"type": "array", "items": {"type": "string"}},
                            "owned_channels": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "platform": {"const": "youtube"},
                                        "channel_id": {"type": "string"},
                                        "verified_by": {"enum": ["issuer_site_link", "manual_review"]},
                                    },
                                },
                            },
                        },
                    },
                }
            },
        },
        "annotations": {"readOnlyHint": True, "openWorldHint": True},
    },
    {
        "name": "list_company_videos",
        "title": "List company videos",
        "description": (
            "List recent uploads from a channel the issuer owns (verified owned-channel registry only). "
            "Returns video IDs with titles and dates for display; only video_id is ever stored. "
            "Windows are at most 366 days and may not end in the future."
        ),
        "scope": "search",
        "inputSchema": {
            "type": "object",
            "required": ["entity_id"],
            "additionalProperties": False,
            "properties": {
                "entity_id": ref("EntityId"),
                "channel_id": {"type": "string", "description": "Must be in the entity's owned_channels"},
                "window": ref("Window"),
                "preset": {"enum": ["last_90_days", "last_reported_quarter", "since_last_10k"], "default": "last_90_days"},
                "max_results": {"type": "integer", "minimum": 1, "maximum": 50, "default": 25},
                "confirmed": {"type": "boolean", "default": False},
            },
        },
        "outputSchema": {
            "type": "object",
            "required": ["window", "videos"],
            "properties": {
                "window": ref("Window"),
                "videos": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["video_id"],
                        "properties": {
                            "video_id": {"type": "string", "pattern": "^[A-Za-z0-9_-]{11}$"},
                            "channel_id": {"type": "string"},
                            "title": {"type": "string"},
                            "published_at": {"type": "string", "format": "date-time"},
                        },
                    },
                },
            },
        },
        "annotations": {"readOnlyHint": True, "openWorldHint": True},
        "ui": "ui://splitrisk/results",
    },
    {
        "name": "analyze_video",
        "title": "Analyze a company video",
        "description": (
            "Extract spoken claims from one YouTube video by video_id (Gemini direct-URL path, no download) "
            "and return claim-risk records anchored by time range. Long-running: returned as a task when the "
            "client supports Tasks, otherwise as a report_id to poll with get_report."
        ),
        "scope": "video",
        "task": "required",
        "inputSchema": {
            "type": "object",
            "required": ["video_id", "domain_pack"],
            "additionalProperties": False,
            "properties": {
                "video_id": {"type": "string", "pattern": "^[A-Za-z0-9_-]{11}$"},
                "entity_id": ref("EntityId"),
                "domain_pack": ref("DomainPack"),
                "tier": {"enum": ["light", "full"], "default": "light"},
                "deep_research": {
                    "type": "boolean",
                    "default": False,
                    "description": "Requires the tenant's terms-rider acknowledgement on file",
                },
            },
        },
        "outputSchema": {
            "oneOf": [
                {
                    "type": "object",
                    "required": ["report_id", "records", "transcript_doc_id"],
                    "properties": {
                        "report_id": ref("ReportId"),
                        "transcript_doc_id": {
                            **ref("DocId"),
                            "description": "WebVTT transcript registered as a document, so records anchor by time range",
                        },
                        "records": _RECORDS,
                    },
                },
                _PENDING,
            ]
        },
        "annotations": {"readOnlyHint": True, "openWorldHint": True},
        "ui": "ui://splitrisk/video",
    },
    {
        "name": "news_window",
        "title": "News in a window",
        "description": (
            "Dated, attributed news for one resolved entity in a bounded window (at most 366 days, not in the "
            "future). Event Registry by default; GDELT only for windows inside the last three months. "
            "Short-seller publishers are flagged as Allegation. Nothing is scheduled or monitored."
        ),
        "scope": "search",
        "inputSchema": {
            "type": "object",
            "required": ["entity_id", "window"],
            "additionalProperties": False,
            "properties": {
                "entity_id": ref("EntityId"),
                "window": ref("Window"),
                "query": {"type": "string", "maxLength": 200, "description": "Topic filter, e.g. 'cyber incident'"},
                "langs": {"type": "array", "items": {"type": "string"}, "default": ["eng"]},
                "max_results": {"type": "integer", "minimum": 1, "maximum": 100, "default": 50},
                "confirmed": {"type": "boolean", "default": False},
            },
        },
        "outputSchema": {
            "type": "object",
            "required": ["provider", "window", "articles"],
            "properties": {
                "provider": {"enum": ["event_registry", "gdelt"]},
                "attribution": {"type": "string", "description": "Required citation text and link for the provider"},
                "window": ref("Window"),
                "articles": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["uri", "headline", "source", "date"],
                        "properties": {
                            "uri": {"type": "string"},
                            "headline": {"type": "string"},
                            "source": {"type": "string"},
                            "date": ref("IsoDate"),
                            "excerpt": {"type": "string", "maxLength": 400},
                            "url": {"type": "string", "format": "uri"},
                            "allegation": {"type": "boolean", "description": "True for short-seller publishers"},
                        },
                    },
                },
            },
        },
        "annotations": {"readOnlyHint": True, "openWorldHint": True},
        "ui": "ui://splitrisk/results",
    },
    {
        "name": "filings_search",
        "title": "Search SEC filings",
        "description": (
            "List an issuer's SEC filings by form inside a bounded window (EDGAR submissions index; EDGAR "
            "full-text search when a query is given), including registration statements and prospectuses "
            "(S-1, F-1, 424B, DRS). Staff comment letters are tagged source_class staff."
        ),
        "scope": "search",
        "inputSchema": {
            "type": "object",
            "required": ["cik", "forms", "window"],
            "additionalProperties": False,
            "properties": {
                "cik": {"type": "string", "pattern": "^[0-9]{1,10}$"},
                "forms": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "enum": [
                            "10-K", "10-Q", "8-K", "20-F", "6-K", "CORRESP", "UPLOAD", "DEF 14A",
                            "S-1", "S-1/A", "F-1", "F-1/A", "424B1", "424B3", "424B4", "DRS", "DRS/A",
                        ]
                    },
                    "description": "A base form also returns its amendments (S-1 includes S-1/A); an /A form returns amendments only.",
                },
                "window": ref("Window"),
                "query": {"type": "string", "maxLength": 200},
                "items": {"type": "array", "items": {"type": "string"}, "description": "8-K items, e.g. 1.05, 2.02"},
                "confirmed": {"type": "boolean", "default": False},
            },
        },
        "outputSchema": {
            "type": "object",
            "required": ["filings"],
            "properties": {
                "filings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["accession", "form", "filed_at", "url"],
                        "properties": {
                            "accession": {"type": "string"},
                            "form": {"type": "string"},
                            "items": {"type": "array", "items": {"type": "string"}},
                            "filed_at": ref("IsoDate"),
                            "url": {"type": "string", "format": "uri"},
                            "source_class": {"enum": ["own", "staff"]},
                        },
                    },
                }
            },
        },
        "annotations": {"readOnlyHint": True, "openWorldHint": True},
    },
    {
        "name": "get_filing_section",
        "title": "Open a filing section",
        "description": (
            "Fetch one SEC filing, register it as a document and return the target for one Item (1A, 1C, 7, or an "
            "8-K item such as 8-K:1.05) or, for registration statements and prospectuses, one section (risk-factors, "
            "use-of-proceeds, mdna, governance...), so the viewer can open it scrolled there."
        ),
        "scope": "search",
        "inputSchema": {
            "type": "object",
            "required": ["accession", "item"],
            "additionalProperties": False,
            "properties": {
                "accession": {"type": "string", "pattern": "^[0-9]{10}-[0-9]{2}-[0-9]{6}$"},
                "cik": {
                    "type": "string",
                    "pattern": "^[0-9]{1,10}$",
                    "description": "Registrant CIK. If omitted it is looked up on EDGAR; the accession prefix is often a filing agent, not the issuer.",
                },
                "item": {
                    "type": "string",
                    "description": "SEC Item (1A, 1C, 7, 8-K:1.05) or, for S-1, F-1, 424B and DRS filings, a prospectus section: "
                    "risk-factors, prospectus-summary, use-of-proceeds, mdna, business, governance, management, "
                    "executive-compensation, principal-stockholders, description-of-capital-stock, underwriting "
                    "(titles such as 'Risk Factors' also work; 1A, 7 and 1 map to risk-factors, mdna and business).",
                },
                "confirmed": {"type": "boolean", "default": False},
            },
        },
        "outputSchema": {
            "type": "object",
            "required": ["doc_id", "target"],
            "properties": {
                "doc_id": ref("DocId"),
                "document_uri": {"type": "string", "description": "splitrisk://documents/{doc_id}"},
                "target": ref("Target"),
                "url": {"type": "string"},
            },
        },
        "annotations": {"readOnlyHint": True, "openWorldHint": True},
    },
    {
        "name": "sanctions_match",
        "title": "Sanctions candidates",
        "description": (
            "Screen a named person or organisation against OpenSanctions. Results are candidates for human "
            "review, not determinations."
        ),
        "scope": "search",
        "inputSchema": {
            "type": "object",
            "required": ["name", "schema"],
            "additionalProperties": False,
            "properties": {
                "name": {"type": "string"},
                "schema": {"enum": ["Person", "Company", "Organization", "Vessel"]},
                "country": {"type": "string"},
                "birth_date": {"type": "string"},
                "confirmed": {"type": "boolean", "default": False},
            },
        },
        "outputSchema": {
            "type": "object",
            "required": ["candidates", "label"],
            "properties": {
                "label": {"const": "Candidates for human review, not determinations"},
                "candidates": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "opensanctions_id": {"type": "string"},
                            "caption": {"type": "string"},
                            "score": {"type": "number"},
                            "datasets": {"type": "array", "items": {"type": "string"}},
                            "url": {"type": "string", "format": "uri"},
                        },
                    },
                },
            },
        },
        "annotations": {"readOnlyHint": True, "openWorldHint": True},
    },
    {
        "name": "search_litigation",
        "title": "Search litigation (licence required)",
        "description": (
            "Docket search. Blocked until a CourtListener commercial agreement is on file for the tenant; "
            "until then it returns LOCK_NO_LICENCE."
        ),
        "scope": "search",
        "inputSchema": {
            "type": "object",
            "required": ["entity_id", "window"],
            "additionalProperties": False,
            "properties": {
                "entity_id": ref("EntityId"),
                "window": ref("Window"),
                "query": {"type": "string", "maxLength": 200},
                "confirmed": {"type": "boolean", "default": False},
            },
        },
        "outputSchema": {
            "type": "object",
            "required": ["dockets"],
            "properties": {"dockets": {"type": "array", "items": {"type": "object"}}},
        },
        "annotations": {"readOnlyHint": True, "openWorldHint": True},
    },
    {
        "name": "compose_assessment",
        "title": "Compose coverage",
        "description": (
            "Roll records into the five-column coverage matrix (own, staff, docket, short, spoken) with a "
            "severity tag per row. Each cell is a dated quote or nothing. Never produces a likelihood grid."
        ),
        "scope": "assess",
        "inputSchema": {
            "type": "object",
            "required": ["record_ids"],
            "additionalProperties": False,
            "properties": {
                "record_ids": {"type": "array", "items": ref("RecordId"), "maxItems": 2000},
                "group_by": {"enum": ["item_1a_heading", "category"], "default": "item_1a_heading"},
            },
        },
        "outputSchema": ref("CoverageMatrix"),
        "annotations": {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
        "ui": "ui://splitrisk/coverage",
    },
    {
        "name": "record_review_action",
        "title": "Review a record",
        "description": (
            "Workpaper write path. Juniors and analysts may only propose; accept, edit, reject and "
            "set_judgment are for general counsel. Every call appends to review.history; nothing is overwritten."
        ),
        "scope": ("propose", "decide"),
        "inputSchema": {
            "type": "object",
            "required": ["record_id", "action"],
            "additionalProperties": False,
            "properties": {
                "record_id": ref("RecordId"),
                "action": {"enum": ["propose", "accept", "edit", "reject", "set_judgment", "clear_judgment"]},
                "verdict_or_action": {"enum": ["REWRITE", "KEEP", "MOVE", "REMOVE", "ADD"]},
                "severity_level": {"enum": ["low", "medium", "high"]},
                "illustrative_rewrite": {"type": "string", "maxLength": 4000},
                "note": {"type": "string", "maxLength": 2000},
                "judgment_likelihood": {
                    "enum": ["remote", "possible", "likely"],
                    "description": "Only with set_judgment, GC role, and the workspace judgment column switched on",
                },
                "expected_version": {"type": "integer", "description": "Optimistic concurrency; rejected if stale"},
            },
        },
        "outputSchema": ref("ClaimRiskRecord"),
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False},
    },
    {
        "name": "get_record",
        "title": "Get a record",
        "description": "Read one claim-risk record with its full evidence and anchors.",
        "scope": "read",
        "inputSchema": {
            "type": "object",
            "required": ["record_id"],
            "additionalProperties": False,
            "properties": {"record_id": ref("RecordId")},
        },
        "outputSchema": ref("ClaimRiskRecord"),
        "annotations": {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
    },
    {
        "name": "get_report",
        "title": "Get a report",
        "description": (
            "Read a report: its status (running, complete or failed), the records ready so far and the "
            "coverage matrix. Use it to page partial results while a long job runs."
        ),
        "scope": "read",
        "inputSchema": {
            "type": "object",
            "required": ["report_id"],
            "additionalProperties": False,
            "properties": {"report_id": ref("ReportId")},
        },
        "outputSchema": {
            "type": "object",
            "required": ["report_id", "status", "records"],
            "properties": {
                "report_id": ref("ReportId"),
                "status": {"enum": ["running", "complete", "failed"]},
                "status_message": {"type": "string"},
                "records_ready": {"type": "integer"},
                "records": _RECORDS,
                "coverage": ref("CoverageMatrix"),
                "viewer_role": {"enum": ["analyst", "gc", "junior", "admin"]},
                "judgment_enabled": {"type": "boolean"},
                "error": ref("ToolError"),
            },
        },
        "annotations": {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
        "ui": "ui://splitrisk/workpaper",
    },
    {
        "name": "export_assessment",
        "title": "Export an assessment",
        "description": (
            "Export a report as JSON, Markdown, xlsx or a W3C Web Annotation collection. Short-seller "
            "allegations and private evidence are left out unless include_internal is true and the role allows it."
        ),
        "scope": "export",
        "inputSchema": {
            "type": "object",
            "required": ["report_id", "format"],
            "additionalProperties": False,
            "properties": {
                "report_id": ref("ReportId"),
                "format": {"enum": ["json", "md", "xlsx", "docx_comments", "w3c_annotations", "audit_pdf"]},
                "include_internal": {
                    "type": "boolean",
                    "default": False,
                    "description": "Short-seller allegations and private evidence are left out unless true and the role allows it",
                },
            },
        },
        "outputSchema": {
            "type": "object",
            "required": ["resource_uri"],
            "properties": {
                "resource_uri": {"type": "string", "description": "splitrisk://exports/{id}, expires in 24 hours"},
                "media_type": {"type": "string"},
                "expires_at": {"type": "string", "format": "date-time"},
            },
        },
        "annotations": {"readOnlyHint": True, "openWorldHint": False},
    },
]

TOOL_NAMES = [t["name"] for t in _TOOLS]
_BY_NAME = {t["name"]: t for t in _TOOLS}


def contract(name: str) -> dict[str, Any]:
    return _BY_NAME[name]


def required_scopes(name: str) -> list[str]:
    scope = _BY_NAME[name]["scope"]
    keys = scope if isinstance(scope, tuple) else (scope,)
    return [SCOPES[k] for k in keys]


def task_policy(name: str) -> str:
    return _BY_NAME[name].get("task", "never")


def published_tool(name: str) -> dict[str, Any]:
    """Tool definition as it appears in ``tools/list``."""
    spec = _BY_NAME[name]
    tool: dict[str, Any] = {
        "name": spec["name"],
        "title": spec["title"],
        "description": spec["description"],
        "inputSchema": bundle(spec["inputSchema"]),
        "outputSchema": bundle(spec["outputSchema"]),
        "annotations": dict(spec["annotations"]),
    }
    if spec.get("ui"):
        tool["_meta"] = {"ui": {"resourceUri": spec["ui"]}}
    return tool


def published_tools() -> list[dict[str, Any]]:
    return [published_tool(n) for n in TOOL_NAMES]
