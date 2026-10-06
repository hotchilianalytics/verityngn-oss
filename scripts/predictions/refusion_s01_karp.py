#!/usr/bin/env python3
"""Re-fuse S01 on Karp local dirs from existing affect + gemini JSON.

Vision is omitted (never fill sympathetic_arousal=0.5). Does not call Gemini.
Stamps overall_congruence onto the corpus report videos[].

Usage:
  PYTHONPATH=. python scripts/refusion_s01_karp.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

VIDEO_IDS = [
    "QNkPpVYagRc",
    "dRgPbNJ5RJc",
    "V7mYWOzdhpc",
    "ijRuuaaM6XM",
    "xe84cwQJKaE",
    "WBu9Ai6OX3I",
    "pHu-FarYZlU",
]

from verityngn.services.fusion.schema import build_fused_index, write_fused_index
from verityngn.services.quant.nuisance import residualize_rows
from verityngn.services.quant.signal_quality import nuisance_leak


def main() -> int:
    os.chdir(ROOT)
    rows = []
    results = {}
    for vid in VIDEO_IDS:
        out_dir = ROOT / ".outputs" / f"karp_local_{vid}"
        affect_p = out_dir / f"{vid}_affect.json"
        ms_p = out_dir / f"{vid}_multisense.json"
        if not affect_p.exists() or not ms_p.exists():
            print(f"[refusion] skip {vid}: missing affect or multisense")
            results[vid] = {"skipped": True}
            continue
        affect = json.loads(affect_p.read_text(encoding="utf-8"))
        gemini = json.loads(ms_p.read_text(encoding="utf-8"))
        # Prefer measured vision when present (T018 MediaPipe); else omit (never 0.5-fill).
        vision = {}
        vis_p = out_dir / f"{vid}_vision.json"
        if vis_p.exists():
            vis = json.loads(vis_p.read_text(encoding="utf-8"))
            backend = ((vis.get("summary") or {}).get("backend") or {})
            src = (vis.get("summary") or {}).get("vision_source") or ""
            real = bool(backend.get("mediapipe") or backend.get("pyfeat") or src.startswith("mediapipe"))
            ar = (vis.get("summary") or {}).get("sympathetic_arousal")
            if not (real and ar is not None):
                vision = {}
            else:
                vision = vis
        fused = build_fused_index(
            video_id=vid,
            affect=affect,
            vision=vision,
            gemini=gemini,
            player_id="ceo_pltr_karp",
        )
        write_fused_index(fused, out_dir / f"{vid}_fused_index.json")
        cm = fused.get("crossmodal") or {}
        cong = cm.get("overall_congruence")
        segs = cm.get("segments") or []
        missing = {}
        for s in segs:
            for ch in s.get("missing_channels") or []:
                missing[ch] = missing.get(ch, 0) + 1
        n_claims = len(affect.get("segments") or [])
        results[vid] = {
            "overall_congruence": cong,
            "n_segments": len(segs),
            "n_claims": n_claims,
            "channels_policy": cm.get("channels_policy"),
            "missing_channel_counts": missing,
            "live_gemini": (gemini.get("summary") or {}).get("live_gemini"),
        }
        rows.append(
            {
                "video_id": vid,
                "s01_congruence": cong,
                "n_claims": n_claims,
                "n_segments": n_claims,
                "duration_sec": None,
                "days_to_print": None,
            }
        )
        print(f"[refusion] {vid} S01={cong} n_claims={n_claims} missing={missing}")

    leak_raw = nuisance_leak(rows, factor_key="s01_congruence")
    resid = residualize_rows(rows, factor_key="s01_congruence")
    leak_res = nuisance_leak(resid, factor_key="s01_resid")
    payload = {
        "trial": os.environ.get("KARP_TRIAL", "T016"),
        "videos": results,
        "nuisance_leak_raw": leak_raw,
        "nuisance_leak_resid": leak_res,
    }
    dest = ROOT / ".outputs" / "t016_s01_refusion.json"
    dest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[refusion] raw leak {leak_raw['max_abs']} resid {leak_res['max_abs']}")
    print(f"[refusion] wrote {dest}")

    corpus = ROOT / ".outputs" / "ceo_pltr_karp_corpus" / "ceo_pltr_karp_signal_report.json"
    if corpus.exists():
        report = json.loads(corpus.read_text(encoding="utf-8"))
        live_qnk = ROOT / ".outputs" / "live_gemini_compare_QNkPpVYagRc" / "compare.json"
        qnk_live = False
        if live_qnk.exists():
            live = json.loads(live_qnk.read_text(encoding="utf-8"))
            qnk_live = bool(live.get("live_gemini_true")) or bool(
                (live.get("live") or {}).get("live_gemini")
            )
        for v in report.get("videos") or []:
            if not isinstance(v, dict):
                continue
            vid = str(v.get("video_id") or "")
            st = results.get(vid) or {}
            if st.get("overall_congruence") is not None:
                v["overall_congruence"] = st["overall_congruence"]
                v["s01_congruence"] = st["overall_congruence"]
            if vid == "QNkPpVYagRc" and qnk_live:
                v["live_gemini"] = True
        report["trial"] = os.environ.get("KARP_TRIAL", "T016")
        corpus.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"[refusion] stamped {corpus}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
