"""
Enhanced Claim Extraction Pipeline

Multi-pass extraction system with probability-based sampling,
specificity scoring, and absence claim generation.
"""

import logging
from typing import Dict, Any, List

from verityngn.workflows.claim_specificity import (
    calculate_specificity_score,
    classify_claim_type,
    predict_verifiability,
)

logger = logging.getLogger(__name__)


async def extract_claims_multi_pass(
    video_url: str,
    video_id: str,
    video_info: Dict[str, Any],
    base_extraction_func: callable,
) -> Dict[str, Any]:
    """
    Multi-pass claim extraction with quality enhancement.

    Pass 1: Initial extraction (20-30 claims)
    Pass 2: Specificity scoring and filtering
    Pass 3: Claim enhancement for semi-specific claims
    Pass 4: Absence claim generation
    Pass 5: Final ranking and selection

    Args:
        video_url: YouTube video URL
        video_id: Video ID
        video_info: Video metadata
        base_extraction_func: Async function to call for initial extraction

    Returns:
        Enhanced claims dictionary
    """
    logger.info(f"🚀 Starting multi-pass claim extraction for {video_id}")

    # PASS 1: Initial broad extraction
    logger.info("📝 PASS 1: Initial claim extraction")
    initial_result = await base_extraction_func(video_url, video_id, video_info)

    if not isinstance(initial_result, dict) or "claims" not in initial_result:
        logger.error("Initial extraction failed or returned invalid format")
        return initial_result

    initial_claims = initial_result.get("claims", [])
    logger.info(f"✅ Extracted {len(initial_claims)} initial claims")

    # PASS 2: Score and filter claims
    logger.info("🔍 PASS 2: Scoring claims for specificity and verifiability")
    scored_claims = []
    for claim in initial_claims:
        claim_text = claim.get("claim_text", "")
        if not claim_text:
            continue

        # Calculate scores
        specificity, breakdown = calculate_specificity_score(claim_text)
        claim_type = classify_claim_type(claim_text)
        verifiability = predict_verifiability(claim_text, claim_type)

        # Add scores to claim
        claim["specificity_score"] = specificity
        claim["specificity_breakdown"] = breakdown
        claim["verifiability_score"] = verifiability
        claim["claim_type"] = claim_type.value
        claim["quality_level"] = _get_quality_level(specificity, verifiability)

        scored_claims.append(claim)

    # Log quality distribution
    quality_dist = {}
    for claim in scored_claims:
        level = claim.get("quality_level", "UNKNOWN")
        quality_dist[level] = quality_dist.get(level, 0) + 1
    logger.info(f"📊 Quality distribution: {quality_dist}")

    filtered_claims = [
        c
        for c in scored_claims
        if c.get("claim_type") != "conspiracy" and c.get("specificity_score", 0) >= 15
    ]
    logger.info(
        f"🔥 Filtered to {len(filtered_claims)} claims (removed conspiracy theories and very weak claims)"
    )

    # PASS 3: Enhance semi-specific claims (optional, commented out for now to avoid extra LLM calls)
    # enhanced_claims = await _enhance_weak_claims(filtered_claims, video_info)
    enhanced_claims = filtered_claims  # Skip enhancement for now

    # PASS 4: Generate absence claims
    logger.info("🚫 PASS 4: Generating absence claims")
    absence_claims = _generate_absence_claims(enhanced_claims, video_info)
    logger.info(f"✅ Generated {len(absence_claims)} absence claims")

    # Combine all claims
    all_claims = enhanced_claims + absence_claims

    # PASS 5: Final ranking and selection
    logger.info("🎯 PASS 5: Final ranking and selection")
    
    # Use config for target count if available, otherwise default to 20
    from verityngn.config.settings import get_config
    config = get_config()
    target_count = config.get("processing.min_claims", 20)
    
    final_claims = _rank_and_select_claims(all_claims, target_count=target_count)

    logger.info(f"✨ Final output: {len(final_claims)} high-quality claims")

    # Return in same format as original
    return {
        "initial_report": initial_result.get("initial_report", ""),
        "claims": final_claims,
        "video_analysis_summary": f"Multi-pass extraction: {len(initial_claims)} → {len(final_claims)} claims",
        "extraction_metadata": {
            "initial_claim_count": len(initial_claims),
            "after_filtering": len(filtered_claims),
            "absence_claims": len(absence_claims),
            "final_count": len(final_claims),
            "quality_distribution": quality_dist,
        },
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


def _generate_absence_claims(
    existing_claims: List[Dict], video_info: Dict[str, Any]
) -> List[Dict]:
    """
    Generate absence claims about missing information.

    Focus on:
    - Missing credentials (medical school, license number, etc.)
    - Missing study details (journal name, DOI, lead author)
    - Missing institutional affiliations

    Args:
        existing_claims: List of claims already extracted
        video_info: Video metadata

    Returns:
        List of absence claim dictionaries
    """
    absence_claims = []

    # Extract all mentioned names/entities from existing claims
    mentioned_people = set()
    mentioned_institutions = set()
    mentioned_studies = set()

    for claim in existing_claims:
        text = claim.get("claim_text", "").lower()

        # Look for names (Dr. X, Professor Y, etc.)
        import re

        names = re.findall(
            r"(?:dr\.|professor|mr\.|ms\.)\s+([a-z]+\s+[a-z]+)", text, re.IGNORECASE
        )
        mentioned_people.update(name.strip() for name in names)

        # Look for institutions
        institutions = re.findall(
            r"([a-z]+\s+(?:university|institute|hospital|college))", text, re.IGNORECASE
        )
        mentioned_institutions.update(inst.strip() for inst in institutions)

        # Look for studies
        if "study" in text or "research" in text:
            mentioned_studies.add(text[:100])  # Store snippet

    # Generate absence claims for frequently mentioned people
    for person in mentioned_people:
        if mentioned_people:  # If there are people mentioned
            # Check what credentials are NOT mentioned
            has_institution_claim = any(
                person.lower() in c.get("claim_text", "").lower()
                and any(
                    inst in c.get("claim_text", "").lower()
                    for inst in ["university", "college", "school"]
                )
                for c in existing_claims
            )

            if not has_institution_claim:
                absence_claims.append(
                    {
                        "claim_text": f"Video does not state where {person} obtained their medical degree or professional training.",
                        "timestamp": "N/A",
                        "speaker": "Analyst",
                        "source_type": "absence_analysis",
                        "initial_assessment": "Absence of verifiable credentials",
                        "specificity_score": 90,  # Absence claims are highly specific
                        "verifiability_score": 0.95,  # Highly verifiable (can check databases)
                        "claim_type": "absence",
                        "quality_level": "EXCELLENT",
                    }
                )

    # Generate generic absence claims if no specific people found
    if not mentioned_people and len(existing_claims) > 0:
        # Look for generic "doctor" or "expert" mentions
        has_expert = any(
            "doctor" in c.get("claim_text", "").lower()
            or "expert" in c.get("claim_text", "").lower()
            for c in existing_claims
        )

        if has_expert:
            absence_claims.append(
                {
                    "claim_text": "Video does not provide medical license numbers or board certifications for featured health experts.",
                    "timestamp": "N/A",
                    "speaker": "Analyst",
                    "source_type": "absence_analysis",
                    "initial_assessment": "Missing professional verification details",
                    "specificity_score": 85,
                    "verifiability_score": 0.9,
                    "claim_type": "absence",
                    "quality_level": "EXCELLENT",
                }
            )

    # Check for vague study references
    vague_study_claims = [
        c
        for c in existing_claims
        if "study" in c.get("claim_text", "").lower()
        and c.get("specificity_score", 0) < 50
    ]

    if len(vague_study_claims) >= 2:
        absence_claims.append(
            {
                "claim_text": "Video references multiple studies but does not provide study names, journal publications, or DOI numbers for verification.",
                "timestamp": "N/A",
                "speaker": "Analyst",
                "source_type": "absence_analysis",
                "initial_assessment": "Missing source attribution for scientific claims",
                "specificity_score": 80,
                "verifiability_score": 0.85,
                "claim_type": "absence",
                "quality_level": "EXCELLENT",
            }
        )

    # Check for product efficacy claims without study backing
    efficacy_claims = [
        c for c in existing_claims if c.get("claim_type") == "product_efficacy"
    ]

    if len(efficacy_claims) >= 3:
        has_backing = any(c.get("specificity_score", 0) > 60 for c in efficacy_claims)
        if not has_backing:
            absence_claims.append(
                {
                    "claim_text": "Video makes product efficacy claims but does not cite peer-reviewed clinical trials or FDA approvals.",
                    "timestamp": "N/A",
                    "speaker": "Analyst",
                    "source_type": "absence_analysis",
                    "initial_assessment": "Missing regulatory or scientific validation",
                    "specificity_score": 75,
                    "verifiability_score": 0.8,
                    "claim_type": "absence",
                    "quality_level": "GOOD",
                }
            )

    logger.info(f"🚫 Generated {len(absence_claims)} absence claims")
    return absence_claims


def _rank_and_select_claims(claims: List[Dict], target_count: int = 15) -> List[Dict]:
    """
    Rank claims by composite score and select top N.

    Ranking criteria:
    - Verifiability (40%)
    - Specificity (30%)
    - Claim type priority (20%)
    - Temporal distribution (10%)

    Args:
        claims: List of claims with scores
        target_count: Number of claims to select

    Returns:
        Top N ranked claims
    """
    # Calculate composite rank score for each claim
    for claim in claims:
        specificity = claim.get("specificity_score", 0) / 100.0  # Normalize to 0-1
        verifiability = claim.get("verifiability_score", 0.0)
        claim_type = claim.get("claim_type", "other")

        # Type priority scoring
        type_priorities = {
            "absence": 1.0,
            "credential": 0.9,
            "publication": 0.85,
            "study": 0.8,
            "product_efficacy": 0.6,
            "celebrity": 0.4,
            "other": 0.5,
        }
        type_priority = type_priorities.get(claim_type, 0.5)

        # Composite score
        composite = (
            verifiability * 0.4
            + specificity * 0.3
            + type_priority * 0.2
            + 0.1  # Base temporal score (simplified for now)
        )

        claim["composite_rank_score"] = composite

    # Sort by composite score
    ranked_claims = sorted(
        claims, key=lambda x: x.get("composite_rank_score", 0), reverse=True
    )

    # Ensure diversity: include at least one from each major type
    selected = []
    type_counts = {}

    # First, ensure we have representation from key types
    priority_types = ["absence", "credential", "publication", "study"]
    for ptype in priority_types:
        type_claims = [
            c
            for c in ranked_claims
            if c.get("claim_type") == ptype and c not in selected
        ]
        if type_claims:
            selected.append(type_claims[0])
            type_counts[ptype] = 1

    # Fill remaining slots with highest-ranked claims
    for claim in ranked_claims:
        if len(selected) >= target_count:
            break
        if claim not in selected:
            selected.append(claim)
            ctype = claim.get("claim_type", "other")
            type_counts[ctype] = type_counts.get(ctype, 0) + 1

    logger.info(f"🎯 Selected {len(selected)} claims with distribution: {type_counts}")

    return selected


async def extract_claims_enhanced_wrapper(
    video_url: str, video_id: str, video_info: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Wrapper function that applies multi-pass extraction.

    This can be used as a drop-in replacement for existing extraction functions.

    Args:
        video_url: YouTube video URL
        video_id: Video ID
        video_info: Video metadata

    Returns:
        Enhanced claims dictionary
    """
    # Import here to avoid circular dependency
    from verityngn.workflows.analysis import (
        extract_claims_with_gemini_multimodal_youtube_url_segmented_vertex,
    )

    return await extract_claims_multi_pass(
        video_url,
        video_id,
        video_info,
        base_extraction_func=extract_claims_with_gemini_multimodal_youtube_url_segmented_vertex,
    )
