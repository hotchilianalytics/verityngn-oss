"""
Env-gated multi-sense sleeve — mirrors deepresearch post-report pattern.

Writes `{video_id}_multisense.json` (+ optional fused index) beside the report.
Set MULTISENSE_ENABLED=1 to opt in. MULTISENSE_OFFLINE=1 forces deterministic proxy.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional
import json
import logging
import os

from verityngn.services.affect.extract import extract_affect_for_report
from verityngn.services.fusion.gemini_multisense import run_gemini_multisense
from verityngn.services.fusion.schema import build_fused_index, write_fused_index

logger = logging.getLogger(__name__)


def multisense_enabled() -> bool:
    return os.environ.get("MULTISENSE_ENABLED", "0") in {"1", "true", "True", "yes"}


def attach_delivery_signals_to_report(
    report: dict[str, Any],
    multisense: dict[str, Any],
) -> dict[str, Any]:
    """Stamp Claim.delivery_signals from multisense claim_delivery rows (in-place)."""
    by_id = {
        row.get("claim_id"): row
        for row in (multisense.get("claim_delivery") or [])
        if isinstance(row, dict)
    }
    claims = report.get("claims_breakdown") or []
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        row = by_id.get(claim.get("claim_id"))
        if row:
            claim["delivery_signals"] = row
    meta = report.setdefault("metadata", {})
    if isinstance(meta, dict):
        meta["multisense"] = {
            "schema_version": multisense.get("schema_version"),
            "signal_tier": multisense.get("signal_tier"),
            "summary": multisense.get("summary"),
            "disclaimer": multisense.get("disclaimer"),
        }
    return report


def run_multisense(
    video_id: str,
    report_path: Path | str,
    *,
    video_source: Optional[str] = None,
    youtube_url: Optional[str] = None,
    audio_path: Optional[Path | str] = None,
    video_path: Optional[Path | str] = None,
    out_dir: Optional[Path | str] = None,
    force: bool = False,
    offline: Optional[bool] = None,
) -> dict[str, Any]:
    """
    Run Gemini multi-sense + measured affect fusion for a finished report.

    Returns a manifest with output paths. No-op (returns skipped) unless
    MULTISENSE_ENABLED=1 or force=True.
    """
    if not force and not multisense_enabled():
        return {"skipped": True, "reason": "MULTISENSE_ENABLED not set"}

    report_path = Path(report_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if not report.get("video_id"):
        report["video_id"] = video_id

    out_dir = Path(out_dir) if out_dir else report_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    # Resolve video URI / YouTube
    gcs_uri = video_source if video_source and str(video_source).startswith("gs://") else None
    yt = youtube_url
    if not yt:
        embed = report.get("media_embed") or {}
        if isinstance(embed, dict):
            yt = embed.get("youtube_url") or embed.get("url")
        if not yt and len(str(video_id)) >= 6:
            # Conventional YouTube id
            yt = f"https://www.youtube.com/watch?v={video_id}"

    ms = run_gemini_multisense(
        report,
        video_uri=gcs_uri,
        youtube_url=yt if not gcs_uri else None,
        offline=offline,
    )
    ms_path = out_dir / f"{video_id}_multisense.json"
    ms.write_json(ms_path)

    # Measured affect (optional audio)
    affect = extract_affect_for_report(
        report,
        audio_path=Path(audio_path) if audio_path else None,
    )
    affect_path = out_dir / f"{video_id}_affect.json"
    affect.write_json(affect_path)

    vision_dict = {}
    if video_path and Path(video_path).exists():
        from verityngn.services.vision.extract import extract_vision_for_video

        vis = extract_vision_for_video(video_id, video_path=video_path)
        vis.write_json(out_dir / f"{video_id}_vision.json")
        backend = ((vis.summary or {}).get("backend") or {})
        # Refuse hash-seeded / synthetic vision — that reintroduces the S01 n_claims leak.
        real = bool(backend.get("mediapipe") or backend.get("pyfeat"))
        if real or os.environ.get("MULTISENSE_ALLOW_SYNTHETIC_VISION") in {"1", "true", "True"}:
            vision_dict = vis.to_dict()
        else:
            logger.info(
                "[multisense] skipping vision fusion for %s (no real extractor; omit rather than fill 0.5)",
                video_id,
            )

    fused = build_fused_index(
        video_id=video_id,
        affect=affect.to_dict(),
        vision=vision_dict,
        gemini=ms.to_dict(),
    )
    fused_path = out_dir / f"{video_id}_fused_index.json"
    write_fused_index(fused, fused_path)

    # Attach delivery_signals onto a sidecar report copy (do not mutate production report
    # unless MULTISENSE_MUTATE_REPORT=1).
    mutate = os.environ.get("MULTISENSE_MUTATE_REPORT", "0") in {"1", "true", "True"}
    stamped = attach_delivery_signals_to_report(dict(report), ms.to_dict())
    stamped_path = out_dir / f"{video_id}_report_with_delivery.json"
    stamped_path.write_text(json.dumps(stamped, indent=2), encoding="utf-8")
    if mutate:
        report_path.write_text(json.dumps(stamped, indent=2), encoding="utf-8")

    manifest = {
        "video_id": video_id,
        "multisense": str(ms_path),
        "affect": str(affect_path),
        "fused_index": str(fused_path),
        "report_with_delivery": str(stamped_path),
        "summary": ms.summary,
        "crossmodal_overall_congruence": (fused.get("crossmodal") or {}).get("overall_congruence"),
        "modality_divergence_rate": (fused.get("crossmodal") or {}).get("modality_divergence_rate"),
        "disclaimer": ms.disclaimer,
    }
    (out_dir / f"{video_id}_multisense_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    logger.info("[multisense] wrote %s", ms_path)
    return manifest
