"""
Google Fact Check Tools API integration.

Queries factchecktools.googleapis.com v1alpha1 claims:search for each claim.
ClaimReview results are returned as evidence-like dicts for Tier 3 injection.
Requires GOOGLE_FACTCHECK_API_KEY (free, 1000 req/day).
"""

import logging
from typing import List, Dict, Any
import urllib.parse

logger = logging.getLogger(__name__)

FACTCHECK_SEARCH_URL = (
    "https://factchecktools.googleapis.com/v1alpha1/claims:search"
)


def fetch_claim_review_evidence(claim_text: str, api_key: str) -> List[Dict[str, Any]]:
    """
    Query Google Fact Check Tools API for existing fact-checks of the claim.
    Returns evidence-like dicts (url, title, text, source_type) for each ClaimReview.
    Used to inject IFCN/ClaimReview as Tier 3 evidence in verification.

    Args:
        claim_text: The claim to look up.
        api_key: GOOGLE_FACTCHECK_API_KEY.

    Returns:
        List of dicts with url, title, text, source_type="fact_check",
        and optionally claim_review_verdict.
    """
    if not api_key or not (claim_text or "").strip():
        return []
    evidence: List[Dict[str, Any]] = []
    try:
        query = (claim_text or "").strip()[:500]  # API limit
        params = {"key": api_key, "query": query}
        url = f"{FACTCHECK_SEARCH_URL}?{urllib.parse.urlencode(params)}"
        import requests
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        claims = data.get("claims") or []
        for claim_obj in claims:
            for review in claim_obj.get("claimReview") or []:
                pub = review.get("publisher") or {}
                pub_name = pub.get("name", "Fact-checker")
                pub_site = pub.get("site", "")
                review_url = review.get("url", "").strip()
                title = (review.get("title") or "").strip() or pub_name
                rating = (review.get("textualRating") or "").strip()
                text = rating or title
                if pub_name and pub_name != "Fact-checker":
                    text = f"{rating} ({pub_name})" if rating else pub_name
                if not review_url:
                    continue
                evidence.append({
                    "url": review_url,
                    "title": title,
                    "text": text,
                    "snippet": text,
                    "source_type": "fact_check",
                    "claim_review_verdict": rating or None,
                    "publisher_site": pub_site,
                })
        if evidence:
            logger.info(
                "Fact Check API: found %s ClaimReview(s) for claim query",
                len(evidence),
            )
    except Exception as e:
        logger.debug("Fact Check API request failed (optional): %s", e)
    return evidence
