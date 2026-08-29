#!/usr/bin/env python3
"""
VerityNgn CLI — zero-friction local analysis.

Usage:
    verityngn analyze https://www.youtube.com/watch?v=VIDEO_ID
    verityngn analyze --file /path/to/deposition.mp4 --title "Expert witness clip"
    verityngn analyze <url> --deep
"""
from __future__ import annotations

import argparse
import asyncio
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
        # Common alternate naming from pipeline
        candidates = list(Path(out_dir).glob("*_report.json"))
        if not candidates:
            print(
                f"Error: no report JSON found in {out_dir} for Deep Research",
                file=sys.stderr,
            )
            return 1
        report_json = candidates[0]
        video_id = report_json.name.split("_report.json")[0]

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
        print(f"\nDeep Research report: {md}")
        return 0
    print(f"\nDeep Research status={status}: {result}", file=sys.stderr)
    return 1


def cmd_analyze(args: argparse.Namespace) -> int:
    from verityngn.workflows.pipeline import run_verification

    config = {}
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
        if not video_url:
            print("Error: provide a YouTube URL or --file", file=sys.stderr)
            return 1

    if getattr(args, "deep_only", False):
        out_dir = args.output or os.getcwd()
        video_id = args.video_id or ""
        if not video_id:
            print("Error: --deep-only requires --video-id", file=sys.stderr)
            return 1
        return _run_deep_research(out_dir, video_id)

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

    if getattr(args, "deep", False) and out_dir and video_id:
        return _run_deep_research(out_dir, video_id)
    return 0


def main(argv: list[str] | None = None) -> None:
    _bootstrap_env()
    parser = argparse.ArgumentParser(
        prog="verityngn",
        description="VerityNgn — open-source video claim verification",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    analyze = sub.add_parser("analyze", help="Analyze a YouTube URL or local video file")
    analyze.add_argument("url", nargs="?", help="YouTube video URL")
    analyze.add_argument("--file", "-f", help="Local .mp4/.mov file (skips YouTube download)")
    analyze.add_argument("--title", help="Display title for file uploads")
    analyze.add_argument("--output", "-o", help="Output directory")
    analyze.add_argument(
        "--deep",
        action="store_true",
        help="After the standard report, run Deep Research (Gemini grounded pass)",
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

    args = parser.parse_args(argv)
    _setup_logging(getattr(args, "verbose", False))
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
