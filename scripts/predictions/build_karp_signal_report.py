#!/usr/bin/env python3
"""Synthesize Karp multimodal outputs into a longitudinal-ready signal report.

Reads QNkPpVYagRc_multisense / _affect / _fused_index (+ optional claims report)
and writes {player_id}_signal_report.{json,html,md} plus chart PNGs.

Congruence / conviction / delivery-risk only — not a lie detector.
"""
from __future__ import annotations

import argparse
import base64
import json
import math
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from verityngn.services.fusion.derailment import score_derailment
DEFAULT_IN = ROOT / ".outputs" / "karp_local_QNkPpVYagRc"
DEFAULT_PLAYER_ID = "ceo_pltr_karp"
PLAYER_ID = DEFAULT_PLAYER_ID  # overridden by --player-id in main()
VIDEO_ID = "QNkPpVYagRc"
YOUTUBE_URL = f"https://www.youtube.com/watch?v={VIDEO_ID}"

DISCLAIMER = (
    "Congruence / conviction / delivery-risk factors for markets research. "
    "Not a lie detector, clinical diagnosis, or veracity judgment. "
    "Not for employment, HR, or education screening (EU AI Act Art. 5(1)(f)). "
    "n=1 video; no cross-speaker norms. Values accumulate as more Karp videos land."
)

def report_stem(player_id: str | None = None) -> str:
    return f"{player_id or PLAYER_ID}_signal_report"


TOPIC_GEO_CUT_SEC = 530.0  # CNBC QNkPpVYagRc observed affect split (fallback)
GEO_KEYWORDS = (
    "israel", "gaza", "october", "terror", "west", "war", "china", "ukraine",
    "defense", "military", "nato", "hamas", "idf",
)
BIZ_KEYWORDS = (
    "palantir", "bootcamp", "aip", "revenue", "profit", "customer", "software",
    "commercial", "enterprise", "platform", "ai", "valuation", "stock",
)


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_float(x: Any, default: float | None = None) -> float | None:
    if x is None:
        return default
    try:
        v = float(x)
    except (TypeError, ValueError):
        return default
    if math.isnan(v) or math.isinf(v):
        return default
    return v


def _band_congruence(v: float) -> str:
    if v >= 0.75:
        return "high"
    if v >= 0.55:
        return "moderate"
    return "low"


def _is_question_style(style: str | None) -> bool:
    s = (style or "").lower()
    return any(w in s for w in ("question", "inquisitive", "probing", "clarifying", "follow-up"))


def _mid(seg: dict[str, Any]) -> float:
    return 0.5 * (float(seg.get("start_sec") or 0) + float(seg.get("end_sec") or 0))


def _dur(seg: dict[str, Any]) -> float:
    return max(0.1, float(seg.get("end_sec") or 0) - float(seg.get("start_sec") or 0))


def _claim_verdict(claim: dict[str, Any]) -> str:
    vr = claim.get("verification_result") or {}
    if isinstance(vr, dict):
        r = vr.get("result") or vr.get("verdict")
        if r:
            return str(r)
    return str(claim.get("initial_assessment") or "unknown")


def _topic_label(
    seg: dict[str, Any],
    *,
    local_blob: str,
    video_id: str,
) -> str:
    blob = " ".join(
        [
            str(seg.get("delivery_style") or ""),
            str(seg.get("vocal_emotion") or ""),
            local_blob,
        ]
    ).lower()
    geo_hit = any(k in blob for k in GEO_KEYWORDS)
    biz_hit = any(k in blob for k in BIZ_KEYWORDS)
    if geo_hit and not biz_hit:
        return "geopolitics"
    if biz_hit and not geo_hit:
        return "business"
    if video_id == "QNkPpVYagRc":
        return "geopolitics" if _mid(seg) < TOPIC_GEO_CUT_SEC else "business"
    emo = str(seg.get("vocal_emotion") or "").lower()
    if geo_hit and biz_hit:
        return "geopolitics" if emo in {"anger", "disgust", "fear"} else "business"
    if emo in {"anger", "disgust"}:
        return "geopolitics"
    if emo in {"trust", "anticipation", "joy"}:
        return "business"
    return "unlabeled"


def compute_signals(
    *,
    ms: dict[str, Any],
    affect: dict[str, Any],
    fused: dict[str, Any],
    claims: list[dict[str, Any]],
    video_id: str = VIDEO_ID,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    segs = [s for s in (ms.get("tier_a") or {}).get("segments") or [] if isinstance(s, dict)]
    tier_b = [b for b in (ms.get("tier_b") or []) if isinstance(b, dict)]
    cm = fused.get("crossmodal") or {}
    cm_segs = [s for s in (cm.get("segments") or []) if isinstance(s, dict)]
    aff_segs = [s for s in (affect.get("segments") or []) if isinstance(s, dict)]
    claim_by_id = {c.get("claim_id"): c for c in claims}

    arousals = [_safe_float(s.get("arousal"), 0.0) or 0.0 for s in segs]
    valences = [_safe_float(s.get("valence"), 0.0) or 0.0 for s in segs]
    a_vol = statistics.pstdev(arousals) if len(arousals) > 1 else 0.0
    v_vol = statistics.pstdev(valences) if len(valences) > 1 else 0.0

    q_ar, a_ar = [], []
    for s in segs:
        a = _safe_float(s.get("arousal"), 0.0) or 0.0
        if _is_question_style(s.get("delivery_style")):
            q_ar.append(a)
        else:
            a_ar.append(a)
    q_mean = statistics.mean(q_ar) if q_ar else None
    a_mean = statistics.mean(a_ar) if a_ar else None
    qa_delta = (a_mean - q_mean) if q_mean is not None and a_mean is not None else None

    geo, biz = [], []
    for s in segs:
        mid = _mid(s)
        near_ocr = []
        for b in tier_b:
            win = b.get("window") or {}
            csec = float(win.get("center_sec") or win.get("start_sec") or 0)
            if abs(csec - mid) <= 90:
                near_ocr.extend(b.get("ocr_on_screen") or [])
        near_claims = []
        for c in claims:
            # timestamp may be mm:ss
            t = c.get("timestamp")
            ts = None
            if isinstance(t, (int, float)):
                ts = float(t)
            elif isinstance(t, str) and ":" in t:
                parts = t.split(":")
                try:
                    ts = float(parts[-2]) * 60 + float(parts[-1]) if len(parts) >= 2 else float(parts[0])
                except ValueError:
                    ts = None
            if ts is not None and abs(ts - mid) <= 90:
                near_claims.append(str(c.get("claim_text") or ""))
        local_blob = " ".join(str(x) for x in near_ocr) + " " + " ".join(near_claims)
        label = _topic_label(s, local_blob=local_blob, video_id=video_id)
        if label == "geopolitics":
            geo.append(s)
        elif label == "business":
            biz.append(s)
    def _topic_stats(bucket: list[dict[str, Any]]) -> dict[str, Any]:
        if not bucket:
            return {"n": 0}
        emos: dict[str, float] = {}
        tot = 0.0
        ar, va = [], []
        for s in bucket:
            d = _dur(s)
            tot += d
            e = str(s.get("vocal_emotion") or "neutral").lower()
            emos[e] = emos.get(e, 0.0) + d
            ar.append(_safe_float(s.get("arousal"), 0.0) or 0.0)
            va.append(_safe_float(s.get("valence"), 0.0) or 0.0)
        top = max(emos, key=emos.get) if emos else None
        return {
            "n": len(bucket),
            "duration_sec": round(tot, 1),
            "dominant_emotion": top,
            "emotion_share": round(emos[top] / tot, 3) if top and tot else None,
            "arousal_mean": round(statistics.mean(ar), 3) if ar else None,
            "valence_mean": round(statistics.mean(va), 3) if va else None,
        }

    geo_s, biz_s = _topic_stats(geo), _topic_stats(biz)

    agreements = [s.get("interpreted_measured") or {} for s in cm_segs]
    ar_ag = [_safe_float(x.get("arousal_agreement")) for x in agreements]
    va_ag = [_safe_float(x.get("valence_agreement")) for x in agreements]
    im_ag = [_safe_float(x.get("interpreted_measured_congruence")) for x in agreements]
    ar_ag_f = [x for x in ar_ag if x is not None]
    va_ag_f = [x for x in va_ag if x is not None]
    im_ag_f = [x for x in im_ag if x is not None]

    z_ex = [_safe_float(s.get("z_exuberance"), 0.0) or 0.0 for s in cm_segs]
    z_range = (min(z_ex), max(z_ex)) if z_ex else (None, None)

    disf = [_safe_float((s.get("disfluency") or {}).get("rate"), 0.0) or 0.0 for s in aff_segs]
    disf_mean = statistics.mean(disf) if disf else 0.0

    pace_trans = 0
    high_pitch = 0
    prev_pace = None
    for s in segs:
        d = s.get("delivery") or {}
        pace = str(d.get("pace_band") or "moderate").split()[0]
        pitch = str(d.get("pitch_variability_band") or "moderate")
        if pitch == "high":
            high_pitch += 1
        if prev_pace and pace != prev_pace and {prev_pace, pace} & {"fast", "slow"}:
            pace_trans += 1
        prev_pace = pace
    high_pitch_share = high_pitch / len(segs) if segs else 0.0

    tb_scores = [_safe_float(b.get("congruence_score")) for b in tier_b]
    tb_scores_f = [x for x in tb_scores if x is not None]
    tb_mean = statistics.mean(tb_scores_f) if tb_scores_f else None

    overall_c = _safe_float(cm.get("overall_congruence"), 0.0) or 0.0
    risk_band = cm.get("overall_delivery_risk_band") or "unknown"

    couplings = []
    for s in cm_segs:
        cid = s.get("claim_id")
        claim = claim_by_id.get(cid) or {}
        couplings.append(
            {
                "claim_id": cid,
                "t_sec": s.get("t_sec"),
                "verdict": _claim_verdict(claim),
                "delivery_risk_band": s.get("delivery_risk_band"),
                "congruence": _safe_float(s.get("congruence")),
                "claim_text": (claim.get("claim_text") or "")[:160],
            }
        )
    all_low_risk = all((c.get("delivery_risk_band") or "low") == "low" for c in couplings) if couplings else False

    signals = [
        {
            "id": "S01_cross_channel_congruence",
            "name": "Cross-channel congruence index",
            "value": round(overall_c, 4),
            "band": _band_congruence(overall_c),
            "n_obs": 1,
            "video_id": video_id,
            "unit": "0..1",
            "method": "fusion.crossmodal.overall_congruence (text/voice/face + interpreted×measured)",
            "required_data": ["fused_index.crossmodal"],
            "this_video": {
                "overall_congruence": round(overall_c, 4),
                "delivery_risk_band": risk_band,
                "modality_divergence_rate": cm.get("modality_divergence_rate"),
            },
            "accumulates": "Per-speaker running mean and rolling 5-video z vs Karp baseline (not cross-CEO).",
        },
        {
            "id": "S02_interpreted_measured_agreement",
            "name": "Interpreted vs measured agreement",
            "value": round(statistics.mean(im_ag_f), 4) if im_ag_f else None,
            "band": "valence_gap" if va_ag_f and min(va_ag_f) < 0.55 else "aligned",
            "n_obs": 1,
            "video_id": video_id,
            "unit": "0..1",
            "method": "Per-claim arousal_agreement / valence_agreement from interpreted_measured block",
            "required_data": ["fused_index.crossmodal.segments.interpreted_measured", "affect", "gemini"],
            "this_video": {
                "interpreted_measured_congruence_mean": round(statistics.mean(im_ag_f), 4) if im_ag_f else None,
                "arousal_agreement_range": [round(min(ar_ag_f), 3), round(max(ar_ag_f), 3)] if ar_ag_f else None,
                "valence_agreement_range": [round(min(va_ag_f), 3), round(max(va_ag_f), 3)] if va_ag_f else None,
                "flag": "Valence agreement lags arousal — Gemini anger/negative vs prosody_proxy mildly positive.",
            },
            "accumulates": "Track valence-gap persistence; if it shrinks with real VAD, it is a sensor artifact.",
        },
        {
            "id": "S03_emotional_arc_volatility",
            "name": "Emotional arc volatility",
            "value": round(a_vol, 4),
            "band": "elevated" if a_vol >= 0.18 else "stable",
            "n_obs": 1,
            "video_id": video_id,
            "unit": "pstdev(arousal)",
            "method": "Population stdev of Tier A arousal and valence across speaking segments",
            "required_data": ["multisense.tier_a.segments"],
            "this_video": {
                "n_segments": len(segs),
                "arousal_pstdev": round(a_vol, 4),
                "valence_pstdev": round(v_vol, 4),
                "arousal_mean": round(statistics.mean(arousals), 3) if arousals else None,
                "valence_mean": round(statistics.mean(valences), 3) if valences else None,
            },
            "accumulates": "Compare volatility on prepared talks vs adversarial interviews.",
        },
        {
            "id": "S04_topic_affect_fingerprint",
            "name": "Topic-affect fingerprint",
            "value": {
                "geopolitics": geo_s.get("dominant_emotion"),
                "business": biz_s.get("dominant_emotion"),
            },
            "band": "split" if geo_s.get("dominant_emotion") != biz_s.get("dominant_emotion") else "uniform",
            "n_obs": 1,
            "video_id": video_id,
            "unit": "dominant emotion by topic window",
            "method": "Keyword tag OCR+claims (israel/war vs palantir/aip); CNBC time-cut fallback at 530s",
            "required_data": ["multisense.tier_a", "tier_b.ocr_on_screen", "claims"],
            "this_video": {"video_id": video_id, "geopolitics": geo_s, "business": biz_s},
            "accumulates": "Lock topic labels from OCR/claims; build Karp emotion-by-topic prior.",
        },
        {
            "id": "S05_qa_reactivity_delta",
            "name": "Q&A reactivity delta",
            "value": round(qa_delta, 4) if qa_delta is not None else None,
            "band": "reactive" if qa_delta is not None and qa_delta >= 0.25 else "flat",
            "n_obs": 1,
            "video_id": video_id,
            "unit": "arousal_answer − arousal_question",
            "method": "delivery_style containing question* vs remaining Karp-answer segments",
            "required_data": ["multisense.tier_a.delivery_style", "arousal"],
            "this_video": {
                "n_question_segs": len(q_ar),
                "n_answer_segs": len(a_ar),
                "question_arousal_mean": round(q_mean, 3) if q_mean is not None else None,
                "answer_arousal_mean": round(a_mean, 3) if a_mean is not None else None,
            },
            "accumulates": "Proxy for prepared-vs-pressured; compare earnings Q&A vs friendly long-form.",
        },
        {
            "id": "S06_exuberance_z_per_claim",
            "name": "Exuberance z-score per claim",
            "value": {
                "min": round(z_range[0], 3) if z_range[0] is not None else None,
                "max": round(z_range[1], 3) if z_range[1] is not None else None,
            },
            "band": "within_video",
            "n_obs": 1,
            "video_id": video_id,
            "unit": "z vs this-video mean",
            "method": "crossmodal z_exuberance from measured exuberance vs within-video baseline",
            "required_data": ["affect.exuberance", "fused_index.crossmodal"],
            "this_video": {
                "exuberance_mean": affect.get("summary", {}).get("exuberance_mean"),
                "per_claim": [
                    {"claim_id": s.get("claim_id"), "t_sec": s.get("t_sec"), "z_exuberance": _safe_float(s.get("z_exuberance"))}
                    for s in cm_segs
                ],
            },
            "accumulates": "Replace within-video z with longitudinal Karp z after ≥5 videos.",
        },
        {
            "id": "S07_disfluency_rate",
            "name": "Disfluency rate",
            "value": round(disf_mean, 4),
            "band": "floor",
            "n_obs": 1,
            "video_id": video_id,
            "unit": "rate 0..1",
            "method": "Text-token disfluency on claim strings (measured audio disfluency not yet fused)",
            "required_data": ["affect.disfluency"],
            "this_video": {
                "mean_rate": round(disf_mean, 4),
                "n_claims": len(aff_segs),
                "note": "Claim-text disfluency is a weak proxy; need ASR word-level um/uh.",
            },
            "accumulates": "ASR-level fillers will make this a real baseline; keep as anchor.",
        },
        {
            "id": "S08_pace_pitch_escalation",
            "name": "Pace / pitch escalation",
            "value": {
                "pace_transitions": pace_trans,
                "high_pitch_share": round(high_pitch_share, 3),
            },
            "band": "active" if high_pitch_share >= 0.2 else "calm",
            "n_obs": 1,
            "video_id": video_id,
            "unit": "count / share of segments",
            "method": "Tier A delivery.pace_band transitions into fast/slow; pitch_variability_band=high share",
            "required_data": ["multisense.tier_a.delivery"],
            "this_video": {
                "n_segments": len(segs),
                "pace_transitions_into_extreme": pace_trans,
                "high_pitch_segments": high_pitch,
                "high_pitch_share": round(high_pitch_share, 3),
            },
            "accumulates": "Map escalation to topic and to Q vs A turns.",
        },
        {
            "id": "S09_facial_vocal_verbal_alignment",
            "name": "Facial–vocal–verbal alignment (Tier B)",
            "value": round(tb_mean, 3) if tb_mean is not None else None,
            "band": "high" if tb_mean is not None and tb_mean >= 0.8 else "moderate",
            "n_obs": 1,
            "video_id": video_id,
            "unit": "Gemini congruence_score 0..1",
            "method": "Tier B clip deep-pass; observational face/gesture/voice vs spoken content",
            "required_data": ["multisense.tier_b"],
            "this_video": {
                "n_clips": len(tier_b),
                "mean_congruence": round(tb_mean, 3) if tb_mean is not None else None,
                "clips": [
                    {
                        "claim_ids": (b.get("window") or {}).get("claim_ids"),
                        "congruence_score": b.get("congruence_score"),
                        "facial_expression": (b.get("facial_expression") or "")[:180],
                        "ocr": (b.get("ocr_on_screen") or [])[:6],
                    }
                    for b in tier_b
                ],
            },
            "accumulates": "Replace prose face descriptions with measured AUs/gaze when py-feat is live.",
        },
        {
            "id": "S10_conviction_claim_coupling",
            "name": "Conviction–claim coupling",
            "value": {"all_low_delivery_risk": all_low_risk, "n_claims": len(couplings)},
            "band": "coupled_low_risk" if all_low_risk else "mixed",
            "n_obs": 1,
            "video_id": video_id,
            "unit": "verdict × delivery_risk_band",
            "method": "Join claims_breakdown.verification_result with fused delivery_risk_band",
            "required_data": ["claims report", "fused_index.crossmodal"],
            "this_video": {"rows": couplings},
            "accumulates": "Watch for TRUE claims with high delivery-risk (or the reverse) as Karp corpus grows.",
        },
    ]

    derail = score_derailment(segs, claims, tier_b=tier_b)
    d_mean = derail.get("mean_derailment")
    signals.append(
        {
            "id": "S11_discourse_derailment",
            "name": "Discourse derailment (expected vs actual Q&A)",
            "value": d_mean,
            "band": derail.get("band"),
            "n_obs": 1,
            "video_id": video_id,
            "unit": "0..1 (0=on-topic, 1=derailed)",
            "method": (
                "Krykoniuk et al. 2026 Discourser adapted to interview Q→A: "
                "LLM expected on-topic replies vs actual Karp answer "
                "(offline: 1−Jaccard). Cue only — not disinformation/deception."
            ),
            "required_data": ["multisense.tier_a.delivery_style", "claims near Q/A"],
            "this_video": {
                "n_pairs": derail.get("n_pairs"),
                "mean_derailment": d_mean,
                "max_derailment": derail.get("max_derailment"),
                "source": derail.get("source"),
                "cues": sorted({c for p in derail.get("pairs") or [] for c in (p.get("cues") or [])}),
            },
            "paper": derail.get("paper"),
            "accumulates": "Join pre-print S11 to next earnings surprise/CAR (T010). Never label a CEO as spreading disinfo.",
        }
    )

    derived = {
        "tier_a_segments": segs,
        "crossmodal_segments": cm_segs,
        "qa_delta": qa_delta,
        "geo": geo_s,
        "biz": biz_s,
        "ar_ag": ar_ag_f,
        "va_ag": va_ag_f,
    }
    return signals, derived


def render_charts(out_dir: Path, ms: dict[str, Any], fused: dict[str, Any], derived: dict[str, Any]) -> dict[str, Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    charts_dir = out_dir / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    segs = derived["tier_a_segments"]
    cm_segs = derived["crossmodal_segments"]

    # 1. Arousal + valence timeline
    fig, ax = plt.subplots(figsize=(10.5, 3.8))
    mids, ar, va, qmask = [], [], [], []
    for s in segs:
        mids.append(_mid(s) / 60.0)
        ar.append(_safe_float(s.get("arousal"), 0.0) or 0.0)
        va.append(_safe_float(s.get("valence"), 0.0) or 0.0)
        qmask.append(_is_question_style(s.get("delivery_style")))
    ax.plot(mids, ar, color="#c0392b", lw=1.8, label="Arousal (0–1)")
    ax.plot(mids, va, color="#2980b9", lw=1.8, label="Valence (−1–1)")
    for i, q in enumerate(qmask):
        if q:
            ax.axvspan(mids[i] - 0.05, mids[i] + 0.05, color="#bdc3c7", alpha=0.35, lw=0)
    ax.axvline(TOPIC_GEO_CUT_SEC / 60.0, color="#7f8c8d", ls="--", lw=1, label="Topic cut (~8.8 min)")
    ax.set_xlabel("Minutes")
    ax.set_ylabel("Score")
    ax.set_title("Tier A arousal / valence track (gray = interviewer-style questions)")
    ax.legend(loc="upper right", fontsize=8)
    ax.set_ylim(-1.05, 1.05)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    p = charts_dir / "arousal_valence_timeline.png"
    fig.savefig(p, dpi=140)
    plt.close(fig)
    paths["arousal_valence_timeline"] = p

    # 2. Per-claim congruence bars
    fig, ax = plt.subplots(figsize=(8.5, 3.6))
    labels = [f"c{s.get('claim_id')}\n{float(s.get('t_sec') or 0)/60:.1f}m" for s in cm_segs]
    cong = [_safe_float(s.get("congruence"), 0.0) or 0.0 for s in cm_segs]
    mult = [_safe_float(s.get("congruence_multiplier"), 0.0) or 0.0 for s in cm_segs]
    x = list(range(len(labels)))
    w = 0.38
    ax.bar([i - w / 2 for i in x], cong, w, color="#1abc9c", label="congruence")
    ax.bar([i + w / 2 for i in x], mult, w, color="#8e44ad", label="congruence_multiplier")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("0–1")
    ax.set_title("Per-claim cross-channel congruence")
    ax.legend(fontsize=8)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    p = charts_dir / "claim_congruence.png"
    fig.savefig(p, dpi=140)
    plt.close(fig)
    paths["claim_congruence"] = p

    # 3. Emotion distribution (duration-weighted)
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    weights: dict[str, float] = {}
    for s in segs:
        e = str(s.get("vocal_emotion") or "neutral").lower()
        weights[e] = weights.get(e, 0.0) + _dur(s)
    items = sorted(weights.items(), key=lambda kv: -kv[1])
    colors = {
        "anger": "#c0392b",
        "neutral": "#95a5a6",
        "trust": "#27ae60",
        "anticipation": "#f39c12",
        "disgust": "#8e44ad",
        "fear": "#2c3e50",
        "joy": "#f1c40f",
        "sadness": "#3498db",
        "surprise": "#e67e22",
    }
    ax.bar([k for k, _ in items], [v / 60.0 for _, v in items], color=[colors.get(k, "#7f8c8d") for k, _ in items])
    ax.set_ylabel("Minutes")
    ax.set_title("Duration-weighted vocal emotion (Tier A)")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    p = charts_dir / "emotion_distribution.png"
    fig.savefig(p, dpi=140)
    plt.close(fig)
    paths["emotion_distribution"] = p

    # 4. Exuberance z per claim
    fig, ax = plt.subplots(figsize=(8.0, 3.4))
    zs = [_safe_float(s.get("z_exuberance"), 0.0) or 0.0 for s in cm_segs]
    labs = [f"c{s.get('claim_id')}" for s in cm_segs]
    bar_colors = ["#27ae60" if z >= 0 else "#c0392b" for z in zs]
    ax.bar(labs, zs, color=bar_colors)
    ax.axhline(0, color="#2c3e50", lw=0.8)
    ax.set_ylabel("z (within video)")
    ax.set_title("Measured exuberance z-score per claim")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    p = charts_dir / "exuberance_z.png"
    fig.savefig(p, dpi=140)
    plt.close(fig)
    paths["exuberance_z"] = p

    # 5. Interpreted vs measured scatter
    fig, ax = plt.subplots(figsize=(5.6, 5.2))
    ax.scatter(derived["ar_ag"], derived["va_ag"], c="#e67e22", s=70, zorder=3)
    for s in cm_segs:
        im = s.get("interpreted_measured") or {}
        ax.annotate(
            f"c{s.get('claim_id')}",
            (float(im.get("arousal_agreement") or 0), float(im.get("valence_agreement") or 0)),
            textcoords="offset points",
            xytext=(6, 4),
            fontsize=8,
        )
    ax.plot([0, 1], [0, 1], color="#95a5a6", ls="--", lw=1)
    ax.set_xlim(0.3, 1.02)
    ax.set_ylim(0.3, 1.02)
    ax.set_xlabel("Arousal agreement")
    ax.set_ylabel("Valence agreement")
    ax.set_title("Interpreted vs measured (Gemini × prosody proxy)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    p = charts_dir / "interpreted_measured_scatter.png"
    fig.savefig(p, dpi=140)
    plt.close(fig)
    paths["interpreted_measured_scatter"] = p

    return paths


def _b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def _img_md(rel: str, alt: str) -> str:
    return f"![{alt}]({rel})\n"


def _img_html(path: Path, alt: str) -> str:
    mime = "image/png"
    return f'<img alt="{alt}" src="data:{mime};base64,{_b64(path)}" />'


ROADMAP = [
    {
        "priority": 1,
        "need": "Gaze aversion, blink rate, head-pose, fidget statistics",
        "why": "Whissle visual lane +0.133 AUC over audio-only digest (arXiv:2606.22699). Highest missing lift for our stack.",
        "cite": "https://arxiv.org/html/2606.22699v1",
        "local_hook": "verityngn/services/vision/ (py-feat Detectorv2 stub)",
        "status": "not_in_this_video",
    },
    {
        "priority": 2,
        "need": "Facial Action Units (AU) per frame, replacing Tier B prose",
        "why": "Measured AUs make facial-vocal-verbal alignment longitudinal instead of Gemini-described.",
        "cite": "https://arxiv.org/html/2407.06005v1",
        "local_hook": "verityngn/services/vision/adapters/pyfeat.py",
        "status": "stub_only",
    },
    {
        "priority": 3,
        "need": "Longitudinal modal incongruence (text vs vocal vs face) per CEO",
        "why": "Oxford-Man 2026: 2,439 CEO interviews; cross-channel misalignment predicts negative outcomes. This is the accumulation target for S01/S02.",
        "cite": "https://oxford-man.ox.ac.uk/wp-content/uploads/2026/06/Siew-Modal-Incongruence-Oxford-Conference-Draft-20260610.pdf",
        "local_hook": "fusion/crossmodal.py interpreted_measured + modality_divergence",
        "status": "n=1_seeded",
    },
    {
        "priority": 4,
        "need": "Real dimensional VAD (audEERING-style) instead of prosody_proxy",
        "why": "This video's valence gap (S02) is consistent with a proxy that cannot represent negative valence well.",
        "cite": "internal affect/adapters/audeering_vad.py",
        "local_hook": "affect/adapters/audeering_vad.py",
        "status": "proxy_used",
    },
    {
        "priority": 5,
        "need": "Pupil / GSR / EEG",
        "why": "Out of scope. Nature 2025: behavioral Audio+Video+GSR+Gaze beat EEG/ECG/EOG fusion by ~15%; invasive sensors not needed for markets research.",
        "cite": "https://www.nature.com/articles/s41598-025-92399-6",
        "local_hook": "none",
        "status": "wont_do",
    },
    {
        "priority": 0,
        "need": "Discourse derailment (expected LLM replies vs actual Q&A)",
        "why": (
            "Krykoniuk et al. 2026: lexical AI-detect is outdated; derailment "
            "(red herring / non sequitur) is a discourse-level cue. Interview "
            "adaptation = S11. Not a disinformation label."
        ),
        "cite": "https://www.nature.com/articles/s41599-026-07900-x",
        "local_hook": "verityngn/services/fusion/derailment.py",
        "status": "live_s11",
    },
]


def build_payload(
    *,
    signals: list[dict[str, Any]],
    ms: dict[str, Any],
    affect: dict[str, Any],
    fused: dict[str, Any],
    claims: list[dict[str, Any]],
    chart_rel: dict[str, str],
    video_id: str = VIDEO_ID,
    title: str | None = None,
) -> dict[str, Any]:
    cm = fused.get("crossmodal") or {}
    titles = {
        "QNkPpVYagRc": "Palantir CEO Alex Karp on Israel, AI and Outlook | CNBC at Davos 2024",
        "dRgPbNJ5RJc": "Conversation with Alex Karp, CEO and Co-Founder, Palantir Technologies | WEF Annual Meeting 2026",
        "ijRuuaaM6XM": "Alex Karp & Jensen Huang on Palantir–NVIDIA partnership | CNBC 2025-10-28",
        "V7mYWOzdhpc": "Alex Karp on US software dominance, DOGE, The Technological Republic | CNBC",
        "xe84cwQJKaE": "Alex Karp: Palantir lethal AI / CNBC Seema Mody | 2026-03-12",
        "WBu9Ai6OX3I": "CNBC interview with Palantir CEO Alex Karp | 2026-06-10",
        "pHu-FarYZlU": "CNBC Squawk Box interview with Palantir CEO Alex Karp | 2026-07-01",
        "-1BYgqw6hYk": "Watch CNBC’s full interview with Palantir CEO Alex Karp | 2026-07-01",
    }
    return {
        "schema_version": "1.0",
        "player_id": PLAYER_ID,
        "video_id": video_id,
        "youtube_url": f"https://www.youtube.com/watch?v={video_id}",
        "title": title or titles.get(video_id) or video_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_videos": 1,
        "trial": "T009",
        "promote": "NO_PROMOTE",
        "disclaimer": DISCLAIMER,
        "not_for_employment_use": True,
        "headline": {
            "overall_congruence": cm.get("overall_congruence"),
            "delivery_risk_band": cm.get("overall_delivery_risk_band"),
            "modality_divergence_rate": cm.get("modality_divergence_rate"),
            "live_gemini": (ms.get("summary") or {}).get("live_gemini"),
            "n_tier_a_segments": (ms.get("summary") or {}).get("n_tier_a_segments"),
            "n_tier_b_clips": (ms.get("summary") or {}).get("n_tier_b_clips"),
            "n_claims": len(claims),
            "exuberance_mean": (affect.get("summary") or {}).get("exuberance_mean"),
            "measured_affect_source": (affect.get("segments") or [{}])[0].get("measured_affect_source"),
        },
        "signals": signals,
        "charts": chart_rel,
        "roadmap": ROADMAP,
        "claims": [
            {
                "claim_id": c.get("claim_id"),
                "timestamp": c.get("timestamp"),
                "speaker": c.get("speaker"),
                "claim_text": c.get("claim_text"),
                "verdict": _claim_verdict(c),
            }
            for c in claims
        ],
    }


def write_md(path: Path, payload: dict[str, Any], chart_rel: dict[str, str]) -> None:
    h = payload["headline"]
    lines = [
        f"# Karp multimodal signal report — `{payload['player_id']}`",
        "",
        f"**Video:** [{payload['title']}]({payload['youtube_url']}) (`{payload['video_id']}`)",
        f"**Generated:** {payload['generated_at']}",
        f"**Corpus:** n={payload['n_videos']} video · trial {payload['trial']} · **{payload['promote']}**",
        "",
        f"> {DISCLAIMER}",
        "",
        "## Headline",
        "",
        f"- Overall congruence: **{h['overall_congruence']:.3f}** ({h['delivery_risk_band']} delivery-risk)",
        f"- Modality divergence rate: {h['modality_divergence_rate']}",
        f"- Live Gemini: {h['live_gemini']} · Tier A segments: {h['n_tier_a_segments']} · Tier B clips: {h['n_tier_b_clips']}",
        f"- Claims: {h['n_claims']} · exuberance mean: {h['exuberance_mean']:.3f} · affect source: `{h['measured_affect_source']}`",
        "",
        "## Seed signals (n=1)",
        "",
        "| ID | Signal | Value | Band | Accumulates |",
        "|----|--------|-------|------|-------------|",
    ]
    for s in payload["signals"]:
        val = s.get("value")
        if isinstance(val, dict):
            val_s = ", ".join(f"{k}={v}" for k, v in val.items())
        else:
            val_s = str(val)
        lines.append(f"| `{s['id']}` | {s['name']} | {val_s} | {s.get('band')} | {s.get('accumulates')} |")
    lines += [
        "",
        "## Charts",
        "",
        "### Arousal / valence timeline",
        "",
        _img_md(chart_rel["arousal_valence_timeline"], "Arousal valence timeline"),
        "Gray bars mark interviewer-style question segments. Dashed line is the geopolitics→business cut observed on this video.",
        "",
        "### Per-claim congruence",
        "",
        _img_md(chart_rel["claim_congruence"], "Claim congruence"),
        "",
        "### Emotion distribution",
        "",
        _img_md(chart_rel["emotion_distribution"], "Emotion distribution"),
        "Anger dominates the first ~9 minutes (Israel / West / trust); trust and anticipation take over on Palantir business.",
        "",
        "### Exuberance z-scores",
        "",
        _img_md(chart_rel["exuberance_z"], "Exuberance z"),
        "",
        "### Interpreted vs measured agreement",
        "",
        _img_md(chart_rel["interpreted_measured_scatter"], "Interpreted measured scatter"),
        "Points below the diagonal are the valence gap (S02 flag).",
        "",
        "## Signal notes",
        "",
    ]
    for s in payload["signals"]:
        lines += [
            f"### {s['name']} (`{s['id']}`)",
            "",
            f"- **Method:** {s['method']}",
            f"- **Required data:** {', '.join(s.get('required_data') or [])}",
            f"- **This video:** `{json.dumps(s.get('this_video'), default=str)[:500]}`",
            "",
        ]
    lines += [
        "## Claims (this video)",
        "",
        "| ID | t | Speaker | Verdict | Claim |",
        "|----|---|---------|---------|-------|",
    ]
    for c in payload["claims"]:
        txt = (c.get("claim_text") or "").replace("|", "/")
        lines.append(
            f"| {c.get('claim_id')} | {c.get('timestamp')} | {c.get('speaker')} | {c.get('verdict')} | {txt[:90]} |"
        )
    lines += ["", "## External roadmap — what to add next", ""]
    for r in ROADMAP:
        lines += [
            f"### {r['priority']}. {r['need']}",
            "",
            f"- Status: `{r['status']}`",
            f"- Why: {r['why']}",
            f"- Cite: {r['cite']}",
            f"- Local hook: `{r['local_hook']}`",
            "",
        ]
    lines += [
        "## Sherlock Step 5 — diagnostics if the next Karp video disagrees",
        "",
        "- Log speaker diarization: Sorkin claim_id=4 currently contaminates Karp affect z.",
        "- If valence gap repeats with real VAD, treat as a Karp trait not a sensor bug.",
        "- Confirm topic cut via OCR rather than a hardcoded 530s.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_html(path: Path, payload: dict[str, Any], chart_paths: dict[str, Path]) -> None:
    h = payload["headline"]
    rows = []
    for s in payload["signals"]:
        val = s.get("value")
        if isinstance(val, dict):
            val_s = json.dumps(val)
        else:
            val_s = str(val)
        rows.append(
            f"<tr><td><code>{s['id']}</code></td><td>{s['name']}</td>"
            f"<td>{val_s}</td><td>{s.get('band')}</td><td>{s.get('accumulates')}</td></tr>"
        )
    claim_rows = []
    for c in payload["claims"]:
        claim_rows.append(
            f"<tr><td>{c.get('claim_id')}</td><td>{c.get('timestamp')}</td>"
            f"<td>{c.get('speaker')}</td><td>{c.get('verdict')}</td>"
            f"<td>{(c.get('claim_text') or '')[:140]}</td></tr>"
        )
    roadmap_html = []
    for r in ROADMAP:
        roadmap_html.append(
            f"<h3>{r['priority']}. {r['need']}</h3>"
            f"<p><strong>Status:</strong> <code>{r['status']}</code><br>"
            f"<strong>Why:</strong> {r['why']}<br>"
            f"<strong>Cite:</strong> <a href=\"{r['cite']}\">{r['cite']}</a><br>"
            f"<strong>Local hook:</strong> <code>{r['local_hook']}</code></p>"
        )
    notes = []
    for s in payload["signals"]:
        notes.append(
            f"<h3>{s['name']}</h3><p><em>{s['method']}</em></p>"
            f"<pre>{json.dumps(s.get('this_video'), indent=2, default=str)}</pre>"
        )
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Karp multimodal signals — {payload['player_id']}</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ font-family: ui-sans-serif, system-ui, sans-serif; max-width: 980px; margin: 2rem auto; padding: 0 1.2rem; line-height: 1.5; }}
  h1 {{ font-size: 1.55rem; }}
  .banner {{ background: #1a1a1a; color: #eee; padding: 0.85rem 1rem; border-radius: 8px; font-size: 0.92rem; }}
  .kpi {{ display: flex; gap: 1rem; flex-wrap: wrap; margin: 1rem 0; }}
  .kpi div {{ border: 1px solid #8884; border-radius: 8px; padding: 0.7rem 0.9rem; min-width: 9rem; }}
  .kpi strong {{ display: block; font-size: 1.25rem; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 0.88rem; }}
  th, td {{ border: 1px solid #8884; padding: 0.4rem 0.5rem; vertical-align: top; text-align: left; }}
  img {{ max-width: 100%; height: auto; border: 1px solid #8883; border-radius: 6px; }}
  pre {{ overflow-x: auto; font-size: 0.78rem; background: #8881; padding: 0.6rem; border-radius: 6px; }}
  .muted {{ color: #666; font-size: 0.9rem; }}
</style>
</head>
<body>
<h1>Karp multimodal signal report</h1>
<p class="muted">{payload['title']} · <a href="{payload['youtube_url']}">{payload['video_id']}</a> · player <code>{payload['player_id']}</code></p>
<p class="banner">{DISCLAIMER}</p>
<div class="kpi">
  <div><span>Congruence</span><strong>{h['overall_congruence']:.3f}</strong></div>
  <div><span>Delivery risk</span><strong>{h['delivery_risk_band']}</strong></div>
  <div><span>Divergence rate</span><strong>{h['modality_divergence_rate']}</strong></div>
  <div><span>Videos in corpus</span><strong>{payload['n_videos']}</strong></div>
  <div><span>Trial</span><strong>{payload['trial']} {payload['promote']}</strong></div>
</div>
<h2>Seed signals</h2>
<table>
<thead><tr><th>ID</th><th>Signal</th><th>Value</th><th>Band</th><th>Accumulates</th></tr></thead>
<tbody>
{''.join(rows)}
</tbody>
</table>
<h2>Charts</h2>
<h3>Arousal / valence timeline</h3>
{_img_html(chart_paths['arousal_valence_timeline'], 'Arousal valence timeline')}
<p class="muted">Gray ticks = interviewer-style questions. Dashed line = geopolitics → business cut.</p>
<h3>Per-claim congruence</h3>
{_img_html(chart_paths['claim_congruence'], 'Claim congruence')}
<h3>Emotion distribution</h3>
{_img_html(chart_paths['emotion_distribution'], 'Emotion distribution')}
<h3>Exuberance z-scores</h3>
{_img_html(chart_paths['exuberance_z'], 'Exuberance z')}
<h3>Interpreted vs measured</h3>
{_img_html(chart_paths['interpreted_measured_scatter'], 'Interpreted measured scatter')}
<h2>Claims</h2>
<table>
<thead><tr><th>ID</th><th>t</th><th>Speaker</th><th>Verdict</th><th>Claim</th></tr></thead>
<tbody>
{''.join(claim_rows)}
</tbody>
</table>
<h2>Signal detail</h2>
{''.join(notes)}
<h2>External roadmap</h2>
{''.join(roadmap_html)}
<p class="muted">Generated {payload['generated_at']}</p>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def _find_claims_report(video_id: str, in_dir: Path, explicit: Path | None) -> Path | None:
    if explicit and explicit.exists():
        return explicit
    candidates = [
        in_dir / f"{video_id}_report.json",
        in_dir / f"{video_id}_report_with_delivery.json",
    ]
    debug = ROOT / "outputs_debug" / video_id
    if debug.is_dir():
        for d in sorted(debug.glob("*_complete"), reverse=True):
            candidates.append(d / f"{video_id}_report.json")
    for p in candidates:
        if p.exists():
            return p
    return None


def analyze_video_dir(in_dir: Path, *, claims_report: Path | None = None) -> dict[str, Any]:
    video_id = in_dir.name.replace("karp_local_", "")
    ms = _load(in_dir / f"{video_id}_multisense.json")
    affect = _load(in_dir / f"{video_id}_affect.json")
    fused = _load(in_dir / f"{video_id}_fused_index.json")
    cr = _find_claims_report(video_id, in_dir, claims_report)
    claims: list[dict[str, Any]] = []
    if cr:
        loaded = _load(cr)
        claims = loaded.get("claims_breakdown") or []
    if not claims:
        claims = [
            {
                "claim_id": s.get("claim_id"),
                "claim_text": "",
                "timestamp": s.get("timestamp"),
                "speaker": s.get("speaker"),
            }
            for s in affect.get("segments") or []
        ]
    signals, derived = compute_signals(
        ms=ms, affect=affect, fused=fused, claims=claims, video_id=video_id
    )
    return {
        "video_id": video_id,
        "in_dir": in_dir,
        "ms": ms,
        "affect": affect,
        "fused": fused,
        "claims": claims,
        "signals": signals,
        "derived": derived,
    }


def _mean_or_none(vals: list[float | None]) -> float | None:
    f = [v for v in vals if v is not None]
    return round(statistics.mean(f), 4) if f else None


def rollup_signals(analyses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Mean numeric S01–S10 across videos; keep per-video this_video under by_video."""
    n = len(analyses)
    by_id: dict[str, list[dict[str, Any]]] = {}
    for a in analyses:
        for s in a["signals"]:
            by_id.setdefault(s["id"], []).append(s)

    rolled: list[dict[str, Any]] = []
    for sid, rows in by_id.items():
        proto = dict(rows[0])
        proto["n_obs"] = n
        proto["by_video"] = {a["video_id"]: r.get("this_video") for a, r in zip(analyses, rows)}
        nums = []
        for r in rows:
            v = r.get("value")
            if isinstance(v, (int, float)):
                nums.append(float(v))
        if nums:
            proto["value"] = round(statistics.mean(nums), 4)
            proto["value_range"] = [round(min(nums), 4), round(max(nums), 4)]
            if sid == "S01_cross_channel_congruence":
                proto["band"] = _band_congruence(proto["value"])
            elif sid == "S03_emotional_arc_volatility":
                proto["band"] = "elevated" if proto["value"] >= 0.18 else "stable"
            elif sid == "S05_qa_reactivity_delta":
                proto["band"] = "reactive" if proto["value"] >= 0.25 else "flat"
            elif sid == "S11_discourse_derailment":
                proto["band"] = (
                    "high" if proto["value"] >= 0.45 else "moderate" if proto["value"] >= 0.25 else "low"
                )
        # S04: keep per-video fingerprints rather than a single collapsed dict
        if sid == "S04_topic_affect_fingerprint":
            proto["value"] = {
                a["video_id"]: r.get("value") for a, r in zip(analyses, rows)
            }
            bands = {str(r.get("band")) for r in rows}
            proto["band"] = "split" if "split" in bands else "uniform"
        proto.pop("video_id", None)
        rolled.append(proto)
    return rolled


def render_corpus_charts(out_dir: Path, analyses: list[dict[str, Any]]) -> dict[str, Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    charts_dir = out_dir / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    vids = [a["video_id"] for a in analyses]

    fig, ax = plt.subplots(figsize=(8.0, 3.6))
    cong, qa = [], []
    for a in analyses:
        s01 = next(s for s in a["signals"] if s["id"].startswith("S01"))
        s05 = next(s for s in a["signals"] if s["id"].startswith("S05"))
        cong.append(float(s01["value"] or 0))
        qa.append(float(s05["value"] or 0) if isinstance(s05.get("value"), (int, float)) else 0)
    x = list(range(len(vids)))
    ax.bar([i - 0.18 for i in x], cong, 0.36, color="#1abc9c", label="congruence")
    ax.bar([i + 0.18 for i in x], qa, 0.36, color="#e67e22", label="Q&A arousal delta")
    ax.set_xticks(x)
    ax.set_xticklabels(vids, fontsize=8)
    ax.set_ylim(0, 1.05)
    ax.set_title("Per-video congruence vs Q&A reactivity")
    ax.legend(fontsize=8)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    p = charts_dir / "corpus_congruence_qa.png"
    fig.savefig(p, dpi=140)
    plt.close(fig)
    paths["corpus_congruence_qa"] = p

    fig, ax = plt.subplots(figsize=(8.0, 3.6))
    dvals = []
    for a in analyses:
        s11 = next((s for s in a["signals"] if s["id"].startswith("S11")), None)
        dvals.append(float(s11["value"]) if s11 and isinstance(s11.get("value"), (int, float)) else 0.0)
    ax.bar(x, dvals, 0.55, color="#8e44ad", label="S11 derailment")
    ax.set_xticks(x)
    ax.set_xticklabels(vids, fontsize=8)
    ax.set_ylim(0, 1.05)
    ax.set_title("Per-video discourse derailment (S11, 0=on-topic)")
    ax.axhline(0.45, color="#c0392b", ls="--", lw=1, label="high ≥0.45")
    ax.legend(fontsize=8)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    p = charts_dir / "corpus_derailment.png"
    fig.savefig(p, dpi=140)
    plt.close(fig)
    paths["corpus_derailment"] = p

    fig, ax = plt.subplots(figsize=(8.5, 3.6))
    weights: dict[str, float] = {}
    for a in analyses:
        for s in a["derived"]["tier_a_segments"]:
            e = str(s.get("vocal_emotion") or "neutral").lower()
            weights[e] = weights.get(e, 0.0) + _dur(s)
    items = sorted(weights.items(), key=lambda kv: -kv[1])
    ax.bar([k for k, _ in items], [v / 60.0 for _, v in items], color="#34495e")
    ax.set_ylabel("Minutes (pooled)")
    ax.set_title("Corpus duration-weighted vocal emotion")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    p = charts_dir / "corpus_emotion.png"
    fig.savefig(p, dpi=140)
    plt.close(fig)
    paths["corpus_emotion"] = p
    return paths


def write_corpus_reports(
    out_dir: Path,
    analyses: list[dict[str, Any]],
    rolled: list[dict[str, Any]],
    chart_paths: dict[str, Path],
) -> None:
    payload = {
        "schema_version": "1.1",
        "player_id": PLAYER_ID,
        "video_ids": [a["video_id"] for a in analyses],
        "n_videos": len(analyses),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "trial": "T009",
        "promote": "NO_PROMOTE",
        "disclaimer": DISCLAIMER.replace("n=1 video", f"n={len(analyses)} videos"),
        "not_for_employment_use": True,
        "videos": [
            {
                "video_id": a["video_id"],
                "youtube_url": f"https://www.youtube.com/watch?v={a['video_id']}",
                "n_claims": len(a["claims"]),
                "overall_congruence": (a["fused"].get("crossmodal") or {}).get("overall_congruence"),
                "live_gemini": (a["ms"].get("summary") or {}).get("live_gemini"),
            }
            for a in analyses
        ],
        "signals": rolled,
        "roadmap": ROADMAP,
    }
    n_live = sum(1 for v in payload["videos"] if v.get("live_gemini"))
    payload["instrument_only"] = n_live < payload["n_videos"]
    try:
        from verityngn.services.quant.signal_quality import fidelity, stamp_instrument_only
        fid = fidelity([
            {
                "live_gemini": v.get("live_gemini"),
                "audio_source": "offline_proxy" if not v.get("live_gemini") else "gemini",
                "gemini_source": "gemini" if v.get("live_gemini") else "offline_proxy",
                "vision_source": "",
                "asr_source": "",
                "sympathetic_arousal": None,
            }
            for v in payload["videos"]
        ])
        payload = stamp_instrument_only(payload, fid)
    except Exception:
        payload["instrument_only"] = True
        payload["promote"] = "NO_PROMOTE"
    json_path = out_dir / f"{report_stem()}.json"
    json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    chart_rel = {k: f"charts/{p.name}" for k, p in chart_paths.items()}
    lines = [
        f"# Player risk panel — `{PLAYER_ID}`",
        "",
        f"**Videos:** {', '.join(payload['video_ids'])} · n={payload['n_videos']}",
        f"**Generated:** {payload['generated_at']} · **{payload['promote']}**",
        "",
        f"> {payload['disclaimer']}",
        "",
        "## Videos",
        "",
        "| Video | Claims | Congruence | Live Gemini |",
        "|-------|--------|------------|-------------|",
    ]
    for v in payload["videos"]:
        lines.append(
            f"| [{v['video_id']}]({v['youtube_url']}) | {v['n_claims']} | "
            f"{v['overall_congruence']:.3f} | {v['live_gemini']} |"
        )
    lines += [
        "",
        "## Rolled signals",
        "",
        "| ID | Signal | Corpus value | Range | Band |",
        "|----|--------|--------------|-------|------|",
    ]
    for s in rolled:
        val = s.get("value")
        if isinstance(val, dict):
            val_s = json.dumps(val)
        else:
            val_s = str(val)
        rng = s.get("value_range")
        rng_s = f"{rng[0]}–{rng[1]}" if rng else "—"
        lines.append(f"| `{s['id']}` | {s['name']} | {val_s} | {rng_s} | {s.get('band')} |")
    lines += ["", "## Charts", ""]
    for key, rel in chart_rel.items():
        lines += [f"### {key}", "", f"![{key}]({rel})", ""]
    lines += ["", "## Per-video S01/S05", ""]
    for a in analyses:
        s01 = next(s for s in a["signals"] if s["id"].startswith("S01"))
        s05 = next(s for s in a["signals"] if s["id"].startswith("S05"))
        s11 = next((s for s in a["signals"] if s["id"].startswith("S11")), None)
        d11 = s11["value"] if s11 else None
        lines.append(
            f"- `{a['video_id']}` congruence={s01['value']} qa_delta={s05['value']} derailment={d11}"
        )
    md_path = out_dir / f"{report_stem()}.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")

    rows = []
    for s in rolled:
        val = s.get("value")
        val_s = json.dumps(val) if isinstance(val, dict) else str(val)
        rows.append(
            f"<tr><td><code>{s['id']}</code></td><td>{s['name']}</td>"
            f"<td>{val_s}</td><td>{s.get('band')}</td></tr>"
        )
    vid_rows = []
    for v in payload["videos"]:
        vid_rows.append(
            f"<tr><td><a href=\"{v['youtube_url']}\">{v['video_id']}</a></td>"
            f"<td>{v['n_claims']}</td><td>{v['overall_congruence']:.3f}</td>"
            f"<td>{v['live_gemini']}</td></tr>"
        )
    imgs = "".join(
        f"<h3>{k}</h3>{_img_html(p, k)}" for k, p in chart_paths.items()
    )
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/>
<title>Player risk panel — {PLAYER_ID}</title>
<style>
body {{ font-family: ui-sans-serif, system-ui, sans-serif; max-width: 980px; margin: 2rem auto; padding: 0 1.2rem; line-height: 1.5; }}
table {{ border-collapse: collapse; width: 100%; font-size: 0.88rem; }}
th, td {{ border: 1px solid #8884; padding: 0.4rem 0.5rem; text-align: left; }}
img {{ max-width: 100%; height: auto; }}
.banner {{ background: #1a1a1a; color: #eee; padding: 0.85rem 1rem; border-radius: 8px; }}
</style></head><body>
<h1>Player risk panel</h1>
<p class="banner">{payload['disclaimer']}</p>
<p>n={payload['n_videos']} · {payload['trial']} · {payload['promote']}</p>
<h2>Videos</h2>
<table><thead><tr><th>Video</th><th>Claims</th><th>Congruence</th><th>Gemini</th></tr></thead>
<tbody>{''.join(vid_rows)}</tbody></table>
<h2>Rolled risk factors</h2>
<table><thead><tr><th>ID</th><th>Signal</th><th>Value</th><th>Band</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
{imgs}
<p>Generated {payload['generated_at']}</p>
</body></html>
"""
    (out_dir / f"{report_stem()}.html").write_text(html, encoding="utf-8")
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    print(f"wrote {out_dir / f'{report_stem()}.html'}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--in-dir", type=Path, default=DEFAULT_IN)
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--claims-report", type=Path, default=None)
    ap.add_argument("--player-id", default=DEFAULT_PLAYER_ID, help="Player id (default ceo_pltr_karp)")
    ap.add_argument(
        "--corpus-dirs",
        nargs="*",
        type=Path,
        help="If set, roll up these local_* dirs into a corpus report",
    )
    args = ap.parse_args()

    global PLAYER_ID
    PLAYER_ID = args.player_id

    if args.corpus_dirs:
        analyses = [analyze_video_dir(p) for p in args.corpus_dirs]
        out_dir = args.out_dir or (ROOT / ".outputs" / f"{PLAYER_ID}_corpus")
        out_dir.mkdir(parents=True, exist_ok=True)
        rolled = rollup_signals(analyses)
        charts = render_corpus_charts(out_dir, analyses)
        write_corpus_reports(out_dir, analyses, rolled, charts)
        for a in analyses:
            vid_out = a["in_dir"]
            signals, derived = a["signals"], a["derived"]
            chart_paths = render_charts(vid_out, a["ms"], a["fused"], derived)
            chart_rel = {k: f"charts/{p.name}" for k, p in chart_paths.items()}
            payload = build_payload(
                signals=signals,
                ms=a["ms"],
                affect=a["affect"],
                fused=a["fused"],
                claims=a["claims"],
                chart_rel=chart_rel,
                video_id=a["video_id"],
            )
            payload["n_videos"] = len(analyses)
            (vid_out / f"{report_stem()}.json").write_text(
                json.dumps(payload, indent=2, default=str), encoding="utf-8"
            )
            write_md(vid_out / f"{report_stem()}.md", payload, chart_rel)
            write_html(vid_out / f"{report_stem()}.html", payload, chart_paths)
        return 0

    in_dir = args.in_dir
    video_id = in_dir.name.replace("karp_local_", "") if in_dir.name.startswith("karp_local_") else VIDEO_ID
    a = analyze_video_dir(in_dir, claims_report=args.claims_report)
    out_dir = args.out_dir or in_dir
    chart_paths = render_charts(out_dir, a["ms"], a["fused"], a["derived"])
    chart_rel = {k: f"charts/{p.name}" for k, p in chart_paths.items()}
    payload = build_payload(
        signals=a["signals"],
        ms=a["ms"],
        affect=a["affect"],
        fused=a["fused"],
        claims=a["claims"],
        chart_rel=chart_rel,
        video_id=a["video_id"],
    )
    json_path = out_dir / f"{report_stem()}.json"
    md_path = out_dir / f"{report_stem()}.md"
    html_path = out_dir / f"{report_stem()}.html"
    json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    write_md(md_path, payload, chart_rel)
    write_html(html_path, payload, chart_paths)
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    print(f"wrote {html_path}")
    for p in chart_paths.values():
        print(f"wrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
