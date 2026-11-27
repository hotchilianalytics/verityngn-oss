"""Published test vectors for the ``sr-norm-1`` normalizer.

``python -m verityngn.agent.mcp_v2.norm_vectors > verityngn/agent/mcp_v2/data/sr-norm-1.vectors.json``
regenerates the committed file; a unit test fails if the file and the code
disagree. Clients that compute anchors themselves (for example the SplitRisk
app) mirror these vectors.
"""

from __future__ import annotations

import hashlib
import json
import sys
from typing import Any

from verityngn.agent.mcp_v2.documents import NORMALIZER, normalize_text, source_hash, to_text

STRIP_SET = [f"U+{c:04X}" for c in range(sys.maxunicode + 1) if chr(c).isspace()]

DEFINITION = {
    "name": NORMALIZER,
    "applies_to": "text/plain registration, and the final step of every other media type (html+sr-norm-1, webvtt+sr-norm-1, docling+sr-norm-1)",
    "steps": [
        "1. Input is a Unicode string. Bytes are decoded as UTF-8 with invalid sequences replaced by U+FFFD.",
        "2. Apply Unicode NFKC normalization.",
        "3. Replace CR LF with LF, then any remaining CR with LF, then U+00A0 with U+0020.",
        "4. Replace every run of one or more of U+0020, U+0009, U+000C, U+000B with a single U+0020.",
        "5. Split on LF. Strip leading and trailing characters of the strip set from each line. Join with LF.",
        "6. Replace every run of three or more LF with exactly two LF.",
        "7. Strip leading and trailing characters of the strip set from the whole text.",
    ],
    "strip_set": STRIP_SET,
    "strip_set_note": "Python str.isspace(). Characters in the set that step 4 does not collapse (for example U+2028, U+0085, U+001C-U+001F, U+1680) are kept inside a line and removed only at line edges. U+200B is not in the set.",
    "line_breaks": "Kept. Paragraph breaks become exactly one blank line.",
    "source_hash": "'sha256:' + lowercase hex SHA-256 of the UTF-8 bytes of the normalized text",
    "doc_id": "'sr:doc:' + tenant + '/' + first 32 lowercase hex chars of SHA-256(UTF-8(tenant + LF + normalized text))",
    "positions": "TextPositionSelector start and end count Unicode code points in the normalized text (W3C Web Annotation). Each vector also gives UTF-16 code-unit offsets for JavaScript clients.",
}

TENK = (
    "ITEM 1A. RISK FACTORS\r\n\r\n"
    "Risks Relating to Cybersecurity.  We may experience cybersecurity incidents that could materially\u00a0adversely affect us.   \r\n"
    "\r\n\r\n\r\n"
    "ITEM 1B.\tUNRESOLVED STAFF COMMENTS\r\nNone.\r\n"
)

_PLAIN: list[tuple[str, str, str, list[str]]] = [
    ("ascii", "Plain ASCII is unchanged.", "We may experience cybersecurity incidents.", ["cybersecurity"]),
    ("crlf-cr", "CR LF and lone CR become LF.", "Line one\r\nLine two\rLine three", ["Line two"]),
    ("horizontal-runs", "Runs of space, tab, form feed and vertical tab collapse to one space; line edges are stripped.",
     "  Risk\t\tfactors \f\v apply.   \n\tNext line  ", ["factors apply"]),
    ("unicode-spaces", "NBSP, narrow NBSP, em space and ideographic space become spaces through NFKC and step 3.",
     "a\u00a0b\u202fc\u2003d\u3000e", ["b c d"]),
    ("ogham-space", "U+1680 survives NFKC and is not collapsed inside a line, but is stripped at line edges.",
     "\u1680x\u1680\u1680y\u1680", ["x\u1680\u1680y"]),
    ("nfkc-compat", "NFKC folds ligatures, full-width letters, superscripts and fractions.",
     "\ufb01led \ufb02ow \uff21\uff22\uff23 x\u00b2 \u00bd", ["filed flow ABC x2 1\u20442"]),
    ("nfkc-compose", "Combining sequences are composed; curly quotes are kept.",
     "Cafe\u0301 \u2019quoted\u2019", ["Caf\u00e9 \u2019quoted\u2019"]),
    ("blank-lines", "Three or more line breaks become one blank line; whitespace-only lines are emptied.",
     "Para one.\n\n\n\nPara two.\n   \n \t \nPara three.", ["Para two.\n\nPara three."]),
    ("outer-whitespace", "Leading and trailing whitespace of the whole text is removed.", "\n\n  \u3000Body text.\u2029\n\n", ["Body text."]),
    ("line-separators", "U+2028 and U+0085 are kept inside a line and stripped at line edges.",
     "alpha\u2028beta\u2028\n\u0085gamma\u0085delta", ["alpha\u2028beta", "gamma\u0085delta"]),
    ("control-separators", "U+001C to U+001F are kept inside a line and stripped at line edges.",
     "\u001cone\u001dtwo\u001f", ["one\u001dtwo"]),
    ("zero-width", "U+200B is not whitespace and is kept everywhere.", "\u200bzero\u200bwidth\u200b", ["zero\u200bwidth"]),
    ("astral", "Characters outside the BMP count as one code point but two UTF-16 units.",
     "Revenue \U0001f4c8 rose 12%. Risk remains.", ["Risk remains"]),
    ("form-feed-pages", "A form feed between pages becomes a space, then is stripped at the line edge.",
     "End of page 1.\f\nStart of page 2.", ["Start of page 2."]),
    ("tenk-excerpt", "A 10-K excerpt with CR LF, NBSP, tabs, trailing spaces and extra blank lines.", TENK,
     ["We may experience cybersecurity incidents", "ITEM 1B. UNRESOLVED STAFF COMMENTS"]),
    ("whitespace-only", "Whitespace-only input normalizes to the empty string (register_document rejects it).", " \t\r\n\u3000\n", []),
]

_PIPELINES: list[tuple[str, str, str, str, list[str]]] = [
    ("html-basic", "text/html", "Block elements become line breaks; script, style and head are dropped; entities are decoded.",
     "<html><head><title>x</title><style>p{}</style></head><body><p>ITEM 1A. RISK FACTORS</p><p>We may&nbsp;fail &amp; recover.</p><script>x()</script></body></html>",
     ["We may fail & recover."]),
    ("html-ixbrl-hidden", "text/html", "Hidden inline-XBRL headers (display:none div, ix:header) are dropped.",
     '<div style="display:none"><ix:header>dei:DocumentType</ix:header></div><div><p>ITEM 1.05 MATERIAL CYBERSECURITY INCIDENTS</p><p>An attack was detected.</p></div>',
     ["An attack was detected."]),
    ("webvtt", "text/vtt", "Cue text only, one cue per line; timings become the document's cue table.",
     "WEBVTT\n\n00:00:01.000 --> 00:00:04.000\n<v Speaker>Welcome  to the update.</v>\n\n00:00:05.000 --> 00:00:09.500\nOur systems were not breached.\n",
     ["Our systems were not breached."]),
]


def _utf16_len(s: str) -> int:
    return len(s.encode("utf-16-le")) // 2


def _doc_id(tenant: str, text: str) -> str:
    return f"sr:doc:{tenant}/" + hashlib.sha256(f"{tenant}\n{text}".encode("utf-8")).hexdigest()[:32]


def _quotes(text: str, quotes: list[str]) -> list[dict[str, Any]]:
    out = []
    for q in quotes:
        start = text.index(q)
        end = start + len(q)
        out.append({"exact": q, "start": start, "end": end, "start_utf16": _utf16_len(text[:start]), "end_utf16": _utf16_len(text[:end])})
    return out


def _vector(vid: str, description: str, media_type: str, raw: str, normalized: str, normalizer: str, quotes: list[str], cues=None) -> dict[str, Any]:
    v: dict[str, Any] = {
        "id": vid,
        "description": description,
        "media_type": media_type,
        "normalizer": normalizer,
        "input": raw,
        "normalized": normalized,
        "length": len(normalized),
        "length_utf16": _utf16_len(normalized),
        "source_hash": source_hash(normalized),
        "doc_id_for_tenant_acme": _doc_id("acme", normalized) if normalized else None,
        "quotes": _quotes(normalized, quotes),
    }
    if cues:
        v["cues"] = cues
    return v


def build() -> dict[str, Any]:
    vectors = [_vector(vid, d, "text/plain", raw, normalize_text(raw), NORMALIZER, q) for vid, d, raw, q in _PLAIN]
    pipelines = []
    for vid, media, d, raw, q in _PIPELINES:
        text, cues, normalizer = to_text(raw.encode("utf-8"), media)
        pipelines.append(_vector(vid, d, media, raw, text, normalizer, q, cues))
    return {
        "definition": DEFINITION,
        "vectors": vectors,
        "pipelines": pipelines,
        "pipelines_note": "Informative. HTML and WebVTT extraction run on the server before sr-norm-1. For documents the server fetched itself, read splitrisk://documents/{doc_id} for the exact normalized text instead of re-implementing extraction.",
    }


if __name__ == "__main__":
    json.dump(build(), sys.stdout, ensure_ascii=True, indent=2, sort_keys=False)
    sys.stdout.write("\n")
