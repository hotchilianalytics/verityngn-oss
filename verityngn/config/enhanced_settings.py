"""
Enhanced Settings for VerityNgn

Configuration flags for enhanced claim extraction and analysis features.
"""

import os

# Enhanced Claim Extraction Settings
ENHANCED_CLAIMS_ENABLED = os.getenv("ENHANCED_CLAIMS_ENABLED", "true").lower() in (
    "true",
    "1",
    "yes",
)
ENHANCED_CLAIMS_MIN_SPECIFICITY = int(
    os.getenv("ENHANCED_CLAIMS_MIN_SPECIFICITY", "40")
)
ENHANCED_CLAIMS_MIN_VERIFIABILITY = float(
    os.getenv("ENHANCED_CLAIMS_MIN_VERIFIABILITY", "0.5")
)
ENHANCED_CLAIMS_TARGET_COUNT = int(os.getenv("ENHANCED_CLAIMS_TARGET_COUNT", "15"))

# YouTube Transcript Analysis Settings
YOUTUBE_TRANSCRIPT_ANALYSIS_ENABLED = os.getenv(
    "YOUTUBE_TRANSCRIPT_ANALYSIS_ENABLED", "true"
).lower() in ("true", "1", "yes")
YOUTUBE_TRANSCRIPT_MAX_VIDEOS = int(os.getenv("YOUTUBE_TRANSCRIPT_MAX_VIDEOS", "3"))
YOUTUBE_TRANSCRIPT_MAX_LENGTH = int(os.getenv("YOUTUBE_TRANSCRIPT_MAX_LENGTH", "10000"))

# Absence Claim Generation
ABSENCE_CLAIMS_ENABLED = os.getenv("ABSENCE_CLAIMS_ENABLED", "true").lower() in (
    "true",
    "1",
    "yes",
)
ABSENCE_CLAIMS_MIN_COUNT = int(os.getenv("ABSENCE_CLAIMS_MIN_COUNT", "3"))

# Display Settings for UI
SHOW_CLAIM_QUALITY_SCORES = os.getenv("SHOW_CLAIM_QUALITY_SCORES", "true").lower() in (
    "true",
    "1",
    "yes",
)
SHOW_ABSENCE_CLAIMS_SEPARATELY = os.getenv(
    "SHOW_ABSENCE_CLAIMS_SEPARATELY", "true"
).lower() in ("true", "1", "yes")
SHOW_TRANSCRIPT_ANALYSIS = os.getenv("SHOW_TRANSCRIPT_ANALYSIS", "true").lower() in (
    "true",
    "1",
    "yes",
)
