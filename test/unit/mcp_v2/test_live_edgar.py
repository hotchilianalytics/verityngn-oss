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


def test_item_105_without_cik_resolves_issuer_not_filing_agent(client):
    sec = client.ok("get_filing_section", {"accession": MSFT_ITEM_105, "item": "8-K:1.05"})
    assert sec["url"].startswith("https://www.sec.gov/Archives/edgar/data/789019/")


ANTHROPIC_CIK = "2130357"
ANTHROPIC_S1 = "0001628280-26-067168"
ANTHROPIC_DRSA = "0002130357-26-000014"
PROSPECTUS_KEYS = {
    "prospectus-summary", "risk-factors", "use-of-proceeds", "mdna", "business", "governance", "management",
    "executive-compensation", "principal-stockholders", "description-of-capital-stock", "underwriting", "financial-statements",
}


def test_anthropic_resolves_before_it_has_a_ticker(client):
    by_name = client.ok("resolve_entity", {"name": "Anthropic"})["candidates"]
    assert by_name[0]["cik"] == ANTHROPIC_CIK and by_name[0]["name"] == "Anthropic, PBC"
    assert client.ok("resolve_entity", {"cik": ANTHROPIC_CIK})["candidates"][0]["name"] == "Anthropic, PBC"


def test_anthropic_registration_statements_are_listed(client):
    import datetime as dt

    window = {"from": "2026-05-01", "to": dt.date.today().isoformat()}
    out = client.ok("filings_search", {"cik": ANTHROPIC_CIK, "forms": ["S-1", "DRS"], "window": window})
    forms = {f["accession"]: f["form"] for f in out["filings"]}
    assert forms[ANTHROPIC_S1] == "S-1" and forms[ANTHROPIC_DRSA] == "DRS/A"


def test_anthropic_s1_sections_without_cik(client):
    sec = client.ok("get_filing_section", {"accession": ANTHROPIC_S1, "item": "Risk Factors"})
    assert sec["url"] == "https://www.sec.gov/Archives/edgar/data/2130357/000162828026067168/anthropicpbc-sx1.htm"
    doc = client.server.store.get_document(sec["doc_id"], "acme")
    assert PROSPECTUS_KEYS <= {e["item"] for e in doc.outline}
    res = anchors.resolve(sec["target"], doc)
    risk = doc.text[res.start:res.end]
    assert res.status == "exact" and risk.startswith("Risk Factors\n\nInvesting in our Class A common stock involves a high degree of risk.")
    assert len(risk) > 100_000 and "Special Note Regarding" not in risk
    for item, heading in (("use-of-proceeds", "Use of Proceeds"), ("MD&A", "Management"), ("governance", "Our Governance Structure"), ("1A", "Risk Factors")):
        s = client.ok("get_filing_section", {"accession": ANTHROPIC_S1, "cik": ANTHROPIC_CIK, "item": item})
        r = anchors.resolve(s["target"], doc)
        assert doc.text[r.start:r.end].startswith(heading), item
    sentence = risk.split("\n\n")[1]
    assert client.ok("verify_quote", {"quote": sentence, "source": sec["doc_id"]})["match_mode"] == "exact"


def test_anthropic_drs_a_outline_aligns_with_s1(client):
    from verityngn.agent.mcp_v2 import documents

    s1 = client.ok("get_filing_section", {"accession": ANTHROPIC_S1, "cik": ANTHROPIC_CIK, "item": "risk-factors"})
    drs = client.ok("get_filing_section", {"accession": ANTHROPIC_DRSA, "cik": ANTHROPIC_CIK, "item": "risk-factors"})
    a = client.server.store.get_document(drs["doc_id"], "acme")
    b = client.server.store.get_document(s1["doc_id"], "acme")
    pairs = documents.align_outlines(a.outline, b.outline)
    assert PROSPECTUS_KEYS <= {p["item"] for p in pairs if p["current"] and p["prior"]}
