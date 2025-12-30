"""Source reputation scoring module for channel and content credibility."""

from .source_reputation import (
    get_channel_reputation,
    get_channel_category,
    is_trusted_investigator,
    TRUSTED_INVESTIGATORS,
    ChannelCategory,
)

__all__ = [
    "get_channel_reputation",
    "get_channel_category",
    "is_trusted_investigator",
    "TRUSTED_INVESTIGATORS",
    "ChannelCategory",
]

