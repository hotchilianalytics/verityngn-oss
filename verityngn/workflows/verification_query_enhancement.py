"""
Verification Query Enhancement Module

Provides type-specific query templates and multi-query strategies
to improve verification source relevance.
"""

import logging
from typing import List, Dict, Any
import re

logger = logging.getLogger(__name__)


def generate_verification_queries(
    claim_text: str, claim_type: str, max_queries: int = 3
) -> List[str]:
    """
    Generate type-specific verification queries for a claim.

    Args:
        claim_text: The claim to verify
        claim_type: Type of claim (from classify_claim_type)
        max_queries: Maximum number of queries to generate

    Returns:
        List of search queries optimized for the claim type
    """
    queries = []

    if claim_type == "credential":
        queries = _generate_credential_queries(claim_text)
    elif claim_type == "publication":
        queries = _generate_publication_queries(claim_text)
    elif claim_type == "study":
        queries = _generate_study_queries(claim_text)
    elif claim_type == "absence":
        queries = _generate_absence_queries(claim_text)
    elif claim_type == "product_efficacy":
        queries = _generate_efficacy_queries(claim_text)
    else:
        queries = _generate_generic_queries(claim_text)

    # Limit to max_queries
    return queries[:max_queries]


def _generate_credential_queries(claim_text: str) -> List[str]:
    """Generate queries for credential claims."""
    queries = []

    # Extract person name
    name_match = re.search(
        r"(?:Dr\.|Professor|Mr\.|Ms\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", claim_text
    )
    if name_match:
        name = name_match.group(1).strip()

        # Query medical license databases
        queries.append(f'"{name}" medical license physician lookup')

        # Query professional directories
        queries.append(f'site:healthgrades.com OR site:doximity.com "{name}"')

        # Extract institution if mentioned
        inst_match = re.search(
            r"([A-Z][a-z]+\s+(?:University|Institute|Hospital|College|School))",
            claim_text,
            re.IGNORECASE,
        )
        if inst_match:
            institution = inst_match.group(1).strip()
            queries.append(f'"{name}" faculty staff "{institution}"')

    # Fallback if no name found
    if not queries:
        queries.append(claim_text[:100])

    return queries


def _generate_publication_queries(claim_text: str) -> List[str]:
    """Generate queries for publication/award claims."""
    queries = []

    # Look for magazine/publication name
    pub_patterns = [
        r"(Time\s+Magazine)",
        r"(New\s+York\s+Times)",
        r"(Forbes)",
        r"(Wall\s+Street\s+Journal)",
    ]

    publication = None
    for pattern in pub_patterns:
        match = re.search(pattern, claim_text, re.IGNORECASE)
        if match:
            publication = match.group(1)
            break

    # Extract year if present
    year_match = re.search(r"\b(20\d{2})\b", claim_text)
    year = year_match.group(1) if year_match else None

    # Extract award/recognition phrase
    award_phrases = ["dubbed", "named", "awarded", "recognized as"]
    award_text = None
    for phrase in award_phrases:
        if phrase in claim_text.lower():
            # Get text after the phrase
            idx = claim_text.lower().find(phrase)
            award_text = claim_text[idx : idx + 100].strip()
            break

    if publication and year:
        queries.append(
            f'site:{publication.lower().replace(" ", "")}.com {year} award expert'
        )

    if publication and award_text:
        queries.append(f'"{publication}" {award_text[:50]}')

    # Generic publication query
    if publication:
        queries.append(f'"{publication}" health expert 2023 2024 recognition')

    # Fallback
    if not queries:
        queries.append(claim_text[:100])

    return queries


def _generate_study_queries(claim_text: str) -> List[str]:
    """Generate queries for study/research claims."""
    queries = []

    # Extract institution
    inst_match = re.search(
        r"([A-Z][a-z]+\s+(?:University|Institute|Hospital))", claim_text, re.IGNORECASE
    )
    institution = inst_match.group(1).strip() if inst_match else None

    # Extract year
    year_match = re.search(r"\b(20\d{2})\b", claim_text)
    year = year_match.group(1) if year_match else None

    # Extract topic keywords
    topic_keywords = []
    topic_terms = [
        "weight loss",
        "turmeric",
        "curcumin",
        "berberine",
        "obesity",
        "inflammation",
    ]
    for term in topic_terms:
        if term in claim_text.lower():
            topic_keywords.append(term)

    # PubMed search
    if institution and year:
        topic_str = " ".join(topic_keywords[:2])
        queries.append(f"site:pubmed.ncbi.nlm.nih.gov {institution} {year} {topic_str}")

    # Google Scholar search
    if institution:
        topic_str = " ".join(topic_keywords[:2])
        queries.append(f'site:scholar.google.com "{institution}" study {topic_str}')

    # Clinical trials registry
    if topic_keywords:
        queries.append(
            f'site:clinicaltrials.gov {" ".join(topic_keywords[:2])} {year or ""}'
        )

    # Fallback generic search
    if not queries:
        queries.append(
            f'study research {" ".join(topic_keywords[:2]) if topic_keywords else claim_text[:50]}'
        )

    return queries


def _generate_absence_queries(claim_text: str) -> List[str]:
    """Generate queries for absence claims (search for what SHOULD exist)."""
    queries = []

    # Extract what's claimed to be missing
    if "medical license" in claim_text.lower():
        # Search for medical license databases
        name_match = re.search(r"Dr\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", claim_text)
        if name_match:
            name = name_match.group(1).strip()
            queries.append(f'"{name}" medical license verification state board')
            queries.append(f'site:abms.org OR site:fsmb.org "{name}"')

    elif (
        "medical school" in claim_text.lower() or "medical degree" in claim_text.lower()
    ):
        name_match = re.search(
            r"(?:Dr\.|doctor)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
            claim_text,
            re.IGNORECASE,
        )
        if name_match:
            name = name_match.group(1).strip()
            queries.append(f'"{name}" MD medical school alumni directory')

    elif "study" in claim_text.lower() and "DOI" in claim_text:
        # Search for the study that should have a DOI
        queries.append(claim_text.replace("does not", "").replace("Video", "")[:100])

    # Fallback: search for the entity mentioned
    else:
        # Remove negation words and search for what should exist
        cleaned = (
            claim_text.replace("does not", "")
            .replace("no mention", "")
            .replace("fails to provide", "")
        )
        queries.append(cleaned[:100].strip())

    return queries


def _generate_efficacy_queries(claim_text: str) -> List[str]:
    """Generate queries for product efficacy claims."""
    queries = []

    # Extract product name
    product_match = re.search(
        r"\b([A-Z][a-z]+(?:zem|trim|lean|fit|loss))\b", claim_text
    )
    product = product_match.group(1) if product_match else None

    # Extract efficacy metrics
    weight_match = re.search(r"(\d+)\s+pounds", claim_text)
    pct_match = re.search(r"(\d+)%", claim_text)

    if product:
        # Search for product reviews and FDA info
        queries.append(f'"{product}" FDA approval clinical trial')
        queries.append(f'"{product}" scam review investigation')

        if weight_match or pct_match:
            queries.append(f'"{product}" weight loss study results verification')

    # Generic efficacy search
    if not queries:
        queries.append(f'weight loss supplement clinical trial FDA {product or ""}')

    return queries


def _generate_generic_queries(claim_text: str) -> List[str]:
    """Generate generic queries for other claim types."""
    # Extract key entities and numbers
    entities = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", claim_text)
    numbers = re.findall(r"\b\d+(?:\.\d+)?%?\b", claim_text)

    # Build query from entities and numbers
    query_parts = []
    if entities[:2]:  # Top 2 entities
        query_parts.extend(entities[:2])
    if numbers[:1]:  # First number
        query_parts.append(numbers[0])

    if query_parts:
        queries = [" ".join(query_parts)]
    else:
        queries = [claim_text[:100]]

    return queries


def generate_multi_query_strategy(
    claim_text: str, claim_type: str
) -> Dict[str, List[str]]:
    """
    Generate multiple query strategies: primary, fallback, and negative.

    Args:
        claim_text: The claim to verify
        claim_type: Type of claim

    Returns:
        Dictionary with 'primary', 'fallback', and 'negative' query lists
    """
    # Primary queries: most specific
    primary = generate_verification_queries(claim_text, claim_type, max_queries=2)

    # Fallback queries: broader terms
    fallback = _generate_fallback_queries(claim_text, claim_type)

    # Negative queries: terms that would disprove the claim
    negative = _generate_negative_queries(claim_text, claim_type)

    return {"primary": primary, "fallback": fallback, "negative": negative}


def _generate_fallback_queries(claim_text: str, claim_type: str) -> List[str]:
    """Generate broader fallback queries."""
    # Remove specific details and use general terms
    general_terms = {
        "credential": "doctor medical license verification",
        "publication": "magazine award health expert",
        "study": "clinical trial research study",
        "absence": claim_text.replace("does not", "")[:50],
        "product_efficacy": "weight loss supplement effectiveness",
        "other": " ".join(claim_text.split()[:10]),
    }

    fallback = general_terms.get(claim_type, claim_text[:80])
    return [fallback]


def _generate_negative_queries(claim_text: str, claim_type: str) -> List[str]:
    """Generate queries that would disprove the claim."""
    negative_terms = {
        "credential": "fraud fake unlicensed medical board complaint",
        "publication": "false claim debunked never said",
        "study": "retracted fabricated no evidence",
        "product_efficacy": "scam fake FDA warning",
        "other": "false debunked myth",
    }

    # Extract main entity
    entity_match = re.search(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b", claim_text)
    entity = entity_match.group(1) if entity_match else ""

    negative_term = negative_terms.get(claim_type, "false claim")

    if entity:
        return [f'"{entity}" {negative_term}']
    else:
        return [f"{claim_text[:50]} {negative_term}"]


def log_query_effectiveness(
    query: str, results_count: int, top_results_relevance: float
) -> None:
    """
    Log query effectiveness metrics for monitoring.

    Args:
        query: The search query
        results_count: Number of results returned
        top_results_relevance: Relevance score (0-1) of top 3 results
    """
    effectiveness = (
        "GOOD"
        if results_count >= 5 and top_results_relevance >= 0.5
        else "POOR" if results_count < 2 or top_results_relevance < 0.3 else "FAIR"
    )

    logger.info(f"Query effectiveness: {effectiveness}")
    logger.info(f"  Query: {query[:80]}...")
    logger.info(f"  Results: {results_count}, Relevance: {top_results_relevance:.2f}")

    if effectiveness == "POOR":
        logger.warning("⚠️  Query returned poor results. Consider refinement.")


