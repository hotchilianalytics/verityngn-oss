"""Section outline for registration statements and prospectuses (S-1, F-1, 424B*).

A prospectus lists its own sections in a table of contents (title lines each
followed by a page number). Each title is located in the body, choosing the
occurrence with the longest span, since summaries repeat some headings. Titles
map to stable keys (``risk-factors``, ``mdna``, ``governance``...); titles
without a known key get a slug of the title. Without a usable table of
contents, a fixed list of standard headings is matched instead.
"""

from __future__ import annotations

import re
from typing import Any, Optional

PROSPECTUS_FORMS = frozenset(
    {"S-1", "S-1/A", "F-1", "F-1/A", "424B1", "424B3", "424B4", "DRS", "DRS/A"}
)

SECTION_KEYS: list[tuple[str, str]] = [
    ("prospectus-summary", r"^(prospectus )?summary$"),
    ("risk-factors", r"^risk factors$"),
    ("forward-looking-statements", r"forward.looking statements"),
    ("market-and-industry-data", r"(market|industry).*data$"),
    ("use-of-proceeds", r"^use of proceeds$"),
    ("dividend-policy", r"^dividend policy$"),
    ("capitalization", r"^capitali[sz]ation$"),
    ("dilution", r"^dilution$"),
    ("selected-financial-data", r"selected .*financial"),
    ("mdna", r"^management.s discussion and analysis"),
    ("business", r"^(our )?business$"),
    ("governance", r"governance"),
    ("management", r"^(directors and )?(executive officers and )?management$"),
    ("executive-compensation", r"^executive compensation$"),
    ("related-party-transactions", r"related (person|party) transactions"),
    ("principal-stockholders", r"^principal (and selling )?(stock|share)holders$"),
    ("description-of-capital-stock", r"^description of (capital stock|share capital)"),
    ("shares-eligible-for-future-sale", r"^shares eligible for future sale"),
    ("tax-considerations", r"tax (consequences|considerations)|^taxation$"),
    ("underwriting", r"^underwriting|^plan of distribution$"),
    ("legal-matters", r"^legal matters$"),
    ("experts", r"^experts$"),
    ("additional-information", r"^where you can find"),
    ("financial-statements", r"^index to .*financial statements"),
]
GOVERNANCE_CHILDREN = (
    "management",
    "executive-compensation",
    "related-party-transactions",
    "principal-stockholders",
    "description-of-capital-stock",
)
ITEM_ALIASES = {"1A": "risk-factors", "7": "mdna", "1": "business", "SUMMARY": "prospectus-summary", "MD&A": "mdna"}

_PAGE = re.compile(r"^(\d{1,3}|[ivxlc]{1,7}|F-\d{1,3}|II-\d{1,3})$", re.I)
_SKIP = {"table of contents", "page", "contents"}


def _norm(s: str) -> str:
    s = s.lower().replace("\u2019", "'").replace("\u2018", "'")
    return re.sub(r"\s+", " ", s).strip()


def section_key(title: str) -> str:
    t = _norm(title)
    for key, pattern in SECTION_KEYS:
        if re.search(pattern, t):
            return key
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:60] or "section"


def normalize_item(requested: str) -> str:
    """Map a requested section ('Risk Factors', 'risk_factors', '1A', 'MD&A') to an outline key."""
    raw = requested.strip()
    if raw.upper() in ITEM_ALIASES:
        return ITEM_ALIASES[raw.upper()]
    key = re.sub(r"[\s_]+", "-", raw.lower())
    if any(key == k for k, _ in SECTION_KEYS):
        return key
    return section_key(raw)


def _lines(text: str) -> list[tuple[int, str]]:
    out = []
    pos = 0
    for line in text.split("\n"):
        s = line.strip()
        if s:
            out.append((pos + (len(line) - len(line.lstrip())), s))
        pos += len(line) + 1
    return out


def _toc(lines: list[tuple[int, str]]) -> tuple[list[str], int]:
    """First run of at least six 'title, page number' pairs.

    Returns the titles and the index of the first line after the run, which may
    be the first body heading itself.
    """
    pairs: list[str] = []
    buf: list[str] = []
    buf_at = 0
    last_page = -1
    for i, (_, line) in enumerate(lines):
        if _PAGE.match(line):
            page = int(line) if line.isdigit() else last_page
            if buf and page >= last_page:
                pairs.append(" ".join(buf if pairs else buf[-1:]))
                last_page = page
                buf = []
                continue
            if len(pairs) >= 6:
                return pairs, buf_at if buf else i
            pairs, buf, last_page = [], [], -1
            continue
        if _norm(line) in _SKIP:
            buf = []
            continue
        if len(line) > 120 or len(buf) >= 3:
            if len(pairs) >= 6:
                return pairs, buf_at if buf else i
            pairs, buf, last_page = [], [], -1
            if len(line) > 120:
                continue
        if not buf:
            buf_at = i
        buf.append(line)
    return (pairs, len(lines)) if len(pairs) >= 6 else ([], 0)


def _page_start(lines: list[tuple[int, str]], i: int) -> bool:
    """A heading that opens a page follows a page number or a 'Table of Contents' link."""
    if i == 0:
        return True
    prev = lines[i - 1][1]
    return bool(_PAGE.match(prev)) or _norm(prev) in _SKIP


def _occurrences(lines: list[tuple[int, str]], start_idx: int, titles: set[str]) -> dict[str, list[tuple[int, str, bool]]]:
    found: dict[str, list[tuple[int, str, bool]]] = {}
    for i in range(start_idx, len(lines)):
        joined = ""
        for k in range(3):
            if i + k >= len(lines):
                break
            joined = (joined + " " + lines[i + k][1]).strip() if k else lines[i][1]
            key = _norm(joined)
            if key in titles:
                found.setdefault(key, []).append((lines[i][0], joined, _page_start(lines, i)))
                break
            if len(joined) > 160:
                break
    return found


def _choose(candidates: list[tuple[int, str, str]], text_len: int, page_starts: frozenset[int] = frozenset()) -> list[tuple[int, str, str]]:
    """Per key, prefer an occurrence that opens a page, then the longest span to the next candidate."""
    candidates.sort()
    best: dict[str, tuple[tuple[bool, int], int, str]] = {}
    for i, (start, key, heading) in enumerate(candidates):
        end = candidates[i + 1][0] if i + 1 < len(candidates) else text_len
        rank = (start in page_starts, end - start)
        if key not in best or rank > best[key][0]:
            best[key] = (rank, start, heading)
    return sorted((s, k, h) for k, (_, s, h) in best.items())


def _in_toc_order(
    chosen: list[tuple[int, str, str]],
    candidates: list[tuple[int, str, str]],
    order: list[str],
    page_starts: frozenset[int] = frozenset(),
) -> list[tuple[int, str, str]]:
    """Re-pick sections whose chosen occurrence breaks the table-of-contents order."""
    by_key = {k: (s, h) for s, k, h in chosen}
    occ: dict[str, list[tuple[int, str]]] = {}
    for s, k, h in candidates:
        occ.setdefault(k, []).append((s, h))
    keys = [k for k in dict.fromkeys(order) if k in by_key]
    for i, key in enumerate(keys):
        lo = by_key[keys[i - 1]][0] if i else -1
        hi = next((by_key[k][0] for k in keys[i + 1:] if by_key[k][0] > lo), None)
        pos = by_key[key][0]
        if pos > lo and (hi is None or pos < hi):
            continue
        fits = [(s, h) for s, h in occ[key] if s > lo and (hi is None or s < hi)]
        if fits:
            by_key[key] = max(fits, key=lambda o: (o[0] in page_starts, _span(o[0], candidates)))
        else:
            del by_key[key]
    return sorted((s, k, h) for k, (s, h) in by_key.items())


def _span(start: int, candidates: list[tuple[int, str, str]]) -> int:
    later = [c[0] for c in candidates if c[0] > start]
    return (min(later) - start) if later else 1 << 30


FURNITURE_MIN_REPEATS = 20
FURNITURE_MIN_CHARS = 25


def furniture_lines(text: str) -> frozenset[str]:
    """Running page headers and footers: lines repeated on many pages (for example a confidential-treatment legend)."""
    counts: dict[str, int] = {}
    for _, line in _lines(text):
        if len(line) <= 200:
            key = _norm(line)
            counts[key] = counts.get(key, 0) + 1
    return frozenset(k for k, n in counts.items() if n >= FURNITURE_MIN_REPEATS and len(k) >= FURNITURE_MIN_CHARS)


def prospectus_sections(text: str) -> list[tuple[int, str, str]]:
    """(start, key, heading) for each top-level prospectus section, in document order."""
    furniture = furniture_lines(text)
    lines = [(p, ln) for p, ln in _lines(text) if _norm(ln) not in furniture]
    titles, after = _toc(lines)
    candidates: list[tuple[int, str, str]] = []
    order: list[str] = []
    if titles:
        wanted = {_norm(t) for t in titles}
        order = [section_key(t) for t in titles]
        page_starts: set[int] = set()
        for title_norm, occ in _occurrences(lines, after, wanted).items():
            key = section_key(title_norm)
            candidates += [(pos, key, heading) for pos, heading, _ in occ]
            page_starts.update(pos for pos, _, opens in occ if opens)
    if len({c[1] for c in candidates}) >= 4:
        return _in_toc_order(_choose(candidates, len(text), frozenset(page_starts)), candidates, order, frozenset(page_starts))
    known = {k for k, _ in SECTION_KEYS}
    fallback = [(pos, section_key(line), line) for pos, line in lines if len(line) <= 120 and section_key(line) in known]
    return _choose(fallback, len(text)) if fallback else []


def trim_page_furniture(text: str, start: int, end: int, furniture: frozenset[str] = frozenset()) -> int:
    """Pull a section end back past trailing page numbers, 'Table of Contents' links and running headers."""
    while end > start:
        line_start = text.rfind("\n", start, end) + 1
        line = text[line_start:end].strip()
        if line and not (_PAGE.match(line) or _norm(line) in _SKIP or _norm(line) in furniture):
            break
        end = max(start, line_start)
        while end > start and text[end - 1].isspace():
            end -= 1
    return end


def part_ii_start(text: str) -> Optional[int]:
    m = re.search(r"\n(part ii\s*\n+\s*)?information not required in (the )?prospectus\s*\n", text, re.I)
    return m.start() + 1 if m else None


def governance_parent(entries: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """A 'governance' entry spanning the contiguous management-to-capital-stock run, when the filing has no governance section."""
    if any(e["item"] == "governance" for e in entries):
        return None
    run = [e for e in entries if e["item"] in GOVERNANCE_CHILDREN]
    if not run:
        return None
    return {
        "heading_path": ["Governance"] + [run[0]["heading_path"][0]],
        "item": "governance",
        "start": run[0]["start"],
        "end": run[-1]["end"],
        "synthetic": True,
    }
