"""
Canonical notice strings for reports (OSS).
"""
from __future__ import annotations

from verityngn.services.report.category_mappings import (
    INDEPENDENT_RESEARCH_DISCLAIMER,
    LLM_PLATFORM_VISIBLE_NOTICE,
)

ARCHITECTURE_NOTICE = (
    "Only the 11-character YouTube video ID is stored in persisted reports. "
    "Title and thumbnail for display are loaded via oEmbed at view time and are not "
    "written into report artefacts. Raw API artefacts (*.info.json) are removed when "
    "the editorial report is written. All verdicts, claims, and analysis are independent "
    "editorial research by HotChili Analytics, LLC and are not official YouTube data."
)

PRIVATE_IN_REPORT_NOTICE = (
    f"{INDEPENDENT_RESEARCH_DISCLAIMER} "
    "This report may include probability distributions and full claim-level "
    "editorial detail. It is not official YouTube data."
)

__all__ = [
    "ARCHITECTURE_NOTICE",
    "INDEPENDENT_RESEARCH_DISCLAIMER",
    "LLM_PLATFORM_VISIBLE_NOTICE",
    "PRIVATE_IN_REPORT_NOTICE",
]
