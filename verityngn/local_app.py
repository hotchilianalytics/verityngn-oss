"""Local analyze helpers — URL/mp4 → reports for OSS v3 testing."""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, Literal, Optional

logger = logging.getLogger(__name__)

Arm = Literal["full", "direct"]
Tier = Literal["local-light", "local-full", "light", "full", ""]


def analyze_local(
    *,
    youtube_url: str = "",
    video_file: str = "",
    out_dir: str = "outputs/local",
    title: str = "",
    deep: bool = False,
    arm: Arm = "full",
    tier: Tier = "",
    download_youtube: bool = True,
    use_live_llm: bool = True,
) -> Dict[str, Any]:
    """
    Run a local analysis for testing the OSS release.

    - arm=full: standard pipeline (+ optional --deep via Deep Research on report.json)
    - arm=direct: DR-direct risk brief without claims inventory
    - tier=local-light|local-full: same as arm=direct|full (tier alias)
    """
    os.makedirs(out_dir, exist_ok=True)
    if tier == "local-light":
        arm = "direct"
    elif tier == "local-full":
        arm = "full"
    video_path = video_file
    url = youtube_url

    if url and download_youtube and not video_path:
        video_path = _maybe_download(url, out_dir) or ""

    if arm == "direct":
        from verityngn.services.ablation.direct import run_dr_direct

        return run_dr_direct(
            out_dir=out_dir,
            youtube_url=url,
            video_path=video_path,
            title=title,
            use_live_llm=use_live_llm,
        )

    # full arm
    from verityngn.workflows.pipeline import run_verification

    config: Dict[str, Any] = {}
    if video_path:
        from verityngn.utils.upload_id import video_id_from_file_path

        vp = str(Path(video_path).expanduser().resolve())
        if not os.path.isfile(vp):
            raise FileNotFoundError(vp)
        vid = video_id_from_file_path(vp)
        config = {
            "ingest_source": "file_upload",
            "video_path": vp,
            "upload_title": title or Path(vp).stem,
            "video_id": vid,
        }
        run_url = url or f"upload://{vid}"
    else:
        if not url:
            raise ValueError("analyze_local requires youtube_url or video_file")
        run_url = url
        vid = ""

    result = run_verification(video_url=run_url, out_dir_path=out_dir, config=config)
    meta: Dict[str, Any] = {"arm": "full", "status": "completed"}
    if isinstance(result, dict):
        meta.update(result)
        out = result.get("output_dir") or result.get("out_dir_path") or out_dir
        vid = result.get("video_id") or vid
    else:
        final_state, out_path = result
        out = out_path or out_dir
        if isinstance(final_state, dict):
            vid = final_state.get("video_id") or vid
            meta["final_state_keys"] = list(final_state.keys())[:20]
    meta["out_dir"] = out
    meta["video_id"] = vid
    meta["video_path"] = video_path or None

    # Sync standard report HTML/JSON from outputs_debug into -o (dual-output contract).
    if vid:
        from verityngn.services.report.artifact_sync import (
            checklist_artifacts,
            sync_standard_report_artifacts,
        )

        meta["artifacts"] = sync_standard_report_artifacts(out, vid)

    if deep and vid:
        import asyncio

        from verityngn.services.deepresearch.pipeline import generate_deep_research_report
        from verityngn.services.report.artifact_sync import checklist_artifacts

        report_json = Path(out) / f"{vid}_report.json"
        if report_json.is_file():
            meta["deep"] = asyncio.run(
                generate_deep_research_report(str(report_json), out, video_id=vid, title=title or None)
            )
            meta["artifacts"] = {
                **(meta.get("artifacts") or {}),
                **checklist_artifacts(out, vid),
            }
        else:
            meta["deep"] = {"status": "skipped", "reason": "no_report_json"}
    return meta


def _maybe_download(youtube_url: str, out_dir: str) -> Optional[str]:
    """Best-effort yt-dlp download into out_dir/downloads; returns path or None."""
    try:
        from verityngn.services.video.downloader import VideoDownloader
        from verityngn.utils.file_utils import extract_video_id
    except Exception as exc:  # noqa: BLE001
        logger.warning("VideoDownloader unavailable: %s", exc)
        return None
    try:
        dl_dir = str(Path(out_dir) / "downloads")
        os.makedirs(dl_dir, exist_ok=True)
        downloader = VideoDownloader()
        # download_video returns (video_path, audio_path, info_path) or similar tuple
        result = downloader.download_video(youtube_url, dl_dir)
        if isinstance(result, tuple) and result:
            path = result[0]
            return path if path and os.path.isfile(path) else None
        if isinstance(result, str) and os.path.isfile(result):
            return result
        # Fallback: look for extracted id file
        vid = extract_video_id(youtube_url) if callable(extract_video_id) else None
        if vid:
            for ext in (".mp4", ".webm", ".mkv"):
                cand = Path(dl_dir) / f"{vid}{ext}"
                if cand.is_file():
                    return str(cand)
        return None
    except Exception as exc:  # noqa: BLE001
        logger.warning("YouTube download skipped: %s", exc)
        return None
