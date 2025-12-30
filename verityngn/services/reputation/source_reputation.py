"""
Source Reputation Scoring Module

This module provides reputation scoring for YouTube channels and content creators,
particularly focused on distinguishing investigative journalists and scam-busters
from promotional or low-credibility sources.

The reputation score affects how the verification system treats claims:
- High reputation (0.7-1.0): Content from trusted investigators gets credibility boost
- Neutral (0.5): Unknown channels use default verification behavior
- Low reputation (0.0-0.4): Known promotional/scam channels get reduced credibility

Usage:
    from verityngn.services.reputation import get_channel_reputation, is_trusted_investigator
    
    reputation = get_channel_reputation("Coffeezilla")
    if is_trusted_investigator("coffeezilla"):
        # Boost credibility for investigative content
        pass
"""

import logging
from enum import Enum
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class ChannelCategory(Enum):
    """Categories of YouTube channels for reputation scoring."""
    SCAM_INVESTIGATION = "scam_investigation"
    MEDIA_CRITICISM = "media_criticism"
    INVESTIGATIVE_JOURNALISM = "investigative_journalism"
    FACT_CHECKING = "fact_checking"
    EDUCATIONAL = "educational"
    NEWS_ANALYSIS = "news_analysis"
    PROMOTIONAL = "promotional"
    ENTERTAINMENT = "entertainment"
    UNKNOWN = "unknown"


# Known reputable investigative channels with reputation scores
# Score range: 0.0 (no credibility) to 1.0 (highest credibility)
# These channels are known for thorough research and accurate reporting
TRUSTED_INVESTIGATORS: Dict[str, Dict] = {
    # Scam investigation and financial fraud
    "coffeezilla": {
        "reputation_score": 0.90,
        "category": ChannelCategory.SCAM_INVESTIGATION,
        "description": "Financial scam investigation, crypto fraud exposure",
        "verification_notes": "Known for thorough research, cited by major news outlets",
    },
    "coffeebreak": {
        "reputation_score": 0.90,
        "category": ChannelCategory.SCAM_INVESTIGATION,
        "description": "Coffeezilla's channel - scam investigation",
        "verification_notes": "Same as Coffeezilla",
    },
    "folding ideas": {
        "reputation_score": 0.85,
        "category": ChannelCategory.MEDIA_CRITICISM,
        "description": "Media criticism, NFT/crypto analysis",
        "verification_notes": "Documentary-style deep dives",
    },
    "dan olson": {
        "reputation_score": 0.85,
        "category": ChannelCategory.MEDIA_CRITICISM,
        "description": "Creator of Folding Ideas",
        "verification_notes": "Same as Folding Ideas",
    },
    
    # Media criticism and analysis
    "hbomberguy": {
        "reputation_score": 0.80,
        "category": ChannelCategory.MEDIA_CRITICISM,
        "description": "Media criticism, plagiarism investigation",
        "verification_notes": "Long-form investigative videos",
    },
    "harry brewis": {
        "reputation_score": 0.80,
        "category": ChannelCategory.MEDIA_CRITICISM,
        "description": "Creator of hbomberguy",
        "verification_notes": "Same as hbomberguy",
    },
    "internet historian": {
        "reputation_score": 0.75,
        "category": ChannelCategory.INVESTIGATIVE_JOURNALISM,
        "description": "Internet history, event investigation",
        "verification_notes": "Well-researched historical content",
    },
    
    # Tech and business investigation
    "louis rossmann": {
        "reputation_score": 0.75,
        "category": ChannelCategory.INVESTIGATIVE_JOURNALISM,
        "description": "Right to repair advocacy, Apple criticism",
        "verification_notes": "First-hand technical expertise",
    },
    "upper echelon gamers": {
        "reputation_score": 0.70,
        "category": ChannelCategory.INVESTIGATIVE_JOURNALISM,
        "description": "Gaming industry investigation",
        "verification_notes": "Gaming industry analysis",
    },
    
    # Fact-checking and debunking
    "thunderf00t": {
        "reputation_score": 0.75,
        "category": ChannelCategory.FACT_CHECKING,
        "description": "Science debunking, tech criticism",
        "verification_notes": "PhD scientist, technical analysis",
    },
    "common sense skeptic": {
        "reputation_score": 0.70,
        "category": ChannelCategory.FACT_CHECKING,
        "description": "Space industry analysis, Tesla criticism",
        "verification_notes": "Data-driven analysis",
    },
    
    # Documentary and long-form journalism
    "atrocity guide": {
        "reputation_score": 0.80,
        "category": ChannelCategory.INVESTIGATIVE_JOURNALISM,
        "description": "Internet culture investigation",
        "verification_notes": "Thorough research methodology",
    },
    "someordinarygamers": {
        "reputation_score": 0.70,
        "category": ChannelCategory.SCAM_INVESTIGATION,
        "description": "Tech scam exposure, deep web investigation",
        "verification_notes": "Technical expertise",
    },
    "mutahar": {
        "reputation_score": 0.70,
        "category": ChannelCategory.SCAM_INVESTIGATION,
        "description": "Creator of SomeOrdinaryGamers",
        "verification_notes": "Same as SomeOrdinaryGamers",
    },
    
    # Health and science debunking
    "medlife crisis": {
        "reputation_score": 0.85,
        "category": ChannelCategory.FACT_CHECKING,
        "description": "Medical misinformation debunking",
        "verification_notes": "Medical doctor, peer-reviewed sources",
    },
    "dr. mike": {
        "reputation_score": 0.75,
        "category": ChannelCategory.EDUCATIONAL,
        "description": "Medical education and fact-checking",
        "verification_notes": "Licensed physician",
    },
}

# Known low-credibility or promotional channels
# These are penalized in verification
LOW_CREDIBILITY_PATTERNS: Dict[str, float] = {
    "official": 0.3,  # Often promotional
    "sales": 0.2,
    "marketing": 0.2,
    "crypto": 0.4,  # Often promotional (unless in trusted list)
    "nft": 0.3,
    "forex": 0.2,
    "trading signals": 0.1,
    "get rich": 0.1,
    "passive income": 0.2,
    "dropshipping": 0.2,
}


def normalize_channel_name(name: str) -> str:
    """Normalize channel name for matching."""
    if not name:
        return ""
    return name.lower().strip().replace("@", "").replace("_", " ")


def get_channel_reputation(channel_name: str) -> float:
    """
    Get reputation score for a YouTube channel.
    
    Args:
        channel_name: The channel name or handle
        
    Returns:
        Reputation score from 0.0 to 1.0:
        - 0.7-1.0: Trusted investigator/journalist
        - 0.5: Unknown/neutral channel
        - 0.0-0.4: Known promotional or low-credibility
    """
    if not channel_name:
        return 0.5
    
    normalized = normalize_channel_name(channel_name)
    
    # Check trusted investigators first
    for key, data in TRUSTED_INVESTIGATORS.items():
        if key in normalized or normalized in key:
            score = data["reputation_score"]
            logger.info(
                f"🏆 Channel '{channel_name}' matched trusted investigator '{key}' "
                f"with reputation score {score}"
            )
            return score
    
    # Check for low-credibility patterns
    for pattern, penalty_score in LOW_CREDIBILITY_PATTERNS.items():
        if pattern in normalized:
            logger.info(
                f"⚠️ Channel '{channel_name}' matched low-credibility pattern "
                f"'{pattern}' with score {penalty_score}"
            )
            return penalty_score
    
    # Unknown channel - neutral score
    return 0.5


def get_channel_category(channel_name: str) -> ChannelCategory:
    """
    Get the category of a YouTube channel.
    
    Args:
        channel_name: The channel name or handle
        
    Returns:
        ChannelCategory enum value
    """
    if not channel_name:
        return ChannelCategory.UNKNOWN
    
    normalized = normalize_channel_name(channel_name)
    
    for key, data in TRUSTED_INVESTIGATORS.items():
        if key in normalized or normalized in key:
            return data["category"]
    
    return ChannelCategory.UNKNOWN


def is_trusted_investigator(channel_name: str) -> bool:
    """
    Check if a channel is a known trusted investigator.
    
    Args:
        channel_name: The channel name or handle
        
    Returns:
        True if the channel is in the trusted investigators list
    """
    if not channel_name:
        return False
    
    normalized = normalize_channel_name(channel_name)
    
    for key in TRUSTED_INVESTIGATORS:
        if key in normalized or normalized in key:
            return True
    
    return False


def get_channel_info(channel_name: str) -> Optional[Dict]:
    """
    Get full channel information if available.
    
    Args:
        channel_name: The channel name or handle
        
    Returns:
        Dict with reputation_score, category, description, verification_notes
        or None if channel not found
    """
    if not channel_name:
        return None
    
    normalized = normalize_channel_name(channel_name)
    
    for key, data in TRUSTED_INVESTIGATORS.items():
        if key in normalized or normalized in key:
            return {
                "matched_key": key,
                **data,
            }
    
    return None


def calculate_content_credibility_boost(
    channel_name: str,
    video_title: str = "",
    video_description: str = ""
) -> Tuple[float, str]:
    """
    Calculate credibility boost for content based on channel reputation.
    
    This is used to adjust verification weights:
    - Investigative content from trusted sources gets positive boost
    - Promotional content from unknown sources gets no boost
    - Content matching investigation patterns gets additional boost
    
    Args:
        channel_name: The channel name
        video_title: The video title (optional)
        video_description: Video description (optional)
        
    Returns:
        Tuple of (boost_multiplier, reason_string)
        - boost_multiplier: 0.8 to 1.5 (1.0 = no change)
        - reason_string: Explanation of the boost
    """
    reputation = get_channel_reputation(channel_name)
    category = get_channel_category(channel_name)
    
    # Start with reputation-based boost
    if reputation >= 0.8:
        boost = 1.3  # 30% credibility boost
        reason = f"Trusted investigator ({channel_name})"
    elif reputation >= 0.7:
        boost = 1.2  # 20% boost
        reason = f"Known credible source ({channel_name})"
    elif reputation >= 0.5:
        boost = 1.0  # No boost
        reason = "Unknown channel - neutral treatment"
    else:
        boost = 0.8  # 20% reduction
        reason = f"Low-credibility pattern detected in {channel_name}"
    
    # Additional boost for scam investigation content
    if category == ChannelCategory.SCAM_INVESTIGATION:
        # Check if video appears to be an investigation
        investigation_keywords = [
            "exposed", "scam", "fraud", "investigation", "debunk",
            "truth about", "real story", "evidence", "proof"
        ]
        content = f"{video_title} {video_description}".lower()
        if any(kw in content for kw in investigation_keywords):
            boost *= 1.1  # Additional 10% for investigative content
            reason += " + investigative content bonus"
    
    return boost, reason

