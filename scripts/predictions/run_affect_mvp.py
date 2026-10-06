#!/usr/bin/env python3
"""P1 Affect MVP — extract prosody/disfluency for 2–3 gallery reports."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running from repo root without install
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from verityngn.services.affect.extract import extract_affect_for_report
from verityngn.services.affect.prosody import synthesize_demo_wav
from verityngn.services.authenticity.adapters import CorsoundAdapter
from verityngn.services.authenticity.gate import run_authenticity_gate
from verityngn.services.deception.risk import assess_deception_risk


DEFAULT_REPORTS = [
    # Resolved relative to --gallery-root if provided
    "iGeXGdYE7UE/2026-03-16_16-07-37_complete/iGeXGdYE7UE_report.json",
    "tLJC8hkK-ao/2026-02-22_21-44-37_complete/tLJC8hkK-ao_report.json",
    "sbChYUijRKE/2026-02-18_20-45-49_complete/sbChYUijRKE_report.json",
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--gallery-root",
        type=Path,
        default=None,
        help="Root containing gallery report folders (e.g. outputs_debug)",
    )
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--use-synth-audio", action="store_true", help="Synthesize demo WAV per video")
    args = ap.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    audio_dir = out_dir / "fixtures" / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    report_paths: list[Path] = []
    if args.gallery_root:
        for rel in DEFAULT_REPORTS:
            p = args.gallery_root / rel
            if p.exists():
                report_paths.append(p)
    if not report_paths:
        print("ERROR: no gallery reports found; pass --gallery-root", file=sys.stderr)
        return 2

    corsound = CorsoundAdapter()
    results = []
    for i, report_path in enumerate(report_paths[:3]):
        report = json.loads(report_path.read_text(encoding="utf-8"))
        video_id = (
            report.get("video_id")
            or report_path.name.replace("_report.json", "")
        )
        audio_path = None
        if args.use_synth_audio:
            audio_path = synthesize_demo_wav(
                audio_dir / f"{video_id}.wav",
                duration_sec=90.0,
                base_f0=130.0 + 10 * i,
                seed=1000 + i,
            )
        auth = run_authenticity_gate(
            video_id=str(video_id),
            corsound=corsound.analyze(str(audio_path) if audio_path else "none"),
        )
        affect = extract_affect_for_report(
            report,
            audio_path=audio_path,
            authenticity=auth.to_dict(),
        )
        # Ensure video_id from filename if unknown
        if affect.video_id == "unknown":
            affect.video_id = str(video_id)
        out_json = out_dir / "affect" / f"{affect.video_id}_affect.json"
        affect.write_json(out_json)
        risk = assess_deception_risk(affect.to_dict())
        risk_path = out_dir / "affect" / f"{affect.video_id}_deception_risk.json"
        risk_path.parent.mkdir(parents=True, exist_ok=True)
        risk_path.write_text(json.dumps(risk.to_dict(), indent=2), encoding="utf-8")
        results.append(
            {
                "video_id": affect.video_id,
                "report": str(report_path),
                "affect": str(out_json),
                "deception_risk": str(risk_path),
                "audio": str(audio_path) if audio_path else None,
                "summary": affect.summary,
            }
        )
        print(f"OK {affect.video_id} segments={affect.summary.get('n_claims')} -> {out_json}")

    manifest = out_dir / "affect" / "mvp_manifest.json"
    manifest.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Wrote {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
