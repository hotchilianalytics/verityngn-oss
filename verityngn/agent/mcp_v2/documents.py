"""Document registration: normalized text, source hash, outline, time cues.

All anchor positions refer to the normalized text produced here and pinned by
``source_hash``. HTML, plain text and WebVTT are handled natively; PDF and DOCX
go through Docling when it is installed.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import html
import ipaddress
import re
import socket
import unicodedata
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from typing import Any, Optional

from verityngn.agent.mcp_v2.errors import EngineNotInstalled, ToolFailure
from verityngn.agent.mcp_v2.store import Document, MemoryStore

NORMALIZER = "sr-norm-1"
MAX_FETCH_BYTES = 25 * 1024 * 1024
SEC_UA_ENV = "SEC_USER_AGENT"

_BLOCK_TAGS = {
    "p", "div", "br", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6",
    "table", "section", "article", "header", "footer", "ul", "ol", "title", "td", "th",
}
_SKIP_TAGS = {"script", "style", "noscript", "head"}


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ")
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def source_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip = 0
        self._hidden = 0
        self._divs: list[bool] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        tag = tag.lower()
        if tag in _SKIP_TAGS:
            self._skip += 1
        if tag == "div":
            style = (dict(attrs).get("style") or "").replace(" ", "").lower()
            hidden = "display:none" in style
            self._divs.append(hidden)
            self._hidden += hidden
        if tag == "ix:header":
            self._hidden += 1
        if tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag.lower() in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in _SKIP_TAGS and self._skip:
            self._skip -= 1
        if tag == "div" and self._divs:
            self._hidden -= self._divs.pop()
        if tag == "ix:header" and self._hidden:
            self._hidden -= 1
        if tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip and not self._hidden:
            self.parts.append(data)


def html_to_text(raw: str) -> str:
    parser = _TextExtractor()
    parser.feed(raw)
    parser.close()
    return html.unescape("".join(parser.parts))


_CUE_TIME = re.compile(r"(?:(\d+):)?(\d{1,2}):(\d{2})[.,](\d{3})")


def _seconds(match: re.Match[str]) -> float:
    h, m, s, ms = match.groups()
    return int(h or 0) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def parse_vtt(raw: str) -> tuple[str, list[dict[str, Any]]]:
    """Return normalized transcript text and cues with character offsets."""
    cues: list[dict[str, Any]] = []
    lines_out: list[str] = []
    pos = 0
    blocks = re.split(r"\n\s*\n", (raw or "").replace("\r\n", "\n"))
    for block in blocks:
        lines = [ln for ln in block.split("\n") if ln.strip()]
        timing_idx = next((i for i, ln in enumerate(lines) if "-->" in ln), None)
        if timing_idx is None:
            continue
        times = _CUE_TIME.findall(lines[timing_idx])
        found = list(_CUE_TIME.finditer(lines[timing_idx]))
        if len(found) < 2 or not times:
            continue
        start_s, end_s = _seconds(found[0]), _seconds(found[1])
        body = normalize_text(re.sub(r"<[^>]+>", "", " ".join(lines[timing_idx + 1:])))
        if not body:
            continue
        if lines_out:
            pos += 1
        cues.append({"start_s": start_s, "end_s": end_s, "start": pos, "end": pos + len(body)})
        lines_out.append(body)
        pos += len(body)
    return "\n".join(lines_out), cues


def _docling_text(data: bytes, suffix: str) -> str:
    try:
        from docling.document_converter import DocumentConverter  # type: ignore
    except ImportError:
        raise EngineNotInstalled(
            "docling",
            "PDF and DOCX registration needs Docling, which is not installed on this server.",
            alternative="Register the document's text instead (media_type text/plain), or install docling.",
        ) from None
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=suffix) as fh:
        fh.write(data)
        fh.flush()
        result = DocumentConverter().convert(fh.name)
    return result.document.export_to_markdown()


_ITEM_10K = re.compile(r"^item\s+(\d{1,2}[a-c]?)\s*[.:\-—–]?\s*(.{0,240})$", re.I)
_ITEM_8K = re.compile(r"^item\s+(\d\.\d{2})\s*[.:\-—–]?\s*(.{0,240})$", re.I)


def build_outline(text: str) -> list[dict[str, Any]]:
    """SEC Item boundaries.

    Running page headers repeat an Item inside its own section, so consecutive
    headings for the same Item merge into one span; table-of-contents entries
    then lose to the longest span for each Item.
    """
    candidates: list[tuple[int, str, str]] = []
    pos = 0
    for line in text.split("\n"):
        stripped = line.strip()
        m = _ITEM_8K.match(stripped) or _ITEM_10K.match(stripped)
        if m:
            candidates.append((pos, m.group(1).upper(), stripped[:200]))
        pos += len(line) + 1
    if not candidates:
        return []
    def titled(heading: str, item: str) -> bool:
        return bool(re.match(rf"^item\s+{re.escape(item)}\s*[.:\-—–]\s*\S", heading, re.I))

    merged: list[tuple[int, str, str]] = []
    for cand in candidates:
        if merged and merged[-1][1] == cand[1]:
            if titled(cand[2], cand[1]) and not titled(merged[-1][2], cand[1]):
                merged[-1] = (merged[-1][0], cand[1], cand[2])
            continue
        merged.append(cand)
    spans = []
    for i, (start, item, heading) in enumerate(merged):
        end = merged[i + 1][0] if i + 1 < len(merged) else len(text)
        spans.append({"item": item, "heading": heading, "start": start, "end": end})
    best: dict[str, dict[str, Any]] = {}
    for span in spans:
        cur = best.get(span["item"])
        if cur is None or (span["end"] - span["start"]) > (cur["end"] - cur["start"]):
            best[span["item"]] = span
    ordered = sorted(best.values(), key=lambda s: s["start"])
    outline = []
    for i, span in enumerate(ordered):
        end = ordered[i + 1]["start"] if i + 1 < len(ordered) else len(text)
        outline.append(
            {
                "heading_path": [span["heading"]],
                "item": span["item"],
                "start": span["start"],
                "end": max(span["start"], end - 1 if end < len(text) else end),
            }
        )
    return outline


def _check_public_host(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ToolFailure("INVALID", "Only public http(s) URLs can be registered.")
    try:
        infos = socket.getaddrinfo(parsed.hostname, None)
    except socket.gaierror:
        raise ToolFailure("UPSTREAM", f"Could not resolve {parsed.hostname}.") from None
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise ToolFailure("INVALID", "URLs that resolve to private or local addresses are not fetched.")


def user_agent() -> str:
    import os

    return os.environ.get(SEC_UA_ENV, "VerityNgn research verityindex.com ajjc@verityindex.com")


def fetch_url(url: str, *, timeout: int = 30) -> tuple[bytes, str]:
    """Fetch one user-named public URL (no crawling). Returns body and content type."""
    _check_public_host(url)
    req = urllib.request.Request(url, headers={"User-Agent": user_agent(), "Accept-Encoding": "identity"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - scheme checked above
            data = resp.read(MAX_FETCH_BYTES + 1)
            ctype = resp.headers.get("Content-Type", "")
    except Exception as exc:  # noqa: BLE001
        raise ToolFailure("UPSTREAM", f"Fetching {url} failed: {exc}") from None
    if len(data) > MAX_FETCH_BYTES:
        raise ToolFailure("INVALID", "Document is larger than 25 MB.")
    return data, ctype


def to_text(data: bytes, media_type: str) -> tuple[str, list[dict[str, Any]], str]:
    """Return (normalized text, cues, normalizer)."""
    if media_type == "application/pdf":
        return normalize_text(_docling_text(data, ".pdf")), [], "docling+" + NORMALIZER
    if media_type.endswith("wordprocessingml.document"):
        return normalize_text(_docling_text(data, ".docx")), [], "docling+" + NORMALIZER
    raw = data.decode("utf-8", errors="replace")
    if media_type == "text/vtt":
        text, cues = parse_vtt(raw)
        return text, cues, "webvtt+" + NORMALIZER
    if media_type == "text/html":
        return normalize_text(html_to_text(raw)), [], "html+" + NORMALIZER
    return normalize_text(raw), [], NORMALIZER


def register(
    store: MemoryStore,
    *,
    tenant: str,
    media_type: str,
    rights: str,
    text: Optional[str] = None,
    data: Optional[bytes] = None,
    url: Optional[str] = None,
    title: str = "",
    video_id: Optional[str] = None,
) -> Document:
    if data is None:
        data = (text or "").encode("utf-8")
    norm, cues, normalizer = to_text(data, media_type)
    if not norm:
        raise ToolFailure("INVALID", "The document has no text after normalization.")
    digest = hashlib.sha256(f"{tenant}\n{norm}".encode("utf-8")).hexdigest()[:32]
    doc = Document(
        doc_id=f"sr:doc:{tenant}/{digest}",
        tenant=tenant,
        text=norm,
        source_hash=source_hash(norm),
        media_type=media_type,
        normalizer=normalizer,
        outline=build_outline(norm),
        title=title,
        url=url,
        rights=rights,
        cues=cues,
        video_id=video_id,
        registered_at=dt.datetime.now(dt.timezone.utc).isoformat(),
    )
    return store.put_document(doc)


def document_uri(doc_id: str) -> str:
    return f"splitrisk://documents/{doc_id}"


def document_payload(doc: Document) -> dict[str, Any]:
    """What a client needs to show a registered document and map anchors onto it.

    ``pages`` maps page numbers to normalized offsets once paged formats are
    extracted (PDF through Docling); text, HTML and WebVTT have no pages.
    ``cues`` maps WebVTT time ranges to normalized offsets.
    """
    return {
        "doc_id": doc.doc_id,
        "source_hash": doc.source_hash,
        "normalizer": doc.normalizer,
        "media_type": doc.media_type,
        "title": doc.title,
        "url": doc.url,
        "rights": doc.rights,
        "length": len(doc.text),
        "length_utf16": len(doc.text.encode("utf-16-le")) // 2,
        "positions": "Unicode code points",
        "outline": doc.outline,
        "pages": [],
        "cues": doc.cues,
        "text": doc.text,
    }
