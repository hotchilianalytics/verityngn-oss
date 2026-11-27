"""W3C anchor model (concept section 2.6): exact, fuzzy, approximate, orphaned."""

from __future__ import annotations

from verityngn.agent.mcp_v2 import anchors, documents
from verityngn.agent.mcp_v2.store import MemoryStore

from .conftest import HEDGED, TENK, VTT


def _doc(text: str, media_type: str = "text/plain"):
    return documents.register(MemoryStore(), tenant="acme", media_type=media_type, rights="public_source", text=text)


def _span(doc, needle: str) -> dict:
    i = doc.text.index(needle)
    return anchors.span_target(doc, i, i + len(needle))


def test_span_target_shape_and_exact_round_trip():
    doc = _doc(TENK)
    target = _span(doc, HEDGED)
    quote, pos = target["selector"]
    assert quote["type"] == "TextQuoteSelector" and quote["exact"] == HEDGED
    assert len(quote["prefix"]) <= 64 and len(quote["suffix"]) <= 64
    assert pos == {"type": "TextPositionSelector", "start": doc.text.index(HEDGED), "end": doc.text.index(HEDGED) + len(HEDGED)}
    res = anchors.resolve(target, doc)
    assert res.status == "exact" and doc.text[res.start:res.end] == HEDGED


def test_whitespace_and_ligature_changes_normalize_away():
    doc = _doc(TENK)
    target = _span(doc, HEDGED)
    rerendered = _doc(TENK.replace("We may experience", "We  may\u00a0experience").replace("Example Corp", "Example Corp\u00a0"))
    res = anchors.resolve(target, rerendered)
    assert res.status in ("exact", "fuzzy")
    assert rerendered.text[res.start:res.end] == HEDGED
    lig = _doc("The \ufb01nancial statements are \ufb01led late.")
    assert "financial" in lig.text and "filed" in lig.text


def test_fuzzy_after_edit_and_shift():
    doc = _doc(TENK)
    target = _span(doc, HEDGED)
    edited = _doc("New preface paragraph inserted by counsel.\n" + TENK.replace("We may experience cybersecurity", "We may experience cyber-security"))
    res = anchors.resolve(target, edited)
    assert res.status == "fuzzy"
    assert res.score >= anchors.FUZZY_ACCEPT
    assert "cyber-security incidents" in edited.text[res.start:res.end]


def test_orphaned_after_deletion_and_assess_reports_it(client):
    doc = _doc(TENK)
    target = _span(doc, HEDGED)
    gone = _doc(TENK.replace("Risks Relating to Cybersecurity. We may experience cybersecurity incidents that could materially adversely affect our business and reputation.\n", ""))
    assert anchors.resolve(target, gone).status == "orphaned"

    v1 = client.ok("register_document", {"text": TENK, "media_type": "text/plain", "rights": "public_source"})
    v2 = client.ok("register_document", {"text": gone.text, "media_type": "text/plain", "rights": "public_source"})
    t = dict(target, source=v2["doc_id"], source_hash=v1["source_hash"])
    err = client.err("assess_selection", {"target": t, "domain_pack": "securities_disclosure"})
    assert err["code"] == "ANCHOR_UNRESOLVED" and err["alternative"]


def test_section_target_from_outline_and_range_selector():
    doc = _doc(TENK)
    entry = next(e for e in doc.outline if e["item"] == "1A")
    target = anchors.section_target(doc, entry)
    rs = target["selector"][0]
    assert rs["type"] == "RangeSelector"
    assert rs["startSelector"]["exact"].startswith("ITEM 1A")
    assert rs["endSelector"]["exact"].startswith("ITEM 1B")
    assert target["section"]["item"] == "1A"
    res = anchors.resolve(target, doc)
    assert res.status == "exact"
    assert HEDGED in doc.text[res.start:res.end] and "ITEM 1B" not in doc.text[res.start:res.end]
    edited = _doc(TENK.replace("Example Corp builds software.", "Example Corp builds software and services."))
    res2 = anchors.resolve(target, edited)
    assert res2.status in ("exact", "fuzzy") and HEDGED in edited.text[res2.start:res2.end]


def test_outline_prefers_body_over_table_of_contents():
    toc = "TABLE OF CONTENTS\nItem 1A. Risk Factors 12\nItem 1B. Unresolved Staff Comments 30\n"
    doc = _doc(toc + TENK)
    one_a = next(e for e in doc.outline if e["item"] == "1A")
    assert HEDGED in doc.text[one_a["start"]:one_a["end"]]


def test_outline_merges_running_page_headers():
    body = (
        "PART I\nItem 1A\nITEM 1A. RISK FACTORS\nFirst risk.\n12\nPART I\nItem 1A\nSecond risk continues here.\n"
        "13\nPART I\nItem 1B, 1C\nITEM 1B. UNRESOLVED STAFF COMMENTS\nNone.\n"
        "ITEM 7. MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS AND OTHER LONG TITLE TEXT THAT RUNS PAST ONE HUNDRED AND TWENTY CHARACTERS\nMD&A text.\n"
    )
    doc = _doc(body)
    items = {e["item"]: e for e in doc.outline}
    one_a = doc.text[items["1A"]["start"]:items["1A"]["end"]]
    assert "First risk." in one_a and "Second risk continues here." in one_a and "UNRESOLVED" not in one_a
    assert items["1A"]["heading_path"] == ["ITEM 1A. RISK FACTORS"]
    assert items["1B"]["heading_path"] == ["ITEM 1B. UNRESOLVED STAFF COMMENTS"]
    assert "7" in items


def test_time_range_round_trip_on_webvtt():
    doc = _doc(VTT, media_type="text/vtt")
    assert len(doc.cues) == 3 and doc.cues[1]["start_s"] == 5.0
    needle = "Our systems have never been breached by any attacker."
    target = _span(doc, needle)
    assert target["scope"] == "time_range"
    frag = target["selector"][0]
    assert frag == {"type": "FragmentSelector", "conformsTo": anchors.MEDIA_FRAGS, "value": "t=5,9", "refinedBy": frag["refinedBy"]}
    assert frag["refinedBy"]["exact"] == needle
    res = anchors.resolve(target, doc)
    assert doc.text[res.start:res.end] == needle and res.status in ("exact", "fuzzy")
    time_only = {"source": doc.doc_id, "scope": "time_range", "selector": [{"type": "FragmentSelector", "conformsTo": anchors.MEDIA_FRAGS, "value": "t=10,12"}]}
    res = anchors.resolve(time_only, doc)
    assert res.status == "approximate" and doc.text[res.start:res.end].startswith("We expect revenue")


def test_pdf_page_fragment_is_echoed(client, doc_id):
    doc = client.server.store.get_document(doc_id, "acme")
    target = _span(doc, HEDGED)
    target["selector"].append({"type": "FragmentSelector", "conformsTo": anchors.RFC3778, "value": "page=23&viewrect=72,410,468,36"})
    out = client.ok("assess_selection", {"target": target, "domain_pack": "securities_disclosure"})
    assert out["target"]["anchor_status"] == "exact"
    assert {"type": "FragmentSelector", "conformsTo": anchors.RFC3778, "value": "page=23&viewrect=72,410,468,36"} in out["target"]["selector"]
