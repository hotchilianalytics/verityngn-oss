#!/usr/bin/env python3
"""
VerityNgn CLI — local claim-risk analysis.

Usage:
    verityngn analyze https://www.youtube.com/watch?v=VIDEO_ID
    verityngn analyze --tier light <url>
    verityngn analyze --tier full <url> --deep
    verityngn analyze --file /path/to/deposition.mp4 --tier local-full
    verityngn captions 'https://youtube.com/watch?v=VIDEO_ID'
    verityngn local analyze --file clip.mp4 -o out/ --arm direct
    verityngn ablate --video-id tLJC8hkK-ao --url '...' --arms direct --offline
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path


def _bootstrap_env() -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def _run_deep_research(out_dir: str, video_id: str) -> int:
    """Run Deep Research on an existing standard report JSON in out_dir."""
    report_json = Path(out_dir) / f"{video_id}_report.json"
    if not report_json.is_file():
        candidates = list(Path(out_dir).glob("*_report.json"))
        # Prefer timestamped complete dir under outputs_debug
        debug_root = Path("outputs_debug") / video_id
        if debug_root.is_dir():
            candidates.extend(debug_root.glob(f"*complete/{video_id}_report.json"))
            candidates.extend(debug_root.rglob(f"{video_id}_report.json"))
        candidates = [c for c in candidates if c.is_file() and not c.name.endswith("_deep_sanitized_input.json")]
        # Exclude deep/private naming collisions: keep *report.json that is the standard report
        candidates = [
            c
            for c in candidates
            if c.name == f"{video_id}_report.json"
            or (c.name.endswith("_report.json") and "deep" not in c.name and "private" not in c.name)
        ]
        if not candidates:
            print(
                f"Error: no report JSON found in {out_dir} for Deep Research",
                file=sys.stderr,
            )
            return 1
        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        report_json = candidates[0]
        video_id = report_json.name.split("_report.json")[0]
        # Materialize into out_dir so artefacts land together
        try:
            dest = Path(out_dir) / f"{video_id}_report.json"
            if not dest.is_file():
                import shutil

                shutil.copy2(report_json, dest)
                report_json = dest
        except Exception:
            pass

    from verityngn.services.deepresearch.pipeline import (
        DeepResearchGateError,
        generate_deep_research_report,
    )

    try:
        result = asyncio.run(
            generate_deep_research_report(
                str(report_json),
                out_dir,
                video_id=video_id,
            )
        )
    except DeepResearchGateError as exc:
        print(f"Deep Research gated: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"Deep Research failed: {exc}", file=sys.stderr)
        return 1

    status = result.get("status")
    md = result.get("markdown_path")
    if status == "completed" and md:
        print(f"\nDeep Research / risk brief: {md}")
        return 0
    print(f"\nDeep Research status={status}: {result}", file=sys.stderr)
    return 1


def cmd_analyze(args: argparse.Namespace) -> int:
    tier = getattr(args, "tier", None)
    deep = bool(getattr(args, "deep", False))

    if getattr(args, "deep_only", False):
        out_dir = args.output or os.getcwd()
        video_id = args.video_id or ""
        if not video_id:
            print("Error: --deep-only requires --video-id", file=sys.stderr)
            return 1
        return _run_deep_research(out_dir, video_id)

    if tier:
        from verityngn.services.tiers.router import run_tier

        if tier in ("local-light", "local-full") and not args.file:
            print(f"Error: --tier {tier} requires --file", file=sys.stderr)
            return 1
        if tier in ("light", "full", "auto") and not args.url and not args.file:
            print(f"Error: --tier {tier} requires a YouTube URL", file=sys.stderr)
            return 1

        try:
            # full / auto / local-full always run Deep Research so -o gets
            # report.html + deep.html (JSON-first dual-output contract).
            meta = run_tier(
                tier,
                youtube_url=args.url or "",
                video_file=args.file or "",
                out_dir=args.output or "outputs",
                title=args.title or "",
                deep=deep or tier in ("full", "auto", "local-full"),
                video_id=args.video_id or "",
                modality=getattr(args, "modality", "auto") or "auto",
            )
        except Exception as exc:  # noqa: BLE001
            print(f"analyze failed: {exc}", file=sys.stderr)
            return 1

        md = meta.get("markdown_path")
        if md:
            print(f"\nReport: {md}")
        elif meta.get("out_dir"):
            print(f"\nOutput directory: {meta['out_dir']}")
        arts = meta.get("artifacts") or {}
        if arts.get("report_html"):
            print(f"report.html: {arts['report_html']}")
        if arts.get("deep_html"):
            print(f"deep.html: {arts['deep_html']}")
        status = meta.get("status")
        return 0 if status in (None, "completed") else 1

    if args.file:
        from verityngn.utils.upload_id import video_id_from_file_path

        video_path = str(Path(args.file).expanduser().resolve())
        if not os.path.isfile(video_path):
            print(f"Error: file not found: {video_path}", file=sys.stderr)
            return 1
        upload_title = args.title or Path(video_path).stem
        video_id = video_id_from_file_path(video_path)
        config = {
            "ingest_source": "file_upload",
            "video_path": video_path,
            "upload_title": upload_title,
            "video_id": video_id,
        }
        video_url = args.url or f"upload://{video_id}"
    else:
        video_url = args.url
        config = {}
        if not video_url:
            print("Error: provide a YouTube URL or --file", file=sys.stderr)
            return 1

    from verityngn.workflows.pipeline import run_verification

    result = run_verification(
        video_url=video_url,
        out_dir_path=args.output,
        config=config,
    )

    out_dir = ""
    video_id = ""
    if isinstance(result, dict):
        out_dir = result.get("output_dir") or result.get("out_dir_path", "") or ""
        video_id = result.get("video_id", "") or ""
        md_path = Path(out_dir) / f"{video_id}_report.md" if out_dir and video_id else None
    else:
        final_state, out_dir = result
        out_dir = out_dir or ""
        video_id = final_state.get("video_id", "") if isinstance(final_state, dict) else ""
        md_path = Path(out_dir) / f"{video_id}_report.md" if out_dir and video_id else None

    if md_path and md_path.is_file():
        print(f"\nReport: {md_path}")
    elif out_dir:
        print(f"\nOutput directory: {out_dir}")

    if deep and out_dir and video_id:
        return _run_deep_research(out_dir, video_id)
    return 0


def cmd_captions(args: argparse.Namespace) -> int:
    from verityngn.services.video.caption_fetch import (
        extract_video_id,
        fetch_and_cache_vtt,
    )

    url = args.url
    video_id = args.video_id or extract_video_id(url) or ""
    if not video_id:
        print("Error: provide URL or --video-id", file=sys.stderr)
        return 1

    out_dir = args.output or str(Path("outputs") / video_id)
    result = fetch_and_cache_vtt(
        video_id,
        url,
        out_dir,
        cache_only=bool(args.cache_only),
    )
    print(
        json.dumps(
            {
                "success": result.get("success"),
                "source": result.get("source"),
                "vtt_path": result.get("vtt_path"),
                "text_chars": len(result.get("text") or ""),
                "errors": result.get("errors"),
                "error": result.get("error"),
            },
            indent=2,
        )
    )
    if args.show_text and result.get("text"):
        print("\n--- transcript excerpt ---\n")
        print((result.get("text") or "")[:2000])
    return 0 if result.get("success") else 1


def cmd_local_analyze(args: argparse.Namespace) -> int:
    from verityngn.local_app import analyze_local

    tier = getattr(args, "tier", None) or ""
    if tier in ("local-light", "local-full"):
        arm = "direct" if tier == "local-light" else "full"
    else:
        arm = args.arm

    try:
        meta = analyze_local(
            youtube_url=args.url or "",
            video_file=args.file or "",
            out_dir=args.output or "outputs/local",
            title=args.title or "",
            deep=bool(args.deep),
            arm=arm,
            tier=tier,
            download_youtube=not args.no_download,
            use_live_llm=not args.offline,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"local analyze failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({k: meta.get(k) for k in (
        "status", "tier", "arm", "video_id", "out_dir", "markdown_path", "html_path", "deep"
    ) if k in meta or meta.get(k) is not None}, indent=2, default=str))
    md = meta.get("markdown_path")
    if md:
        print(f"\nRisk brief / report: {md}")
    if args.story_arc and (args.file or meta.get("video_path")):
        from verityngn.services.vision.story_arc import summarize_continuity

        vid = meta.get("video_id") or "unknown"
        summary = summarize_continuity(vid, video_path=args.file or meta.get("video_path"))
        outp = Path(args.output or "outputs/local") / f"{vid}_continuity.json"
        summary.write_json(outp)
        print(f"Continuity summary: {outp} (status={summary.status})")
    status = meta.get("status")
    if status in (None, "completed") or meta.get("arm") == "full":
        return 0
    return 1


def cmd_ablate(args: argparse.Namespace) -> int:
    mode = getattr(args, "mode", "dr") or "dr"
    if mode == "claims":
        from verityngn.services.ablation import run_claims_ablation

        arms = args.arms
        if arms in ("full", "direct"):
            print(
                f"error: --arms {arms} is for --mode dr; "
                "use transcript|multimodal|both with --mode claims",
                file=sys.stderr,
            )
            return 2
        if arms not in ("transcript", "multimodal", "both"):
            arms = "both"
        result = run_claims_ablation(
            out_dir=args.output or "outputs/ablation_claims",
            arms=arms,
            youtube_url=args.url or "",
            video_id=args.video_id or "",
            title=args.title or "",
            use_live_llm=not args.offline,
        )
        cmp = result.get("compare") or {}
        print(
            json.dumps(
                {
                    "mode": "claims",
                    "compare_path": result.get("compare_path"),
                    "video_id": result.get("video_id"),
                    "decision_hint": cmp.get("decision_hint"),
                    "claim_jaccard": cmp.get("claim_jaccard"),
                    "n_only_multimodal": cmp.get("n_only_multimodal"),
                    "n_only_transcript": cmp.get("n_only_transcript"),
                },
                indent=2,
            )
        )
        return 0

    from verityngn.services.ablation import run_ablation

    arms = args.arms
    if arms in ("transcript", "multimodal"):
        print(
            f"error: --arms {arms} requires --mode claims",
            file=sys.stderr,
        )
        return 2
    if arms not in ("full", "direct", "both"):
        arms = "direct"

    result = run_ablation(
        out_dir=args.output or "outputs/ablation",
        arms=arms,
        youtube_url=args.url or "",
        video_path=args.file or "",
        video_id=args.video_id or "",
        title=args.title or "",
        use_live_llm=not args.offline,
        run_full_deep=not args.skip_full_deep,
    )
    print(
        json.dumps(
            {
                "mode": "dr",
                "compare_path": result.get("compare_path"),
                "video_id": result.get("video_id"),
                "decision_hint": (result.get("compare") or {}).get("decision_hint"),
                "topic_jaccard": (result.get("compare") or {}).get("topic_jaccard"),
            },
            indent=2,
        )
    )
    return 0


def main(argv: list[str] | None = None) -> None:
    _bootstrap_env()
    parser = argparse.ArgumentParser(
        prog="verityngn",
        description="VerityNgn — open-source video claim risk analysis",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    analyze = sub.add_parser("analyze", help="Analyze a YouTube URL or local video file")
    analyze.add_argument("url", nargs="?", help="YouTube video URL")
    analyze.add_argument("--file", "-f", help="Local .mp4/.mov file (skips YouTube download)")
    analyze.add_argument("--title", help="Display title for file uploads")
    analyze.add_argument("--output", "-o", help="Output directory")
    analyze.add_argument(
        "--tier",
        choices=("light", "full", "auto", "local-light", "local-full"),
        help="Analysis tier: light (VTT+DR), full (pipeline+DR), auto (sufficiency routing), local-* for files",
    )
    analyze.add_argument(
        "--deep",
        action="store_true",
        help="After full tier / standard report, run Deep Research (grounded risk brief). "
        "Also implied by --tier full|auto|local-full.",
    )
    analyze.add_argument(
        "--modality",
        choices=("auto", "transcript", "video"),
        default="auto",
        help="Claim extract modality: auto (caption+optical density), transcript-only, or video multimodal",
    )
    analyze.add_argument(
        "--deep-only",
        action="store_true",
        help="Skip analysis; run Deep Research on an existing report JSON in --output",
    )
    analyze.add_argument(
        "--video-id",
        help="Video id for --deep-only (filename prefix of *_report.json)",
    )
    analyze.add_argument("--verbose", "-v", action="store_true")
    analyze.set_defaults(func=cmd_analyze)

    captions = sub.add_parser(
        "captions",
        help="Fetch and cache YouTube .en.vtt (no LLM) — operator debugging",
    )
    captions.add_argument("url", nargs="?", help="YouTube video URL")
    captions.add_argument("--video-id", help="YouTube video id (if URL omitted)")
    captions.add_argument("-o", "--output", help="Output run directory (default outputs/VIDEO_ID)")
    captions.add_argument(
        "--cache-only",
        action="store_true",
        help="Only read cached VTT (same as SKIP_LIVE_CAPTION_FETCH=1)",
    )
    captions.add_argument("--show-text", action="store_true", help="Print transcript excerpt")
    captions.add_argument("--verbose", "-v", action="store_true")
    captions.set_defaults(func=cmd_captions)

    local = sub.add_parser("local", help="Local testing helpers")
    local_sub = local.add_subparsers(dest="local_command", required=True)
    la = local_sub.add_parser("analyze", help="Local URL/mp4 analyze (full or DR-direct)")
    la.add_argument("--url", help="YouTube URL")
    la.add_argument("--file", "-f", help="Local mp4/mov")
    la.add_argument("--title", default="")
    la.add_argument("-o", "--output", default="outputs/local")
    la.add_argument("--deep", action="store_true", help="Run Deep Research after full arm")
    la.add_argument("--arm", choices=("full", "direct"), default="full")
    la.add_argument(
        "--tier",
        choices=("local-light", "local-full"),
        help="Tier alias for --arm direct|full",
    )
    la.add_argument("--no-download", action="store_true", help="Do not pre-download YouTube to mp4")
    la.add_argument("--offline", action="store_true", help="Stub LLM on direct arm")
    la.add_argument("--story-arc", action="store_true", help="Also write vision continuity JSON")
    la.add_argument("--verbose", "-v", action="store_true")
    la.set_defaults(func=cmd_local_analyze)

    ablate = sub.add_parser(
        "ablate",
        help="Ablation: DR full vs direct (--mode dr) or transcript vs multimodal claims (--mode claims)",
    )
    ablate.add_argument(
        "--mode",
        choices=("dr", "claims"),
        default="dr",
        help="dr: full pipeline vs DR-direct; claims: transcript vs multimodal inventories",
    )
    ablate.add_argument("--url", help="YouTube URL")
    ablate.add_argument("--file", "-f", help="Local mp4/mov (DR mode full arm)")
    ablate.add_argument("--video-id", default="")
    ablate.add_argument("--title", default="")
    ablate.add_argument("-o", "--output", default="outputs/ablation")
    ablate.add_argument(
        "--arms",
        choices=("full", "direct", "both", "transcript", "multimodal"),
        default="both",
        help="dr: full|direct|both; claims: transcript|multimodal|both",
    )
    ablate.add_argument("--offline", action="store_true")
    ablate.add_argument("--skip-full-deep", action="store_true")
    ablate.add_argument("--verbose", "-v", action="store_true")
    ablate.set_defaults(func=cmd_ablate)

    args = parser.parse_args(argv)
    _setup_logging(getattr(args, "verbose", False))
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
