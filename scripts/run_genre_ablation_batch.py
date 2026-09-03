#!/usr/bin/env python3
"""T-ABL-006: batch claims ablations for genre_ablation_seeds.json → summary.json."""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def _bootstrap() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass


def main() -> int:
    _bootstrap()
    parser = argparse.ArgumentParser(description="T-ABL-006 genre claims ablation batch")
    parser.add_argument(
        "--seeds",
        default="evaluation/genre_ablation_seeds.json",
        help="Path to genre_ablation_seeds.json",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="outputs/ablation_T006",
        help="Output root (per-seed dirs + summary.json)",
    )
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    seeds_path = Path(args.seeds)
    data = json.loads(seeds_path.read_text(encoding="utf-8"))
    seeds: List[Dict[str, Any]] = data.get("seeds") or []
    out_root = Path(args.output)
    out_root.mkdir(parents=True, exist_ok=True)

    from verityngn.services.ablation import run_claims_ablation

    rows: List[Dict[str, Any]] = []
    for seed in seeds:
        sid = seed.get("id") or "unknown"
        vid = seed.get("video_id") or ""
        url = seed.get("url") or (f"https://www.youtube.com/watch?v={vid}" if vid else "")
        if not vid or not url:
            logger.warning("Skipping seed %s — missing video_id/url", sid)
            continue
        seed_out = out_root / sid
        logger.info("=== %s (%s) → %s ===", sid, vid, seed_out)
        result = run_claims_ablation(
            out_dir=str(seed_out),
            arms="both",
            youtube_url=url,
            video_id=vid,
            title=seed.get("title") or "",
            use_live_llm=not args.offline,
        )
        cmp = result.get("compare") or {}
        gate = result.get("genre_sleeve_gate") or {}
        tx = result.get("transcript") or {}
        mm = result.get("multimodal") or {}
        row = {
            "seed_id": sid,
            "genre": seed.get("genre"),
            "video_id": vid,
            "url": url,
            "duration_sec": seed.get("duration_sec"),
            "title": seed.get("title"),
            "n_transcript": tx.get("n_claims"),
            "n_multimodal": mm.get("n_claims"),
            "claim_jaccard": cmp.get("claim_jaccard"),
            "only_multimodal_share_of_union": cmp.get("only_multimodal_share_of_union"),
            "visual_only_multimodal_share": cmp.get("visual_only_multimodal_share"),
            "visual_only_multimodal_count": cmp.get("visual_only_multimodal_count"),
            "decision_hint": cmp.get("decision_hint"),
            "sleeve_validated": gate.get("sleeve_validated"),
            "genre_gate": gate,
            "compare_path": result.get("compare_path"),
            "multimodal_source_type_histogram": cmp.get("multimodal_source_type_histogram"),
            "caption_source": tx.get("transcript_source"),
            "transcript_chars": tx.get("transcript_chars"),
            "transcript_elapsed_sec": tx.get("elapsed_sec"),
            "multimodal_elapsed_sec": mm.get("elapsed_sec"),
            "only_multimodal_examples": (cmp.get("only_multimodal") or [])[:8],
        }
        rows.append(row)
        logger.info(
            "%s: TX=%s MM=%s jaccard=%s visual_only=%s gate=%s",
            sid,
            row["n_transcript"],
            row["n_multimodal"],
            row["claim_jaccard"],
            row["visual_only_multimodal_share"],
            row["sleeve_validated"],
        )

    n_pass = sum(1 for r in rows if r.get("sleeve_validated"))
    min_pass = int((data.get("gate") or {}).get("min_seeds_passing") or 2)
    summary = {
        "trial_id": data.get("trial_id") or "T-ABL-006",
        "seeds_file": str(seeds_path),
        "out_dir": str(out_root),
        "n_seeds": len(rows),
        "n_sleeve_validated": n_pass,
        "min_seeds_passing": min_pass,
        "aggregate_gate_pass": n_pass >= min_pass,
        "rows": rows,
    }
    summary_path = out_root / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"summary_path": str(summary_path), **{k: summary[k] for k in (
        "trial_id", "n_seeds", "n_sleeve_validated", "aggregate_gate_pass"
    )}}, indent=2))
    return 0 if rows else 1


if __name__ == "__main__":
    # Ensure repo root on path
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    raise SystemExit(main())
