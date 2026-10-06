#!/usr/bin/env python3
"""Compute signal-quality loss L on a Karp (or any player) corpus panel.

Register the trial in docs/trials_ledger.md BEFORE running against a new config.

Reads:
  --report  player risk-panel JSON (ceo_*_signal_report.json)
  --earnings  optional T010 karp_earnings_effect.json (for n_with_car)
  --trials  docs/trials_ledger.md (count Txxx rows)

Writes data/predictions/quant/signal_quality.json by default.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from verityngn.services.quant.signal_quality import score_signal_quality


VENUE_HINTS = {
    "davos": "davos",
    "wef": "wef",
    "cnbc": "cnbc",
    "squawk": "cnbc",
    "power lunch": "cnbc",
}


def _count_trials(ledger: Path) -> int:
    text = ledger.read_text(encoding="utf-8")
    labels = re.findall(r"\|\s*T\d+[a-z]?\s*\|", text)
    return max(len(labels), 1)


def _venue(title: str, note: str = "") -> str:
    blob = f"{title} {note}".lower()
    for k, v in VENUE_HINTS.items():
        if k in blob:
            return v
    return "other"


def sidecar_for_video(root: Path, vid: str) -> dict[str, Any]:
    """Read measured-lane tags from local affect / live-gemini sidecars."""
    out: dict[str, Any] = {}
    if not vid:
        return out
    affect_path = root / ".outputs" / f"karp_local_{vid}" / f"{vid}_affect.json"
    if affect_path.exists():
        try:
            affect = json.loads(affect_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            affect = {}
        summary = affect.get("summary") or {}
        asr = str(summary.get("asr_source") or "")
        if asr:
            out["asr_source"] = asr
            # Only credit audio tags from runs that also had ASR (T014+). Older
            # affect.json files tagged audeering_wav2vec2 without torch/whisper.
            segs = [s for s in (affect.get("segments") or []) if isinstance(s, dict)]
            sources = [str(s.get("measured_affect_source") or "") for s in segs]
            sources = [s for s in sources if s]
            if sources:
                out["audio_source"] = Counter(sources).most_common(1)[0][0]
    live_path = root / ".outputs" / f"live_gemini_compare_{vid}" / "compare.json"
    if live_path.exists():
        try:
            live = json.loads(live_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            live = {}
        live_ok = bool(live.get("live_gemini_true")) or bool((live.get("live") or {}).get("live_gemini"))
        if live_ok:
            out["live_gemini"] = True
            out["gemini_source"] = "gemini"
    return out


def rows_from_report(report: dict[str, Any], earnings: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
    earn_by_vid: dict[str, dict[str, Any]] = {}
    if earnings:
        for r in earnings.get("rows") or []:
            if r.get("video_id"):
                earn_by_vid[str(r["video_id"])] = r

    videos = report.get("videos") or report.get("video_rows") or []
    if not videos:
        # corpus report shape: analyses-like records
        videos = report.get("per_video") or []

    rows: list[dict[str, Any]] = []
    for v in videos:
        if not isinstance(v, dict):
            continue
        vid = str(v.get("video_id") or v.get("id") or "")
        e = earn_by_vid.get(vid, {})
        title = str(v.get("title") or v.get("venue") or "")
        n_claims = v.get("n_claims") or v.get("claims")
        s01 = (
            v.get("s01_congruence")
            or v.get("overall_congruence")
            or v.get("congruence")
            or e.get("s01_congruence")
        )
        rows.append(
            {
                "video_id": vid,
                "s01_congruence": s01,
                "n_claims": n_claims,
                "duration_sec": v.get("duration_sec"),
                "n_segments": v.get("n_segments") or n_claims,
                "days_to_print": v.get("days_to_print"),
                "venue": v.get("venue") or _venue(title, str(v.get("note") or "")),
                "live_gemini": v.get("live_gemini"),
                "audio_source": v.get("audio_source") or v.get("measured_affect_source") or "prosody_proxy",
                "gemini_source": "gemini" if v.get("live_gemini") else "offline_proxy",
                "vision_source": v.get("vision_source") or "",
                "asr_source": v.get("asr_source") or "",
                "sympathetic_arousal": v.get("sympathetic_arousal"),
                "car_h1": e.get("car_h1"),
            }
        )
        side = sidecar_for_video(ROOT, vid)
        row = rows[-1]
        if side.get("audio_source") and (
            not row["audio_source"] or row["audio_source"] in {"prosody_proxy", "missing_audio", ""}
            or side["audio_source"] == "audeering_wav2vec2"
        ):
            row["audio_source"] = side["audio_source"]
        if side.get("asr_source"):
            row["asr_source"] = side["asr_source"]
        if side.get("live_gemini") is True:
            row["live_gemini"] = True
            row["gemini_source"] = "gemini"

    if not rows and report.get("signals"):
        # fall back: one rolled row — insufficient for leak, still scores fidelity
        live = False
        n = int(report.get("n_videos") or 0)
        s01 = None
        for s in report.get("signals") or []:
            if str(s.get("id") or "").startswith("S01") and isinstance(s.get("value"), (int, float)):
                s01 = float(s["value"])
        rows.append(
            {
                "video_id": "corpus",
                "s01_congruence": s01,
                "n_claims": None,
                "duration_sec": None,
                "n_segments": None,
                "days_to_print": None,
                "venue": "corpus",
                "live_gemini": live,
                "audio_source": "prosody_proxy",
                "gemini_source": "offline_proxy",
                "vision_source": "",
                "asr_source": "",
                "sympathetic_arousal": None,
                "car_h1": None,
                "n_videos": n,
            }
        )
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--report",
        type=Path,
        default=ROOT / ".outputs" / "ceo_pltr_karp_corpus" / "ceo_pltr_karp_signal_report.json",
    )
    ap.add_argument(
        "--earnings",
        type=Path,
        default=ROOT / ".outputs" / "ceo_pltr_karp_corpus" / "karp_earnings_effect.json",
    )
    ap.add_argument("--trials", type=Path, default=ROOT / "docs" / "trials_ledger.md")
    ap.add_argument("--out", type=Path, default=ROOT / "data" / "predictions" / "quant" / "signal_quality.json")
    ap.add_argument("--icir", type=float, default=None)
    args = ap.parse_args()

    report = json.loads(args.report.read_text(encoding="utf-8")) if args.report.exists() else {}
    earnings = json.loads(args.earnings.read_text(encoding="utf-8")) if args.earnings.exists() else None
    n_trials = _count_trials(args.trials) if args.trials.exists() else 13

    rows = rows_from_report(report, earnings)
    # Enrich n_claims from corpus table if present
    if not any(r.get("n_claims") for r in rows):
        # md-derived fallback from known Karp snapshot lives in videos list with "claims"
        pass

    summary = (earnings or {}).get("summary") or {}
    n_events = summary.get("n_with_car")
    scored = score_signal_quality(
        rows,
        n_events=int(n_events) if n_events is not None else None,
        n_trials=n_trials,
        icir=args.icir,
    )
    scored["n_rows"] = len(rows)
    scored["source_report"] = str(args.report)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(scored, indent=2), encoding="utf-8")
    print(json.dumps(scored, indent=2))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
