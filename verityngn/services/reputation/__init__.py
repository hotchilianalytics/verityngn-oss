"""Source reputation scoring module for channel and content credibility."""

from .source_reputation import (
    get_channel_reputation,
    get_channel_category,
    is_trusted_investigator,
    TRUSTED_INVESTIGATORS,
    ChannelCategory,
)
from .domain_reputation import (
    EvidenceTier,
    TIER_WEIGHTS,
    get_domain_tier,
    get_domain_weight,
    get_tier_breakdown,
)
from .url_safety import (
    filter_safe_evidence,
    filter_safe_urls,
    is_safe_url,
    sanitize_report_dict_urls,
    sanitize_url_list_in_text,
)

__all__ = [
    "get_channel_reputation",
    "get_channel_category",
    "is_trusted_investigator",
    "TRUSTED_INVESTIGATORS",
    "ChannelCategory",
    "EvidenceTier",
    "TIER_WEIGHTS",
    "get_domain_tier",
    "get_domain_weight",
    "get_tier_breakdown",
    "is_safe_url",
    "filter_safe_urls",
    "filter_safe_evidence",
    "sanitize_url_list_in_text",
    "sanitize_report_dict_urls",
]
