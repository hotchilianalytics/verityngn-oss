#!/usr/bin/env python3
"""Run DR-direct vs full-pipeline ablation.

Register a trials_ledger row BEFORE live LLM peeks when scoring promotion decisions.

Examples:
  python scripts/run_dr_direct_ablation.py --arms direct --offline \\
      --video-id tLJC8hkK-ao --url 'https://www.youtube.com/watch?v=tLJC8hkK-ao' \\
      -o outputs/ablation_tL

  verityngn ablate --arms both --file clip.mp4 -o outputs/ablation_local
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv: list[str] | None = None) -> int:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    p = argparse.ArgumentParser(description="VerityNgn DR-direct ablation")
    p.add_argument("--url", help="YouTube URL")
    p.add_argument("--file", "-f", help="Local mp4/mov")
    p.add_argument("--video-id", default="", help="Optional video id override")
    p.add_argument("--title", default="")
    p.add_argument("-o", "--output", default="outputs/ablation", help="Output directory")
    p.add_argument("--arms", choices=("full", "direct", "both"), default="direct")
    p.add_argument(
        "--offline",
        action="store_true",
        help="Stub the direct-arm LLM (no Vertex/Gemini call)",
    )
    p.add_argument(
        "--skip-full-deep",
        action="store_true",
        help="On full arm, skip Deep Research after standard report",
    )
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="[%(asctime)s] [%(levelname)s] %(message)s",
    )

    if not args.url and not args.file and args.arms != "direct":
        # direct can still run with video-id alone if transcript/files nearby
        if not args.video_id:
            print("Provide --url and/or --file (and --video-id for direct-only)", file=sys.stderr)
            return 1

    from verityngn.services.ablation import run_ablation

    result = run_ablation(
        out_dir=args.output,
        arms=args.arms,
        youtube_url=args.url or "",
        video_path=args.file or "",
        video_id=args.video_id or "",
        title=args.title or "",
        use_live_llm=not args.offline,
        run_full_deep=not args.skip_full_deep,
    )
    print(json.dumps({
        "compare_path": result.get("compare_path"),
        "video_id": result.get("video_id"),
        "decision_hint": (result.get("compare") or {}).get("decision_hint"),
        "topic_jaccard": (result.get("compare") or {}).get("topic_jaccard"),
        "direct_status": (result.get("direct") or {}).get("status"),
        "full_status": (result.get("full") or {}).get("status"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
