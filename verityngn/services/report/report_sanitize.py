"""Sanitize VerityReport for persistence (no YouTube API statistics at rest)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from verityngn.models.report import VerityReport
from verityngn.services.storage.yt_artefact_cleanup import strip_yt_fields_from_report_dict


def apply_audit_and_sanitize(
    report: VerityReport,
    *,
    source_info_hash: Optional[str] = None,
    info_ingested_at: Optional[str] = None,
) -> VerityReport:
    report.source_info_hash = source_info_hash
    report.info_ingested_at = info_ingested_at
    report.report_generated_at = datetime.now(timezone.utc).isoformat()

    if report.media_embed:
        report.media_embed.title = ""
        report.media_embed.thumbnail_url = None
        report.media_embed.video_url = None
        report.media_embed.description = ""
        report.media_embed.view_count = None
        report.media_embed.upload_date = None
        report.media_embed.uploader = None
        report.media_embed.uploader_id = None
        report.media_embed.channel = None
        report.media_embed.channel_follower_count = None
        report.media_embed.comment_count = None

    report.description = ""
    report.title = ""

    for item in report.youtube_counter_intelligence or []:
        if isinstance(item, dict):
            item.pop("view_count", None)
            item.pop("channel_title", None)
            item.pop("like_count", None)

    return report


def report_to_persisted_dict(report: VerityReport) -> Dict[str, Any]:
    return strip_yt_fields_from_report_dict(report.model_dump())
