"""Orchestrate full vs DR-direct and transcript vs multimodal claim ablations."""
from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Literal, Optional

from verityngn.services.ablation.claim_compare import compare_claim_inventories, evaluate_genre_sleeve_gate
from verityngn.services.ablation.compare import compare_arms
from verityngn.services.ablation.direct import run_dr_direct
from verityngn.services.ablation.multimodal_arm import run_multimodal_claims_arm
from verityngn.services.ablation.transcript_arm import run_transcript_claims_arm

logger = logging.getLogger(__name__)

Arm = Literal["full", "direct", "both"]
ClaimsArm = Literal["transcript", "multimodal", "both"]
AblationMode = Literal["dr", "claims"]


def _latest_timestamped_report(video_id: str) -> Optional[Path]:
    """Find newest {video_id}_report.md under OUTPUTS_DIR timestamped completes."""
    if not video_id:
        return None
    try:
        from verityngn.config.settings import OUTPUTS_DIR
    except Exception:
        return None
    base = Path(OUTPUTS_DIR) / video_id
    if not base.is_dir():
        # Also check repo-relative outputs_debug (common local DEBUG_OUTPUTS layout)
        alt = Path("outputs_debug") / video_id
        base = alt if alt.is_dir() else base
    if not base.is_dir():
        return None
    mds = sorted(
        [p for p in base.rglob(f"{video_id}_report.md") if "_complete" in p.parts or "complete" in p.name],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not mds:
        mds = sorted(base.rglob(f"{video_id}_report.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    return mds[0] if mds else None


def _resolve_report_paths(out: str, video_id: str) -> tuple[Optional[Path], Optional[Path]]:
    """Return (report_json, report_md) from arm dir or timestamped storage."""
    out_p = Path(out)
    report_json = out_p / f"{video_id}_report.json"
    report_md = out_p / f"{video_id}_report.md"
    if not report_json.is_file():
        cands = list(out_p.glob("*_report.json"))
        if cands:
            report_json = cands[0]
            video_id = report_json.name.split("_report.json")[0]
            report_md = out_p / f"{video_id}_report.md"
    if report_json.is_file() and report_md.is_file():
        return report_json, report_md

    ts_md = _latest_timestamped_report(video_id)
    if ts_md and ts_md.is_file():
        ts_json = ts_md.with_suffix(".json")
        if not ts_json.is_file():
            # sibling may be named *_report.json already
            ts_json = ts_md.parent / f"{video_id}_report.json"
        return (ts_json if ts_json.is_file() else None), ts_md
    return (
        report_json if report_json.is_file() else None,
        report_md if report_md.is_file() else None,
    )


def _run_full(
    *,
    out_dir: str,
    youtube_url: str = "",
    video_path: str = "",
    title: str = "",
    video_id: str = "",
    run_deep: bool = True,
) -> Dict[str, Any]:
    from verityngn.workflows.pipeline import run_verification

    t0 = time.perf_counter()
    config: Dict[str, Any] = {}
    if video_path:
        from verityngn.utils.upload_id import video_id_from_file_path

        vp = str(Path(video_path).expanduser().resolve())
        vid = video_id or video_id_from_file_path(vp)
        config = {
            "ingest_source": "file_upload",
            "video_path": vp,
            "upload_title": title or Path(vp).stem,
            "video_id": vid,
        }
        url = youtube_url or f"upload://{vid}"
    else:
        url = youtube_url
        if not url:
            raise ValueError("full arm requires youtube_url or video_path")
        vid = video_id

    arm_dir = os.path.join(out_dir, "full")
    os.makedirs(arm_dir, exist_ok=True)
    result = run_verification(video_url=url, out_dir_path=arm_dir, config=config)

    out = arm_dir
    resolved_id = vid or ""
    if isinstance(result, dict):
        out = result.get("output_dir") or result.get("out_dir_path") or arm_dir
        resolved_id = result.get("video_id") or resolved_id
    else:
        final_state, out_path = result
        out = out_path or arm_dir
        if isinstance(final_state, dict):
            resolved_id = final_state.get("video_id") or resolved_id

    meta: Dict[str, Any] = {
        "status": "completed",
        "arm": "full",
        "video_id": resolved_id,
        "out_dir": out,
        "elapsed_sec": time.perf_counter() - t0,
        "pipeline_elapsed_sec": time.perf_counter() - t0,
    }

    report_json, md = _resolve_report_paths(out, resolved_id)
    if report_json and report_json.is_file():
        resolved_id = report_json.name.split("_report.json")[0] or resolved_id
        meta["video_id"] = resolved_id

    meta["report_json"] = str(report_json) if report_json and report_json.is_file() else None
    meta["standard_markdown_path"] = str(md) if md and md.is_file() else None
    if md and md.is_file():
        meta["timestamped_markdown_path"] = str(md)

    if run_deep and report_json and report_json.is_file():
        import asyncio

        from verityngn.services.deepresearch.pipeline import generate_deep_research_report

        t1 = time.perf_counter()
        try:
            dr = asyncio.run(
                generate_deep_research_report(
                    str(report_json), out, video_id=resolved_id, title=title or None
                )
            )
            meta["deep"] = dr
            meta["markdown_path"] = dr.get("markdown_path")
            meta["deep_elapsed_sec"] = time.perf_counter() - t1
        except Exception as exc:  # noqa: BLE001
            logger.exception("full arm deep research failed")
            meta["deep"] = {"status": "failed", "reason": str(exc)}
            meta["markdown_path"] = meta.get("standard_markdown_path")
    else:
        meta["markdown_path"] = meta.get("standard_markdown_path")
        if run_deep and not (report_json and report_json.is_file()):
            meta["deep"] = {
                "status": "skipped",
                "reason": "no report JSON found in arm dir or timestamped storage",
            }

    meta["elapsed_sec"] = time.perf_counter() - t0
    return meta


def run_ablation(
    *,
    out_dir: str,
    arms: Arm = "both",
    youtube_url: str = "",
    video_path: str = "",
    video_id: str = "",
    title: str = "",
    use_live_llm: bool = True,
    run_full_deep: bool = True,
) -> Dict[str, Any]:
    """Run selected arms and write compare.json under out_dir."""
    os.makedirs(out_dir, exist_ok=True)
    full_meta: Optional[Dict[str, Any]] = None
    direct_meta: Optional[Dict[str, Any]] = None

    if arms in ("full", "both"):
        logger.info("[ablation] running FULL arm → %s", out_dir)
        full_meta = _run_full(
            out_dir=out_dir,
            youtube_url=youtube_url,
            video_path=video_path,
            title=title,
            video_id=video_id,
            run_deep=run_full_deep,
        )

    if arms in ("direct", "both"):
        logger.info("[ablation] running DIRECT arm → %s", out_dir)
        d_dir = os.path.join(out_dir, "direct")
        direct_meta = run_dr_direct(
            out_dir=d_dir,
            video_id=video_id
            or (full_meta or {}).get("video_id")
            or "",
            youtube_url=youtube_url,
            video_path=video_path,
            title=title,
            use_live_llm=use_live_llm,
        )

    comparison = compare_arms(full_meta, direct_meta)
    payload = {
        "out_dir": out_dir,
        "arms": arms,
        "youtube_url": youtube_url,
        "video_path": video_path,
        "video_id": video_id or (full_meta or {}).get("video_id") or (direct_meta or {}).get("video_id"),
        "full": full_meta,
        "direct": direct_meta,
        "compare": comparison,
    }
    compare_path = Path(out_dir) / "compare.json"
    compare_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    payload["compare_path"] = str(compare_path)
    return payload


def run_claims_ablation(
    *,
    out_dir: str,
    arms: ClaimsArm = "both",
    youtube_url: str = "",
    video_id: str = "",
    title: str = "",
    use_live_llm: bool = True,
) -> Dict[str, Any]:
    """Compare YouTube transcript-only claims vs multimodal pipeline claims."""
    os.makedirs(out_dir, exist_ok=True)
    tx_meta: Optional[Dict[str, Any]] = None
    mm_meta: Optional[Dict[str, Any]] = None

    if arms in ("transcript", "both"):
        logger.info("[ablation:claims] running TRANSCRIPT arm → %s", out_dir)
        tx_meta = run_transcript_claims_arm(
            out_dir=os.path.join(out_dir, "transcript"),
            video_id=video_id,
            youtube_url=youtube_url,
            title=title,
            use_live_llm=use_live_llm,
        )

    if arms in ("multimodal", "both"):
        logger.info("[ablation:claims] running MULTIMODAL arm → %s", out_dir)
        mm_meta = run_multimodal_claims_arm(
            out_dir=os.path.join(out_dir, "multimodal"),
            video_id=video_id or (tx_meta or {}).get("video_id") or "",
            youtube_url=youtube_url,
            title=title,
            use_live_llm=use_live_llm,
        )

    comparison = compare_claim_inventories(
        (tx_meta or {}).get("claims"),
        (mm_meta or {}).get("claims"),
    )
    genre_gate = evaluate_genre_sleeve_gate(comparison)
    # Slim arm metas for compare file (drop full claim lists duplicated under compare)
    def _slim(meta: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not meta:
            return None
        return {k: v for k, v in meta.items() if k != "claims"}

    payload = {
        "mode": "claims",
        "out_dir": out_dir,
        "arms": arms,
        "youtube_url": youtube_url,
        "video_id": video_id
        or (tx_meta or {}).get("video_id")
        or (mm_meta or {}).get("video_id"),
        "transcript": _slim(tx_meta),
        "multimodal": _slim(mm_meta),
        "compare": comparison,
        "genre_sleeve_gate": genre_gate,
    }
    compare_path = Path(out_dir) / "compare_claims.json"
    compare_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    payload["compare_path"] = str(compare_path)
    return payload
