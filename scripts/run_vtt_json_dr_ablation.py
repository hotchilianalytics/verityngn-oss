#!/usr/bin/env python3
"""T-ABL-005: VTT→DR-direct vs report-JSON→Deep Research ablation."""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def _bootstrap() -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


def _find_report_json(video_id: str, hint: str = "") -> Optional[Path]:
    if hint:
        p = Path(hint)
        if p.is_file():
            return p
    cands: list[Path] = []
    for base in (Path("outputs_debug") / video_id, Path("outputs") / video_id, Path("outputs")):
        if base.is_dir():
            cands.extend(base.rglob(f"{video_id}_report.json"))
    # Prefer timestamped *_complete dirs (full pipeline) over ablation/transcript artefacts
    def _rank(p: Path) -> tuple:
        parts = p.parts
        in_complete = any("complete" in part for part in parts)
        in_ablation = any("ablation" in part or "transcript" in part for part in parts)
        return (in_complete, not in_ablation, p.stat().st_mtime)

    cands = sorted({p for p in cands if p.is_file()}, key=_rank, reverse=True)
    return cands[0] if cands else None


def _count_claims(report_json: Path) -> int:
    try:
        data = json.loads(report_json.read_text(encoding="utf-8"))
        claims = data.get("claims_breakdown") or data.get("claims") or []
        return len(claims) if isinstance(claims, list) else 0
    except (OSError, json.JSONDecodeError):
        return 0


def run_vtt_dr_arm(
    *,
    video_id: str,
    youtube_url: str,
    out_dir: Path,
    use_live_llm: bool,
) -> Dict[str, Any]:
    from verityngn.services.video.caption_fetch import fetch_and_cache_vtt
    from verityngn.services.ablation.direct import run_dr_direct

    t0 = time.perf_counter()
    run_root = out_dir / "vtt_dr"
    run_root.mkdir(parents=True, exist_ok=True)
    per_vid = run_root / video_id
    per_vid.mkdir(parents=True, exist_ok=True)

    caption = fetch_and_cache_vtt(
        video_id,
        youtube_url,
        str(per_vid),
        cache_only=not use_live_llm and os.getenv("SKIP_LIVE_CAPTION_FETCH") == "1",
    )
    dr = run_dr_direct(
        out_dir=str(per_vid),
        video_id=video_id,
        youtube_url=youtube_url,
        use_live_llm=use_live_llm,
    )
    dr["caption_source"] = caption.get("source")
    dr["caption_synthetic"] = caption.get("synthetic", False)
    dr["caption_vtt_path"] = caption.get("vtt_path")
    dr["caption_chars"] = len(caption.get("text") or "")
    dr["arm"] = "vtt_dr"
    dr["elapsed_sec"] = time.perf_counter() - t0
    return dr


def run_json_dr_arm(
    *,
    video_id: str,
    report_json: Path,
    out_dir: Path,
    title: str = "",
) -> Dict[str, Any]:
    from verityngn.services.deepresearch.pipeline import generate_deep_research_report

    t0 = time.perf_counter()
    arm_dir = out_dir / "json_dr"
    arm_dir.mkdir(parents=True, exist_ok=True)
    n_claims = _count_claims(report_json)
    dr = asyncio.run(
        generate_deep_research_report(
            str(report_json),
            str(arm_dir),
            video_id=video_id,
            title=title or None,
        )
    )
    dr["arm"] = "json_dr"
    dr["n_claims"] = n_claims
    dr["report_json"] = str(report_json)
    dr["elapsed_sec"] = time.perf_counter() - t0
    return dr


def main(argv: list[str] | None = None) -> int:
    _bootstrap()
    parser = argparse.ArgumentParser(description="VTT→DR vs JSON→DR ablation (T-ABL-005)")
    parser.add_argument("--video-id", default="tLJC8hkK-ao")
    parser.add_argument("--url", default="")
    parser.add_argument("-o", "--output", default="outputs/ablation_vtt_json_dr")
    parser.add_argument("--report-json", default="", help="Existing full pipeline report JSON")
    parser.add_argument("--offline", action="store_true", help="Stub DR-direct; cache-only captions")
    parser.add_argument("--skip-vtt", action="store_true", help="Skip VTT arm")
    parser.add_argument("--skip-json", action="store_true", help="Skip JSON DR arm")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    vid = args.video_id
    url = args.url or f"https://www.youtube.com/watch?v={vid}"
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    vtt_meta: Optional[Dict[str, Any]] = None
    json_meta: Optional[Dict[str, Any]] = None

    if not args.skip_vtt:
        logger.info("Running VTT→DR arm …")
        vtt_meta = run_vtt_dr_arm(
            video_id=vid,
            youtube_url=url,
            out_dir=out,
            use_live_llm=not args.offline,
        )

    if not args.skip_json:
        report_json = _find_report_json(vid, args.report_json)
        if not report_json:
            logger.error("No report JSON found for %s — run full pipeline first or pass --report-json", vid)
            if not vtt_meta:
                return 1
        else:
            logger.info("Running JSON→DR arm from %s …", report_json)
            json_meta = run_json_dr_arm(
                video_id=vid,
                report_json=report_json,
                out_dir=out,
            )

    from verityngn.services.ablation.compare import compare_arms

    # compare_arms expects full=direct naming; map json_dr→full, vtt_dr→direct
    comparison = compare_arms(json_meta, vtt_meta)
    payload = {
        "trial": "T-ABL-005",
        "mode": "vtt_dr_vs_json_dr",
        "video_id": vid,
        "youtube_url": url,
        "out_dir": str(out),
        "vtt_dr": vtt_meta,
        "json_dr": json_meta,
        "compare": comparison,
    }
    compare_path = out / "compare_vtt_json_dr.json"
    compare_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(json.dumps(
        {
            "compare_path": str(compare_path),
            "topic_jaccard": (comparison or {}).get("topic_jaccard"),
            "decision_hint": (comparison or {}).get("decision_hint"),
            "vtt_caption_source": (vtt_meta or {}).get("caption_source"),
            "vtt_transcript_chars": (vtt_meta or {}).get("transcript_chars"),
            "json_n_claims": (json_meta or {}).get("n_claims"),
        },
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
