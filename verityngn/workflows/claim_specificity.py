"""
Claim Specificity Module

Provides functions for scoring claim specificity, predicting verifiability,
and classifying claim types to improve claim extraction quality.
"""

import re
import logging
from typing import Dict, Any, Tuple, List
from enum import Enum

logger = logging.getLogger(__name__)


class ClaimType(Enum):
    """Enumeration of claim types for classification."""

    CREDENTIAL = "credential"
    PUBLICATION = "publication"
    STUDY = "study"
    PRODUCT_EFFICACY = "product_efficacy"
    CELEBRITY_ENDORSEMENT = "celebrity"
    CONSPIRACY_THEORY = "conspiracy"
    ABSENCE = "absence"
    OTHER = "other"


def calculate_specificity_score(claim_text: str) -> Tuple[int, Dict[str, int]]:
    """
    Calculate specificity score for a claim (0-100 scale).

    Scoring breakdown:
    - Proper nouns (30 pts): Names, institutions, publications
    - Temporal specificity (25 pts): Dates, durations, timeframes
    - Quantitative data (20 pts): Numbers, percentages, measurements
    - Source attribution (25 pts): Citations, references, credentials

    Args:
        claim_text: The claim text to score

    Returns:
        Tuple of (total_score, breakdown_dict)
    """
    breakdown = {"proper_nouns": 0, "temporal": 0, "quantitative": 0, "attribution": 0}

    # Special handling for absence claims - they're inherently specific!
    text_lower = claim_text.lower()
    if any(
        phrase in text_lower
        for phrase in [
            "does not state",
            "does not mention",
            "no mention of",
            "fails to provide",
            "video does not",
        ]
    ):
        # Absence claims are highly specific by nature
        breakdown["attribution"] = 25  # Full attribution points
        breakdown["proper_nouns"] = 20  # High proper noun score
        total_score = 85  # Base score for absence claims
        return total_score, breakdown

    # 1. PROPER NOUNS (30 pts max)
    # Check for specific names (Title + Multiple Capitalized Words)
    proper_noun_patterns = [
        r"\b(?:Dr\.|Professor|Mr\.|Ms\.|Mrs\.)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b",  # Dr. John Smith
        r"\b[A-Z][a-z]+\s+(?:University|Institute|Hospital|College|School)\b",  # Harvard University
        r"\b(?:Johns?\s+Hopkins|Harvard|Yale|Stanford|MIT|Oxford|Cambridge)\b",  # Specific institutions
        r"\bTime\s+Magazine\b|\bNew\s+York\s+Times\b|\bWSJ\b|\bJAMA\b",  # Publications
    ]

    proper_noun_count = sum(
        len(re.findall(pattern, claim_text)) for pattern in proper_noun_patterns
    )

    if proper_noun_count >= 3:
        breakdown["proper_nouns"] = 30
    elif proper_noun_count == 2:
        breakdown["proper_nouns"] = 20
    elif proper_noun_count == 1:
        breakdown["proper_nouns"] = 10
    else:
        # Generic check for any capitalized multi-word phrases
        generic_proper = len(re.findall(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b", claim_text))
        breakdown["proper_nouns"] = min(5, generic_proper * 2)

    # 2. TEMPORAL SPECIFICITY (25 pts max)
    # Full dates (e.g., "March 15, 2023")
    full_date_pattern = r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b"
    # Years
    year_pattern = r"\b(19|20)\d{2}\b"
    # Specific durations
    duration_pattern = r"\b\d+\s+(?:days?|weeks?|months?|years?)\b"

    if re.search(full_date_pattern, claim_text):
        breakdown["temporal"] = 25
    elif len(re.findall(year_pattern, claim_text)) >= 2:
        breakdown["temporal"] = 20
    elif re.search(year_pattern, claim_text):
        breakdown["temporal"] = 15
    elif re.search(duration_pattern, claim_text):
        breakdown["temporal"] = 10
    elif any(term in claim_text.lower() for term in ["recently", "soon", "currently"]):
        breakdown["temporal"] = 2

    # 3. QUANTITATIVE DATA (20 pts max)
    # Percentages
    percentage_pattern = r"\d+(?:\.\d+)?%"
    # Numbers with context
    number_with_context = r"\d+(?:,\d{3})*(?:\.\d+)?\s+(?:people|participants|volunteers|subjects|patients|pounds|kg|lbs|dollars|\$)"
    # Sample sizes
    sample_size_pattern = (
        r"\b(?:n\s*=|sample\s+size\s+of|over|more\s+than)\s+\d+(?:,\d{3})*\b"
    )

    percentages = len(re.findall(percentage_pattern, claim_text))
    contextual_numbers = len(re.findall(number_with_context, claim_text, re.IGNORECASE))
    sample_sizes = len(re.findall(sample_size_pattern, claim_text, re.IGNORECASE))

    quant_score = 0
    if sample_sizes > 0:
        quant_score += 10
    if percentages > 0:
        quant_score += 7
    if contextual_numbers > 0:
        quant_score += min(5, contextual_numbers * 3)

    breakdown["quantitative"] = min(20, quant_score)

    # 4. SOURCE ATTRIBUTION (25 pts max)
    # Specific citations (e.g., "Smith et al. 2023 in JAMA")
    specific_citation = r"\b[A-Z][a-z]+\s+et\s+al\.?\s+\(?\d{4}\)?"
    # DOI or PMID
    doi_pattern = r"\b(?:DOI|doi):\s*10\.\d+/[^\s]+"
    # Named studies/trials
    named_study = r'\b(?:called|titled|named)\s+"[^"]+"'
    # Journal names
    journal_pattern = r"\b(?:published\s+in|in\s+the)\s+(?:Journal\s+of|American\s+Journal|JAMA|Nature|Science|Lancet)\b"

    if re.search(doi_pattern, claim_text, re.IGNORECASE):
        breakdown["attribution"] = 25
    elif re.search(specific_citation, claim_text):
        breakdown["attribution"] = 20
    elif re.search(named_study, claim_text, re.IGNORECASE):
        breakdown["attribution"] = 15
    elif re.search(journal_pattern, claim_text, re.IGNORECASE):
        breakdown["attribution"] = 10
    elif any(
        term in claim_text
        for term in ["University", "Institute", "Hospital", "Medical School"]
    ):
        breakdown["attribution"] = 8
    elif re.search(r"\bstudy\s+(?:by|from|at)\s+[A-Z]", claim_text):
        breakdown["attribution"] = 5
    elif any(
        vague in claim_text.lower()
        for vague in ["a study", "experts say", "researchers", "some doctors"]
    ):
        breakdown["attribution"] = 2

    total_score = sum(breakdown.values())

    logger.debug(f"Specificity score for claim: {total_score}/100 - {breakdown}")

    return total_score, breakdown


def predict_verifiability(claim_text: str, claim_type: ClaimType) -> float:
    """
    Predict verifiability likelihood for a claim (0.0-1.0 scale).

    Based on historical corpus analysis:
    - High verifiability (0.8-1.0): Specific awards, credentials, publications
    - Medium verifiability (0.5-0.7): Product efficacy with numbers, study references
    - Low verifiability (0.2-0.4): Generic statements, opinions, marketing
    - Unverifiable (0.0-0.1): Conspiracy theories, celebrity secrets, anecdotes

    Args:
        claim_text: The claim text
        claim_type: Classified claim type

    Returns:
        Verifiability score between 0.0 and 1.0
    """
    # Base score by claim type
    type_base_scores = {
        ClaimType.CREDENTIAL: 0.7,
        ClaimType.PUBLICATION: 0.75,
        ClaimType.STUDY: 0.6,
        ClaimType.PRODUCT_EFFICACY: 0.4,
        ClaimType.CELEBRITY_ENDORSEMENT: 0.3,
        ClaimType.CONSPIRACY_THEORY: 0.1,
        ClaimType.ABSENCE: 0.9,  # Absence claims are highly verifiable!
        ClaimType.OTHER: 0.4,
    }

    base_score = type_base_scores.get(claim_type, 0.4)

    # Adjust based on specificity
    specificity_score, _ = calculate_specificity_score(claim_text)
    specificity_factor = specificity_score / 100.0

    # Weight: 60% type-based, 40% specificity-based
    final_score = (base_score * 0.6) + (specificity_factor * 0.4)

    # Penalties for vague language
    vague_terms = [
        "a study",
        "experts",
        "some people",
        "many",
        "often",
        "recently",
        "reportedly",
    ]
    vagueness_count = sum(
        1 for term in vague_terms if term.lower() in claim_text.lower()
    )
    final_score = max(0.0, final_score - (vagueness_count * 0.05))

    # Bonus for specific elements
    if re.search(r"\b(19|20)\d{2}\b", claim_text):  # Has year
        final_score = min(1.0, final_score + 0.1)

    if re.search(
        r"\b[A-Z][a-z]+\s+(?:University|Institute)\b", claim_text
    ):  # Has institution
        final_score = min(1.0, final_score + 0.1)

    logger.debug(
        f"Verifiability prediction: {final_score:.2f} (type={claim_type.value}, spec={specificity_score})"
    )

    return final_score


def classify_claim_type(claim_text: str) -> ClaimType:
    """
    Classify claim into one of the predefined types.

    Args:
        claim_text: The claim text to classify

    Returns:
        ClaimType enum value
    """
    text_lower = claim_text.lower()

    # Check for absence claims (NEW!)
    if any(
        phrase in text_lower
        for phrase in [
            "does not state",
            "does not mention",
            "no mention of",
            "fails to provide",
            "missing",
            "absent",
        ]
    ):
        return ClaimType.ABSENCE

    # Check for conspiracy theories
    conspiracy_indicators = [
        "threatened",
        "suppressed",
        "hidden truth",
        "big pharma",
        "they dont want you to know",
        "conspiracy",
    ]
    if any(ind in text_lower for ind in conspiracy_indicators):
        return ClaimType.CONSPIRACY_THEORY

    # Check for credentials
    credential_indicators = [
        "dr.",
        "doctor",
        "phd",
        "md",
        "professor",
        "credentials",
        "graduated from",
        "studied at",
        "board certified",
        "licensed",
        "medical school",
    ]
    if any(ind in text_lower for ind in credential_indicators):
        return ClaimType.CREDENTIAL

    # Check for publications/awards
    publication_indicators = [
        "magazine",
        "newspaper",
        "published",
        "article",
        "journal",
        "dubbed",
        "named",
        "awarded",
        "won",
        "recognized as",
    ]
    if any(ind in text_lower for ind in publication_indicators):
        return ClaimType.PUBLICATION

    # Check for studies/research
    study_indicators = [
        "study",
        "research",
        "clinical trial",
        "experiment",
        "participants",
        "volunteers",
        "peer-reviewed",
        "findings",
        "meta-analysis",
    ]
    if any(ind in text_lower for ind in study_indicators):
        return ClaimType.STUDY

    # Check for celebrity endorsements
    celebrity_indicators = [
        "celebrity",
        "hollywood",
        "stars",
        "famous",
        "secret weapon",
        "a-list",
    ]
    if any(ind in text_lower for ind in celebrity_indicators):
        return ClaimType.CELEBRITY_ENDORSEMENT

    # Check for product efficacy
    efficacy_indicators = [
        "lost",
        "lose",
        "pounds",
        "weight",
        "effective",
        "works",
        "results",
        "improved",
        "reduced",
        "increased",
        "benefit",
    ]
    if any(ind in text_lower for ind in efficacy_indicators):
        return ClaimType.PRODUCT_EFFICACY

    return ClaimType.OTHER


def enhance_claim_specificity(
    claim_text: str, video_content: str = None
) -> Dict[str, Any]:
    """
    Analyze a claim and suggest how to make it more specific/verifiable.

    Args:
        claim_text: The claim to analyze
        video_content: Optional video transcript/content for context

    Returns:
        Dictionary with enhancement suggestions
    """
    specificity_score, breakdown = calculate_specificity_score(claim_text)
    claim_type = classify_claim_type(claim_text)
    verifiability = predict_verifiability(claim_text, claim_type)

    suggestions = []

    # Analyze what's missing
    if breakdown["attribution"] < 10:
        if "study" in claim_text.lower():
            suggestions.append(
                "Add study details: lead author, institution, journal name, or DOI"
            )
        elif any(word in claim_text.lower() for word in ["doctor", "dr.", "expert"]):
            suggestions.append(
                "Add credentials: institution, degree, license number, or affiliation"
            )

    if breakdown["temporal"] < 10:
        suggestions.append("Add temporal specificity: exact date, year, or duration")

    if breakdown["quantitative"] < 10 and claim_type == ClaimType.STUDY:
        suggestions.append(
            "Add quantitative data: sample size, percentages, or measurements"
        )

    if breakdown["proper_nouns"] < 15:
        suggestions.append(
            "Add proper nouns: specific names, institutions, or publications"
        )

    # Check for vague language
    vague_terms = {
        "a study": "Name the specific study or author",
        "experts": "Name specific experts or institutions",
        "researchers": "Identify the research team or institution",
        "recently": "Provide specific date or year",
        "many": "Provide specific number or percentage",
        "often": "Provide frequency or study data",
    }

    for vague, fix in vague_terms.items():
        if vague in claim_text.lower():
            suggestions.append(f"Replace '{vague}' with: {fix}")

    return {
        "original_claim": claim_text,
        "specificity_score": specificity_score,
        "score_breakdown": breakdown,
        "claim_type": claim_type.value,
        "verifiability": verifiability,
        "quality_level": _get_quality_level(specificity_score, verifiability),
        "suggestions": suggestions,
        "is_verifiable": verifiability >= 0.6 and specificity_score >= 40,
    }


def _get_quality_level(specificity: int, verifiability: float) -> str:
    """Determine overall quality level of a claim."""
    if specificity >= 70 and verifiability >= 0.8:
        return "EXCELLENT"
    elif specificity >= 50 and verifiability >= 0.6:
        return "GOOD"
    elif specificity >= 40 and verifiability >= 0.5:
        return "ACCEPTABLE"
    elif specificity >= 30 or verifiability >= 0.4:
        return "WEAK"
    else:
        return "POOR"


def filter_low_quality_claims(
    claims: List[Dict[str, Any]],
    min_specificity: int = 40,
    min_verifiability: float = 0.5,
) -> Tuple[List[Dict], List[Dict]]:
    """
    Filter claims based on quality thresholds.

    Args:
        claims: List of claim dictionaries
        min_specificity: Minimum specificity score (0-100)
        min_verifiability: Minimum verifiability score (0-1)

    Returns:
        Tuple of (passed_claims, failed_claims)
    """
    passed = []
    failed = []

    for claim in claims:
        claim_text = claim.get("claim_text", "")
        claim_type = classify_claim_type(claim_text)

        # Calculate scores
        specificity, _ = calculate_specificity_score(claim_text)
        verifiability = predict_verifiability(claim_text, claim_type)

        # Add scores to claim
        claim["specificity_score"] = specificity
        claim["verifiability_score"] = verifiability
        claim["claim_type"] = claim_type.value

        # Filter out conspiracy theories regardless of scores
        if claim_type == ClaimType.CONSPIRACY_THEORY:
            failed.append(claim)
            continue

        # Check thresholds
        if specificity >= min_specificity and verifiability >= min_verifiability:
            passed.append(claim)
        else:
            failed.append(claim)

    logger.info(
        f"Quality filtering: {len(passed)} passed, {len(failed)} failed (threshold: spec>={min_specificity}, ver>={min_verifiability})"
    )

    return passed, failed
