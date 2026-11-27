"""Server-side locks (concept section 2.2): every rejection names an allowed alternative."""

from __future__ import annotations

import datetime as dt

import pytest

from verityngn.agent.mcp_v2 import locks
from verityngn.agent.mcp_v2.errors import ToolFailure

from .conftest import Client, make_server

TODAY = dt.date.today()


def _w(days_back: int, end_back: int = 0) -> dict[str, str]:
    return {"from": (TODAY - dt.timedelta(days=days_back)).isoformat(), "to": (TODAY - dt.timedelta(days=end_back)).isoformat()}


def _entity(client: Client, token: str = "dev:acme:analyst") -> str:
    return client.ok("resolve_entity", {"ticker": "EXMP"}, token=token)["candidates"][0]["entity_id"]


def test_window_rules_unit():
    assert locks.check_window(_w(366))
    with pytest.raises(ToolFailure) as e:
        locks.check_window(_w(367))
    assert e.value.code == "LOCK_WINDOW" and e.value.alternative
    with pytest.raises(ToolFailure) as e:
        locks.check_window({"from": TODAY.isoformat(), "to": (TODAY + dt.timedelta(days=1)).isoformat()})
    assert e.value.code == "LOCK_WINDOW" and "today" in e.value.alternative
    with pytest.raises(ToolFailure) as e:
        locks.check_window({"from": TODAY.isoformat(), "to": (TODAY - dt.timedelta(days=3)).isoformat()})
    assert e.value.code == "INVALID"


def test_window_over_366_days_returns_lock_window(client):
    ent = _entity(client)
    err = client.err("news_window", {"entity_id": ent, "window": _w(400)})
    assert err["code"] == "LOCK_WINDOW" and err["alternative"]
    err = client.err("filings_search", {"cik": "1", "forms": ["8-K"], "window": _w(10, -5)})
    assert err["code"] == "LOCK_WINDOW"


def test_no_tool_accepts_a_schedule(client):
    ent = _entity(client)
    err = client.err("news_window", {"entity_id": ent, "window": _w(30), "schedule": "daily"})
    assert err["code"] == "INVALID"
    assert "re-run" in err["alternative"]


def test_non_owned_channel_is_locked_with_alternative(client):
    ent = _entity(client)
    err = client.err("list_company_videos", {"entity_id": ent, "channel_id": "UCsomebodyElse00000000"})
    assert err["code"] == "LOCK_CHANNEL_NOT_OWNED"
    assert "UCexampleOwned000000000" in err["alternative"] and "register_document" in err["alternative"]
    ok = client.ok("list_company_videos", {"entity_id": ent})
    assert ok["videos"][0]["video_id"] == "abcdefghijk"


def test_litigation_needs_licence(client):
    ent = _entity(client)
    err = client.err("search_litigation", {"entity_id": ent, "window": _w(30)})
    assert err["code"] == "LOCK_NO_LICENCE" and err["alternative"]
    err = client.err("search_litigation", {"entity_id": ent, "window": _w(30)}, token="dev:acme:analyst:ann:lic=courtlistener_commercial")
    assert err["code"] == "ENGINE_NOT_INSTALLED"


def test_junior_searches_need_confirmation(client):
    ent = _entity(client, token="dev:acme:junior")
    err = client.err("news_window", {"entity_id": ent, "window": _w(30)}, token="dev:acme:junior")
    assert err["code"] == "NEEDS_CONFIRMATION"
    assert err["details"]["entity"]["name"] == "EXAMPLE CORP"
    assert err["details"]["window"] == _w(30)
    ok = client.ok("news_window", {"entity_id": ent, "window": _w(30), "confirmed": True}, token="dev:acme:junior")
    assert ok["provider"] == "gdelt"


def test_old_news_without_event_registry_offers_narrower_window(client):
    ent = _entity(client)
    err = client.err("news_window", {"entity_id": ent, "window": _w(200)})
    assert err["code"] == "UPSTREAM" and "three months" in err["alternative"]


def _record_id(client: Client, doc_id: str) -> str:
    out = client.ok("assess_selection", {"target": {"source": doc_id, "scope": "document"}, "domain_pack": "securities_disclosure"})
    return out["records"][0]["claim_id"]


def test_junior_cannot_decide_or_set_judgment(client, doc_id):
    rid = _record_id(client, doc_id)
    for action in ("accept", "reject", "set_judgment"):
        args = {"record_id": rid, "action": action}
        if action == "set_judgment":
            args["judgment_likelihood"] = "likely"
        err = client.err("record_review_action", args, token="dev:acme:junior")
        assert err["code"] == "LOCK_ROLE"
        assert "propose" in err["alternative"]
    rec = client.ok("record_review_action", {"record_id": rid, "action": "propose", "note": "Looks stale"}, token="dev:acme:junior")
    assert rec["review"]["history"][-1]["action"] == "propose"


def test_judgment_needs_gc_and_switched_on_column(doc_id):
    off = Client(make_server())
    doc = off.ok("register_document", {"text": "ITEM 1A. RISK FACTORS\nWe may experience cybersecurity incidents today.", "media_type": "text/plain", "rights": "public_source"}, token="dev:acme:gc")["doc_id"]
    rid = off.ok("assess_selection", {"target": {"source": doc, "scope": "document"}, "domain_pack": "securities_disclosure"}, token="dev:acme:gc")["records"][0]["claim_id"]
    err = off.err("record_review_action", {"record_id": rid, "action": "set_judgment", "judgment_likelihood": "possible"}, token="dev:acme:gc")
    assert err["code"] == "LOCK_ROLE" and "switched off" in err["message"]

    on = Client(make_server(judgment_workspaces=("acme",)))
    doc = on.ok("register_document", {"text": "ITEM 1A. RISK FACTORS\nWe may experience cybersecurity incidents today.", "media_type": "text/plain", "rights": "public_source"}, token="dev:acme:gc")["doc_id"]
    rid = on.ok("assess_selection", {"target": {"source": doc, "scope": "document"}, "domain_pack": "securities_disclosure"}, token="dev:acme:gc")["records"][0]["claim_id"]
    rec = on.ok("record_review_action", {"record_id": rid, "action": "set_judgment", "judgment_likelihood": "possible"}, token="dev:acme:gc")
    assert rec["judgment"]["label"] == "Reviewer judgment, not computed"
    assert rec["judgment"]["entered_by"] == "dev-gc"
    analyst_view = on.ok("get_record", {"record_id": rid}, token="dev:acme:analyst")
    assert "judgment" not in analyst_view
    cov = on.ok("compose_assessment", {"record_ids": [rid]}, token="dev:acme:gc")
    assert "judgment" not in str(cov) and "likelihood" not in str(cov)
    err = on.err("record_review_action", {"record_id": rid, "action": "edit", "judgment_likelihood": "likely"}, token="dev:acme:gc")
    assert err["code"] == "INVALID"


def test_junior_cannot_export_internal_content(client, doc_id):
    out = client.ok("assess_selection", {"target": {"source": doc_id, "scope": "document"}, "domain_pack": "securities_disclosure"})
    err = client.err("export_assessment", {"report_id": out["report_id"], "format": "json", "include_internal": True}, token="dev:acme:junior")
    assert err["code"] == "LOCK_ROLE" and err["alternative"]


def test_video_scope_is_refused_for_juniors_with_insufficient_scope(client):
    resp, payload = client.raw("tools/call", {"name": "analyze_video", "arguments": {"video_id": "abcdefghijk", "domain_pack": "securities_disclosure"}}, token="dev:acme:junior")
    assert resp.status == 403
    assert 'error="insufficient_scope"' in resp.headers["WWW-Authenticate"]
    assert 'scope="splitrisk.video"' in resp.headers["WWW-Authenticate"]
    assert payload["error"]["data"]["alternative"]


def test_cross_tenant_handle_looks_like_missing(client, doc_id):
    rid = _record_id(client, doc_id)
    missing = client.err("get_record", {"record_id": "sr:rec:other/doesnotexist"}, token="dev:other:analyst")
    foreign = client.err("get_record", {"record_id": rid}, token="dev:other:analyst")
    assert missing["code"] == foreign["code"] == "NOT_FOUND"
    assert set(missing) == set(foreign)
    foreign_doc = client.err("assess_document", {"doc_id": doc_id, "domain_pack": "securities_disclosure"}, token="dev:other:analyst")
    assert foreign_doc["code"] == "NOT_FOUND"
