"""Registration statements and prospectuses: outline, sections, forms, entities and the prior-version path.

The synthetic S-1 below reproduces what the real Anthropic, PBC S-1 (accession
0001628280-26-067168) and its DRS/A look like after extraction: an all-caps
table of contents with page numbers, title-case body headings, a summary that
repeats "Risk Factors", wrapped multi-line headings, a "Legal Matters" note in
the financial statements, a running confidential-treatment legend, page
numbers with "Table of Contents" links, and Part II Items 13-17.
"""

from __future__ import annotations

import datetime as dt

import pytest

from verityngn.agent.mcp_v2 import anchors, documents, prospectus
from verityngn.agent.mcp_v2.adapters import edgar as edgar_mod
from verityngn.agent.mcp_v2.store import MemoryStore
from verityngn.agent.mcp_v2.tools import find_section

from .conftest import Client, FakeDisclosure, fake_adapters, make_server, output_valid

LEGEND = "Confidential Treatment Requested by Example AI, PBC"
TOC = [
    ("PROSPECTUS SUMMARY", "1"),
    ("RISK FACTORS", "9"),
    ("SPECIAL NOTE REGARDING FORWARD-LOOKING STATEMENTS", "40"),
    ("USE OF PROCEEDS", "42"),
    ("DILUTION", "44"),
    ("MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF\nOPERATIONS", "46"),
    ("BUSINESS", "70"),
    ("OUR GOVERNANCE STRUCTURE AND ITS GOALS", "90"),
    ("MANAGEMENT", "95"),
    ("EXECUTIVE COMPENSATION", "100"),
    ("PRINCIPAL AND SELLING STOCKHOLDERS", "110"),
    ("DESCRIPTION OF CAPITAL STOCK", "112"),
    ("MATERIAL U.S. FEDERAL INCOME TAX CONSEQUENCES TO NON-U.S. HOLDERS OF OUR CLASS A\nCOMMON STOCK", "120"),
    ("UNDERWRITING", "124"),
    ("LEGAL MATTERS", "130"),
    ("EXPERTS", "130"),
    ("INDEX TO CONSOLIDATED FINANCIAL STATEMENTS", "F-1"),
]
BODY = [
    ("Prospectus Summary", "This summary highlights selected information.\nRisk Factors\nOur business is subject to risks summarized here."),
    ("Risk Factors", "Investing in our Class A common stock involves a high degree of risk.\nWe may experience security incidents that could harm us."),
    ("Special Note Regarding Forward-looking\nStatements", "This prospectus contains forward-looking statements."),
    ("Use of Proceeds", "We estimate net proceeds of $1.0 billion and intend to use them for general corporate purposes."),
    ("Dilution", "Purchasers will experience immediate dilution."),
    ("Management’s Discussion and Analysis of\nFinancial Condition and Results of Operations", "Revenue grew significantly.\nBusiness\nOur business is described below as context."),
    ("Business", "We build frontier AI systems."),
    ("Our Governance Structure and Its Goals", "Our board balances stockholder interests with our public benefit purpose."),
    ("Management", "Our executive officers and directors are listed below."),
    ("Executive Compensation", "Compensation is set by the compensation committee."),
    ("Principal and Selling Stockholders", "The following table sets forth beneficial ownership."),
    ("Description of Capital Stock", "Our authorized capital stock consists of Class A, Class B and Class N common stock."),
    ("Material U.S. Federal Income Tax Consequences\nto Non-U.S. Holders of Our Class A Common\nStock", "The following is a summary of tax consequences."),
    ("Underwriting", "The underwriters named below have agreed to purchase shares."),
    ("Legal Matters", "The validity of the shares will be passed upon by counsel."),
    ("Experts", "The financial statements have been audited."),
    ("Index to Consolidated Financial Statements", "Consolidated Balance Sheets\nNotes to Consolidated Financial Statements\nLegal Matters\nFrom time to time we are party to legal proceedings described in this long note about contingencies and claims."),
]


def synthetic_s1() -> str:
    parts = ["Example AI, PBC", "Class A Common Stock", "Table of Contents", "Table of Contents"]
    for title, page in TOC:
        parts += [title, page]
    page = 1
    for heading, body in BODY:
        parts += [LEGEND, "Table of Contents", heading]
        for para in body.split("\n"):
            parts.append(para if len(para) < 40 else para + " " + "Additional disclosure text. " * 20)
        parts += [str(page), "Table of Contents", LEGEND]
        page += 1
    parts += ["Part II", "INFORMATION NOT REQUIRED IN PROSPECTUS",
              "Item 13.Other Expenses of Issuance and Distribution.", "The expenses are estimated.",
              "Item 14.Indemnification of Directors and Officers.", "Delaware law permits indemnification.",
              "Item 16.Exhibits and Financial Statement Schedules.", "See the exhibit index.",
              "Item 17.Undertakings.", "The registrant undertakes as follows."]
    return documents.normalize_text("\n\n".join(parts))


def _doc(text: str, kind: str = "prospectus"):
    return documents.register(MemoryStore(), tenant="acme", media_type="text/plain", rights="public_source", text=text, outline_kind=kind)


def _section(doc, key: str) -> str:
    e = next(x for x in doc.outline if x["item"] == key)
    return doc.text[e["start"]:e["end"]]


def test_outline_follows_table_of_contents():
    doc = _doc(synthetic_s1())
    keys = [e["item"] for e in doc.outline]
    assert keys == [
        "prospectus-summary", "risk-factors", "forward-looking-statements", "use-of-proceeds", "dilution", "mdna",
        "business", "governance", "management", "executive-compensation", "principal-stockholders",
        "description-of-capital-stock", "tax-considerations", "underwriting", "legal-matters", "experts",
        "financial-statements", "13", "14", "16", "17",
    ]
    rf = _section(doc, "risk-factors")
    assert rf.startswith("Risk Factors\n\nInvesting in our Class A common stock")
    assert "summarized here" not in rf, "the summary's own 'Risk Factors' line is not the section"
    assert rf.rstrip().endswith("Additional disclosure text."), "page numbers, TOC links and legends are trimmed"
    assert _section(doc, "mdna").startswith("Management’s Discussion and Analysis of\nFinancial Condition")
    assert "Our business is described below" in _section(doc, "mdna"), "a 'Business' line inside MD&A is not the section"
    assert _section(doc, "tax-considerations").startswith("Material U.S. Federal Income Tax Consequences")
    assert _section(doc, "legal-matters").startswith("Legal Matters\n\nThe validity of the shares")
    assert "Part II" not in _section(doc, "financial-statements")
    assert _section(doc, "17").startswith("Item 17.Undertakings.")
    heading = next(e for e in doc.outline if e["item"] == "governance")["heading_path"]
    assert heading == ["Our Governance Structure and Its Goals"]


def test_auto_detection_keeps_10k_items():
    from .conftest import TENK

    assert [e["item"] for e in _doc(TENK, "auto").outline] == ["1", "1A", "1B", "2"]
    assert _doc(synthetic_s1(), "auto").outline[0]["item"] == "prospectus-summary"


def test_synthetic_governance_parent_when_no_governance_section():
    text = synthetic_s1().replace("Our Governance Structure and Its Goals", "Our Mission").replace(
        "OUR GOVERNANCE STRUCTURE AND ITS GOALS", "OUR MISSION")
    doc = _doc(text)
    gov = next(e for e in doc.outline if e["item"] == "governance")
    assert gov.get("synthetic") is True and gov["heading_path"][0] == "Governance"
    span = doc.text[gov["start"]:gov["end"]]
    assert span.startswith("Management\n\nOur executive officers") and "Our authorized capital stock" in span
    assert "Material U.S. Federal" not in span


def test_fallback_without_table_of_contents():
    text = "\n\n".join(f"{h}\n\n{b} " + "Text. " * 30 for h, b in BODY)
    keys = [e["item"] for e in _doc(text).outline]
    assert {"prospectus-summary", "risk-factors", "use-of-proceeds", "mdna", "business", "underwriting"} <= set(keys)


@pytest.mark.parametrize(
    "requested,key",
    [("risk-factors", "risk-factors"), ("Risk Factors", "risk-factors"), ("risk_factors", "risk-factors"), ("1A", "risk-factors"),
     ("MD&A", "mdna"), ("7", "mdna"), ("Use of Proceeds", "use-of-proceeds"), ("summary", "prospectus-summary"),
     ("governance", "governance"), ("17", "17")],
)
def test_section_names_and_aliases(requested, key):
    doc = _doc(synthetic_s1())
    assert find_section(doc.outline, requested)["item"] == key


def test_10k_items_win_over_aliases():
    from .conftest import TENK

    doc = _doc(TENK, "auto")
    assert find_section(doc.outline, "1A")["item"] == "1A"
    assert find_section(doc.outline, "8-K:1A")["item"] == "1A"


# ----------------------------------------------------------- tools, mocked EDGAR


def _submissions():
    return {
        "name": "Example AI, PBC",
        "tickers": [],
        "filings": {"recent": {
            "accessionNumber": ["0001628280-26-000002", "0001628280-26-000001", "0000000009-26-000005", "0000000009-26-000004", "0000000009-26-000003"],
            "filingDate": ["2026-10-27", "2026-10-26", "2026-10-09", "2026-06-01", "2026-11-30"],
            "form": ["S-1/A", "S-1", "DRS/A", "DRS", "424B4"],
            "primaryDocument": ["s1a.htm", "s1.htm", "filename1.htm", "filename1.htm", "424b4.htm"],
            "items": ["", "", "", "", ""],
        }, "files": []},
    }


@pytest.fixture
def mocked(monkeypatch):
    urls: list[str] = []
    html = "<html><body>" + "".join(f"<p>{line}</p>" for line in synthetic_s1().split("\n\n")) + "</body></html>"

    def rj(url, **kw):
        urls.append(url)
        if "CIK0000000009.json" in url:
            return _submissions()
        if "CIK0000789019.json" in url:
            return {"name": "MICROSOFT CORP", "formerNames": []}
        if "keysTyped" in url:
            return {"hits": {"hits": [{"_source": {"entity": "Example AI, PBC"}}, {"_source": {"entity": "Example AI SPV LP"}}]}}
        if "efts.sec.gov" in url and "%220001628280-26-000001%22" in url:
            return {"hits": {"hits": [{"_source": {"adsh": "0001628280-26-000001", "ciks": ["0000000009"]}}]}}
        if "efts.sec.gov" in url:
            return {"hits": {"hits": [
                {"_id": "0001628280-26-000002:s1a.htm", "_source": {"adsh": "0001628280-26-000002", "form": "S-1/A", "file_date": "2026-10-27"}},
                {"_id": "0001628280-26-000001:s1.htm", "_source": {"adsh": "0001628280-26-000001", "form": "S-1", "file_date": "2026-10-26"}},
            ]}}
        raise AssertionError(url)

    def rb(url, **kw):
        urls.append(url)
        if "browse-edgar" in url and "Example+AI%2C+PBC" in url:
            return b"<feed><company-info><cik>0000000009</cik><conformed-name>Example AI, PBC</conformed-name></company-info><entry></entry></feed>"
        if "browse-edgar" in url:
            return b"<feed><entry><company-info><cik>0000000077</cik></company-info></entry></feed>"
        return html.encode()

    monkeypatch.setattr(edgar_mod, "request_json", rj)
    monkeypatch.setattr(edgar_mod, "request", rb)
    monkeypatch.setattr(edgar_mod.EdgarClient, "company_tickers", lambda self: [{"cik_str": 789019, "ticker": "MSFT", "title": "MICROSOFT CORP"}])
    client = Client(make_server(adapters=fake_adapters(edgar=edgar_mod.EdgarClient())))
    return client, urls


def test_prospectus_forms_in_filings_search(mocked):
    client, urls = mocked
    window = {"from": "2026-05-01", "to": (dt.date.today()).isoformat()}

    def forms(requested):
        out = client.ok("filings_search", {"cik": "9", "forms": requested, "window": window})
        output_valid("filings_search", out)
        return [f["form"] for f in out["filings"]]

    assert forms(["S-1"]) == ["S-1/A", "S-1"], "a base form includes its amendments"
    assert forms(["S-1/A"]) == ["S-1/A"], "an /A form returns amendments only"
    assert forms(["DRS"]) == ["DRS/A", "DRS"]
    assert forms(["F-1", "424B1"]) == []
    out = client.ok("filings_search", {"cik": "9", "forms": ["S-1/A"], "query": "public benefit", "window": window})
    assert [f["form"] for f in out["filings"]] == ["S-1/A"]
    assert any("forms=S-1&" in u for u in urls if "efts" in u and "public" in u), "full-text search asks for the base form"


def test_pre_ipo_registrant_resolves_by_name_and_cik(mocked):
    client, _ = mocked
    by_name = client.ok("resolve_entity", {"name": "Example AI"})["candidates"]
    assert by_name[0]["cik"] == "9" and by_name[0]["name"] == "Example AI, PBC" and by_name[0]["tickers"] == []
    assert len(by_name) == 1, "a multi-company feed without a top-level company is skipped"
    by_cik = client.ok("resolve_entity", {"cik": "9"})["candidates"]
    assert by_cik[0]["entity_id"] == "sr:ent:cik0000000009" and by_cik[0]["name"] == "Example AI, PBC"
    assert client.ok("resolve_entity", {"ticker": "MSFT"})["candidates"][0]["cik"] == "789019"


def test_get_filing_section_for_s1(mocked):
    client, urls = mocked
    out = client.ok("get_filing_section", {"accession": "0001628280-26-000001", "item": "Risk Factors"})
    output_valid("get_filing_section", out)
    assert out["url"].endswith("/data/9/000162828026000001/s1.htm")
    assert out["target"]["section"]["item"] == "risk-factors" and out["target"]["anchor_status"] == "exact"
    assert not any("/data/1628280/" in u for u in urls), "the filing agent's CIK is never used"
    body = client.rpc("resources/read", {"uri": out["document_uri"]})
    import json

    doc = json.loads(body["contents"][0]["text"])
    assert doc["normalizer"] == "html+sr-norm-1" and doc["outline"][0]["item"] == "prospectus-summary"
    stored = client.server.store.get_document(out["doc_id"], "acme")
    res = anchors.resolve(out["target"], stored)
    assert stored.text[res.start:res.end].startswith("Risk Factors\n\nInvesting")
    for item in ("use-of-proceeds", "MD&A", "governance", "1A"):
        assert client.ok("get_filing_section", {"accession": "0001628280-26-000001", "cik": "9", "item": item})["target"]["section"]["item"]
    err = client.err("get_filing_section", {"accession": "0001628280-26-000001", "cik": "9", "item": "Item 1C"})
    assert err["code"] == "ANCHOR_UNRESOLVED" and "risk-factors" in err["details"]["items_found"]


def test_prior_version_reaches_the_engine_section_by_section():
    engine = FakeDisclosure()
    client = Client(make_server(adapters=fake_adapters(disclosure=engine)))
    current = synthetic_s1()
    prior = current.replace("Use of Proceeds", "Uses of Funds").replace("USE OF PROCEEDS", "USES OF FUNDS")
    prior_id = client.ok("register_document", {"text": prior, "media_type": "text/plain", "rights": "public_source"})["doc_id"]
    doc_id = client.ok("register_document", {"text": current, "media_type": "text/plain", "rights": "public_source"})["doc_id"]
    out = client.ok("assess_document", {"doc_id": doc_id, "domain_pack": "securities_disclosure", "prior_doc_id": prior_id})
    client.wait_report(out["report_id"])
    req = engine.calls[-1]
    assert req.prior_text and req.prior_outline
    pairs = {p["item"]: p for p in req.section_pairs}
    assert pairs["risk-factors"]["current"] and pairs["risk-factors"]["prior"]
    assert pairs["use-of-proceeds"]["prior"] is None and pairs["uses-of-funds"]["current"] is None
    assert current[pairs["risk-factors"]["current"]["start"]:].startswith("Risk Factors")


def test_prospectus_forms_constant_matches_contract():
    from verityngn.agent.mcp_v2.contracts import contract

    enum = set(contract("filings_search")["inputSchema"]["properties"]["forms"]["items"]["enum"])
    assert prospectus.PROSPECTUS_FORMS <= enum
