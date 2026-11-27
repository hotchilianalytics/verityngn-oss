"""Tool results: records with anchors, tasks, review workflow, exports, widgets, adapters."""

from __future__ import annotations

import base64
import datetime as dt
import io
import json
import time

import pytest
from jsonschema import Draft202012Validator

from verityngn.agent.mcp_v2 import anchors
from verityngn.agent.mcp_v2.adapters import Adapters
from verityngn.agent.mcp_v2.adapters import edgar as edgar_mod
from verityngn.agent.mcp_v2.adapters import news as news_mod
from verityngn.agent.mcp_v2.adapters import sanctions as sanctions_mod
from verityngn.agent.mcp_v2.adapters import youtube as youtube_mod
from verityngn.agent.mcp_v2.adapters.disclosure import UnavailableDisclosureEngine, load_disclosure_engine
from verityngn.agent.mcp_v2.adapters.video import VerityNgnVideoEngine
from verityngn.agent.mcp_v2.schema_defs import bundle, ref

from .conftest import HEDGED, TENK, Client, FakeDisclosure, FakeVideo, fake_adapters, make_server, output_valid

RECORD = Draft202012Validator(bundle(ref("ClaimRiskRecord")))
TODAY = dt.date.today()


def _assess(client: Client, doc_id: str, **kw) -> dict:
    out = client.ok("assess_selection", {"target": {"source": doc_id, "scope": "document"}, "domain_pack": "securities_disclosure"}, **kw)
    output_valid("assess_selection", out)
    return out


def test_assess_selection_returns_anchored_extended_records(client, doc_id):
    doc = client.server.store.get_document(doc_id, "acme")
    i = doc.text.index(HEDGED)
    target = anchors.span_target(doc, i - 20, i + len(HEDGED) + 30)
    out = client.ok("assess_selection", {"target": target, "domain_pack": "securities_disclosure"})
    output_valid("assess_selection", out)
    assert out["target"]["anchor_status"] == "exact"
    [rec] = out["records"]
    assert RECORD.is_valid(rec)
    assert rec["schema_version"] == "2.0" and rec["claim_id"].startswith("sr:rec:acme/")
    assert rec["doc_id"] == doc_id and rec["claim_kind"] == "disclosure_pair" and rec["verdict_or_action"] == "REWRITE"
    res = anchors.resolve(rec["target"], doc)
    assert res.status == "exact" and doc.text[res.start:res.end] == HEDGED
    assert rec["severity"] == {"level": "high", "basis": "engine", "rule": "SEV-OWN-PAIR", "rationale": rec["severity"]["rationale"]}
    assert rec["coverage"]["own"]["state"] == "hit" and rec["coverage"]["own"]["date"] == "2024-01-19"
    assert rec["coverage"]["short"]["allegation"] is True
    assert rec["allegation"] is True and rec["visibility"] == "internal"
    assert set(rec["disclaimers"]) >= {"not_legal_advice", "allegation_only"}
    assert rec["provenance"]["engine"] == "rfkit" and rec["provenance"]["engine_version"] == "0.0-test"
    assert all(e["quote_sha256"] for e in rec["evidence"])
    assert rec["review"] == {"state": "proposed", "version": 1, "history": []}


def test_selection_outside_the_finding_returns_no_records(client, doc_id):
    doc = client.server.store.get_document(doc_id, "acme")
    i = doc.text.index("Our credit facility")
    out = client.ok("assess_selection", {"target": anchors.span_target(doc, i, i + 40), "domain_pack": "securities_disclosure"})
    assert out["records"] == []


def test_assess_document_as_task_with_partial_results():
    client = Client(make_server(adapters=fake_adapters(disclosure=FakeDisclosure(delay=0.3))))
    doc_id = client.ok("register_document", {"text": TENK, "media_type": "text/plain", "rights": "public_source"})["doc_id"]
    created = client.tool("assess_document", {"doc_id": doc_id, "domain_pack": "securities_disclosure"}, tasks=True)
    assert created["resultType"] == "task"
    assert created["status"] == "working" and created["pollIntervalMs"] == 5000 and created["ttlMs"] == 86_400_000
    assert set(created) >= {"taskId", "createdAt", "lastUpdatedAt"}
    report_id = created["_meta"]["com.verityindex.splitrisk/report_id"]
    running = client.ok("get_report", {"report_id": report_id})
    assert running["status"] == "running"
    done = client.wait_task(created["taskId"])
    assert done["status"] == "completed" and done["resultType"] == "complete"
    result = done["result"]
    assert not result.get("isError")
    output_valid("assess_document", result["structuredContent"])
    cov = result["structuredContent"]["coverage"]
    assert cov["columns"] == ["own", "staff", "docket", "short", "spoken"]
    assert cov["rows"][0]["heading"] == "Risks Relating to Cybersecurity" and cov["rows"][0]["severity"]["level"] == "high"
    rep = client.ok("get_report", {"report_id": report_id})
    assert rep["status"] == "complete" and rep["records_ready"] == 1
    output_valid("get_report", rep)


def test_assess_document_without_tasks_returns_report_handle(client, doc_id):
    out = client.ok("assess_document", {"doc_id": doc_id, "domain_pack": "securities_disclosure"})
    assert out["status"] == "running" and out["report_id"].startswith("sr:rep:acme/")
    output_valid("assess_document", out)
    rep = client.wait_report(out["report_id"])
    assert rep["status"] == "complete" and len(rep["records"]) == 1


def test_tasks_methods_require_the_capability(client):
    resp, payload = client.raw("tasks/get", {"taskId": "x"})
    assert payload["error"]["code"] == -32021
    assert payload["error"]["data"]["requiredCapabilities"]["extensions"] == {"io.modelcontextprotocol/tasks": {}}
    resp, payload = client.raw("tasks/get", {"taskId": "nope"}, tasks=True)
    assert payload["error"]["code"] == -32602


def test_task_cancel_stops_the_engine_and_fails_the_report():
    slow = FakeDisclosure(delay=5)
    client = Client(make_server(adapters=fake_adapters(disclosure=slow)))
    doc_id = client.ok("register_document", {"text": TENK, "media_type": "text/plain", "rights": "public_source"})["doc_id"]
    created = client.tool("assess_document", {"doc_id": doc_id, "domain_pack": "securities_disclosure"}, tasks=True)
    time.sleep(0.2)
    assert client.rpc("tasks/cancel", {"taskId": created["taskId"]}, tasks=True)["resultType"] == "complete"
    t0 = time.time()
    done = client.wait_task(created["taskId"], timeout=3)
    assert done["status"] == "cancelled" and time.time() - t0 < 2
    rep = client.ok("get_report", {"report_id": created["_meta"]["com.verityindex.splitrisk/report_id"]})
    assert rep["status"] == "failed"
    other = client.raw("tasks/get", {"taskId": created["taskId"]}, tasks=True, token="dev:other:analyst")[1]
    assert other["error"]["code"] == -32602


def test_tool_errors_inside_tasks_complete_with_is_error():
    plain = Client(make_server(adapters=fake_adapters(disclosure=UnavailableDisclosureEngine("not installed"))))
    doc = plain.ok("register_document", {"text": TENK, "media_type": "text/plain", "rights": "public_source"})["doc_id"]
    created = plain.tool("assess_document", {"doc_id": doc, "domain_pack": "securities_disclosure"}, tasks=True)
    done = plain.wait_task(created["taskId"])
    assert done["status"] == "completed"
    assert done["result"]["isError"] is True and done["result"]["structuredContent"]["code"] == "ENGINE_NOT_INSTALLED"


def test_default_disclosure_engine_reports_not_installed(monkeypatch):
    monkeypatch.delenv("SPLITRISK_DISCLOSURE_ENGINE", raising=False)
    engine = load_disclosure_engine()
    client = Client(make_server(adapters=fake_adapters(disclosure=engine)))
    doc = client.ok("register_document", {"text": TENK, "media_type": "text/plain", "rights": "public_source"})["doc_id"]
    err = client.err("assess_selection", {"target": {"source": doc, "scope": "document"}, "domain_pack": "securities_disclosure"})
    assert err["code"] == "ENGINE_NOT_INSTALLED" and err["details"]["engine"] == "rfkit" and err["alternative"]


def test_disclosure_engine_loads_from_env(monkeypatch):
    monkeypatch.setenv("SPLITRISK_DISCLOSURE_ENGINE", "test.unit.mcp_v2.conftest:FakeDisclosure")
    assert isinstance(load_disclosure_engine(), FakeDisclosure)
    monkeypatch.setenv("SPLITRISK_DISCLOSURE_ENGINE", "no.such.module:engine")
    assert isinstance(load_disclosure_engine(), UnavailableDisclosureEngine)


def test_analyze_video_task_returns_time_anchored_records():
    client = Client(make_server())
    created = client.tool("analyze_video", {"video_id": "abcdefghijk", "domain_pack": "securities_disclosure"}, tasks=True)
    assert created["resultType"] == "task" and created["pollIntervalMs"] == 10_000
    done = client.wait_task(created["taskId"])
    sc = done["result"]["structuredContent"]
    output_valid("analyze_video", sc)
    assert len(sc["records"]) == 2
    rec = sc["records"][0]
    assert rec["doc_id"] == sc["transcript_doc_id"] and rec["source_lane"] == "video"
    assert rec["target"]["scope"] == "time_range" and rec["target"]["selector"][0]["value"] == "t=5,9"
    ev = rec["evidence"][0]
    assert ev["source_class"] == "spoken" and ev["url"].endswith("&t=5s") and ev["date"] == "2026-09-30"
    assert ev["anchor"]["source"] == "urn:splitrisk:video:youtube:abcdefghijk"
    assert "youtube_editorial" in rec["disclaimers"] and "llm_editorial" in rec["disclaimers"]
    assert sc["records"][1]["verdict_or_action"] == "UNRESOLVED" and sc["records"][1]["claim_kind"] == "prediction"
    store = client.server.store
    blob = json.dumps([d.__dict__ for d in store.docs.values()], default=str) + json.dumps(store.records)
    assert "Q3 update" not in blob, "video titles are never persisted"
    sel = client.ok("assess_selection", {"target": {"source": "urn:splitrisk:video:youtube:abcdefghijk", "scope": "time_range",
        "selector": [{"type": "FragmentSelector", "conformsTo": anchors.MEDIA_FRAGS, "value": "t=10,14"}]}, "domain_pack": "securities_disclosure"})
    assert sel["target"]["anchor_status"] == "approximate"


def test_analyze_video_without_tasks_falls_back_to_report(client):
    out = client.ok("analyze_video", {"video_id": "abcdefghijk", "domain_pack": "securities_disclosure"})
    assert out["status"] == "running"
    rep = client.wait_report(out["report_id"])
    assert rep["status"] == "complete" and len(rep["records"]) == 2


def test_deep_research_rider_uses_input_required():
    client = Client(make_server(adapters=fake_adapters(video=FakeVideo())))
    created = client.tool("analyze_video", {"video_id": "abcdefghijk", "domain_pack": "securities_disclosure", "deep_research": True}, tasks=True)
    waiting = client.wait_task(created["taskId"], until=("input_required",))
    req = waiting["inputRequests"]["deep_research_rider"]
    assert req["method"] == "elicitation/create" and req["params"]["requestedSchema"]["required"] == ["acknowledge"]
    assert client.rpc("tasks/update", {"taskId": created["taskId"], "inputResponses": {"deep_research_rider": {"action": "accept", "content": {"acknowledge": True}}}}, tasks=True)["resultType"] == "complete"
    done = client.wait_task(created["taskId"])
    assert done["status"] == "completed"
    assert done["result"]["structuredContent"]["code"] == "ENGINE_NOT_INSTALLED"

    created = client.tool("analyze_video", {"video_id": "abcdefghijk", "domain_pack": "securities_disclosure", "deep_research": True}, tasks=True)
    client.wait_task(created["taskId"], until=("input_required",))
    client.rpc("tasks/update", {"taskId": created["taskId"], "inputResponses": {"deep_research_rider": {"action": "decline"}}}, tasks=True)
    assert client.wait_task(created["taskId"])["result"]["structuredContent"]["code"] == "LOCK_NO_LICENCE"
    err = client.err("analyze_video", {"video_id": "abcdefghijk", "domain_pack": "securities_disclosure", "deep_research": True})
    assert err["code"] == "LOCK_NO_LICENCE"


def test_real_video_adapter_never_fakes_results(monkeypatch):
    for k in ("GEMINI_API_KEY", "VERITY_GEMINI_KEY", "GOOGLE_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    client = Client(make_server(adapters=fake_adapters(video=VerityNgnVideoEngine())))
    for tier, codes in (("full", {"ENGINE_NOT_INSTALLED"}), ("light", {"ENGINE_NOT_INSTALLED", "UPSTREAM"})):
        out = client.ok("analyze_video", {"video_id": "abcdefghijk", "domain_pack": "securities_disclosure", "tier": tier})
        rep = client.wait_report(out["report_id"])
        assert rep["status"] == "failed" and rep["records"] == []
        assert rep["error"]["code"] in codes


def test_review_history_is_append_only_with_optimistic_concurrency(client, doc_id):
    rid = _assess(client, doc_id)["records"][0]["claim_id"]
    rec = client.ok("record_review_action", {"record_id": rid, "action": "propose", "note": "check lag"}, token="dev:acme:junior")
    assert rec["review"]["version"] == 2
    stale = client.err("record_review_action", {"record_id": rid, "action": "accept", "expected_version": 1}, token="dev:acme:gc")
    assert stale["code"] == "INVALID" and stale["details"]["current_version"] == 2
    rec = client.ok("record_review_action", {"record_id": rid, "action": "edit", "expected_version": 2, "severity_level": "medium",
                                              "illustrative_rewrite": "We experienced an incident in January 2024.", "note": "reviewed"}, token="dev:acme:gc")
    output_valid("record_review_action", rec)
    assert rec["severity"] == {"level": "medium", "basis": "reviewer", "rationale": "reviewed"}
    assert rec["review"]["state"] == "edited" and rec["review"]["version"] == 3
    hist = rec["review"]["history"]
    assert [h["action"] for h in hist] == ["propose", "edit"]
    assert hist[1]["role"] == "gc" and hist[1]["evidence_hash"].startswith("sha256:")
    assert hist[1]["changes"]["severity_level"] == "medium"
    audit = client.server.audit.rows
    assert any(r["tool"] == "record_review_action" and r["role"] == "gc" for r in audit)
    assert all({"tenant", "user", "role", "tool", "arguments_sha256", "record_ids", "at"} <= set(r) for r in audit)


def test_compose_assessment_and_exports(client, doc_id):
    out = _assess(client, doc_id)
    rid = out["records"][0]["claim_id"]
    cov = client.ok("compose_assessment", {"record_ids": [rid], "group_by": "category"})
    output_valid("compose_assessment", cov)
    assert cov["rows"][0]["heading"] == "cybersecurity"
    assert cov["rows"][0]["cells"]["own"]["quote"].startswith("On January 12, 2024")
    assert cov["rows"][0]["cells"]["docket"] == {"state": "none"}

    exp = client.ok("export_assessment", {"report_id": out["report_id"], "format": "json"})
    output_valid("export_assessment", exp)
    body = client.rpc("resources/read", {"uri": exp["resource_uri"]})
    assert body["cacheScope"] == "private"
    data = json.loads(body["contents"][0]["text"])
    assert data["records"] == [], "allegation records stay out unless include_internal"
    internal = client.ok("export_assessment", {"report_id": out["report_id"], "format": "json", "include_internal": True})
    data = json.loads(client.rpc("resources/read", {"uri": internal["resource_uri"]})["contents"][0]["text"])
    assert len(data["records"]) == 1 and "Not legal advice" in data["notice"]

    w3c = client.ok("export_assessment", {"report_id": out["report_id"], "format": "w3c_annotations", "include_internal": True})
    coll = json.loads(client.rpc("resources/read", {"uri": w3c["resource_uri"]})["contents"][0]["text"])
    assert coll["type"] == "AnnotationCollection" and coll["first"]["items"][0]["target"][0]["source"] == doc_id

    md = client.ok("export_assessment", {"report_id": out["report_id"], "format": "md", "include_internal": True})
    text = client.rpc("resources/read", {"uri": md["resource_uri"]})["contents"][0]["text"]
    assert "Not legal advice" in text and "| Risks Relating to Cybersecurity | high |" in text

    pytest.importorskip("openpyxl")
    from openpyxl import load_workbook

    x = client.ok("export_assessment", {"report_id": out["report_id"], "format": "xlsx", "include_internal": True}, token="dev:acme:gc")
    blob = client.rpc("resources/read", {"uri": x["resource_uri"]}, token="dev:acme:gc")["contents"][0]["blob"]
    wb = load_workbook(io.BytesIO(base64.b64decode(blob)))
    assert wb["Coverage"]["G2"].value == "short" and "not computed" in wb["Coverage"]["I2"].value

    err = client.err("export_assessment", {"report_id": out["report_id"], "format": "audit_pdf"})
    assert err["code"] == "INVALID" and "json" in err["alternative"]
    missing = client.raw("resources/read", {"uri": exp["resource_uri"]}, token="dev:other:analyst")[1]
    assert missing["error"]["code"] == -32602


def test_records_and_reports_are_resources(client, doc_id):
    out = _assess(client, doc_id)
    rid = out["records"][0]["claim_id"]
    rec = json.loads(client.rpc("resources/read", {"uri": f"splitrisk://records/{rid}"})["contents"][0]["text"])
    assert rec["claim_id"] == rid
    rep = json.loads(client.rpc("resources/read", {"uri": f"splitrisk://reports/{out['report_id']}"})["contents"][0]["text"])
    assert rep["status"] == "complete"
    templates = client.rpc("resources/templates/list")["resourceTemplates"]
    assert {t["uriTemplate"] for t in templates} >= {"splitrisk://records/{record_id}", "splitrisk://reports/{report_id}"}
    schema = json.loads(client.rpc("resources/read", {"uri": "splitrisk://schema/v1"})["contents"][0]["text"])
    assert schema["$id"] == "urn:splitrisk:schema:v1"


def test_ui_widgets_are_mcp_apps_resources(client):
    listing = client.rpc("resources/list")
    uis = [r for r in listing["resources"] if r["uri"].startswith("ui://")]
    assert {r["uri"] for r in uis} == {f"ui://splitrisk/{n}" for n in ("assessment", "coverage", "results", "video", "workpaper")}
    assert all(r["mimeType"] == "text/html;profile=mcp-app" for r in uis)
    for r in uis:
        res = client.rpc("resources/read", {"uri": r["uri"]})
        content = res["contents"][0]
        html = content["text"]
        assert content["mimeType"] == "text/html;profile=mcp-app" and html.startswith("<!doctype html>")
        assert content["_meta"]["ui"]["csp"]["connectDomains"] == []
        assert "Not legal advice" in html and 'id="allegation-banner"' in html
        assert "ui/initialize" in html and "ui/notifications/tool-result" in html and "2026-01-26" in html
        for banned in ("localStorage", "sessionStorage", "indexedDB", "fetch(", "XMLHttpRequest", "WebSocket", "document.cookie"):
            assert banned not in html, (r["uri"], banned)
    video = client.rpc("resources/read", {"uri": "ui://splitrisk/video"})["contents"][0]
    assert video["_meta"]["ui"]["csp"]["frameDomains"] == ["https://www.youtube-nocookie.com"]
    work = client.rpc("resources/read", {"uri": "ui://splitrisk/workpaper"})["contents"][0]["text"]
    assert "record_review_action" in work and "Reviewer judgment, not computed".lower() in work.lower()


def test_get_report_judgment_visibility():
    client = Client(make_server(judgment_workspaces=("acme",)))
    doc = client.ok("register_document", {"text": TENK, "media_type": "text/plain", "rights": "public_source"})["doc_id"]
    out = _assess(client, doc, token="dev:acme:gc")
    rid = out["records"][0]["claim_id"]
    client.ok("record_review_action", {"record_id": rid, "action": "set_judgment", "judgment_likelihood": "likely"}, token="dev:acme:gc")
    gc = client.ok("get_report", {"report_id": out["report_id"]}, token="dev:acme:gc")
    analyst = client.ok("get_report", {"report_id": out["report_id"]}, token="dev:acme:analyst")
    assert gc["records"][0]["judgment"]["likelihood"] == "likely" and gc["judgment_enabled"] is True
    assert "judgment" not in analyst["records"][0] and analyst["viewer_role"] == "analyst"
    exp = client.ok("export_assessment", {"report_id": out["report_id"], "format": "json", "include_internal": True}, token="dev:acme:gc")
    assert "judgment" not in client.rpc("resources/read", {"uri": exp["resource_uri"]}, token="dev:acme:gc")["contents"][0]["text"]


def test_verify_quote_modes(client, doc_id):
    exact = client.ok("verify_quote", {"quote": HEDGED, "source": doc_id})
    output_valid("verify_quote", exact)
    assert exact["match_mode"] == "exact" and exact["target"]["anchor_status"] == "exact"
    fuzzy = client.ok("verify_quote", {"quote": "We may experience cyber security incidents", "source": doc_id})
    assert fuzzy["match_mode"] == "fuzzy" and fuzzy["score"] >= 0.9
    assert "[-" in fuzzy["diff"] or "{+" in fuzzy["diff"]
    assert fuzzy["matched_text"] == HEDGED
    failed = client.ok("verify_quote", {"quote": "Our auditors resigned in protest.", "source": doc_id})
    assert failed["match_mode"] == "failed" and "target" not in failed


def test_register_document_rights_and_idempotency(client):
    a = client.ok("register_document", {"text": "Hello  world", "media_type": "text/plain", "rights": "own_or_client_document"})
    b = client.ok("register_document", {"text": "Hello world", "media_type": "text/plain", "rights": "own_or_client_document"})
    assert a["doc_id"] == b["doc_id"] and a["source_hash"] == b["source_hash"]
    err = client.err("register_document", {"text": "x", "media_type": "text/plain", "rights": "licensed_without_ai"})
    assert err["code"] == "INVALID"
    assert client.server.audit.rows[0]["rights"] == "own_or_client_document"
    err = client.err("register_document", {"url": "http://127.0.0.1/secret", "media_type": "text/html", "rights": "public_source"})
    assert err["code"] == "INVALID" and "private" in err["message"]
    err = client.err("register_document", {"text": "%PDF", "media_type": "application/pdf", "rights": "public_source"})
    assert err["code"] == "ENGINE_NOT_INSTALLED" and err["details"]["engine"] == "docling"
    err = client.err("register_document", {"upload_ref": "s3://x", "media_type": "text/plain", "rights": "public_source"})
    assert err["code"] == "ENGINE_NOT_INSTALLED"


def test_html_and_vtt_registration(client):
    html = "<html><head><style>x{}</style></head><body><p>ITEM 1A. RISK FACTORS</p><p>We may &amp; might fail.</p><script>bad()</script></body></html>"
    out = client.ok("register_document", {"text": html, "media_type": "text/html", "rights": "public_source"})
    doc = client.server.store.get_document(out["doc_id"], "acme")
    assert doc.text == "ITEM 1A. RISK FACTORS\n\nWe may & might fail." and out["outline"][0]["item"] == "1A"
    ixbrl = ('<html><body><div style="display:none"><ix:header><ix:hidden>dei:Hidden</ix:hidden></ix:header></div>'
             "<div><p>ITEM 1.05 MATERIAL CYBERSECURITY INCIDENTS</p><p>An attack was detected.</p></div></body></html>")
    out = client.ok("register_document", {"text": ixbrl, "media_type": "text/html", "rights": "public_source"})
    doc = client.server.store.get_document(out["doc_id"], "acme")
    assert "An attack was detected." in doc.text and "dei:Hidden" not in doc.text


# ----------------------------------------------------------- real adapters


class _Recorder:
    def __init__(self, responses):
        self.responses = responses
        self.urls: list[str] = []

    def __call__(self, url, **kw):
        self.urls.append(url)
        for key, value in self.responses.items():
            if key in url:
                return value(kw) if callable(value) else value
        raise AssertionError(f"unexpected URL {url}")


def _submissions():
    return {
        "name": "EXAMPLE CORP",
        "formerNames": [{"name": "EXAMPLE SOFTWARE INC"}],
        "filings": {
            "recent": {
                "accessionNumber": ["0000000001-24-000003", "0000000001-24-000002", "0000000001-24-000001", "0000000001-23-000009"],
                "filingDate": ["2024-03-01", "2024-02-15", "2024-01-19", "2023-07-27"],
                "form": ["CORRESP", "UPLOAD", "8-K", "10-K"],
                "primaryDocument": ["c.htm", "u.pdf", "x8k.htm", "k.htm"],
                "items": ["", "", "1.05,9.01", ""],
            },
            "files": [],
        },
    }


def test_edgar_adapter_through_tools(monkeypatch):
    rec = _Recorder({"data.sec.gov/submissions": _submissions()})
    monkeypatch.setattr(edgar_mod, "request_json", rec)
    monkeypatch.setattr(edgar_mod.EdgarClient, "company_tickers", lambda self: [{"cik_str": 1, "ticker": "EXMP", "title": "EXAMPLE CORP"}])
    client = Client(make_server(adapters=fake_adapters(edgar=edgar_mod.EdgarClient())))
    cands = client.ok("resolve_entity", {"ticker": "exmp"})["candidates"]
    assert cands[0]["entity_id"] == "sr:ent:cik0000000001" and cands[0]["aliases"] == ["EXAMPLE SOFTWARE INC"]
    assert cands[0]["owned_channels"][0]["verified_by"] == "issuer_site_link"
    out = client.ok("filings_search", {"cik": "1", "forms": ["8-K", "UPLOAD", "CORRESP"], "window": {"from": "2024-01-01", "to": "2024-12-31"}})
    output_valid("filings_search", out)
    forms = {f["form"]: f for f in out["filings"]}
    assert forms["8-K"]["items"] == ["1.05", "9.01"] and forms["8-K"]["source_class"] == "own"
    assert forms["UPLOAD"]["source_class"] == "staff" and forms["CORRESP"]["source_class"] == "staff"
    assert forms["8-K"]["url"] == "https://www.sec.gov/Archives/edgar/data/1/000000000124000001/x8k.htm"
    only_105 = client.ok("filings_search", {"cik": "1", "forms": ["8-K"], "items": ["1.05"], "window": {"from": "2024-01-01", "to": "2024-12-31"}})
    assert [f["accession"] for f in only_105["filings"]] == ["0000000001-24-000001"]

    efts = {"hits": {"hits": [{"_id": "0000000001-24-000001:x8k.htm", "_source": {"adsh": "0000000001-24-000001", "form": "8-K", "file_date": "2024-01-19", "items": ["1.05"]}}]}}
    rec.responses["efts.sec.gov"] = efts
    out = client.ok("filings_search", {"cik": "1", "forms": ["8-K"], "query": "nation-state", "window": {"from": "2024-01-01", "to": "2024-12-31"}})
    assert out["filings"][0]["accession"] == "0000000001-24-000001"
    assert any("efts.sec.gov/LATEST/search-index" in u and "ciks=0000000001" in u for u in rec.urls)

    eightk = b"<html><body><p>ITEM 1.05 MATERIAL CYBERSECURITY INCIDENTS</p><p>On January 12, 2024, the Company detected a nation-state attack.</p><p>ITEM 9.01 FINANCIAL STATEMENTS AND EXHIBITS</p><p>None.</p></body></html>"
    monkeypatch.setattr(edgar_mod, "request", lambda url, **kw: eightk)
    sec = client.ok("get_filing_section", {"accession": "0000000001-24-000001", "cik": "1", "item": "8-K:1.05"})
    output_valid("get_filing_section", sec)
    doc = client.server.store.get_document(sec["doc_id"], "acme")
    res = anchors.resolve(sec["target"], doc)
    assert "nation-state attack" in doc.text[res.start:res.end] and "9.01" not in doc.text[res.start:res.end]
    vq = client.ok("verify_quote", {"quote": "the Company detected a nation-state attack", "source": sec["url"]})
    assert vq["match_mode"] == "exact"
    err = client.err("get_filing_section", {"accession": "0000000001-24-000001", "cik": "1", "item": "1A"})
    assert err["code"] == "ANCHOR_UNRESOLVED" and err["details"]["items_found"] == ["1.05", "9.01"]


def test_youtube_adapter_uses_uploads_playlist_only(monkeypatch):
    end = TODAY - dt.timedelta(days=1)
    pages = {
        "/channels?": {"items": [{"contentDetails": {"relatedPlaylists": {"uploads": "UUexample"}}}]},
        "/playlistItems?": {"items": [
            {"contentDetails": {"videoId": "AAAAAAAAAAA", "videoPublishedAt": end.isoformat() + "T10:00:00Z"}, "snippet": {"title": "Recent"}},
            {"contentDetails": {"videoId": "BBBBBBBBBBB", "videoPublishedAt": (TODAY - dt.timedelta(days=200)).isoformat() + "T10:00:00Z"}, "snippet": {"title": "Old"}},
        ]},
    }
    rec = _Recorder(pages)
    monkeypatch.setattr(youtube_mod, "request_json", rec)
    yt = youtube_mod.YouTubeUploads(api_key="k")
    client = Client(make_server(adapters=fake_adapters(youtube=yt)))
    ent = client.ok("resolve_entity", {"ticker": "EXMP"})["candidates"][0]["entity_id"]
    out = client.ok("list_company_videos", {"entity_id": ent, "preset": "last_90_days"})
    output_valid("list_company_videos", out)
    assert [v["video_id"] for v in out["videos"]] == ["AAAAAAAAAAA"]
    assert all("/search?" not in u for u in rec.urls) and any("/playlistItems?" in u for u in rec.urls)
    assert "Recent" not in json.dumps(client.server.store.records)
    no_key = Client(make_server(adapters=fake_adapters(youtube=youtube_mod.YouTubeUploads(api_key=""))))
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    ent = no_key.ok("resolve_entity", {"ticker": "EXMP"})["candidates"][0]["entity_id"]
    err = no_key.err("list_company_videos", {"entity_id": ent})
    assert err["code"] == "UPSTREAM" and err["alternative"]


def test_owned_channel_registry_requires_verification(tmp_path):
    p = tmp_path / "owned.json"
    p.write_text(json.dumps({"issuers": {"0000000001": [
        {"channel_id": "UCgood", "verified_by": "issuer_site_link"},
        {"channel_id": "UCunverified", "verified_by": "fan_page"},
    ]}}))
    reg = youtube_mod.OwnedChannelRegistry(p)
    assert reg.channels("1") == [{"platform": "youtube", "channel_id": "UCgood", "verified_by": "issuer_site_link"}]
    assert reg.channels("2") == []


def test_gdelt_adapter_flags_short_sellers(monkeypatch):
    rec = _Recorder({"api.gdeltproject.org": {"articles": [
        {"url": "https://www.reuters.com/a", "title": "Example Corp breach", "seendate": "20261020T120000Z", "domain": "reuters.com"},
        {"url": "https://hindenburgresearch.com/example", "title": "Example Corp: report", "seendate": "20261021T120000Z", "domain": "hindenburgresearch.com"},
    ]}})
    monkeypatch.setattr(news_mod, "request_json", rec)
    client = Client(make_server(adapters=fake_adapters(gdelt=news_mod.GdeltNews(), event_registry=news_mod.EventRegistryNews(api_key=""))))
    ent = client.ok("resolve_entity", {"ticker": "EXMP"})["candidates"][0]["entity_id"]
    window = {"from": (TODAY - dt.timedelta(days=30)).isoformat(), "to": TODAY.isoformat()}
    out = client.ok("news_window", {"entity_id": ent, "window": window, "query": "cyber incident"})
    output_valid("news_window", out)
    assert out["provider"] == "gdelt" and "GDELT" in out["attribution"]
    assert [a["allegation"] for a in out["articles"]] == [False, True]
    assert out["articles"][0]["date"] == "2026-10-20"
    assert "EXAMPLE+CORP" in rec.urls[0] and "sourcelang%3Aenglish" in rec.urls[0]


def test_opensanctions_adapter(monkeypatch):
    seen = {}

    def fake(url, **kw):
        seen.update(url=url, **kw)
        return {"responses": {"q": {"results": [{"id": "NK-1", "caption": "Jane Roe", "score": 0.93, "datasets": ["us_ofac_sdn"]}]}}}

    monkeypatch.setattr(sanctions_mod, "request_json", fake)
    client = Client(make_server(adapters=fake_adapters(sanctions=sanctions_mod.OpenSanctions(api_key="k"))))
    out = client.ok("sanctions_match", {"name": "Jane Roe", "schema": "Person", "country": "ru"})
    output_valid("sanctions_match", out)
    assert out["label"] == "Candidates for human review, not determinations"
    assert out["candidates"][0]["url"] == "https://www.opensanctions.org/entities/NK-1/"
    assert seen["body"]["queries"]["q"]["properties"] == {"name": ["Jane Roe"], "country": ["ru"]}
    assert seen["headers"]["Authorization"] == "ApiKey k"
    unconfigured = Client(make_server(adapters=fake_adapters(sanctions=sanctions_mod.OpenSanctions(api_key=""))))
    monkeypatch.delenv("OPENSANCTIONS_API_KEY", raising=False)
    err = unconfigured.err("sanctions_match", {"name": "Jane Roe", "schema": "Person"})
    assert err["code"] == "UPSTREAM" and err["alternative"]


def test_default_adapters_construct_without_network():
    a = Adapters()
    assert a.disclosure.name == "rfkit"
