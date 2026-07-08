"""
YouTube API artefact cleanup — compliance-by-architecture (ToS III.E.4).

Deletes ephemeral ``*.info.json`` after report generation; returns audit fingerprint.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_YT_PERSIST_BANNED = frozenset(
    {
        "view_count",
        "like_count",
        "description",
        "tags",
        "categories",
        "thumbnail",
        "thumbnail_url",
        "title",
        "upload_date",
        "duration",
        "uploader",
        "uploader_id",
        "channel",
        "channel_id",
        "channel_url",
        "channel_title",
        "extractor",
        "video_url",
        "webpage_url",
    }
)

_CI_LIST_KEYS = (
    "youtube_counter_intelligence",
    "press_release_counter_intelligence",
    "evidence_summary",
)


def compute_info_hash(info_path: Path) -> Optional[str]:
    if not info_path.is_file():
        return None
    h = hashlib.sha256()
    with open(info_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def _delete_if_exists(path: Path) -> bool:
    try:
        if path.is_file():
            path.unlink()
            return True
    except OSError as exc:
        logger.warning("Failed to delete %s: %s", path, exc)
    return False


def _collect_info_json_paths(out_dir: Path, video_id: str) -> List[Path]:
    paths: List[Path] = []
    analysis = out_dir / "analysis"
    primary = analysis / f"{video_id}.info.json"
    if primary.is_file():
        paths.append(primary)
    for pattern in ("*.info.json",):
        if analysis.is_dir():
            paths.extend(analysis.glob(pattern))
        for sub in ("counter_intelligence", "sherlock_analysis"):
            base = out_dir / sub
            if base.is_dir():
                paths.extend(base.rglob(pattern))
        for sherlock in out_dir.glob("sherlock_analysis_*"):
            ci = sherlock / "counter_intelligence"
            if ci.is_dir():
                paths.extend(ci.rglob(pattern))
    seen = set()
    unique: List[Path] = []
    for p in paths:
        key = str(p.resolve())
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


def capture_info_audit(out_dir: str | Path, video_id: str) -> Dict[str, Optional[str]]:
    out = Path(out_dir)
    primary = out / "analysis" / f"{video_id}.info.json"
    ingested_at: Optional[str] = None
    if primary.is_file():
        try:
            ingested_at = datetime.fromtimestamp(
                primary.stat().st_mtime, tz=timezone.utc
            ).isoformat()
        except OSError:
            ingested_at = datetime.now(timezone.utc).isoformat()
    return {
        "source_info_hash": compute_info_hash(primary),
        "info_ingested_at": ingested_at,
    }


def cleanup_yt_api_artefacts(out_dir: str | Path, video_id: str) -> Dict[str, Any]:
    out = Path(out_dir)
    deleted: List[str] = []
    audit = capture_info_audit(out, video_id)

    analysis = out / "analysis"
    for name in (
        f"{video_id}.info.json",
        f"{video_id}_partial_info.json",
        f"{video_id}.description",
    ):
        p = analysis / name
        if _delete_if_exists(p):
            deleted.append(str(p))

    for info_path in _collect_info_json_paths(out, video_id):
        if _delete_if_exists(info_path):
            deleted.append(str(info_path))

    logger.info(
        "YT artefact cleanup | video_id=%s deleted=%d hash=%s",
        video_id,
        len(deleted),
        audit.get("source_info_hash"),
    )
    return {**audit, "deleted_paths": deleted}


def strip_yt_fields_from_report_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    import copy

    out = copy.deepcopy(data)

    for key in list(out.keys()):
        if key in _YT_PERSIST_BANNED:
            out.pop(key, None)
    out["description"] = ""

    media = out.get("media_embed")
    if isinstance(media, dict):
        for k in _YT_PERSIST_BANNED:
            media.pop(k, None)
        media["description"] = ""
        for k in (
            "view_count",
            "upload_date",
            "uploader",
            "uploader_id",
            "channel",
            "thumbnail_url",
            "video_url",
            "webpage_url",
        ):
            media.pop(k, None)

    for list_key in _CI_LIST_KEYS:
        items = out.get(list_key)
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict):
                for k in _YT_PERSIST_BANNED:
                    item.pop(k, None)

    out.pop("last_yt_metadata_refresh", None)
    qs = out.get("quick_summary")
    if isinstance(qs, dict):
        qs.pop("last_yt_metadata_refresh", None)

    return out
