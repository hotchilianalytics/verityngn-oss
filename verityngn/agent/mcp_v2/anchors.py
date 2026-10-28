"""W3C Web Annotation targets (SplitRisk concept section 2.6).

A target carries a robust selector (the quote with prefix and suffix) and a
fast one (a position in the normalized text). The quote is authoritative.
Resolution order: exact, fuzzy (>= 0.85, prefix/suffix scored), approximate
(page or time fragment only), orphaned.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from typing import Any, Optional

from verityngn.agent.mcp_v2.errors import ToolFailure
from verityngn.agent.mcp_v2.store import Document

RFC3778 = "http://tools.ietf.org/rfc/rfc3778"
MEDIA_FRAGS = "http://www.w3.org/TR/media-frags/"
CONTEXT_CHARS = 32
FUZZY_ACCEPT = 0.85
VIDEO_SOURCE = "urn:splitrisk:video:youtube:"


@dataclass
class Resolved:
    start: int
    end: int
    status: str
    score: float = 1.0


def _quote(text: str, start: int, end: int) -> dict[str, Any]:
    sel: dict[str, Any] = {"type": "TextQuoteSelector", "exact": text[start:end]}
    prefix = text[max(0, start - CONTEXT_CHARS):start]
    suffix = text[end:end + CONTEXT_CHARS]
    if prefix:
        sel["prefix"] = prefix
    if suffix:
        sel["suffix"] = suffix
    return sel


def _position(start: int, end: int) -> dict[str, Any]:
    return {"type": "TextPositionSelector", "start": start, "end": end}


def _fmt_t(seconds: float) -> str:
    return f"{seconds:.3f}".rstrip("0").rstrip(".")


def cues_for(doc: Document, start: int, end: int) -> list[dict[str, Any]]:
    return [c for c in doc.cues if c["end"] > start and c["start"] < end]


def span_target(doc: Document, start: int, end: int, *, status: Optional[str] = None) -> dict[str, Any]:
    selectors = [_quote(doc.text, start, end), _position(start, end)]
    scope = "span"
    if doc.cues:
        hit = cues_for(doc, start, end)
        if hit:
            scope = "time_range"
            selectors = [
                {
                    "type": "FragmentSelector",
                    "conformsTo": MEDIA_FRAGS,
                    "value": f"t={_fmt_t(hit[0]['start_s'])},{_fmt_t(hit[-1]['end_s'])}",
                    "refinedBy": _quote(doc.text, start, end),
                },
                _position(start, end),
            ]
    target: dict[str, Any] = {
        "source": doc.doc_id,
        "scope": scope,
        "selector": selectors,
        "source_hash": doc.source_hash,
    }
    if status:
        target["anchor_status"] = status
    return target


def section_target(doc: Document, entry: dict[str, Any], *, status: Optional[str] = None) -> dict[str, Any]:
    start, end = entry["start"], entry["end"]
    heading_end = doc.text.find("\n", start, end)
    heading_end = end if heading_end == -1 else heading_end
    nxt = end
    while nxt < len(doc.text) and doc.text[nxt].isspace():
        nxt += 1
    after = doc.text[nxt:nxt + 120].split("\n", 1)[0][:64]
    end_sel = {"type": "TextQuoteSelector", "exact": after} if after else _quote(doc.text, max(start, end - 64), end)
    target: dict[str, Any] = {
        "source": doc.doc_id,
        "scope": "section",
        "selector": [
            {"type": "RangeSelector", "startSelector": _quote(doc.text, start, heading_end), "endSelector": end_sel},
            _position(start, end),
        ],
        "section": {"item": entry.get("item", ""), "heading_path": entry.get("heading_path", [])},
        "source_hash": doc.source_hash,
    }
    if status:
        target["anchor_status"] = status
    return target


def document_target(doc: Document, *, status: Optional[str] = None) -> dict[str, Any]:
    target: dict[str, Any] = {"source": doc.doc_id, "scope": "document", "source_hash": doc.source_hash}
    if status:
        target["anchor_status"] = status
    return target


def video_target(video_id: str, start_s: float, end_s: float, quote: str = "") -> dict[str, Any]:
    frag: dict[str, Any] = {"type": "FragmentSelector", "conformsTo": MEDIA_FRAGS, "value": f"t={_fmt_t(start_s)},{_fmt_t(end_s)}"}
    if quote:
        frag["refinedBy"] = {"type": "TextQuoteSelector", "exact": quote}
    return {"source": VIDEO_SOURCE + video_id, "scope": "time_range", "selector": [frag]}


def _selectors(target: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    return [s for s in target.get("selector") or [] if s.get("type") == kind]


def _context_score(text: str, start: int, end: int, sel: dict[str, Any]) -> float:
    score = 0.0
    prefix, suffix = sel.get("prefix") or "", sel.get("suffix") or ""
    if prefix:
        score += difflib.SequenceMatcher(None, text[max(0, start - len(prefix)):start], prefix).ratio()
    if suffix:
        score += difflib.SequenceMatcher(None, text[end:end + len(suffix)], suffix).ratio()
    return score


def _ratio(a: str, b: str) -> float:
    try:
        from rapidfuzz import fuzz

        return fuzz.ratio(a, b) / 100.0
    except ImportError:
        return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


def _refine(text: str, needle: str, s: int, e: int, slack: int = 8) -> tuple[int, int, float]:
    """Nudge alignment boundaries so insertions or deletions inside the quote are covered."""
    best = (s, e, _ratio(needle, text[s:e]))
    for ds in range(-slack, slack + 1):
        for de in range(-slack, slack + 1):
            s2, e2 = max(0, s + ds), min(len(text), e + de)
            if e2 <= s2:
                continue
            r = _ratio(needle, text[s2:e2])
            if r > best[2] or (r == best[2] and (e2 - s2) < (best[1] - best[0])):
                best = (s2, e2, r)
    s, e, r = best
    while s < e and text[s].isspace():
        s += 1
    while e > s and text[e - 1].isspace():
        e -= 1
    return s, e, r


def fuzzy_find(text: str, needle: str, hint: Optional[int], accept: float = FUZZY_ACCEPT) -> Optional[tuple[int, int, float]]:
    """Best approximate occurrence of ``needle``: (start, end, similarity), or None below ``accept``."""
    if not needle:
        return None
    try:
        from rapidfuzz import fuzz
    except ImportError:
        fuzz = None
    windows = []
    if hint is not None:
        lo = max(0, hint - 4000)
        windows.append((lo, min(len(text), hint + len(needle) + 4000)))
    windows.append((0, len(text)))
    for lo, hi in windows:
        hay = text[lo:hi]
        if fuzz is not None:
            res = fuzz.partial_ratio_alignment(needle, hay, score_cutoff=accept * 100 - 5)
            if res is None:
                continue
            s, e = lo + res.dest_start, lo + res.dest_end
        else:
            m = difflib.SequenceMatcher(None, hay, needle, autojunk=False).find_longest_match(0, len(hay), 0, len(needle))
            if not m.size:
                continue
            s = lo + max(0, m.a - m.b)
            e = min(len(text), s + len(needle))
        s, e, ratio = _refine(text, needle, s, e)
        if ratio >= accept:
            return s, e, ratio
    return None


def best_alignment(text: str, needle: str) -> float:
    """Similarity of the best alignment, for reporting a failed match."""
    try:
        from rapidfuzz import fuzz

        res = fuzz.partial_ratio_alignment(needle, text)
        return (res.score / 100.0) if res else 0.0
    except ImportError:
        return 0.0


def resolve_quote(doc: Document, sel: dict[str, Any], hint: Optional[int], hash_ok: bool) -> Optional[Resolved]:
    text, exact = doc.text, sel.get("exact") or ""
    if not exact:
        return None
    hits = [m.start() for m in re.finditer(re.escape(exact), text)]
    if hits:
        def rank(s: int) -> tuple[float, float]:
            return (_context_score(text, s, s + len(exact), sel), -abs(s - hint) if hint is not None else 0.0)

        best = max(hits, key=rank)
        status = "exact" if hash_ok and hint == best else "fuzzy"
        return Resolved(best, best + len(exact), status, 1.0)
    found = fuzzy_find(text, exact, hint)
    if found:
        return Resolved(found[0], found[1], "fuzzy", round(found[2], 4))
    return None


def _time_range(value: str) -> Optional[tuple[float, float]]:
    m = re.match(r"^t=(?:npt:)?([\d.]+)(?:,([\d.]+))?$", value or "")
    if not m:
        return None
    start = float(m.group(1))
    return start, float(m.group(2)) if m.group(2) else start


def resolve(target: dict[str, Any], doc: Document) -> Resolved:
    """Resolve a target against the current text of ``doc``."""
    scope = target.get("scope")
    hash_ok = not target.get("source_hash") or target.get("source_hash") == doc.source_hash
    if scope == "document":
        return Resolved(0, len(doc.text), "exact" if hash_ok else "approximate")

    positions = _selectors(target, "TextPositionSelector")
    pos = positions[0] if positions else None
    hint = pos["start"] if pos else None

    if scope == "section":
        item = (target.get("section") or {}).get("item")
        ranges = _selectors(target, "RangeSelector")
        if ranges:
            rs = ranges[0]
            s = resolve_quote(doc, rs.get("startSelector") or {}, hint, hash_ok)
            if s:
                e = resolve_quote(doc, rs.get("endSelector") or {}, pos["end"] if pos else None, hash_ok)
                end = e.start if e and e.start > s.start else (pos["end"] if pos and hash_ok else len(doc.text))
                while end > s.start and doc.text[end - 1].isspace():
                    end -= 1
                end_exact = not e or e.status == "exact" or (
                    hash_ok and pos is not None and pos["end"] <= e.start and not doc.text[pos["end"]:e.start].strip()
                )
                status = "exact" if s.status == "exact" and end_exact else "fuzzy"
                return Resolved(s.start, end, status, min(s.score, e.score if e else 1.0))
        if item:
            for entry in doc.outline:
                if entry.get("item", "").upper() == str(item).upper():
                    return Resolved(entry["start"], entry["end"], "exact" if hash_ok else "fuzzy")
        if pos and hash_ok and pos["end"] <= len(doc.text):
            return Resolved(pos["start"], pos["end"], "exact")
        return Resolved(0, 0, "orphaned", 0.0)

    quotes = _selectors(target, "TextQuoteSelector")
    frags = _selectors(target, "FragmentSelector")
    for frag in frags:
        refined = frag.get("refinedBy") or {}
        if refined.get("type") == "TextQuoteSelector":
            quotes.append(refined)

    if pos and hash_ok and quotes and 0 <= pos["start"] <= pos["end"] <= len(doc.text):
        if doc.text[pos["start"]:pos["end"]] == quotes[0].get("exact"):
            return Resolved(pos["start"], pos["end"], "exact")
    for q in quotes:
        res = resolve_quote(doc, q, hint, hash_ok)
        if res:
            return res
    if not quotes and pos and hash_ok and 0 <= pos["start"] <= pos["end"] <= len(doc.text):
        return Resolved(pos["start"], pos["end"], "exact")

    for frag in frags:
        if frag.get("conformsTo") == MEDIA_FRAGS and doc.cues:
            tr = _time_range(frag.get("value", ""))
            if tr:
                hit = [c for c in doc.cues if c["end_s"] > tr[0] and c["start_s"] <= tr[1]]
                if hit:
                    return Resolved(hit[0]["start"], hit[-1]["end"], "approximate", 0.0)
    return Resolved(0, 0, "orphaned", 0.0)


def resolve_input(target: dict[str, Any], doc: Document) -> Resolved:
    res = resolve(target, doc)
    if res.status == "orphaned" or res.end <= res.start:
        raise ToolFailure(
            "ANCHOR_UNRESOLVED",
            "The selection could not be found in this version of the document.",
            alternative="Re-select the passage in the current version, or assess the whole document.",
            details={"source": target.get("source"), "source_hash": doc.source_hash},
        )
    return res


def echo_target(target: dict[str, Any], doc: Document, res: Resolved) -> dict[str, Any]:
    """The input target, re-anchored to the current text with ``anchor_status`` set."""
    if target.get("scope") == "document":
        return document_target(doc, status=res.status)
    if target.get("scope") == "section":
        entry = {
            "start": res.start,
            "end": res.end,
            "item": (target.get("section") or {}).get("item", ""),
            "heading_path": (target.get("section") or {}).get("heading_path", []),
        }
        return section_target(doc, entry, status=res.status)
    out = span_target(doc, res.start, res.end, status=res.status)
    for frag in _selectors(target, "FragmentSelector"):
        if frag.get("conformsTo") == RFC3778:
            out["selector"].append(frag)
    return out
