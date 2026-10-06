#!/usr/bin/env python3
"""Run vision + fusion offline over gallery affect JSONs."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from verityngn.services.fusion.schema import build_fused_index, write_fused_index
from verityngn.services.vision.extract import extract_vision_for_video


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--affect-dir", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--player-id", default="gallery_proxy")
    args = ap.parse_args()

    out_dir = args.out_dir
    (out_dir / "vision").mkdir(parents=True, exist_ok=True)
    (out_dir / "fusion").mkdir(parents=True, exist_ok=True)

    results = []
    for p in sorted(args.affect_dir.glob("*_affect.json")):
        affect = json.loads(p.read_text(encoding="utf-8"))
        video_id = str(affect.get("video_id") or p.name.replace("_affect.json", ""))
        # Approximate duration from last claim timestamp
        segs = affect.get("segments") or []
        dur = 60.0
        if segs:
            dur = max(float(s.get("timestamp_sec") or 0.0) for s in segs) + 5.0
        vision = extract_vision_for_video(video_id, duration_sec=min(dur, 180.0))
        vpath = out_dir / "vision" / f"{video_id}_vision.json"
        vision.write_json(vpath)
        fused = build_fused_index(
            video_id=video_id,
            affect=affect,
            vision=vision.to_dict(),
            player_id=args.player_id,
        )
        fpath = write_fused_index(fused, out_dir / "fusion" / f"{video_id}_fused.json")
        results.append(
            {
                "video_id": video_id,
                "vision": str(vpath),
                "fusion": str(fpath),
                "n_arcs": len(fused.get("story_arcs") or []),
                "congruence": (fused.get("crossmodal") or {}).get("overall_congruence"),
            }
        )
        print(f"OK {video_id} arcs={results[-1]['n_arcs']} cong={results[-1]['congruence']}")

    man = out_dir / "fusion" / "fusion_manifest.json"
    man.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Wrote {man}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
