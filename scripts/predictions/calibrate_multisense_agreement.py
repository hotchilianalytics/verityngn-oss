#!/usr/bin/env python3
"""
Calibration harness: interpreted (Gemini offline proxy) vs measured affect agreement.

Registers trial T007 metrics into an output JSON (ledger row is documented in
docs/trials_ledger.md). Runs fully offline by default.

Usage:
  python scripts/calibrate_multisense_agreement.py \\
    --report-dir path/to/gallery_reports \\
    --out data/predictions/calibration/T007_multisense_agreement.json
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

# Allow running from repo root / worktree root
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from verityngn.services.affect.extract import extract_affect_for_report
from verityngn.services.fusion.crossmodal import interpreted_measured_agreement
from verityngn.services.fusion.gemini_multisense import run_gemini_multisense
from verityngn.services.fusion.schema import build_fused_index


def _load_reports(report_dir: Path) -> list[Path]:
    paths = sorted(report_dir.glob("*_report.json"))
    if not paths:
        paths = sorted(report_dir.glob("*.json"))
    return [p for p in paths if "affect" not in p.name and "multisense" not in p.name]


def _synthetic_mini_report(video_id: str) -> dict:
    """Fallback when no gallery reports are present."""
    return {
        "video_id": video_id,
        "claims_breakdown": [
            {
                "claim_id": 1,
                "claim_text": "We expect strong revenue growth this quarter.",
                "timestamp": "00:30",
                "speaker": "CEO",
                "initial_assessment": "TRUE",
                "verification_result": {"result": "TRUE"},
            },
            {
                "claim_id": 2,
                "claim_text": "There is no material risk to our guidance.",
                "timestamp": "01:15",
                "speaker": "CEO",
                "initial_assessment": "TRUE",
                "verification_result": {"result": "UNCERTAIN"},
            },
            {
                "claim_id": 3,
                "claim_text": "Margins will expand to record levels.",
                "timestamp": "02:00",
                "speaker": "CFO",
                "initial_assessment": "MIXED",
                "verification_result": {"result": "FALSE"},
            },
        ],
    }


def calibrate_one(report: dict) -> dict:
    ms = run_gemini_multisense(report, offline=True)
    affect = extract_affect_for_report(report, audio_path=None)
    fused = build_fused_index(
        video_id=str(report.get("video_id") or "unknown"),
        affect=affect.to_dict(),
        vision={},
        gemini=ms.to_dict(),
    )
    scores = []
    for row in fused.get("fused_rows") or []:
        if row.get("gemini_arousal") is None:
            continue
        im = interpreted_measured_agreement(
            gemini_arousal=float(row.get("gemini_arousal") or 0.5),
            gemini_valence=float(row.get("gemini_valence") or 0.0),
            measured_arousal=float("nan")
            if row.get("measured_arousal") is None
            else float(row["measured_arousal"]),
            measured_valence=float("nan")
            if row.get("measured_valence") is None
            else float(row["measured_valence"]),
            exuberance=float(row.get("exuberance") or 0.5),
        )
        scores.append(im["interpreted_measured_congruence"])
    cross = fused.get("crossmodal") or {}
    return {
        "video_id": report.get("video_id"),
        "n_claims": len(report.get("claims_breakdown") or []),
        "n_scored": len(scores),
        "mean_interpreted_measured_congruence": (
            statistics.fmean(scores) if scores else None
        ),
        "overall_congruence": cross.get("overall_congruence"),
        "modality_divergence_rate": cross.get("modality_divergence_rate"),
        "multisense_source": (ms.summary or {}).get("source"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-dir", type=Path, default=None)
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("data/predictions/calibration/T007_multisense_agreement.json"),
    )
    args = ap.parse_args()

    results = []
    if args.report_dir and args.report_dir.exists():
        for p in _load_reports(args.report_dir)[:5]:
            report = json.loads(p.read_text(encoding="utf-8"))
            results.append(calibrate_one(report))
    if not results:
        for vid in ("gallery_demo_a", "gallery_demo_b", "gallery_demo_c"):
            results.append(calibrate_one(_synthetic_mini_report(vid)))

    means = [
        r["mean_interpreted_measured_congruence"]
        for r in results
        if r.get("mean_interpreted_measured_congruence") is not None
    ]
    payload = {
        "trial_id": "T007",
        "label": "interpreted-measured-agreement",
        "registered": "2026-08-10",
        "status": "NO_PROMOTE",
        "note": (
            "Offline proxy calibration. Replace with live Gemini + executive-domain "
            "audio before any H1 promote claim. Cross-domain collapse risk remains."
        ),
        "n_videos": len(results),
        "mean_agreement": statistics.fmean(means) if means else None,
        "per_video": results,
        "gates": {
            "promote_requires": [
                "live_gemini_tier_a",
                "executive_domain_audio",
                "ICIR>=0.40 on linked CAR trial",
            ]
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"wrote": str(args.out), "mean_agreement": payload["mean_agreement"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
