"""Fixes from the SplitRisk app's end-to-end run (internal/splitrisk-app-mcp-alignment.md)."""

from __future__ import annotations

import json
from pathlib import Path

from verityngn.agent.mcp_v2 import documents, norm_vectors
from verityngn.agent.mcp_v2.adapters import edgar as edgar_mod
from verityngn.agent.mcp_v2.auth import Principal
from verityngn.agent.mcp_v2.config import ServerConfig
from verityngn.agent.mcp_v2.server import McpServer
from verityngn.agent.mcp_v2.store import MemoryStore

from .conftest import HEDGED, TENK, Client, FakeDisclosure, fake_adapters, make_server, output_valid

VECTORS = Path(documents.__file__).resolve().parent / "data" / "sr-norm-1.vectors.json"


# ------------------------------------------------------------- sr-norm-1


def test_published_vectors_match_the_code():
    assert json.loads(VECTORS.read_text(encoding="utf-8")) == json.loads(json.dumps(norm_vectors.build()))


def test_each_vector_round_trips():
    data = json.loads(VECTORS.read_text(encoding="utf-8"))
    assert data["definition"]["name"] == "sr-norm-1"
    ids = {v["id"] for v in data["vectors"]}
    assert {"tenk-excerpt", "astral", "line-separators", "zero-width", "blank-lines"} <= ids
    for v in data["vectors"]:
        out = documents.normalize_text(v["input"])
        assert out == v["normalized"], v["id"]
        assert documents.source_hash(out) == v["source_hash"]
        for q in v["quotes"]:
            assert out[q["start"]:q["end"]] == q["exact"]
            assert out.encode("utf-16-le")[2 * q["start_utf16"]:2 * q["end_utf16"]].decode("utf-16-le") == q["exact"]
        if v["normalized"]:
            doc = documents.register(MemoryStore(), tenant="acme", media_type="text/plain", rights="public_source", text=v["input"])
            assert doc.doc_id == v["doc_id_for_tenant_acme"] and doc.source_hash == v["source_hash"]
    tenk = next(v for v in data["vectors"] if v["id"] == "tenk-excerpt")
    assert "\n\n" in tenk["normalized"], "sr-norm-1 keeps line breaks"
    astral = next(v for v in data["vectors"] if v["id"] == "astral")
    assert astral["length_utf16"] == astral["length"] + 1


def test_vectors_and_documents_are_resources(client, doc_id):
    listing = client.rpc("resources/list")["resources"]
    assert any(r["uri"] == "splitrisk://normalizer/sr-norm-1" for r in listing)
    res = client.rpc("resources/read", {"uri": "splitrisk://normalizer/sr-norm-1"})
    assert res["cacheScope"] == "public" and json.loads(res["contents"][0]["text"])["definition"]["name"] == "sr-norm-1"

    reg = client.ok("register_document", {"text": TENK, "media_type": "text/plain", "rights": "public_source"})
    assert reg["document_uri"] == f"splitrisk://documents/{reg['doc_id']}"
    body = client.rpc("resources/read", {"uri": reg["document_uri"]})
    assert body["cacheScope"] == "private"
    doc = json.loads(body["contents"][0]["text"])
    assert doc["source_hash"] == reg["source_hash"] and doc["normalizer"] == "sr-norm-1"
    assert doc["text"][doc["text"].index(HEDGED):].startswith(HEDGED)
    assert doc["outline"] == reg["outline"] and doc["pages"] == [] and doc["positions"] == "Unicode code points"
    templates = {t["uriTemplate"] for t in client.rpc("resources/templates/list")["resourceTemplates"]}
    assert "splitrisk://documents/{doc_id}" in templates
    other = client.raw("resources/read", {"uri": reg["document_uri"]}, token="dev:other:analyst")[1]
    assert other["error"]["code"] == -32602


# ------------------------------------------------- get_filing_section CIK


class _Edgar:
    def __init__(self, efts_ciks):
        self.efts_ciks = efts_ciks
        self.urls: list[str] = []

    def __call__(self, url, **kw):
        self.urls.append(url)
        if "efts.sec.gov" in url:
            hits = [{"_id": "0001193125-24-000001:x8k.htm", "_source": {"adsh": "0001193125-24-000001", "ciks": self.efts_ciks}}] if self.efts_ciks else []
            return {"hits": {"hits": hits}}
        if "CIK0000000001.json" in url:
            return {"filings": {"recent": {"accessionNumber": ["0001193125-24-000001"], "filingDate": ["2024-01-19"],
                                           "form": ["8-K"], "primaryDocument": ["x8k.htm"], "items": ["1.05"]}}}
        if "CIK0001193125.json" in url:
            return {"filings": {"recent": {"accessionNumber": [], "filingDate": [], "form": [], "primaryDocument": [], "items": []}}}
        raise AssertionError(url)


def _filing_client(monkeypatch, efts_ciks):
    rec = _Edgar(efts_ciks)
    monkeypatch.setattr(edgar_mod, "request_json", rec)
    monkeypatch.setattr(edgar_mod, "request", lambda url, **kw: b"<p>ITEM 1.05 MATERIAL CYBERSECURITY INCIDENTS</p><p>Detected.</p>")
    return Client(make_server(adapters=fake_adapters(edgar=edgar_mod.EdgarClient()))), rec


def test_filing_section_resolves_issuer_not_filing_agent(monkeypatch):
    client, rec = _filing_client(monkeypatch, ["0000000001"])
    out = client.ok("get_filing_section", {"accession": "0001193125-24-000001", "item": "8-K:1.05"})
    output_valid("get_filing_section", out)
    assert out["url"] == "https://www.sec.gov/Archives/edgar/data/1/000119312524000001/x8k.htm"
    assert not any("CIK0001193125" in u or "/data/1193125/" in u for u in rec.urls)


def test_filing_section_with_several_registrants_asks_for_cik(monkeypatch):
    client, _ = _filing_client(monkeypatch, ["0000000001", "0000000002"])
    err = client.err("get_filing_section", {"accession": "0001193125-24-000001", "item": "8-K:1.05"})
    assert err["code"] == "INVALID" and err["details"]["ciks"] == ["1", "2"] and "cik" in err["alternative"]


def test_filing_section_never_falls_back_to_an_agent_prefix(monkeypatch):
    client, rec = _filing_client(monkeypatch, [])
    err = client.err("get_filing_section", {"accession": "0001193125-24-000001", "item": "8-K:1.05"})
    assert err["code"] == "NOT_FOUND" and "cik" in err["alternative"]
    assert any("CIK0001193125.json" in u for u in rec.urls), "prefix is checked against its own submissions only"


# ------------------------------------------------------------ 403 alternative


def test_role_lock_403_keeps_the_alternative_everywhere(client):
    resp, payload = client.raw("tools/call", {"name": "analyze_video", "arguments": {"video_id": "abcdefghijk", "domain_pack": "securities_disclosure"}}, token="dev:acme:junior")
    assert resp.status == 403
    err = payload["error"]
    alt = err["data"]["alternative"]
    assert alt and "Instead: " + alt in err["message"]
    assert err["data"]["code"] == "LOCK_ROLE" and err["data"]["step_up"] is False and err["data"]["role"] == "junior"
    header = resp.headers["WWW-Authenticate"]
    assert 'error="insufficient_scope"' in header and alt.split(",")[0] in header
    assert all(0x20 <= ord(c) <= 0x7E for c in header)


class _ScopedValidator:
    def validate(self, token):
        return Principal(sub="gc-1", tenant="acme", role="gc", scopes=frozenset({"splitrisk.read", "splitrisk.assess"}))


def test_gc_missing_decide_scope_gets_step_up(client, doc_id):
    rid = client.ok("assess_selection", {"target": {"source": doc_id, "scope": "document"}, "domain_pack": "securities_disclosure"})["records"][0]["claim_id"]
    gc = McpServer(ServerConfig(), validator=_ScopedValidator(), store=client.server.store, adapters=fake_adapters())
    resp, payload = Client(gc).raw("tools/call", {"name": "record_review_action", "arguments": {"record_id": rid, "action": "accept"}}, token="x")
    assert resp.status == 403
    assert payload["error"]["data"]["step_up"] is True and "code" not in payload["error"]["data"]
    assert 'scope="splitrisk.review.decide"' in resp.headers["WWW-Authenticate"]
    assert "Re-authorize with scope splitrisk.review.decide" in payload["error"]["message"]


# ------------------------------------------------- review history + identity


def test_history_entries_carry_label_outcome_and_name(client, doc_id):
    rid = client.ok("assess_selection", {"target": {"source": doc_id, "scope": "document"}, "domain_pack": "securities_disclosure"})["records"][0]["claim_id"]
    client.ok("record_review_action", {"record_id": rid, "action": "propose", "note": "stale"}, token="dev:acme:junior:j1:name=Jo_Junior")
    rec = client.ok("record_review_action", {"record_id": rid, "action": "edit", "severity_level": "medium", "verdict_or_action": "ADD"}, token="dev:acme:gc:g1:name=Gale_Counsel")
    output_valid("record_review_action", rec)
    first, second = rec["review"]["history"]
    assert (first["label"], first["by"], first["by_name"]) == ("Proposed", "j1", "Jo Junior")
    assert first["outcome"]["state"] == "proposed" and first["outcome"]["severity"]["basis"] == "engine"
    assert (second["label"], second["by_name"]) == ("Edited", "Gale Counsel")
    assert second["outcome"] == {"state": "edited", "verdict_or_action": "ADD", "severity": {"level": "medium", "basis": "reviewer"}}


def test_reassessment_keeps_ids_and_workpaper_state():
    engine = FakeDisclosure()
    client = Client(make_server(adapters=fake_adapters(disclosure=engine)))
    doc = client.ok("register_document", {"text": TENK, "media_type": "text/plain", "rights": "public_source"})["doc_id"]
    args = {"target": {"source": doc, "scope": "document"}, "domain_pack": "securities_disclosure"}
    first = client.ok("assess_selection", args)["records"][0]
    client.ok("record_review_action", {"record_id": first["claim_id"], "action": "edit", "severity_level": "low",
                                       "illustrative_rewrite": "Counsel's text."}, token="dev:acme:gc")
    again = client.ok("assess_selection", args)["records"][0]
    assert again["claim_id"] == first["claim_id"]
    assert again["illustrative_rewrite"] == "Counsel's text." and again["severity"]["basis"] == "reviewer"
    assert [h["action"] for h in again["review"]["history"]] == ["edit"]

    original = engine.assess

    def changed(request, progress):
        out = original(request, progress)
        out[0]["evidence"][0]["quote"] = "Updated 8-K/A wording about the incident."
        return out

    engine.assess = changed
    third = client.ok("assess_selection", args)["records"][0]
    assert third["claim_id"] == first["claim_id"]
    assert [h["action"] for h in third["review"]["history"]] == ["edit", "reassessed"]
    assert third["review"]["version"] == 3
    other_pack = client.ok("assess_selection", dict(args, domain_pack="analyst_sift"))["records"][0]
    assert other_pack["claim_id"] != first["claim_id"]
