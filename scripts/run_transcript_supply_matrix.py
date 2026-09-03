#!/usr/bin/env python3
"""T-TX-002: transcript supply matrix across free + paid paths (C0–C6)."""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def _bootstrap() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass


def _run_path(name: str, video_id: str, url: str, out_dir: Path) -> Dict[str, Any]:
    from verityngn.services.video.caption_fetch import (
        _fetch_via_cached_vtt,
        _fetch_via_gemini_youtube,
        _fetch_via_youtube_transcript_api,
        _fetch_via_ytdlp_subs,
        vtt_to_text,
    )

    t0 = time.perf_counter()
    try:
        if name == "cached":
            r = _fetch_via_cached_vtt(video_id, 50000, str(out_dir))
        elif name == "ytdlp":
            r = _fetch_via_ytdlp_subs(video_id, url, str(out_dir), 50000)
        elif name == "api":
            r = _fetch_via_youtube_transcript_api(video_id, 50000)
        elif name == "supadata":
            from verityngn.services.video.transcript_providers.supadata import SupadataProvider

            prov = SupadataProvider()
            if not prov.available():
                return {
                    "path": name,
                    "success": False,
                    "skipped": True,
                    "reason": "no_api_key",
                    "latency_sec": 0.0,
                    "usd_estimate": 0.0,
                }
            tr = prov.fetch(video_id=video_id, url=url, mode="native")
            return {
                "path": name,
                "success": tr.success,
                "source": tr.source,
                "kind": tr.kind,
                "latency_sec": tr.latency_sec,
                "usd_estimate": tr.usd_estimate,
                "chars": len(tr.text or ""),
                "error": tr.error,
            }
        elif name == "supadata_generate":
            from verityngn.services.video.transcript_providers.supadata import SupadataProvider

            if os.getenv("TRANSCRIPT_ALLOW_GENERATE", "").strip().lower() not in ("1", "true", "yes"):
                return {
                    "path": name,
                    "success": False,
                    "skipped": True,
                    "reason": "TRANSCRIPT_ALLOW_GENERATE not set",
                    "latency_sec": 0.0,
                    "usd_estimate": 0.0,
                }
            prov = SupadataProvider()
            if not prov.available():
                return {
                    "path": name,
                    "success": False,
                    "skipped": True,
                    "reason": "no_api_key",
                    "latency_sec": 0.0,
                    "usd_estimate": 0.0,
                }
            tr = prov.fetch(video_id=video_id, url=url, mode="generate")
            return {
                "path": name,
                "success": tr.success,
                "source": tr.source,
                "kind": tr.kind,
                "latency_sec": tr.latency_sec,
                "usd_estimate": tr.usd_estimate,
                "chars": len(tr.text or ""),
                "error": tr.error,
            }
        elif name == "asr_groq":
            from verityngn.services.video.transcript_providers.asr_groq import GroqAsrProvider

            prov = GroqAsrProvider()
            if not prov.available():
                return {
                    "path": name,
                    "success": False,
                    "skipped": True,
                    "reason": "no_api_key",
                    "latency_sec": 0.0,
                    "usd_estimate": 0.0,
                }
            tr = prov.fetch(video_id=video_id, url=url)
            return {
                "path": name,
                "success": tr.success,
                "source": tr.source,
                "kind": tr.kind,
                "latency_sec": tr.latency_sec,
                "usd_estimate": tr.usd_estimate,
                "chars": len(tr.text or ""),
                "error": tr.error,
            }
        elif name == "gemini":
            r = _fetch_via_gemini_youtube(video_id, url, str(out_dir), 50000)
        else:
            return {"path": name, "success": False, "error": "unknown path"}

        return {
            "path": name,
            "success": bool(r.get("success")),
            "source": r.get("source"),
            "latency_sec": time.perf_counter() - t0,
            "usd_estimate": 0.0,
            "chars": len(r.get("text") or ""),
            "error": r.get("error"),
            "vtt_path": r.get("vtt_path"),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "path": name,
            "success": False,
            "latency_sec": time.perf_counter() - t0,
            "usd_estimate": 0.0,
            "error": str(exc),
        }


def classify_condition(seed: Dict[str, Any], path_results: List[Dict[str, Any]]) -> str:
    """Heuristic C0–C6 label from seed notes + path outcomes."""
    notes = (seed.get("notes") or "").lower()
    probe = (seed.get("caption_probe") or {}).get("caption_kind") or ""
    if "c4" in notes or probe == "none":
        return "C4"
    ytdlp = next((p for p in path_results if p["path"] == "ytdlp"), {})
    cached = next((p for p in path_results if p["path"] == "cached"), {})
    if cached.get("success"):
        return "C0"
    if ytdlp.get("success"):
        return "C2"
    if ytdlp.get("success") is False and "potoken" in str(ytdlp.get("error") or "").lower():
        return "C3"
    if not ytdlp.get("success"):
        return "C3"
    return "C2"


def main() -> int:
    _bootstrap()
    parser = argparse.ArgumentParser(description="T-TX-002 transcript supply matrix")
    parser.add_argument("--seeds", default="evaluation/seed_pool.json")
    parser.add_argument("-o", "--output", default="outputs/transcript_supply_T002")
    parser.add_argument("--limit", type=int, default=8, help="Max seeds to probe live")
    parser.add_argument("--paths", default="cached,ytdlp,api,supadata,asr_groq,gemini")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    seeds_path = Path(args.seeds)
    if not seeds_path.is_file():
        print(f"missing seeds: {seeds_path}", file=sys.stderr)
        return 1
    pool = json.loads(seeds_path.read_text(encoding="utf-8"))
    seeds = (pool.get("seeds") or [])[: args.limit]
    out_root = Path(args.output)
    out_root.mkdir(parents=True, exist_ok=True)
    paths = [p.strip() for p in args.paths.split(",") if p.strip()]

    rows: List[Dict[str, Any]] = []
    for seed in seeds:
        vid = seed["video_id"]
        url = seed.get("url") or f"https://www.youtube.com/watch?v={vid}"
        seed_out = out_root / vid
        seed_out.mkdir(parents=True, exist_ok=True)
        logger.info("=== T-TX-002 %s ===", vid)
        path_results = [_run_path(p, vid, url, seed_out) for p in paths]
        cond = classify_condition(seed, path_results)
        rows.append(
            {
                "video_id": vid,
                "title": seed.get("title"),
                "duration_sec": seed.get("duration_sec"),
                "stratum": seed.get("stratum"),
                "genre": seed.get("genre"),
                "condition": cond,
                "paths": path_results,
                "any_success": any(p.get("success") for p in path_results),
                "cheapest_success_usd": min(
                    (p.get("usd_estimate") or 0.0 for p in path_results if p.get("success")),
                    default=None,
                ),
            }
        )

    # Aggregate by path
    by_path: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        for p in row["paths"]:
            name = p["path"]
            agg = by_path.setdefault(
                name,
                {"path": name, "n": 0, "n_success": 0, "n_skipped": 0, "latencies": [], "usd": []},
            )
            agg["n"] += 1
            if p.get("skipped"):
                agg["n_skipped"] += 1
            if p.get("success"):
                agg["n_success"] += 1
                agg["latencies"].append(p.get("latency_sec") or 0)
                agg["usd"].append(p.get("usd_estimate") or 0)

    summary_paths = []
    for name, agg in by_path.items():
        n_live = agg["n"] - agg["n_skipped"]
        summary_paths.append(
            {
                "path": name,
                "n": agg["n"],
                "n_success": agg["n_success"],
                "n_skipped": agg["n_skipped"],
                "success_rate": (agg["n_success"] / n_live) if n_live else None,
                "mean_latency_sec": (
                    sum(agg["latencies"]) / len(agg["latencies"]) if agg["latencies"] else None
                ),
                "mean_usd": (sum(agg["usd"]) / len(agg["usd"]) if agg["usd"] else None),
            }
        )

    matrix = {
        "trial_id": "T-TX-002",
        "n_seeds": len(rows),
        "paths": summary_paths,
        "rows": rows,
        "economics_note": "Supadata ~$0.99–1.57/1k; Groq ASR ~$0.02–0.04/audio-hr (2026-09-02)",
    }
    out_path = out_root / "matrix.json"
    out_path.write_text(json.dumps(matrix, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"matrix_path": str(out_path), "n_seeds": len(rows), "paths": summary_paths}, indent=2))
    return 0


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    raise SystemExit(main())
