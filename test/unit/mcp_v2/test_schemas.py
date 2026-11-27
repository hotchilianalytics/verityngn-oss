"""Tool contracts, the extended ClaimRiskRecord, and vocabulary locks."""

from __future__ import annotations

import json
import re

import pytest
from jsonschema import Draft202012Validator

from verityngn.agent.mcp_v2 import ui
from verityngn.agent.mcp_v2.contracts import TOOL_NAMES, published_tools
from verityngn.agent.mcp_v2.schema_defs import bundle, definitions_document, ref
from verityngn.agent.mcp_v2.server import INSTRUCTIONS
from verityngn.schemas.claim_risk import from_disclosure, from_video_claim, neutral_verdict

EXPECTED_TOOLS = [
    "register_document", "assess_selection", "assess_document", "verify_quote", "resolve_entity",
    "list_company_videos", "analyze_video", "news_window", "filings_search", "get_filing_section",
    "sanctions_match", "search_litigation", "compose_assessment", "record_review_action", "get_record",
    "get_report", "export_assessment",
]
BANNED = re.compile(r"\b(truthful\w*|truthfulness|lie|lies|lying|liar|lie[- ]detect\w*|decepti\w+|deceiv\w+)\b", re.I)


def _walk(node, path=()):
    if isinstance(node, dict):
        for k, v in node.items():
            yield path + (k,), k, v
            yield from _walk(v, path + (k,))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk(v, path + (i,))


def test_tool_list_is_complete_and_deterministic():
    assert TOOL_NAMES == EXPECTED_TOOLS
    assert [t["name"] for t in published_tools()] == EXPECTED_TOOLS


@pytest.mark.parametrize("tool", published_tools(), ids=lambda t: t["name"])
def test_published_schemas_are_valid_and_self_contained(tool):
    for key in ("inputSchema", "outputSchema"):
        schema = tool[key]
        Draft202012Validator.check_schema(schema)
        refs = [v for _, k, v in _walk(schema) if k == "$ref"]
        assert all(r.startswith("#/$defs/") for r in refs), refs
        for r in refs:
            assert r.split("/")[-1] in schema["$defs"]
    assert tool["inputSchema"]["type"] == "object"
    assert set(tool["annotations"]) >= {"readOnlyHint", "openWorldHint"}


def test_ui_links_point_at_real_widgets():
    linked = {t["name"]: t["_meta"]["ui"]["resourceUri"] for t in published_tools() if "_meta" in t}
    assert linked == {
        "assess_selection": "ui://splitrisk/assessment",
        "assess_document": "ui://splitrisk/coverage",
        "list_company_videos": "ui://splitrisk/results",
        "analyze_video": "ui://splitrisk/video",
        "news_window": "ui://splitrisk/results",
        "compose_assessment": "ui://splitrisk/coverage",
        "get_report": "ui://splitrisk/workpaper",
    }
    for uri in set(linked.values()):
        assert uri.rsplit("/", 1)[-1] in ui.WIDGET_NAMES


def test_annotations_follow_contract():
    by = {t["name"]: t["annotations"] for t in published_tools()}
    assert by["register_document"] == {"readOnlyHint": False, "idempotentHint": True, "openWorldHint": False}
    assert by["record_review_action"]["destructiveHint"] is False
    assert by["verify_quote"]["idempotentHint"] is True


def test_no_computed_likelihood_anywhere():
    allowed = {
        ("ClaimRiskRecord", "judgment"),
        ("record_review_action", "judgment_likelihood"),
    }
    hits = set()
    for tool in published_tools():
        for path, key, _ in _walk(tool):
            if "likelihood" in str(key).lower():
                owner = "ClaimRiskRecord" if "ClaimRiskRecord" in path else tool["name"]
                hits.add((owner, "judgment" if "judgment" in path else key))
    assert hits <= allowed, hits
    rec = definitions_document()["$defs"]["ClaimRiskRecord"]
    assert "likelihood" not in rec["properties"]
    assert rec["properties"]["confidence"]["description"] == "Evidence confidence; not likelihood"
    assert rec["properties"]["judgment"]["properties"]["label"] == {"const": "Reviewer judgment, not computed"}


def test_coverage_matrix_has_no_numeric_cells():
    cov = definitions_document()["$defs"]["CoverageCell"]
    assert set(cov["properties"]) == {"state", "quote", "date", "url", "record_id", "allegation"}
    assert all(v.get("type") != "number" for v in cov["properties"].values())


def test_banned_vocabulary_absent_from_tool_text_and_widgets():
    blobs = [json.dumps(published_tools()), INSTRUCTIONS] + [ui.html(n) for n in ui.WIDGET_NAMES]
    for blob in blobs:
        assert not BANNED.search(blob), BANNED.search(blob).group(0)


def _record(**kw):
    base = {
        "claim_id": "sr:rec:acme/abc",
        "domain_pack": "securities_disclosure",
        "claim_text": "We may experience incidents",
        "claim_kind": "source_backed_fact",
        "evidence": [{"source": "8-K", "quote": "q", "date": "2024-01-19", "url": "https://x"}],
        "verdict_or_action": "SUPPORTED",
    }
    base.update(kw)
    return base


def test_record_rules_enforced_by_schema():
    v = Draft202012Validator(bundle(ref("ClaimRiskRecord")))
    assert v.is_valid(_record())
    assert not v.is_valid(_record(claim_kind="prediction")), "SUPPORTED only on source_backed_fact"
    assert not v.is_valid(_record(verdict_or_action="CONTESTED", claim_kind="reasoned_opinion"))
    assert v.is_valid(_record(verdict_or_action="UNRESOLVED", claim_kind="prediction"))
    assert not v.is_valid(_record(allegation=True, visibility="public")), "Allegation implies internal"
    assert not v.is_valid(_record(allegation=True)), "Allegation needs an explicit internal visibility"
    assert v.is_valid(_record(allegation=True, visibility="internal"))
    assert not v.is_valid(_record(judgment={"likelihood": "likely", "label": "computed", "entered_by": "x", "entered_at": "2026-10-28T00:00:00Z"}))
    assert not v.is_valid(_record(verdict_or_action="TRUE"))


def test_legacy_record_helpers_still_work():
    video = from_video_claim({"claim_id": 7, "claim_text": "c", "initial_assessment": "CONTESTED", "claim_kind": "source_backed_fact"})
    disc = from_disclosure({"pair_id": "msft-1", "hedged": "h", "materialized": "m", "action": "Rewrite", "score": 0.8})
    assert set(video.model_dump()) == set(disc.model_dump())
    assert disc.claim_kind == "disclosure_pair"
    assert "judgment" in video.model_dump() and video.judgment is None


def test_neutral_verdict_mapping():
    assert neutral_verdict("TRUE", claim_kind="source_backed_fact") == "SUPPORTED"
    assert neutral_verdict("highly_likely_to_be_false", claim_kind="source_backed_fact") == "CONTESTED"
    assert neutral_verdict("LIKELY_TRUE", claim_kind="prediction") == "UNRESOLVED"
    assert neutral_verdict("Move to General Risk Factors", claim_kind="disclosure_pair") == "MOVE"
    assert neutral_verdict("nonsense", claim_kind="source_backed_fact") == "UNRESOLVED"
