"""
URL safety filter for evidence / citation links in reports.

Blocks SEO-poisoned open redirects, compromised OJS journal PDF viewers,
krpano/data: XSS payloads, and known scam funnel hosts before they reach
report JSON or HTML.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import parse_qs, unquote, urlparse

logger = logging.getLogger(__name__)

_ALLOWED_SCHEMES = frozenset({"http", "https"})

UNSAFE_HOST_FRAGMENTS: tuple[str, ...] = (
    "hon-yu.com",
    "videos-gtag.xyz",
    "mtsap.com",
    "su7u.shop",
    "uo00.shop",
    "fg00.shop",
    "solalal.com",
    "feelcools.com",
)

KNOWN_SCAM_HOSTS: tuple[str, ...] = UNSAFE_HOST_FRAGMENTS

TRUSTED_DOMAINS: frozenset[str] = frozenset({
    "nytimes.com",
    "hubermanlab.com",
    "mcgill.ca",
    "nih.gov",
    "ncbi.nlm.nih.gov",
    "theguardian.com",
    "examine.com",
    "opss.org",
    "ahajournals.org",
    "nature.com",
    "science.org",
    "bmj.com",
    "nejm.org",
    "youtube.com",
    "youtu.be",
    "google.com",
    "wikipedia.org",
    "gov",
    "edu",
})

_FUZZY_SCAM_THRESHOLD = 88

UNSAFE_DECODED_FRAGMENTS: tuple[str, ...] = (
    "data:",
    "javascript:",
    "vbscript:",
    ".shop/male",
    ".shop/male3",
    ".shop/cbd",
    "/male/",
    "/male3/",
    "/cbd2/",
    "signout?source=",
    "login/signout",
    "loadpano(",
    "<krpano",
    "videos-gtag.xyz",
    "alpha-pro-force-gummies",
    "male-extra-overview",
    "male-performance-gummy",
)

_OJS_VIEWER_MARKER = "pdfjsviewer/pdf.js/web/viewer.html"
_OJS_REDIRECT_MARKERS = (
    "signout",
    "signout?source",
    "login/signout",
    ".shop",
    "/male",
    "/cbd",
    "feelcools",
    "solalal",
    "su7u",
    "uo00",
    "fg00",
)

_REDIRECT_PARAM_NAMES = frozenset(
    {"file", "url", "redirect", "redirect_url", "target", "dest", "destination", "goto", "next", "xml"}
)


def _decoded(url: str) -> str:
    if not url:
        return ""
    out = url
    for _ in range(3):
        try:
            nxt = unquote(out)
        except Exception:
            break
        if nxt == out:
            break
        out = nxt
    return out.lower()


def _has_embedded_redirect(decoded: str) -> bool:
    if not decoded:
        return False
    for marker in (
        "signout?source=",
        "login/signout",
        "%2f%2f",
        "://videos-gtag",
        "loadpano(",
    ):
        if marker in decoded:
            return True
    try:
        parsed = urlparse(decoded if "://" in decoded else f"http://x?{decoded}")
        qs = parse_qs(parsed.query, keep_blank_values=True)
        for name, values in qs.items():
            if name.lower() not in _REDIRECT_PARAM_NAMES and name.lower() != "file":
                continue
            for val in values:
                dv = _decoded(val)
                if not dv:
                    continue
                if any(m in dv for m in _OJS_REDIRECT_MARKERS):
                    return True
                if re.search(r"https?://", dv):
                    return True
                if dv.startswith("//"):
                    return True
    except Exception:
        pass
    return False


def _is_ojs_open_redirect(url: str, decoded: str) -> bool:
    if _OJS_VIEWER_MARKER not in decoded:
        return False
    return any(m in decoded for m in _OJS_REDIRECT_MARKERS)


def _registrable_domain(host: str) -> str:
    host = (host or "").lower().split(":")[0]
    if host.startswith("www."):
        host = host[4:]
    parts = [p for p in host.split(".") if p]
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return host


def _host_is_trusted(host: str) -> bool:
    host = (host or "").lower()
    reg = _registrable_domain(host)
    if reg in TRUSTED_DOMAINS:
        return True
    if reg.endswith(".gov") or reg.endswith(".edu"):
        return True
    for trusted in TRUSTED_DOMAINS:
        if trusted in {".gov", ".edu"}:
            if host.endswith(trusted) or reg.endswith(trusted):
                return True
        elif host == trusted or host.endswith(f".{trusted}"):
            return True
    return False


def _is_fuzzy_scam_host(host: str) -> bool:
    host = (host or "").lower().split(":")[0]
    if not host or _host_is_trusted(host):
        return False
    try:
        from rapidfuzz import fuzz  # type: ignore
    except ImportError:
        return False

    reg = _registrable_domain(host)
    for scam in KNOWN_SCAM_HOSTS:
        for a, b in ((host, scam), (reg, scam), (reg, _registrable_domain(scam))):
            if fuzz.ratio(a, b) >= _FUZZY_SCAM_THRESHOLD:
                return True
            if fuzz.token_set_ratio(a, b) >= _FUZZY_SCAM_THRESHOLD:
                return True
    return False


def is_safe_url(url: Optional[str]) -> bool:
    if not url or not str(url).strip():
        return False

    raw = str(url).strip()
    decoded = _decoded(raw)

    if "data:" in decoded or "javascript:" in decoded or "vbscript:" in decoded:
        return False

    try:
        parsed = urlparse(raw)
    except Exception:
        return False

    scheme = (parsed.scheme or "").lower()
    if scheme and scheme not in _ALLOWED_SCHEMES:
        return False

    if not scheme:
        if raw.startswith("#"):
            return True
        return False

    host = (parsed.netloc or "").lower()
    for frag in UNSAFE_HOST_FRAGMENTS:
        if frag in host:
            return False

    if _is_fuzzy_scam_host(host):
        return False

    for frag in UNSAFE_DECODED_FRAGMENTS:
        if frag in decoded:
            return False

    if _is_ojs_open_redirect(raw, decoded):
        return False

    if _has_embedded_redirect(decoded):
        return False

    if "base64," in decoded and ("krpano" in decoded or "loadpano" in decoded):
        return False
    if re.search(r"[?&]xml=data:", decoded):
        return False

    return True


def filter_safe_urls(urls: Iterable[Any]) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for item in urls or []:
        url = item
        if isinstance(item, dict):
            url = item.get("url", "")
        if not isinstance(url, str):
            continue
        url = url.strip()
        if not url or url in seen:
            continue
        if is_safe_url(url):
            out.append(url)
            seen.add(url)
        else:
            logger.debug("Filtered unsafe citation URL: %s", url[:120])
    return out


def filter_safe_evidence(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        url = (item.get("url") or "").strip()
        if url and not is_safe_url(url):
            logger.debug("Filtered unsafe evidence item: %s", url[:120])
            continue
        out.append(item)
    return out


def sanitize_report_dict_urls(data: Dict[str, Any]) -> Dict[str, Any]:
    import copy

    out = copy.deepcopy(data)
    claims = out.get("claims_breakdown", [])
    if not isinstance(claims, list):
        return out

    for claim in claims:
        if not isinstance(claim, dict):
            continue
        vr = claim.get("verification_result")
        if isinstance(vr, dict):
            if isinstance(vr.get("sources"), list):
                vr["sources"] = filter_safe_urls(vr["sources"])
            if isinstance(vr.get("pr_sources"), list):
                vr["pr_sources"] = filter_safe_evidence(vr["pr_sources"])
            if isinstance(vr.get("youtube_counter_sources"), list):
                vr["youtube_counter_sources"] = filter_safe_evidence(vr["youtube_counter_sources"])
            if isinstance(vr.get("evidence"), str):
                vr["evidence"] = sanitize_url_list_in_text(vr["evidence"])

    for key in ("youtube_counter_intelligence", "press_release_counter_intelligence"):
        section = out.get(key)
        if isinstance(section, list):
            out[key] = filter_safe_evidence(section)
    es = out.get("evidence_summary")
    if isinstance(es, list):
        out["evidence_summary"] = filter_safe_evidence(es)

    return out


def sanitize_url_list_in_text(text: str) -> str:
    if not text or not isinstance(text, str):
        return text or ""

    def _replace(match: re.Match) -> str:
        u = match.group(0)
        return u if is_safe_url(u) else ""

    return re.sub(r"https?://[^\s\]\)\"'<>]+", _replace, text)
