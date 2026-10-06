"""Align vision / audio / text / gemini streams onto a common timebase."""
from __future__ import annotations

from typing import Any, Optional


def _claim_rows(affect: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for s in affect.get("segments") or []:
        if not isinstance(s, dict):
            continue
        rows.append(
            {
                "t_sec": float(s.get("timestamp_sec") or 0.0),
                "claim_id": s.get("claim_id"),
                "text_sentiment": float(s.get("text_sentiment") or 0.0),
                "exuberance": s.get("exuberance"),
                "disfluency_rate": float((s.get("disfluency") or {}).get("rate") or 0.0),
                "prosody": s.get("prosody") or {},
                "object": "claim",
                # Measured VAD (audEERING) if present on segment
                "measured_arousal": s.get("measured_arousal"),
                "measured_valence": s.get("measured_valence"),
                "measured_dominance": s.get("measured_dominance"),
            }
        )
    return rows


def _gemini_by_claim(gemini: dict[str, Any]) -> dict[Any, dict[str, Any]]:
    out: dict[Any, dict[str, Any]] = {}
    for row in gemini.get("claim_delivery") or []:
        if isinstance(row, dict) and row.get("claim_id") is not None:
            out[row["claim_id"]] = row
    return out


def _gemini_nearest_tier_a(gemini: dict[str, Any], t_sec: float) -> Optional[dict[str, Any]]:
    best = None
    best_d = 1e18
    for s in (gemini.get("tier_a") or {}).get("segments") or []:
        if not isinstance(s, dict):
            continue
        mid = 0.5 * (float(s.get("start_sec") or 0.0) + float(s.get("end_sec") or 0.0))
        d = abs(mid - t_sec)
        if d < best_d:
            best_d = d
            best = s
    return best


def align_modalities(
    *,
    affect: Optional[dict[str, Any]] = None,
    vision: Optional[dict[str, Any]] = None,
    gemini: Optional[dict[str, Any]] = None,
    hop_sec: float = 1.0,
) -> list[dict[str, Any]]:
    """
    Produce fused rows merging claim-anchored affect with vision + Gemini interpreted track.

    Late-fusion baseline: broadcast video-level vision stats onto each claim window;
    attach nearest Gemini Tier A / claim_delivery Tier B fields when present.
    """
    del hop_sec  # reserved for future dense timebase
    affect = affect or {}
    vision = vision or {}
    gemini = gemini or {}
    claims = _claim_rows(affect)
    vsum = vision.get("summary") or {}
    spectral = vision.get("spectral") or {}
    gaze = vision.get("gaze_blink") or {}
    ocr = vision.get("ocr_geo") or {}
    g_by_claim = _gemini_by_claim(gemini)

    if not claims:
        # Still emit a single fused row from vision / gemini alone
        g0 = _gemini_nearest_tier_a(gemini, 0.0) or {}
        return [
            {
                "t_sec": 0.0,
                "object": "fused",
                "text_sentiment": 0.0,
                "exuberance": None,
                "sympathetic_arousal": vsum.get("sympathetic_arousal"),
                "cognitive_load_proxy": vsum.get("cognitive_load_proxy"),
                "rppg_consistency": spectral.get("rppg_consistency"),
                "blink_rate_per_min": gaze.get("blink_rate_per_min"),
                "venues": ocr.get("venues"),
                "gemini_arousal": g0.get("arousal"),
                "gemini_valence": g0.get("valence"),
                "gemini_emotion": g0.get("vocal_emotion"),
                "gemini_congruence": None,
                "signal_tier_gemini": "interpreted" if g0 else None,
                "modality_present": {
                    "audio": False,
                    "vision": bool(vision),
                    "text": False,
                    "gemini": bool(g0),
                },
            }
        ]

    fused = []
    for c in claims:
        g_row = g_by_claim.get(c.get("claim_id"))
        g_a = (g_row or {}).get("tier_a") if g_row else _gemini_nearest_tier_a(gemini, c["t_sec"])
        g_b = (g_row or {}).get("tier_b") if g_row else None
        g_a = g_a or {}
        fused.append(
            {
                **c,
                "object": "fused",
                "sympathetic_arousal": vsum.get("sympathetic_arousal"),
                "cognitive_load_proxy": vsum.get("cognitive_load_proxy"),
                "rppg_consistency": spectral.get("rppg_consistency"),
                "blink_rate_per_min": gaze.get("blink_rate_per_min"),
                "venues": ocr.get("venues"),
                "gemini_arousal": g_a.get("arousal"),
                "gemini_valence": g_a.get("valence"),
                "gemini_emotion": g_a.get("vocal_emotion"),
                "gemini_delivery": g_a.get("delivery"),
                "gemini_congruence": (g_b or {}).get("congruence_score") if g_b else None,
                "gemini_congruence_statement": (g_b or {}).get("congruence_statement") if g_b else None,
                "gemini_sr_segments": g_a.get("sr_segments") or (g_b or {}).get("sr_segments"),
                "signal_tier_gemini": "interpreted" if (g_a or g_b) else None,
                "modality_present": {
                    "audio": c.get("exuberance") is not None,
                    "vision": bool(vision),
                    "text": True,
                    "gemini": bool(g_a or g_b),
                },
            }
        )
    return fused
