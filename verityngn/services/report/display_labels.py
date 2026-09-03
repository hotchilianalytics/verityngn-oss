"""User-facing display labels for claim risk assessment.

Internal probability keys remain TRUE / FALSE / UNCERTAIN.
Wire AssessmentLevel enum *values* stay stable for gallery compatibility;
these helpers map them to risk-abatement language for docs/UI/CLI.
"""
from __future__ import annotations

from typing import Mapping

# Soft display names for AssessmentLevel.value strings (report.py)
ASSESSMENT_DISPLAY: dict[str, str] = {
    "Highly Likely to be True": "Low claim risk (well supported)",
    "Likely to be True": "Low–moderate claim risk (mostly supported)",
    "Mixed Truthfulness": "Elevated claim risk (contested / mixed)",
    "Likely to be False": "High claim risk (mostly contested)",
    "Highly Likely to be False": "Severe claim risk (strongly contested)",
    "Unable to Determine": "Unresolved claim risk",
}

# Three-state probability category → risk display
CATEGORY_DISPLAY: dict[str, str] = {
    "TRUE": "Supported",
    "FALSE": "Contested",
    "UNCERTAIN": "Unresolved",
}

VERIFICATION_RESULT_DISPLAY: dict[str, str] = {
    "HIGHLY_LIKELY_TRUE": "Low claim risk (well supported)",
    "LIKELY_TRUE": "Low–moderate claim risk (mostly supported)",
    "LEANING_TRUE": "Leaning supported",
    "UNCERTAIN": "Unresolved claim risk",
    "LEANING_FALSE": "Leaning contested",
    "LIKELY_FALSE": "High claim risk (mostly contested)",
    "HIGHLY_LIKELY_FALSE": "Severe claim risk (strongly contested)",
}

# Claim extraction modality (analysis.py source_type field)
VISUAL_SOURCE_TYPES: frozenset[str] = frozenset(
    {"visual_text", "graphic", "chart", "demonstration"}
)

MODALITY_DISPLAY: dict[str, str] = {
    "spoken": "Spoken",
    "visual_text": "On-screen text",
    "graphic": "Graphic",
    "chart": "Chart",
    "demonstration": "Demo / action",
    "video_analysis": "Video analysis",
    "unknown": "Unknown",
}


def claim_modality_display_label(source_type: str | None) -> str:
    """User-facing label for claim extraction modality (spoken vs on-screen etc.)."""
    if not source_type:
        return MODALITY_DISPLAY["unknown"]
    key = str(source_type).strip().lower()
    return MODALITY_DISPLAY.get(key, key.replace("_", " ").title())


def is_visual_only_claim(source_type: str | None) -> bool:
    """True when the claim is attributed to pixels, not transcript speech."""
    if not source_type:
        return False
    return str(source_type).strip().lower() in VISUAL_SOURCE_TYPES


def display_assessment(level: str | None) -> str:
    if not level:
        return ASSESSMENT_DISPLAY["Unable to Determine"]
    return ASSESSMENT_DISPLAY.get(level, level)


def display_category(category: str | None) -> str:
    if not category:
        return CATEGORY_DISPLAY["UNCERTAIN"]
    key = str(category).upper()
    return CATEGORY_DISPLAY.get(key, category)


def display_verification_result(result: str | None) -> str:
    if not result:
        return VERIFICATION_RESULT_DISPLAY["UNCERTAIN"]
    key = str(result).upper().replace(" ", "_")
    return VERIFICATION_RESULT_DISPLAY.get(key, result)


def category_from_prob_dist(prob_dist: Mapping[str, float] | None) -> str:
    """Map TRUE/FALSE/UNCERTAIN masses to a single category key."""
    if not prob_dist:
        return "UNCERTAIN"
    t = float(prob_dist.get("TRUE", 0) or 0)
    f = float(prob_dist.get("FALSE", 0) or 0)
    u = float(prob_dist.get("UNCERTAIN", 0) or 0)
    best = max(("TRUE", t), ("FALSE", f), ("UNCERTAIN", u), key=lambda x: x[1])
    return best[0]
