#!/usr/bin/env python3
"""Re-run ONE video live vs offline_proxy and diff live_gemini + S01.

Requires MULTISENSE_ENABLED=1, credentials, MULTISENSE_OFFLINE unset.
Does not peek any CAR. Register trial T013 (or next free) before a market join.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from verityngn.services.fusion.run_multisense import run_multisense


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--video-id", default="QNkPpVYagRc")
    ap.add_argument("--report", type=Path, default=None)
    ap.add_argument("--out-dir", type=Path, default=None)
    args = ap.parse_args()
    vid = args.video_id
    report = args.report
    if report is None:
        local = ROOT / ".outputs" / f"karp_local_{vid}"
        for name in (f"{vid}_final_report.json", f"{vid}_report.json", f"{vid}_report_with_delivery.json"):
            cand = local / name
            if cand.exists():
                report = cand
                break
    if report is None or not Path(report).exists():
        # Prefer final_report over delivery/signal sidecars
        cands = sorted(
            (ROOT / ".outputs").glob(f"**/karp_local_{vid}/{vid}_final_report.json")
        ) or sorted((ROOT / ".outputs").glob(f"**/{vid}_final_report.json"))
        if not cands:
            cands = [
                p
                for p in (ROOT / ".outputs").glob(f"**/{vid}*report*.json")
                if "signal_report" not in p.name and "compare" not in str(p)
            ]
        if not cands:
            print(f"no report for {vid}")
            return 1
        report = cands[0]
    report = Path(report)
    print(f"[live_gemini] using report {report}")
    off_dir = args.out_dir or (ROOT / ".outputs" / f"live_gemini_compare_{vid}")
    off = off_dir / "offline"
    live = off_dir / "live"
    off.mkdir(parents=True, exist_ok=True)
    live.mkdir(parents=True, exist_ok=True)

    os.environ["MULTISENSE_ENABLED"] = "1"
    os.environ["MULTISENSE_OFFLINE"] = "1"
    m_off = run_multisense(vid, report, force=True, offline=True, out_dir=off)
    os.environ.pop("MULTISENSE_OFFLINE", None)
    m_live = run_multisense(vid, report, force=True, offline=False, out_dir=live)

    def _lg(manifest):
        ms_path = manifest.get("multisense")
        if not ms_path:
            return None, None
        doc = json.loads(Path(ms_path).read_text(encoding="utf-8"))
        return (doc.get("summary") or {}).get("live_gemini"), (doc.get("summary") or {}).get("source")

    lg_off, src_off = _lg(m_off)
    lg_live, src_live = _lg(m_live)
    summary = {
        "video_id": vid,
        "offline": {"live_gemini": lg_off, "source": src_off, "congruence": m_off.get("crossmodal_overall_congruence")},
        "live": {"live_gemini": lg_live, "source": src_live, "congruence": m_live.get("crossmodal_overall_congruence")},
        "live_gemini_true": bool(lg_live) is True,
    }
    (off_dir / "compare.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if not summary["live_gemini_true"]:
        print("live_gemini stayed False — check credentials, MULTISENSE_OFFLINE, and video URI")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
