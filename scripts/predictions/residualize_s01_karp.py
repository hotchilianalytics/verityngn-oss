#!/usr/bin/env python3
"""Residualize S01 on n_claims/duration and re-score NuisanceLeak + L.

Does not add CEOs. Writes data/predictions/quant/signal_quality_resid.json
and stamps s01_congruence_resid onto the corpus report when present.

Usage:
  PYTHONPATH=. python scripts/residualize_s01_karp.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.score_signal_quality import _count_trials, rows_from_report, sidecar_for_video
from verityngn.services.quant.nuisance import residualize_rows
from verityngn.services.quant.signal_quality import nuisance_leak, score_signal_quality


def main() -> int:
    corpus = ROOT / ".outputs" / "ceo_pltr_karp_corpus" / "ceo_pltr_karp_signal_report.json"
    if not corpus.exists():
        print(f"missing {corpus}")
        return 1
    report = json.loads(corpus.read_text(encoding="utf-8"))
    earnings_path = ROOT / ".outputs" / "ceo_pltr_karp_corpus" / "karp_earnings_effect.json"
    if not earnings_path.exists():
        earnings_path = ROOT / ".outputs" / "karp_earnings_effect.json"
    earnings = None
    if earnings_path.exists():
        earnings = json.loads(earnings_path.read_text(encoding="utf-8"))

    rows = rows_from_report(report, earnings)
    for r in rows:
        vid = str(r.get("video_id") or "")
        side = sidecar_for_video(ROOT, vid)
        r.update({k: v for k, v in side.items() if v is not None and v != ""})
        # Prefer vision stamps already on report videos
        for v in report.get("videos") or []:
            if str(v.get("video_id") or "") != vid:
                continue
            if v.get("vision_source"):
                r["vision_source"] = v["vision_source"]
            if v.get("sympathetic_arousal") is not None:
                r["sympathetic_arousal"] = v["sympathetic_arousal"]
            if v.get("live_gemini") is True:
                r["live_gemini"] = True
                r["gemini_source"] = "gemini"

    leak_raw = nuisance_leak(rows, factor_key="s01_congruence")
    resid_rows = residualize_rows(
        rows,
        factor_key="s01_congruence",
        nuisance_keys=("n_claims", "duration_sec", "days_to_print"),
    )
    leak_res = nuisance_leak(resid_rows, factor_key="s01_congruence_resid")

    n_trials = _count_trials(ROOT / "docs" / "trials_ledger.md")
    n_events = sum(1 for r in rows if r.get("car_h1") is not None)
    scored_raw = score_signal_quality(
        rows,
        factor_key="s01_congruence",
        n_events=n_events or None,
        n_trials=n_trials,
    )
    scored_resid = score_signal_quality(
        resid_rows,
        factor_key="s01_congruence_resid",
        n_events=n_events or None,
        n_trials=n_trials,
    )

    # For resid L, swap factor rows that have resid into the scorer's view of leak
    payload = {
        "trial": "T019",
        "promote": "NO_PROMOTE",
        "nuisance_leak_raw": leak_raw,
        "nuisance_leak_resid": leak_res,
        "score_raw": scored_raw,
        "score_on_resid_factor": scored_resid,
        "note": (
            "Residualized S01 may enter a market test only after leak < 0.20 and "
            "Fidelity ≥ 0.60. Raw stays on the panel for QA. Do not add CEOs to fix leak."
        ),
        "rows": [
            {
                "video_id": r.get("video_id"),
                "s01_congruence": r.get("s01_congruence"),
                "s01_congruence_resid": r.get("s01_congruence_resid"),
                "n_claims": r.get("n_claims"),
                "n_segments": r.get("n_segments"),
                "duration_sec": r.get("duration_sec"),
                "days_to_print": r.get("days_to_print"),
                "venue": r.get("venue"),
                "live_gemini": r.get("live_gemini"),
                "vision_source": r.get("vision_source"),
                "sympathetic_arousal": r.get("sympathetic_arousal"),
            }
            for r in resid_rows
        ],
    }
    out = ROOT / "data" / "predictions" / "quant" / "signal_quality_resid.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({
        "leak_raw": leak_raw.get("max_abs"),
        "leak_resid": leak_res.get("max_abs"),
        "L_raw": scored_raw.get("L"),
        "L_resid_factor": scored_resid.get("L"),
        "fidelity": scored_raw.get("fidelity"),
        "wrote": str(out),
    }, indent=2))

    # Stamp resid onto corpus videos
    by_vid = {str(r.get("video_id")): r for r in resid_rows}
    for v in report.get("videos") or []:
        if not isinstance(v, dict):
            continue
        st = by_vid.get(str(v.get("video_id") or ""))
        if not st:
            continue
        if st.get("s01_congruence_resid") is not None:
            v["s01_congruence_resid"] = st["s01_congruence_resid"]
    report["nuisance_leak_raw"] = leak_raw.get("max_abs")
    report["nuisance_leak_resid"] = leak_res.get("max_abs")
    corpus.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
