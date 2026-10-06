#!/usr/bin/env python3
"""T018 — MediaPipe Face Landmarker on Karp local mp4s.

Register T018 in docs/trials_ledger.md BEFORE scoring.

Runs Face Landmarker on local media, writes {vid}_vision.json, refuses to fuse
synthetic vision, rebuilds S01 with real face terms when coverage is ok, stamps
HFAsy_proxy + vision_source onto the corpus report.

Preferred talking-heads: QNkPpVYagRc, WBu9Ai6OX3I, pHu-FarYZlU.
ijRuuaaM6XM is the two-shot coverage-fail test.

Usage:
  PYTHONPATH=. python scripts/run_mediapipe_karp.py
  PYTHONPATH=. python scripts/run_mediapipe_karp.py --video-id WBu9Ai6OX3I
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

from verityngn.services.fusion.schema import build_fused_index, write_fused_index
from verityngn.services.quant.nuisance import residualize_rows
from verityngn.services.quant.signal_quality import nuisance_leak
from verityngn.services.vision.adapters.mediapipe import VISION_SOURCE, try_face_landmarker
from verityngn.services.vision.extract import extract_vision_for_video

PREFERRED = ["QNkPpVYagRc", "WBu9Ai6OX3I", "pHu-FarYZlU"]
COVERAGE_FAIL_TEST = "ijRuuaaM6XM"
DEFAULT_VIDEOS = PREFERRED + [COVERAGE_FAIL_TEST]


def _find_mp4(vid: str) -> Path | None:
    media = ROOT / ".outputs" / f"karp_local_{vid}" / "media"
    if not media.exists():
        return None
    for p in sorted(media.glob("*.mp4")):
        return p
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--video-id", action="append", dest="video_ids")
    ap.add_argument("--sample-fps", type=float, default=2.0)
    ap.add_argument("--max-frames", type=int, default=400)
    args = ap.parse_args()
    vids = args.video_ids or DEFAULT_VIDEOS
    os.chdir(ROOT)

    results: dict[str, dict] = {}
    rows = []
    for vid in vids:
        mp4 = _find_mp4(vid)
        out_dir = ROOT / ".outputs" / f"karp_local_{vid}"
        out_dir.mkdir(parents=True, exist_ok=True)
        if mp4 is None:
            print(f"[t018] skip {vid}: no local mp4")
            results[vid] = {"skipped": True, "reason": "no_mp4"}
            continue

        print(f"[t018] {vid} ← {mp4.name}")
        # Direct landmarker call (also exercised via extract_vision_for_video)
        mp = try_face_landmarker(
            mp4,
            video_id=vid,
            sample_fps=args.sample_fps,
            max_frames=args.max_frames,
        )
        vis = extract_vision_for_video(vid, video_path=mp4, run_authenticity_with_rppg=False)
        vis_path = out_dir / f"{vid}_vision.json"
        # Stamp mediapipe block onto summary if extract path missed it
        if mp and not (vis.summary or {}).get("mediapipe"):
            vis.summary["mediapipe"] = mp
            if mp.get("status") == "ok":
                vis.summary["sympathetic_arousal"] = mp.get("sympathetic_arousal")
                vis.summary["valence"] = mp.get("valence")
                vis.summary["arousal"] = mp.get("arousal")
                vis.summary["hfasy_proxy"] = mp.get("hfasy_proxy")
                vis.summary["face_coverage"] = mp.get("face_coverage")
                vis.summary["vision_source"] = VISION_SOURCE
                vis.summary.setdefault("backend", {})["mediapipe"] = True
        vis.write_json(vis_path)

        mp_sum = (vis.summary or {}).get("mediapipe") or mp or {}
        ok = mp_sum.get("status") == "ok" and float(mp_sum.get("face_coverage") or 0) >= 0.25
        vision_dict = vis.to_dict() if ok else {}

        affect_p = out_dir / f"{vid}_affect.json"
        ms_p = out_dir / f"{vid}_multisense.json"
        cong = None
        n_claims = None
        if affect_p.exists() and ms_p.exists() and vision_dict:
            affect = json.loads(affect_p.read_text(encoding="utf-8"))
            gemini = json.loads(ms_p.read_text(encoding="utf-8"))
            fused = build_fused_index(
                video_id=vid,
                affect=affect,
                vision=vision_dict,
                gemini=gemini,
                player_id="ceo_pltr_karp",
            )
            write_fused_index(fused, out_dir / f"{vid}_fused_index.json")
            cong = (fused.get("crossmodal") or {}).get("overall_congruence")
            n_claims = len(affect.get("segments") or [])
            print(f"[t018] {vid} fused S01={cong} face_cov={mp_sum.get('face_coverage')} HFAsy={mp_sum.get('hfasy_proxy')}")
        elif not ok:
            print(
                f"[t018] {vid} coverage-fail status={mp_sum.get('status')} "
                f"cov={mp_sum.get('face_coverage')} multi={mp_sum.get('multi_face_frame_share')}"
            )

        results[vid] = {
            "mp4": str(mp4),
            "vision_source": VISION_SOURCE if ok else "",
            "status": mp_sum.get("status"),
            "face_coverage": mp_sum.get("face_coverage"),
            "multi_face_frame_share": mp_sum.get("multi_face_frame_share"),
            "hfasy_proxy": mp_sum.get("hfasy_proxy"),
            "sympathetic_arousal": mp_sum.get("sympathetic_arousal") if ok else None,
            "valence": mp_sum.get("valence") if ok else None,
            "s01_congruence": cong,
            "n_claims": n_claims,
            "fused": bool(vision_dict),
            "caveat": mp_sum.get("caveat"),
        }
        if cong is not None:
            rows.append(
                {
                    "video_id": vid,
                    "s01_congruence": cong,
                    "n_claims": n_claims,
                    "n_segments": n_claims,
                    "duration_sec": mp_sum.get("duration_sec"),
                    "days_to_print": None,
                    "vision_source": VISION_SOURCE,
                    "sympathetic_arousal": mp_sum.get("sympathetic_arousal"),
                }
            )

    leak_raw = nuisance_leak(rows, factor_key="s01_congruence") if len(rows) >= 3 else {"max_abs": None}
    resid = residualize_rows(rows, factor_key="s01_congruence") if rows else []
    leak_res = (
        nuisance_leak(resid, factor_key="s01_congruence_resid") if len(resid) >= 3 else {"max_abs": None}
    )
    payload = {
        "trial": "T018",
        "promote": "NO_PROMOTE",
        "videos": results,
        "nuisance_leak_raw": leak_raw,
        "nuisance_leak_resid": leak_res,
        "disclaimer": (
            "HFAsy_proxy is blendshape L/R L1 — not Banker CNN HFAsy. "
            "Congruence / delivery-risk only. NO_PROMOTE."
        ),
    }
    dest = ROOT / ".outputs" / "t018_mediapipe_face.json"
    dest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[t018] wrote {dest}")

    # Stamp corpus report when present
    corpus = ROOT / ".outputs" / "ceo_pltr_karp_corpus" / "ceo_pltr_karp_signal_report.json"
    if corpus.exists():
        report = json.loads(corpus.read_text(encoding="utf-8"))
        for v in report.get("videos") or []:
            if not isinstance(v, dict):
                continue
            vid = str(v.get("video_id") or "")
            st = results.get(vid) or {}
            if st.get("s01_congruence") is not None:
                v["overall_congruence"] = st["s01_congruence"]
                v["s01_congruence"] = st["s01_congruence"]
            if st.get("vision_source"):
                v["vision_source"] = st["vision_source"]
                v["sympathetic_arousal"] = st.get("sympathetic_arousal")
                v["hfasy_proxy"] = st.get("hfasy_proxy")
                v["face_coverage"] = st.get("face_coverage")
        report["trial"] = "T018"
        report["promote"] = "NO_PROMOTE"
        corpus.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"[t018] stamped {corpus}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
