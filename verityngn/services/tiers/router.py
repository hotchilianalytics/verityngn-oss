"""Dispatch analysis by tier: light | full | auto | local-light | local-full."""
from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Literal, Optional

from verityngn.services.video.caption_fetch import (
    extract_video_id,
    fetch_and_cache_vtt,
)

logger = logging.getLogger(__name__)

AnalysisTier = Literal["light", "full", "auto", "local-light", "local-full"]


def _resolve_video_id(url: str = "", video_path: str = "", video_id: str = "") -> str:
    if video_id:
        return video_id
    vid = extract_video_id(url)
    if vid:
        return vid
    if video_path:
        from verityngn.utils.upload_id import video_id_from_file_path

        return video_id_from_file_path(video_path)
    return ""


def _probe_duration(youtube_url: str) -> float:
    if not youtube_url:
        return 0.0
    try:
        import yt_dlp

        with yt_dlp.YoutubeDL(
            {"quiet": True, "no_warnings": True, "skip_download": True, "ignoreerrors": True}
        ) as ydl:
            info = ydl.extract_info(youtube_url, download=False) or {}
        return float(info.get("duration") or 0)
    except Exception as exc:  # noqa: BLE001
        logger.debug("duration probe failed: %s", exc)
        return 0.0


def run_tier(
    tier: AnalysisTier,
    *,
    youtube_url: str = "",
    video_file: str = "",
    out_dir: str = "outputs",
    title: str = "",
    deep: bool = False,
    video_id: str = "",
    use_live_llm: bool = True,
    download_youtube: bool = True,
) -> Dict[str, Any]:
    """
    Route to the appropriate analysis pipeline.

    - **light**: YouTube VTT → DR-direct (no full CI/verify)
    - **full**: YouTube VTT cache + full VerityNgn pipeline (+ optional DR)
    - **auto**: preflight sufficiency → light or full (+ quality-floor escalation)
    - **local-light**: local file transcript → DR-direct
    - **local-full**: local file full pipeline (+ optional DR)
    """
    os.makedirs(out_dir, exist_ok=True)
    meta: Dict[str, Any] = {"tier": tier, "status": "completed"}

    if tier == "auto":
        return _run_auto(
            youtube_url=youtube_url,
            out_dir=out_dir,
            title=title,
            video_id=video_id,
            use_live_llm=use_live_llm,
            deep=deep,
            meta=meta,
        )

    if tier == "light":
        return _run_light(
            youtube_url=youtube_url,
            out_dir=out_dir,
            title=title,
            video_id=video_id,
            use_live_llm=use_live_llm,
            meta=meta,
        )

    if tier == "full":
        return _run_full(
            youtube_url=youtube_url,
            out_dir=out_dir,
            title=title,
            deep=deep,
            video_id=video_id,
            meta=meta,
        )

    if tier == "local-light":
        from verityngn.local_app import analyze_local

        result = analyze_local(
            youtube_url=youtube_url,
            video_file=video_file,
            out_dir=out_dir,
            title=title,
            deep=False,
            arm="direct",
            tier="local-light",
            download_youtube=download_youtube,
            use_live_llm=use_live_llm,
        )
        result["tier"] = tier
        return result

    if tier == "local-full":
        from verityngn.local_app import analyze_local

        result = analyze_local(
            youtube_url=youtube_url,
            video_file=video_file,
            out_dir=out_dir,
            title=title,
            deep=deep,
            arm="full",
            tier="local-full",
            download_youtube=download_youtube,
            use_live_llm=use_live_llm,
        )
        result["tier"] = tier
        return result

    raise ValueError(f"Unknown tier: {tier}")


def _run_auto(
    *,
    youtube_url: str,
    out_dir: str,
    title: str,
    video_id: str,
    use_live_llm: bool,
    deep: bool,
    meta: Dict[str, Any],
) -> Dict[str, Any]:
    """Preflight → light or full; escalate light → full if quality floor fails."""
    from verityngn.services.ablation.sufficiency import (
        preflight_features,
        quality_floor_escalation,
        route_decision,
    )

    if not youtube_url:
        raise ValueError("tier=auto requires a YouTube URL")

    vid = _resolve_video_id(youtube_url, video_id=video_id)
    if not vid:
        raise ValueError("Could not resolve video_id from URL")

    run_root = out_dir
    if Path(out_dir).name != vid:
        run_root = str(Path(out_dir) / vid)
    os.makedirs(run_root, exist_ok=True)

    duration = _probe_duration(youtube_url)
    caption = fetch_and_cache_vtt(vid, youtube_url, run_root)
    vtt_raw = ""
    vtt_path = caption.get("vtt_path")
    if vtt_path and Path(str(vtt_path)).is_file():
        vtt_raw = Path(str(vtt_path)).read_text(encoding="utf-8", errors="ignore")

    feats = preflight_features(
        duration_sec=duration,
        transcript_chars=len(caption.get("text") or ""),
        caption_source=str(caption.get("source") or ""),
        vtt_text=vtt_raw,
        title=title,
        youtube_url=youtube_url,
        synthetic=bool(caption.get("synthetic")),
        visual_probe=False,
    )
    decision = route_decision(feats)
    meta["auto"] = {
        "preflight": feats,
        "decision": decision,
        "caption": {
            "success": caption.get("success"),
            "source": caption.get("source"),
            "vtt_path": caption.get("vtt_path"),
        },
    }
    route_path = Path(run_root) / "auto_route.json"
    route_path.write_text(json.dumps(meta["auto"], indent=2, default=str), encoding="utf-8")
    meta["auto_route_path"] = str(route_path)

    chosen = decision.get("route") or "full"
    logger.info("[tier=auto] route=%s reasons=%s", chosen, decision.get("reasons"))

    if chosen == "light":
        light_meta = _run_light(
            youtube_url=youtube_url,
            out_dir=out_dir,
            title=title,
            video_id=vid,
            use_live_llm=use_live_llm,
            meta={"tier": "light", "status": "completed"},
            duration_sec=duration,
        )
        md_path = light_meta.get("markdown_path")
        brief = ""
        if md_path and Path(str(md_path)).is_file():
            brief = Path(str(md_path)).read_text(encoding="utf-8", errors="ignore")
        floor = quality_floor_escalation(brief)
        meta["auto"]["quality_floor"] = floor
        route_path.write_text(json.dumps(meta["auto"], indent=2, default=str), encoding="utf-8")
        if floor.get("escalated"):
            logger.warning("[tier=auto] escalating light→full: %s", floor.get("reason"))
            meta["auto"]["escalated"] = True
            full_meta = _run_full(
                youtube_url=youtube_url,
                out_dir=out_dir,
                title=title,
                deep=deep,
                video_id=vid,
                meta={"tier": "full", "status": "completed"},
            )
            full_meta["tier"] = "auto"
            full_meta["auto"] = meta["auto"]
            full_meta["chosen_route"] = "full"
            full_meta["requested_route"] = "light"
            return full_meta
        light_meta["tier"] = "auto"
        light_meta["auto"] = meta["auto"]
        light_meta["chosen_route"] = "light"
        return light_meta

    full_meta = _run_full(
        youtube_url=youtube_url,
        out_dir=out_dir,
        title=title,
        deep=deep,
        video_id=vid,
        meta={"tier": "full", "status": "completed"},
    )
    full_meta["tier"] = "auto"
    full_meta["auto"] = meta["auto"]
    full_meta["chosen_route"] = "full"
    return full_meta


def _run_light(
    *,
    youtube_url: str,
    out_dir: str,
    title: str,
    video_id: str,
    use_live_llm: bool,
    meta: Dict[str, Any],
    duration_sec: float = 0.0,
) -> Dict[str, Any]:
    if not youtube_url:
        raise ValueError("tier=light requires a YouTube URL")

    vid = _resolve_video_id(youtube_url, video_id=video_id)
    if not vid:
        raise ValueError("Could not resolve video_id from URL")

    run_root = out_dir
    if Path(out_dir).name != vid:
        run_root = str(Path(out_dir) / vid)
    os.makedirs(run_root, exist_ok=True)

    caption = fetch_and_cache_vtt(vid, youtube_url, run_root)
    meta["caption"] = {
        "success": caption.get("success"),
        "source": caption.get("source"),
        "vtt_path": caption.get("vtt_path"),
        "errors": caption.get("errors"),
        "usd_estimate": caption.get("usd_estimate"),
    }

    from verityngn.services.ablation.direct import run_dr_direct

    if duration_sec <= 0:
        duration_sec = _probe_duration(youtube_url)

    dr = run_dr_direct(
        out_dir=run_root,
        video_id=vid,
        youtube_url=youtube_url,
        title=title,
        description="",
        use_live_llm=use_live_llm,
        duration_sec=duration_sec,
    )
    meta.update(dr)
    meta["tier"] = "light"
    meta["out_dir"] = run_root
    return meta


def _run_full(
    *,
    youtube_url: str,
    out_dir: str,
    title: str,
    deep: bool,
    video_id: str,
    meta: Dict[str, Any],
) -> Dict[str, Any]:
    if not youtube_url:
        raise ValueError("tier=full requires a YouTube URL")

    vid = _resolve_video_id(youtube_url, video_id=video_id)
    run_root = out_dir
    if vid and Path(out_dir).name != vid:
        run_root = str(Path(out_dir) / vid)
    os.makedirs(run_root, exist_ok=True)

    if vid:
        caption = fetch_and_cache_vtt(vid, youtube_url, run_root)
        meta["caption"] = {
            "success": caption.get("success"),
            "source": caption.get("source"),
            "vtt_path": caption.get("vtt_path"),
        }

    from verityngn.workflows.pipeline import run_verification

    result = run_verification(video_url=youtube_url, out_dir_path=run_root)
    if isinstance(result, dict):
        meta.update(result)
        out = result.get("output_dir") or result.get("out_dir_path") or run_root
        vid = result.get("video_id") or vid
    else:
        final_state, out_path = result
        out = out_path or run_root
        if isinstance(final_state, dict):
            vid = final_state.get("video_id") or vid

    meta["out_dir"] = out
    meta["video_id"] = vid
    meta["tier"] = "full"

    if deep and vid:
        from verityngn.services.deepresearch.pipeline import generate_deep_research_report

        report_json = Path(out) / f"{vid}_report.json"
        if report_json.is_file():
            meta["deep"] = asyncio.run(
                generate_deep_research_report(str(report_json), out, video_id=vid, title=title or None)
            )
        else:
            meta["deep"] = {"status": "skipped", "reason": "no_report_json"}
    return meta


def run_deep_research_on_report(out_dir: str, video_id: str) -> Dict[str, Any]:
    """Helper for CLI --deep-only."""
    from verityngn.services.deepresearch.pipeline import generate_deep_research_report

    report_json = Path(out_dir) / f"{video_id}_report.json"
    if not report_json.is_file():
        candidates = list(Path(out_dir).glob("*_report.json"))
        if not candidates:
            raise FileNotFoundError(f"no report JSON in {out_dir}")
        report_json = candidates[0]
        video_id = report_json.name.split("_report.json")[0]
    return asyncio.run(
        generate_deep_research_report(str(report_json), out_dir, video_id=video_id)
    )
