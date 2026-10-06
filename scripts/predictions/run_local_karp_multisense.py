#!/usr/bin/env python3
"""Local debug: claims pipeline + multi-sense sleeve for Karp CNBC clip.

Usage (from worktree root, conda env verityngn):

  set -a && source .env && set +a
  export PYTHONPATH=.
  export MULTISENSE_ENABLED=1
  # optional: MULTISENSE_OFFLINE=1 for proxy-only sleeve
  python scripts/run_local_karp_multisense.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

VIDEO_ID = os.environ.get("KARP_VIDEO_ID", "QNkPpVYagRc")
VIDEO_URL = os.environ.get(
    "KARP_VIDEO_URL", f"https://www.youtube.com/watch?v={VIDEO_ID}"
)
OUT_DIR = Path(
    os.environ.get(
        "KARP_OUT_DIR",
        str(ROOT / ".outputs" / f"karp_local_{VIDEO_ID}"),
    )
)


def _find_report_json(video_id: str, out_dir: Path, root: Path) -> Path | None:
    """Locate {video_id}_report.json in out_dir or timestamped outputs_debug."""
    candidates = [
        out_dir / f"{video_id}_report.json",
        out_dir / "report.json",
    ]
    debug_root = root / "outputs_debug" / video_id
    if debug_root.is_dir():
        # Prefer newest *_complete* then any report.json
        stamped = sorted(debug_root.glob("*_complete"), reverse=True)
        stamped += sorted(debug_root.glob("*"), reverse=True)
        for d in stamped:
            if d.is_dir():
                candidates.append(d / f"{video_id}_report.json")
    for p in candidates:
        if p.exists():
            return p
    return None


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    os.chdir(ROOT)

    # Prefer research .env key name for API-key Gemini clients
    if not os.environ.get("GOOGLE_API_KEY") and os.environ.get("VERITY_GEMINI_KEY"):
        os.environ["GOOGLE_API_KEY"] = os.environ["VERITY_GEMINI_KEY"]

    print(f"[karp-local] video={VIDEO_URL}")
    print(f"[karp-local] out={OUT_DIR}")
    print(f"[karp-local] MULTISENSE_ENABLED={os.environ.get('MULTISENSE_ENABLED')}")
    print(f"[karp-local] MULTISENSE_OFFLINE={os.environ.get('MULTISENSE_OFFLINE')}")

    skip_claims = os.environ.get("KARP_SKIP_CLAIMS", "0") in {"1", "true", "True"}
    report_path = Path(os.environ.get("KARP_REPORT_PATH", "")) if os.environ.get("KARP_REPORT_PATH") else None

    if not skip_claims and report_path is None:
        from verityngn.workflows.pipeline import run_verification

        result = run_verification(VIDEO_URL, out_dir_path=str(OUT_DIR))
        # API returns a dict; older docs showed a (state, out_dir) tuple.
        if isinstance(result, dict):
            out_dir = Path(result.get("output_dir") or OUT_DIR)
            print(
                f"[karp-local] claims done: video_id={result.get('video_id')} "
                f"claims={result.get('claims_count')}"
            )
        elif isinstance(result, (tuple, list)) and len(result) >= 2:
            out_dir = Path(result[1])
        else:
            out_dir = OUT_DIR
            print(f"[karp-local] WARN: unexpected run_verification return: {type(result)}")

        report_path = _find_report_json(VIDEO_ID, out_dir, ROOT)
    elif report_path is None:
        report_path = _find_report_json(VIDEO_ID, OUT_DIR, ROOT)

    if report_path is None or not report_path.exists():
        print(f"[karp-local] ERROR: no {VIDEO_ID}_report.json under out_dir / outputs_debug")
        return 2

    print(f"[karp-local] report ok: {report_path}")

    os.environ.setdefault("MULTISENSE_ENABLED", "1")
    from verityngn.services.fusion.run_multisense import run_multisense

    media = OUT_DIR / "media" / f"{VIDEO_ID}.mp4"
    manifest = run_multisense(
        VIDEO_ID,
        report_path,
        youtube_url=VIDEO_URL,
        video_source=str(media) if media.exists() else None,
        audio_path=media if media.exists() else None,
        out_dir=OUT_DIR,
        force=True,
        offline=os.environ.get("MULTISENSE_OFFLINE", "0") in {"1", "true", "True"},
    )
    man_path = OUT_DIR / f"{VIDEO_ID}_local_run_manifest.json"
    man_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[karp-local] multisense manifest:\n{json.dumps(manifest, indent=2)}")
    print(f"[karp-local] wrote {man_path}")
    return 0 if not manifest.get("skipped") else 1


if __name__ == "__main__":
    raise SystemExit(main())
