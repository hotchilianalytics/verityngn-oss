"""Cross-modal congruence / divergence + per-speaker longitudinal baselines.

Spoken Alpha lesson: cross-speaker corpora are noise; deviation from a speaker's
own history is signal. Outputs are congruence / delivery-risk bands — never
veracity.

Also scores interpreted (Gemini) vs measured (prosody / VAD / vision) agreement.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional
import math
import statistics


def _safe(x: Any, default: float = 0.0) -> float:
    try:
        v = float(x)
        return default if v != v else v  # NaN check
    except (TypeError, ValueError):
        return default


def text_voice_divergence(text_sentiment: float, exuberance: float) -> float:
    delivery = exuberance * 2.0 - 1.0
    return float(min(1.0, abs(text_sentiment - delivery) / 2.0))


def voice_face_divergence(exuberance: float, arousal: float) -> float:
    return float(min(1.0, abs(exuberance - arousal)))


def face_text_divergence(arousal: float, text_sentiment: float) -> float:
    # map sentiment [-1,1] → [0,1]
    valence = (text_sentiment + 1.0) / 2.0
    return float(min(1.0, abs(arousal - valence)))


def interpreted_measured_agreement(
    *,
    gemini_arousal: float,
    gemini_valence: float,
    measured_arousal: float,
    measured_valence: float,
    exuberance: float,
) -> dict[str, float]:
    """
    Agreement between Gemini interpreted affect and local measured features.

    Returns scores in [0,1] where 1 = perfect agreement, plus a composite.
    """
    # Prefer explicit measured VAD arousal; fall back to exuberance
    m_ar = measured_arousal if measured_arousal == measured_arousal else exuberance
    m_va = measured_valence if measured_valence == measured_valence else (exuberance * 2.0 - 1.0)
    ar_agree = 1.0 - min(1.0, abs(gemini_arousal - m_ar))
    # valence both roughly [-1,1]
    va_agree = 1.0 - min(1.0, abs(gemini_valence - m_va) / 2.0)
    composite = 0.55 * ar_agree + 0.45 * va_agree
    return {
        "arousal_agreement": float(ar_agree),
        "valence_agreement": float(va_agree),
        "interpreted_measured_congruence": float(composite),
    }


@dataclass
class SpeakerBaseline:
    player_id: str
    n_obs: int = 0
    exuberance_mean: float = 0.5
    exuberance_std: float = 0.15
    arousal_mean: float = 0.5
    arousal_std: float = 0.15
    disfluency_mean: float = 0.05
    disfluency_std: float = 0.03

    def z(self, value: float, mean: float, std: float) -> float:
        if std < 1e-9 or value != value:
            return 0.0
        return (value - mean) / std

    def to_dict(self) -> dict[str, Any]:
        return {
            "player_id": self.player_id,
            "n_obs": self.n_obs,
            "exuberance_mean": self.exuberance_mean,
            "exuberance_std": self.exuberance_std,
            "arousal_mean": self.arousal_mean,
            "arousal_std": self.arousal_std,
            "disfluency_mean": self.disfluency_mean,
            "disfluency_std": self.disfluency_std,
        }


def fit_speaker_baseline(player_id: str, rows: list[dict[str, Any]]) -> SpeakerBaseline:
    ex = [_safe(r.get("exuberance"), math.nan) for r in rows]
    ex = [v for v in ex if v == v]
    ar = [_safe(r.get("sympathetic_arousal"), math.nan) for r in rows]
    ar = [v for v in ar if v == v]
    di = [_safe(r.get("disfluency_rate"), math.nan) for r in rows]
    di = [v for v in di if v == v]
    b = SpeakerBaseline(player_id=player_id, n_obs=len(rows))
    if ex:
        b.exuberance_mean = statistics.fmean(ex)
        b.exuberance_std = statistics.pstdev(ex) if len(ex) > 1 else 0.15
    if ar:
        b.arousal_mean = statistics.fmean(ar)
        b.arousal_std = statistics.pstdev(ar) if len(ar) > 1 else 0.15
    if di:
        b.disfluency_mean = statistics.fmean(di)
        b.disfluency_std = statistics.pstdev(di) if len(di) > 1 else 0.03
    return b


def _present(v: Any) -> bool:
    """True when a modality value was actually measured (not missing / NaN)."""
    if v is None:
        return False
    try:
        f = float(v)
    except (TypeError, ValueError):
        return False
    return f == f


def score_crossmodal(
    fused_rows: list[dict[str, Any]],
    *,
    player_id: str = "unknown",
    baseline: Optional[SpeakerBaseline] = None,
    prepared_vs_qa: Optional[dict[str, float]] = None,
    divergence_threshold: float = 0.45,
) -> dict[str, Any]:
    baseline = baseline or fit_speaker_baseline(player_id, fused_rows)
    segment_scores = []
    for r in fused_rows:
        sent = _safe(r.get("text_sentiment"))
        has_voice = _present(r.get("exuberance"))
        has_face = _present(r.get("sympathetic_arousal"))
        ex = _safe(r.get("exuberance"), 0.5) if has_voice else 0.5
        ar = _safe(r.get("sympathetic_arousal"), 0.5) if has_face else None

        # Renormalize over available channels. NEVER substitute 0.5 for missing face —
        # that constant carried 60% of S01 weight and made congruence track n_claims.
        tv = text_voice_divergence(sent, ex) if has_voice else None
        vf = voice_face_divergence(ex, float(ar)) if (has_voice and has_face and ar is not None) else None
        ft = face_text_divergence(float(ar), sent) if (has_face and ar is not None) else None
        w_tv, w_vf, w_ft = 0.40, 0.35, 0.25
        parts: list[tuple[float, float]] = []
        if tv is not None:
            parts.append((w_tv, tv))
        if vf is not None:
            parts.append((w_vf, vf))
        if ft is not None:
            parts.append((w_ft, ft))
        wsum = sum(w for w, _ in parts)
        if wsum > 0:
            cong = 1.0 - sum((w / wsum) * d for w, d in parts)
        else:
            cong = 0.5
        missing_channels = [c for c, ok in (("voice", has_voice), ("face", has_face)) if not ok]

        # Interpreted vs measured
        g_ar = r.get("gemini_arousal")
        g_va = r.get("gemini_valence")
        im = None
        modality_divergence = False
        congruence_multiplier = 1.0
        if g_ar is not None or g_va is not None:
            im = interpreted_measured_agreement(
                gemini_arousal=_safe(g_ar, 0.5),
                gemini_valence=_safe(g_va, 0.0),
                measured_arousal=_safe(r.get("measured_arousal"), math.nan),
                measured_valence=_safe(r.get("measured_valence"), math.nan),
                exuberance=ex,
            )
            # Also fold Gemini's own Tier-B congruence if present
            g_cong = r.get("gemini_congruence")
            if g_cong is not None:
                im["gemini_self_congruence"] = _safe(g_cong, 0.5)
                im["interpreted_measured_congruence"] = (
                    0.7 * im["interpreted_measured_congruence"] + 0.3 * _safe(g_cong, 0.5)
                )
            congruence_multiplier = 0.5 + 0.5 * im["interpreted_measured_congruence"]
            cong = cong * congruence_multiplier
            modality_divergence = im["interpreted_measured_congruence"] < divergence_threshold

        z_ex = baseline.z(ex, baseline.exuberance_mean, baseline.exuberance_std)
        z_ar = baseline.z(float(ar), baseline.arousal_mean, baseline.arousal_std) if ar is not None else 0.0
        z_di = baseline.z(
            _safe(r.get("disfluency_rate")),
            baseline.disfluency_mean,
            baseline.disfluency_std,
        )
        segment_scores.append(
            {
                "t_sec": r.get("t_sec"),
                "claim_id": r.get("claim_id"),
                "text_voice_divergence": tv,
                "voice_face_divergence": vf,
                "face_text_divergence": ft,
                "congruence": cong,
                "congruence_multiplier": congruence_multiplier,
                "interpreted_measured": im,
                "modality_divergence": modality_divergence,
                "z_exuberance": z_ex,
                "z_arousal": z_ar,
                "z_disfluency": z_di,
                "missing_channels": missing_channels,
                "channels_used": sorted({"text"} | ({"voice"} if has_voice else set()) | ({"face"} if has_face else set())),
                "delivery_risk_band": (
                    "elevated" if cong < 0.4 else ("moderate" if cong < 0.65 else "low")
                ),
            }
        )

    if segment_scores:
        mean_cong = statistics.fmean(s["congruence"] for s in segment_scores)
        n_div = sum(1 for s in segment_scores if s.get("modality_divergence"))
    else:
        mean_cong = 0.5
        n_div = 0

    return {
        "player_id": player_id,
        "baseline": baseline.to_dict(),
        "segments": segment_scores,
        "overall_congruence": mean_cong,
        "overall_delivery_risk_band": (
            "elevated" if mean_cong < 0.4 else ("moderate" if mean_cong < 0.65 else "low")
        ),
        "n_modality_divergence": n_div,
        "modality_divergence_rate": (n_div / max(1, len(segment_scores))),
        "prepared_vs_qa": prepared_vs_qa or {"status": "not_computed"},
        "label": "congruence",
        "channels_policy": "renormalize_available_omit_missing_never_fill_0.5",
        "disclaimer": (
            "Congruence / delivery-risk only. Not a lie detector. "
            "Per-speaker longitudinal z-scores; not cross-speaker norms. "
            "Interpreted (Gemini) vs measured agreement is a research signal."
        ),
    }
