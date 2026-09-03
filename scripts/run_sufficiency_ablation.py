#!/usr/bin/env python3
"""T-ABL-007: light (untruncated transcript+DR) vs full routing ablation by duration stratum."""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _bootstrap() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass


def _load_claims_from_report(video_id: str) -> List[Dict[str, Any]]:
    search_roots = [
        Path("outputs_debug") / video_id,
        Path("outputs") / video_id,
        Path("outputs") / "ablation_T006",
        Path("outputs") / "ablation_T007",
        Path("outputs"),
    ]
    # Prefer multimodal claim inventories for ground truth
    for base in search_roots:
        if not base.exists():
            continue
        for name in ("claims_multimodal.json", f"{video_id}_report.json"):
            for p in sorted(base.rglob(name), key=lambda x: x.stat().st_mtime, reverse=True):
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                # Scope: path or payload must reference this video
                if video_id not in str(p) and data.get("video_id") not in (None, video_id):
                    # For T006 folder layout (G1_...), accept if claims look present and
                    # parent compare references video — check sibling compare_claims
                    sibling = p.parent.parent / "compare_claims.json"
                    if sibling.is_file():
                        try:
                            cmp = json.loads(sibling.read_text(encoding="utf-8"))
                            if cmp.get("video_id") != video_id:
                                continue
                        except (OSError, json.JSONDecodeError):
                            continue
                    elif video_id not in str(p):
                        continue
                claims = data.get("claims") or data.get("claims_breakdown") or []
                if isinstance(claims, list) and claims:
                    return claims
    return []


def run_one(seed: Dict[str, Any], out_root: Path, *, skip_full: bool) -> Dict[str, Any]:
    from verityngn.services.ablation.cost import (
        build_arm_cost,
        estimate_multimodal_input_tokens,
        estimate_transcript_tokens,
        write_arm_cost,
    )
    from verityngn.services.ablation.direct import run_dr_direct
    from verityngn.services.ablation.sufficiency import (
        compare_sufficiency,
        preflight_features,
        route_decision,
    )
    from verityngn.services.video.caption_fetch import fetch_and_cache_vtt

    vid = seed["video_id"]
    url = seed.get("url") or f"https://www.youtube.com/watch?v={vid}"
    duration = float(seed.get("duration_sec") or 0)
    seed_out = out_root / vid
    seed_out.mkdir(parents=True, exist_ok=True)

    caption = fetch_and_cache_vtt(vid, url, str(seed_out))
    vtt_raw = ""
    if caption.get("vtt_path") and Path(str(caption["vtt_path"])).is_file():
        vtt_raw = Path(str(caption["vtt_path"])).read_text(encoding="utf-8", errors="ignore")

    feats = preflight_features(
        duration_sec=duration,
        transcript_chars=len(caption.get("text") or ""),
        caption_source=str(caption.get("source") or ""),
        vtt_text=vtt_raw,
        title=seed.get("title") or "",
        genre_hint=seed.get("genre") or "",
        youtube_url=url,
        synthetic=bool(caption.get("synthetic")),
    )
    decision = route_decision(feats)

    # Light arm (untruncated — default 50k)
    light = run_dr_direct(
        out_dir=str(seed_out / "light"),
        video_id=vid,
        youtube_url=url,
        title=seed.get("title") or "",
        use_live_llm=True,
        duration_sec=duration,
    )
    light_md = ""
    if light.get("markdown_path") and Path(str(light["markdown_path"])).is_file():
        light_md = Path(str(light["markdown_path"])).read_text(encoding="utf-8", errors="ignore")

    full_meta: Dict[str, Any] = {"skipped": skip_full}
    full_claims: List[Dict[str, Any]] = []
    full_elapsed = 0.0
    full_usd = 0.0

    if not skip_full:
        # Cost-controlled: reuse existing report claims when present; else run multimodal claims only
        full_claims = _load_claims_from_report(vid)
        if not full_claims:
            from verityngn.services.ablation.multimodal_arm import run_multimodal_claims_arm

            t0 = time.perf_counter()
            mm = run_multimodal_claims_arm(
                out_dir=str(seed_out / "full_claims"),
                video_id=vid,
                youtube_url=url,
                title=seed.get("title") or "",
                use_live_llm=True,
            )
            full_elapsed = time.perf_counter() - t0
            full_claims = mm.get("claims") or []
            in_tok = estimate_multimodal_input_tokens(duration)
            out_tok = max(500, len(json.dumps(full_claims)) // 4)
            cost = build_arm_cost(
                arm="full_claims",
                latency_sec=full_elapsed,
                n_llm_calls=1,
                input_tokens=in_tok,
                output_tokens=out_tok,
                duration_sec=duration,
            )
            write_arm_cost(str(seed_out / "full_claims"), cost)
            full_usd = float(cost.get("usd_estimate") or 0)
            full_meta = {"status": mm.get("status"), "n_claims": len(full_claims), "arm_cost": cost}
        else:
            # Estimate full cost from duration heuristic (historical full pipeline ~ linear)
            full_elapsed = max(60.0, duration * 0.8)  # ~0.8s wall per video-second observed
            in_tok = estimate_multimodal_input_tokens(duration) + 20_000
            out_tok = 8_000
            cost = build_arm_cost(
                arm="full_reused_report",
                latency_sec=full_elapsed,
                n_llm_calls=3,
                input_tokens=in_tok,
                output_tokens=out_tok,
                duration_sec=duration,
                extra={"reused_claims": True, "n_claims": len(full_claims)},
            )
            write_arm_cost(str(seed_out), cost, name="full_arm_cost_estimate.json")
            full_usd = float(cost.get("usd_estimate") or 0)
            full_meta = {"status": "reused", "n_claims": len(full_claims), "arm_cost": cost}

    cmp = compare_sufficiency(
        full_claims=full_claims,
        light_brief_md=light_md,
        full_elapsed=full_elapsed,
        light_elapsed=float(light.get("elapsed_sec") or 0),
        full_usd=full_usd,
        light_usd=float(light.get("usd_estimate") or 0),
        k=10,
    )

    row = {
        "video_id": vid,
        "title": seed.get("title"),
        "stratum": seed.get("stratum"),
        "genre": seed.get("genre"),
        "duration_sec": duration,
        "preflight": feats,
        "route_decision": decision,
        "light": {
            k: light.get(k)
            for k in (
                "status",
                "elapsed_sec",
                "transcript_chars_fetched",
                "transcript_chars_used",
                "transcript_truncated",
                "usd_estimate",
                "n_llm_calls",
                "markdown_path",
            )
        },
        "full": full_meta,
        "sufficiency": cmp,
    }
    (seed_out / "compare_sufficiency.json").write_text(
        json.dumps(row, indent=2, default=str), encoding="utf-8"
    )
    return row


def main() -> int:
    _bootstrap()
    parser = argparse.ArgumentParser(description="T-ABL-007 sufficiency routing ablation")
    parser.add_argument("--seeds", default="evaluation/seed_pool.json")
    parser.add_argument("-o", "--output", default="outputs/ablation_T007")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument(
        "--skip-full-llm",
        action="store_true",
        help="Reuse existing report/MM claims only; never call multimodal extract",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    pool = json.loads(Path(args.seeds).read_text(encoding="utf-8"))
    seeds = (pool.get("seeds") or [])[: args.limit]
    out_root = Path(args.output)
    out_root.mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, Any]] = []
    for seed in seeds:
        logger.info("=== T-ABL-007 %s (%s) ===", seed.get("video_id"), seed.get("stratum"))
        try:
            rows.append(run_one(seed, out_root, skip_full=args.skip_full_llm))
        except Exception as exc:  # noqa: BLE001
            logger.exception("seed failed")
            rows.append({"video_id": seed.get("video_id"), "error": str(exc)})

    # Calibrate TAU suggestion from competitive lights
    competitive = [
        r
        for r in rows
        if (r.get("sufficiency") or {}).get("decision_hint") == "light_competitive"
    ]
    summary = {
        "trial_id": "T-ABL-007",
        "n_seeds": len(rows),
        "n_light_competitive": len(competitive),
        "mean_latency_speedup": _mean(
            [(r.get("sufficiency") or {}).get("latency_speedup") for r in rows]
        ),
        "mean_cost_speedup": _mean(
            [(r.get("sufficiency") or {}).get("cost_speedup") for r in rows]
        ),
        "mean_risk_recall": _mean(
            [(r.get("sufficiency") or {}).get("risk_recall") for r in rows]
        ),
        "truncation_violations": sum(
            1
            for r in rows
            if (r.get("light") or {}).get("transcript_truncated")
        ),
        "suggested_thresholds": {
            "TAU_COV": 0.70,
            "TAU_VIS": 0.35,
            "TAU_DUR": 900,
            "note": "Defaults retained; tighten TAU_COV if false-light rate high",
        },
        "rows": rows,
    }
    path = out_root / "summary.json"
    path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(
        json.dumps(
            {
                "summary_path": str(path),
                "n_seeds": summary["n_seeds"],
                "n_light_competitive": summary["n_light_competitive"],
                "mean_risk_recall": summary["mean_risk_recall"],
                "mean_latency_speedup": summary["mean_latency_speedup"],
                "mean_cost_speedup": summary["mean_cost_speedup"],
                "truncation_violations": summary["truncation_violations"],
            },
            indent=2,
        )
    )
    return 0


def _mean(vals: List[Optional[float]]) -> Optional[float]:
    xs = [float(v) for v in vals if v is not None]
    if not xs:
        return None
    return round(sum(xs) / len(xs), 4)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    raise SystemExit(main())
