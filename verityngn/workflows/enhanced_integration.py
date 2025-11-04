"""
Enhanced Features Integration for VerityNgn

This module provides integration hooks for enhanced claim extraction
and analysis features, allowing them to be easily toggled on/off.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Import settings
try:
    from verityngn.config.enhanced_settings import (
        ENHANCED_CLAIMS_ENABLED,
        ENHANCED_CLAIMS_MIN_SPECIFICITY,
        ENHANCED_CLAIMS_MIN_VERIFIABILITY,
        ENHANCED_CLAIMS_TARGET_COUNT,
        ABSENCE_CLAIMS_ENABLED,
    )
except ImportError:
    # Defaults if config not found
    ENHANCED_CLAIMS_ENABLED = True
    ENHANCED_CLAIMS_MIN_SPECIFICITY = 40
    ENHANCED_CLAIMS_MIN_VERIFIABILITY = 0.5
    ENHANCED_CLAIMS_TARGET_COUNT = 15
    ABSENCE_CLAIMS_ENABLED = True


async def enhance_extracted_claims(
    initial_result: Dict[str, Any],
    video_url: str,
    video_id: str,
    video_info: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Post-process extracted claims with quality scoring and absence claim generation.

    This function enhances claims AFTER initial extraction, adding:
    - Specificity scores
    - Verifiability predictions
    - Claim type classification
    - Quality filtering
    - Absence claim generation

    Args:
        initial_result: Result from initial claim extraction
        video_url: Video URL
        video_id: Video ID
        video_info: Video metadata

    Returns:
        Enhanced result with scored and filtered claims
    """
    if not ENHANCED_CLAIMS_ENABLED:
        logger.info("Enhanced claims extraction is disabled, returning original claims")
        return initial_result

    logger.info("🎯 Enhancing claims with quality scoring and absence generation")

    try:
        from verityngn.workflows.claim_specificity import (
            calculate_specificity_score,
            classify_claim_type,
            predict_verifiability,
        )
        from verityngn.workflows.enhanced_claim_extraction import (
            _generate_absence_claims,
        )

        if not isinstance(initial_result, dict) or "claims" not in initial_result:
            logger.warning("Invalid initial result format, skipping enhancement")
            return initial_result

        initial_claims = initial_result.get("claims", [])
        logger.info(f"📝 Scoring {len(initial_claims)} initial claims")

        # PASS 1: Score all claims
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

        # PASS 2: Filter low-quality claims
        filtered_claims = [
            c
            for c in scored_claims
            if c.get("claim_type") != "conspiracy"
            and c.get("specificity_score", 0) >= ENHANCED_CLAIMS_MIN_SPECIFICITY
            and c.get("verifiability_score", 0) >= ENHANCED_CLAIMS_MIN_VERIFIABILITY
        ]

        logger.info(
            f"🔥 Filtered to {len(filtered_claims)} claims (removed {len(scored_claims) - len(filtered_claims)} low-quality)"
        )

        # PASS 3: Generate absence claims if enabled
        absence_claims = []
        if ABSENCE_CLAIMS_ENABLED:
            logger.info("🚫 Generating absence claims")
            absence_claims = _generate_absence_claims(filtered_claims, video_info)
            logger.info(f"✅ Generated {len(absence_claims)} absence claims")

        # PASS 4: Rank and select
        all_claims = filtered_claims + absence_claims

        # Sort by composite score
        for claim in all_claims:
            specificity = claim.get("specificity_score", 0) / 100.0
            verifiability = claim.get("verifiability_score", 0.0)
            type_priority = _get_type_priority(claim.get("claim_type", "other"))
            claim["composite_rank_score"] = (
                verifiability * 0.4 + specificity * 0.3 + type_priority * 0.2 + 0.1
            )

        # Sort by composite score
        ranked_claims = sorted(
            all_claims, key=lambda x: x.get("composite_rank_score", 0), reverse=True
        )

        # Select top claims with diversity
        final_claims = _select_diverse_claims(
            ranked_claims, ENHANCED_CLAIMS_TARGET_COUNT
        )

        logger.info(f"✨ Final selection: {len(final_claims)} high-quality claims")

        # Return enhanced result
        return {
            **initial_result,
            "claims": final_claims,
            "extraction_metadata": {
                "initial_claim_count": len(initial_claims),
                "after_scoring": len(scored_claims),
                "after_filtering": len(filtered_claims),
                "absence_claims": len(absence_claims),
                "final_count": len(final_claims),
                "quality_distribution": quality_dist,
                "enhancement_applied": True,
            },
        }

    except Exception as e:
        logger.error(f"Enhancement failed: {e}. Returning original claims.")
        import traceback

        traceback.print_exc()
        return initial_result


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


def _get_type_priority(claim_type: str) -> float:
    """Get priority score for claim type."""
    priorities = {
        "absence": 1.0,
        "credential": 0.9,
        "publication": 0.85,
        "study": 0.8,
        "product_efficacy": 0.6,
        "celebrity": 0.4,
        "other": 0.5,
    }
    return priorities.get(claim_type, 0.5)


def _select_diverse_claims(ranked_claims: list, target_count: int) -> list:
    """Select claims ensuring diversity across types."""
    selected = []
    type_counts = {}

    # First, ensure representation from key types
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



