"""Live SEC EDGAR round trip on the public Microsoft cyber fixture (deselect with -m 'not live')."""

from __future__ import annotations

import pytest

from verityngn.agent.mcp_v2 import anchors
from verityngn.agent.mcp_v2.adapters import Adapters
from verityngn.agent.mcp_v2.adapters.edgar import EdgarClient

from .conftest import Client, FakeChannels, make_server

pytestmark = pytest.mark.live

MSFT_ITEM_105 = "0001193125-24-011295"


@pytest.fixture(scope="module")
def client() -> Client:
    return Client(make_server(adapters=Adapters(edgar=EdgarClient(), channels=FakeChannels())))


def test_resolve_and_search_microsoft(client):
    cands = client.ok("resolve_entity", {"ticker": "MSFT"})["candidates"]
    assert cands[0]["cik"] == "789019" and cands[0]["entity_id"] == "sr:ent:cik0000789019"
    out = client.ok("filings_search", {"cik": "789019", "forms": ["8-K"], "items": ["1.05"], "window": {"from": "2024-01-01", "to": "2024-03-31"}})
    assert MSFT_ITEM_105 in [f["accession"] for f in out["filings"]]
    fts = client.ok("filings_search", {"cik": "789019", "forms": ["8-K"], "query": "nation-state", "window": {"from": "2024-01-01", "to": "2024-02-28"}})
    assert MSFT_ITEM_105 in [f["accession"] for f in fts["filings"]]


def test_item_105_section_and_quote(client):
    sec = client.ok("get_filing_section", {"accession": MSFT_ITEM_105, "cik": "789019", "item": "8-K:1.05"})
    doc = client.server.store.get_document(sec["doc_id"], "acme")
    res = anchors.resolve(sec["target"], doc)
    section = doc.text[res.start:res.end]
    assert res.status == "exact" and "nation-state" in section.lower()
    sentence = next(s for s in section.split(". ") if "nation-state" in s.lower())
    vq = client.ok("verify_quote", {"quote": sentence, "source": sec["doc_id"]})
    assert vq["match_mode"] == "exact" and vq["target"]["anchor_status"] == "exact"
