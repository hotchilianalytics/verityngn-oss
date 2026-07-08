#!/usr/bin/env python3
"""
VerityNgn CLI — zero-friction local analysis.

Usage:
    verityngn analyze https://www.youtube.com/watch?v=VIDEO_ID
    verityngn analyze --file /path/to/deposition.mp4 --title "Expert witness clip"
"""
from __future__ import annotations

import argparse
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

    result = run_verification(
        video_url=video_url,
        out_dir_path=args.output,
        config=config,
    )

    if isinstance(result, dict):
        out_dir = result.get("output_dir") or result.get("out_dir_path", "")
        video_id = result.get("video_id", "")
        md_path = Path(out_dir) / f"{video_id}_report.md" if out_dir and video_id else None
    else:
        final_state, out_dir = result
        video_id = final_state.get("video_id", "") if isinstance(final_state, dict) else ""
        md_path = Path(out_dir) / f"{video_id}_report.md" if out_dir and video_id else None

    if md_path and md_path.is_file():
        print(f"\n✅ Report: {md_path}")
    elif out_dir:
        print(f"\n✅ Output directory: {out_dir}")
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
    analyze.add_argument("--verbose", "-v", action="store_true")
    analyze.set_defaults(func=cmd_analyze)

    args = parser.parse_args(argv)
    _setup_logging(getattr(args, "verbose", False))
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
