"""Multi-hop source expansion (layers 2–3) for Deep Research.

Layer 2: creator / speaker secondary posts + official domains from L1.
Layer 3: outbound / related CSE from L2 URLs.
Public CSE only — no authenticated LinkedIn scrape.
"""
from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_SPEAKER_RE = re.compile(
    r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b"
)


def _hops_enabled() -> int:
    try:
        n = int(os.getenv("DEEP_SOURCE_HOPS", "2"))
    except Exception:
        n = 2
    return max(0, min(3, n))


def _speakers_from_report(report: Dict[str, Any]) -> List[str]:
    names: List[str] = []
    seen: Set[str] = set()
    skip_tokens = (
        "visual", "text", "graphic", "chart", "narrator", "speaker", "unknown",
        "on-screen", "website", "policy helper",
    )
    for c in report.get("claims_breakdown") or []:
        if not isinstance(c, dict):
            continue
        sp = (c.get("speaker") or "").strip()
        if not sp:
            continue
        # Drop parenthetical visual notes
        sp = re.split(r"\(|visual|chart|graphic", sp, maxsplit=1)[0].strip()
        low = sp.lower()
        if len(sp) < 4 or low in seen:
            continue
        if any(tok in low for tok in skip_tokens):
            continue
        # Prefer Person Name patterns (2–3 Capitalized tokens)
        if not re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}$", sp):
            continue
        seen.add(low)
        names.append(sp)
        if len(names) >= 3:
            break
    return names


def _hosts_from_urls(urls: List[str]) -> List[str]:
    hosts: List[str] = []
    seen: Set[str] = set()
    skip = {"facebook.com", "twitter.com", "x.com", "tiktok.com", "instagram.com"}
    for u in urls:
        try:
            h = (urlparse(u).netloc or "").lower().lstrip("www.")
        except Exception:
            continue
        if not h or h in skip or h in seen:
            continue
        seen.add(h)
        hosts.append(h)
        if len(hosts) >= 5:
            break
    return hosts


def expand_sources(
    report: Dict[str, Any],
    *,
    layer1_uris: Optional[List[str]] = None,
    primary_urls: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Run CSE hops 2–3. Returns audit dict with ``allowlist_urls`` to merge into binder.
    """
    hops = _hops_enabled()
    audit: Dict[str, Any] = {
        "hops_requested": hops,
        "layers": [],
        "allowlist_urls": [],
        "queries": [],
    }
    if hops < 2:
        return audit

    try:
        from verityngn.services.search.web_search import (
            evidence_relevance_score,
            google_search,
            search_for_evidence,
        )
    except Exception as exc:
        logger.warning("source_expander: search unavailable: %s", exc)
        return audit

    claim_blob = " ".join(
        str(c.get("claim_text") or "")
        for c in (report.get("claims_breakdown") or [])
        if isinstance(c, dict)
    )[:500]
    speakers = _speakers_from_report(report)
    l1 = list(layer1_uris or []) + list(primary_urls or [])
    allow: List[str] = []
    seen: Set[str] = set(l1)

    def _add_results(results: List[Dict[str, Any]], layer: int) -> None:
        kept = []
        for r in results:
            url = (r.get("url") or r.get("link") or "").strip()
            if not url or url in seen:
                continue
            score = evidence_relevance_score(r, claim_blob) if claim_blob else 0.3
            # Creator secondary: keep LinkedIn even if score medium
            host = (urlparse(url).netloc or "").lower()
            if "linkedin.com" in host:
                score = max(score, 0.35)
            if score < 0.25:
                continue
            seen.add(url)
            allow.append(url)
            kept.append({"url": url, "score": round(score, 3), "title": r.get("title") or ""})
            if len(kept) >= 8:
                break
        audit["layers"].append({"layer": layer, "kept": kept})

    # --- Layer 2 ---
    l2_queries: List[str] = []
    for sp in speakers[:2]:
        l2_queries.append(f'"{sp}" LinkedIn OR site:linkedin.com')
        l2_queries.append(f'"{sp}" interview OR statement OR testimony OR hearing')
    # Short entity keys for site: hops (full claim blob kills CSE recall)
    bill_m = re.search(r"\b((?:SB|HB)\s*\d{2,5})\b", claim_blob, re.I)
    entity = bill_m.group(1) if bill_m else " ".join(claim_blob.split()[:6])
    for host in _hosts_from_urls(l1)[:3]:
        if host.endswith(".gov") or "legislature" in host or "ballotpedia" in host:
            l2_queries.append(f"site:{host} {entity}")
    l2_queries = l2_queries[:5]
    audit["queries"].extend({"layer": 2, "q": q} for q in l2_queries)

    l2_hits: List[Dict[str, Any]] = []
    for q in l2_queries:
        try:
            if q.strip().lower().startswith("site:"):
                hits = google_search(q, num_results=5)
                for h in hits:
                    l2_hits.append(
                        {
                            "url": h.get("link"),
                            "title": h.get("title"),
                            "text": h.get("snippet"),
                        }
                    )
            else:
                l2_hits.extend(search_for_evidence(q, num_results=5, tier=2))
        except Exception as exc:
            logger.debug("L2 search failed for %r: %s", q[:60], exc)
    _add_results(l2_hits, 2)

    if hops < 3:
        audit["allowlist_urls"] = allow
        return audit

    # --- Layer 3: expand from L2 titles / domains ---
    l3_queries: List[str] = []
    for item in (audit["layers"][-1].get("kept") if audit["layers"] else [])[:4]:
        title = (item.get("title") or "")[:80]
        if title:
            l3_queries.append(f"{title} official OR document OR hearing")
    l3_queries = l3_queries[:4]
    audit["queries"].extend({"layer": 3, "q": q} for q in l3_queries)
    l3_hits: List[Dict[str, Any]] = []
    for q in l3_queries:
        try:
            l3_hits.extend(search_for_evidence(q, num_results=4, tier=2))
        except Exception as exc:
            logger.debug("L3 search failed: %s", exc)
    # Cap L3 adds
    before = len(allow)
    _add_results(l3_hits, 3)
    # Trim L3 to max 10 new URLs
    if len(allow) - before > 10:
        allow = allow[: before + 10]
        if audit["layers"] and audit["layers"][-1].get("layer") == 3:
            audit["layers"][-1]["kept"] = audit["layers"][-1]["kept"][:10]

    audit["allowlist_urls"] = allow
    logger.info(
        "source_expander: hops=%d allowlist=%d speakers=%s",
        hops,
        len(allow),
        speakers,
    )
    return audit
