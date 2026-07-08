"""
Domain-level reputation for graduated evidence weighting.

Maps evidence URLs to one of 5 tiers. Used by verification to weight evidence
by source type: academic > official > trusted news > anti-scam/bloggers > unknown.
"""

import logging
from enum import Enum
from typing import Set
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class EvidenceTier(int, Enum):
    """Evidence source tier for graduated truth measures."""

    ACADEMIC = 1      # Peer-reviewed, academic (weight 1.5)
    OFFICIAL = 2      # Government, courts, regulators (weight 1.3)
    TRUSTED_NEWS = 3  # IFCN, high-credibility journalism (weight 1.0)
    ANTISCAM = 4      # Trusted bloggers, anti-scam, investigators (weight 0.85)
    UNKNOWN = 5       # Everything else (weight 0.6)


# Weight multipliers applied to evidence power per tier
TIER_WEIGHTS = {
    EvidenceTier.ACADEMIC: 1.5,
    EvidenceTier.OFFICIAL: 1.3,
    EvidenceTier.TRUSTED_NEWS: 1.0,
    EvidenceTier.ANTISCAM: 0.85,
    EvidenceTier.UNKNOWN: 0.6,
}

# Tier 1: Academic / peer-reviewed (DOI, PubMed, arXiv, .edu, etc.)
ACADEMIC_DOMAIN_FRAGMENTS: Set[str] = {
    "doi.org",
    "ncbi.nlm.nih.gov",
    "pubmed.",
    "pmc.ncbi.",
    "arxiv.org",
    "ssrn.com",
    "jstor.org",
    "scholar.google",
    "research.google",
    "academic.oup.com",
    "nature.com",
    "science.org",
    "springer.com",
    "tandfonline.com",
    "sciencedirect.com",
    "plos.org",
    "bmj.com",
    "thelancet.com",
    "ieee.org",
    "acm.org",
    "semanticscholar.org",
    "connectedpapers.com",
}

# Tier 2: Official / government / courts / regulators
OFFICIAL_DOMAIN_FRAGMENTS: Set[str] = {
    ".gov",
    ".mil",
    "sec.gov",
    "justice.gov",
    "fbi.gov",
    "ftc.gov",
    "cfpb.gov",
    "courtlistener.com",
    "pacer.gov",
    "law.cornell.edu",
    "congress.gov",
    "gao.gov",
    "oig.",
    "treasury.gov",
    "federalreserve.gov",
    "fdic.gov",
    "occ.gov",
}

# Tier 4: Trusted anti-scam / investigators / bloggers (known domains)
ANTISCAM_DOMAIN_FRAGMENTS: Set[str] = {
    "coffeezilla.com",
    "behindmlm.com",
    "scamadviser.com",
    "tina.org",           # TruthInAdvertising
    "bbb.org",
    "consumer.ftc.gov",
    "actionfraud.police.uk",
    "fincen.gov",
    "finra.org",
    "investor.gov",
    "nasa.gov",
    "cdc.gov",
    "who.int",
}

# Trusted news / fact-check (Tier 3) — subset we can recognize by domain without API
# Full Tier 3 would use NewsGuard/MBFC API; these are well-known fact-check / wire
TRUSTED_NEWS_DOMAIN_FRAGMENTS: Set[str] = {
    "reuters.com",
    "apnews.com",
    "factcheck.org",
    "politifact.com",
    "snopes.com",
    "factcheck.afp.com",
    "fullfact.org",
    "checkyourfact.com",
    "leadstories.com",
    "dpa.com",
    "afp.com",
    "bbc.com",
    "bbc.co.uk",
    "npr.org",
    "poynter.org",
    "pbs.org",
    "propublica.org",
}


def _normalize_host(url: str) -> str:
    """Extract and normalize host from URL (lowercase, no www)."""
    if not url or not url.strip():
        return ""
    try:
        parsed = urlparse(url.strip())
        host = (parsed.netloc or parsed.path or "").lower()
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return ""


def _host_matches(host: str, fragments: Set[str]) -> bool:
    """True if host contains any of the fragment strings."""
    if not host:
        return False
    return any(frag in host for frag in fragments)


def get_domain_tier(url: str) -> EvidenceTier:
    """
    Map a URL to an evidence tier.

    Order of checks: Academic > Official > Trusted News > Anti-scam > Unknown.
    """
    host = _normalize_host(url)
    if not host:
        return EvidenceTier.UNKNOWN

    if _host_matches(host, ACADEMIC_DOMAIN_FRAGMENTS):
        return EvidenceTier.ACADEMIC
    if host.endswith(".edu"):
        return EvidenceTier.ACADEMIC

    if _host_matches(host, OFFICIAL_DOMAIN_FRAGMENTS):
        return EvidenceTier.OFFICIAL
    if host.endswith(".gov") or host.endswith(".mil"):
        return EvidenceTier.OFFICIAL

    if _host_matches(host, TRUSTED_NEWS_DOMAIN_FRAGMENTS):
        return EvidenceTier.TRUSTED_NEWS

    if _host_matches(host, ANTISCAM_DOMAIN_FRAGMENTS):
        return EvidenceTier.ANTISCAM

    return EvidenceTier.UNKNOWN


def get_domain_weight(url: str) -> float:
    """Return the evidence weight multiplier for this URL (0.6 to 1.5)."""
    tier = get_domain_tier(url)
    return TIER_WEIGHTS[tier]


def get_tier_breakdown(urls: list) -> dict:
    """
    Return counts per tier for a list of URLs.
    Keys: tier_1, tier_2, tier_3, tier_4, tier_5 (and optionally tier_names).
    """
    counts = {
        EvidenceTier.ACADEMIC: 0,
        EvidenceTier.OFFICIAL: 0,
        EvidenceTier.TRUSTED_NEWS: 0,
        EvidenceTier.ANTISCAM: 0,
        EvidenceTier.UNKNOWN: 0,
    }
    for u in urls or []:
        tier = get_domain_tier(u)
        counts[tier] = counts.get(tier, 0) + 1
    return {
        "tier_1": counts[EvidenceTier.ACADEMIC],
        "tier_2": counts[EvidenceTier.OFFICIAL],
        "tier_3": counts[EvidenceTier.TRUSTED_NEWS],
        "tier_4": counts[EvidenceTier.ANTISCAM],
        "tier_5": counts[EvidenceTier.UNKNOWN],
    }
