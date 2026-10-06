#!/usr/bin/env python3
"""Run claims+MULTISENSE for the five pre-print Karp videos, then rollup + T010."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "docs" / "karp_pre_earnings_videos.json"


def main() -> int:
    os.chdir(ROOT)
    cat = json.loads(CATALOG.read_text(encoding="utf-8"))
    videos = cat["run_five"]
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", ".")
    env.setdefault("MULTISENSE_ENABLED", "1")
    failed = []
    for item in videos:
        vid = item["video_id"]
        out = ROOT / ".outputs" / f"karp_local_{vid}"
        report = out / "ceo_pltr_karp_signal_report.json"
        fused = out / f"{vid}_fused_index.json"
        if fused.exists() and env.get("KARP_FORCE", "0") not in {"1", "true"}:
            print(f"[batch] skip {vid} (fused exists)")
            continue
        print(f"[batch] === {vid} recorded={item.get('recorded')} next={item.get('next_print')} ===")
        env["KARP_VIDEO_ID"] = vid
        env["KARP_VIDEO_URL"] = item.get("source") or f"https://www.youtube.com/watch?v={vid}"
        env["KARP_OUT_DIR"] = str(out)
        rc = subprocess.call([sys.executable, "scripts/run_local_karp_multisense.py"], env=env, cwd=str(ROOT))
        if rc != 0:
            print(f"[batch] FAIL {vid} rc={rc}")
            failed.append(vid)
            continue
        print(f"[batch] ok {vid}")
    dirs = [ROOT / ".outputs" / "karp_local_QNkPpVYagRc", ROOT / ".outputs" / "karp_local_dRgPbNJ5RJc"]
    for item in videos:
        d = ROOT / ".outputs" / f"karp_local_{item['video_id']}"
        if (d / f"{item['video_id']}_fused_index.json").exists() or (d / f"{item['video_id']}_multisense.json").exists():
            dirs.append(d)
    cmd = [sys.executable, "scripts/build_karp_signal_report.py", "--corpus-dirs", *[str(p) for p in dirs],
           "--out-dir", str(ROOT / ".outputs" / "ceo_pltr_karp_corpus")]
    print("[batch] rollup", cmd[-len(dirs) - 2 :])
    subprocess.call(cmd, env=env, cwd=str(ROOT))
    subprocess.call([sys.executable, "scripts/karp_earnings_effect.py"], env=env, cwd=str(ROOT))
    if failed:
        print("[batch] failed videos:", failed)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
