"""Bind Deep Research citations to grounding URIs (fail-closed)."""
from __future__ import annotations

import re
from typing import Iterable, List, Set
from urllib.parse import urlparse

_REF_RE = re.compile(
    r"\[Reference:\s*(https?://[^\]\s]+|Currently Claim is Unverified)\]",
    re.IGNORECASE,
)
_UNVERIFIED = "[Reference: Currently Claim is Unverified]"


def _norm_url(url: str) -> str:
    try:
        p = urlparse((url or "").strip())
        return f"{(p.scheme or 'https').lower()}://{(p.netloc or '').lower()}{(p.path or '').rstrip('/')}"
    except Exception:
        return (url or "").strip().lower()


def bind_citations(
    markdown: str,
    grounding_uris: Iterable[str],
    allowlist: Iterable[str] | None = None,
) -> str:
    """
    Replace [Reference: url] with Unverified when url is not in grounding ∪ allowlist.
    Leaves the Unverified token unchanged.
    """
    allowed: Set[str] = set()
    for u in list(grounding_uris or []) + list(allowlist or []):
        if u:
            allowed.add(_norm_url(u))
            # also allow by netloc for near-matches
            try:
                allowed.add((urlparse(u).netloc or "").lower())
            except Exception:
                pass

    def _replace(match: re.Match) -> str:
        ref = match.group(1).strip()
        if ref.lower().startswith("currently claim is unverified"):
            return _UNVERIFIED
        n = _norm_url(ref)
        host = ""
        try:
            host = (urlparse(ref).netloc or "").lower()
        except Exception:
            pass
        if n in allowed or host in allowed:
            return match.group(0)
        return _UNVERIFIED

    return _REF_RE.sub(_replace, markdown or "")


def force_unverified_all(markdown: str) -> str:
    """Rewrite every Reference URL to Unverified (used when grounding is empty)."""
    return _REF_RE.sub(_UNVERIFIED, markdown or "")
