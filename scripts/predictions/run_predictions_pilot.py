#!/usr/bin/env python3
"""P2–P5 pilot: players, mediasphere, timeseries, dossiers."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from verityngn.services.predictions.pipeline import run_predictions_pilot
from verityngn.services.predictions.renderer import markdown_to_html_stub
from verityngn.services.affect.adapters import MillionwaysAdapter
from verityngn.services.deception.adapters import NemesyscoAdapter, RevealenseAdapter
from verityngn.services.authenticity.adapters import CorsoundAdapter
import json


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--affect-dir", type=Path, default=None)
    args = ap.parse_args()

    # P4: exercise vendor adapter surface (stubs)
    vendors = {
        "millionways": MillionwaysAdapter().analyze_audio("stub.wav").to_dict(),
        "corsound": CorsoundAdapter().analyze("stub.wav"),
        "nemesysco": NemesyscoAdapter().analyze({"audio": "stub.wav"}),
        "revealense": RevealenseAdapter().analyze({"video": "stub.mp4"}),
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "vendors_stub_status.json").write_text(json.dumps(vendors, indent=2), encoding="utf-8")

    affect_dir = args.affect_dir or (args.out_dir / "affect")
    manifest = run_predictions_pilot(args.out_dir, affect_dir=affect_dir)

    # HTML stubs for dossiers
    for pid, paths in (manifest.get("dossiers") or {}).items():
        md = Path(paths["md"])
        html = md.with_suffix(".html")
        markdown_to_html_stub(md, html)
        paths["html"] = str(html)

    (args.out_dir / "pilot_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "manifest": str(args.out_dir / "pilot_manifest.json")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
