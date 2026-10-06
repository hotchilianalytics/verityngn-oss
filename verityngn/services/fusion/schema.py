"""Canonical fused index schema — extends Spot Runner sr_keywords_csv.md."""
from __future__ import annotations

from typing import Any, Optional
import json
from pathlib import Path

from verityngn.services.fusion.align import align_modalities
from verityngn.services.fusion.arcs import segment_story_arcs
from verityngn.services.fusion.crossmodal import score_crossmodal
from verityngn.services.fusion.plutchik import map_affect_to_segments


FULL_INDEX_OBJECTS = ("scene", "audio", "text", "face", "physio", "claim", "gemini")

DISCLAIMER = (
    "Fused multimodal index for markets research. Congruence / conviction / "
    "delivery-risk only — not a lie detector. Not for employment, HR, or "
    "education screening (EU AI Act Art. 5(1)(f))."
)


def build_fused_index(
    *,
    video_id: str,
    affect: Optional[dict[str, Any]] = None,
    vision: Optional[dict[str, Any]] = None,
    gemini: Optional[dict[str, Any]] = None,
    player_id: str = "unknown",
) -> dict[str, Any]:
    affect = affect or {}
    vision = vision or {}
    gemini = gemini or {}
    fused_rows = align_modalities(affect=affect, vision=vision, gemini=gemini)
    cross = score_crossmodal(fused_rows, player_id=player_id)
    arcs = segment_story_arcs(fused_rows)

    full_index = []
    emotional_index = []
    for r in fused_rows:
        t = r.get("t_sec")
        full_index.append(
            {
                "time": t,
                "object": "claim",
                "value": r.get("claim_id"),
                "signal_tier": "measured",
            }
        )
        if r.get("exuberance") is not None:
            full_index.append(
                {
                    "time": t,
                    "object": "audio",
                    "value": f"exuberance={r.get('exuberance')}",
                    "signal_tier": "measured",
                }
            )
        if r.get("sympathetic_arousal") is not None:
            full_index.append(
                {
                    "time": t,
                    "object": "physio",
                    "value": f"arousal={r.get('sympathetic_arousal')}",
                    "signal_tier": "measured",
                }
            )
        if r.get("cognitive_load_proxy") is not None:
            full_index.append(
                {
                    "time": t,
                    "object": "face",
                    "value": f"cognitive_load={r.get('cognitive_load_proxy')}",
                    "signal_tier": "measured",
                }
            )
        if r.get("gemini_emotion") is not None or r.get("gemini_arousal") is not None:
            full_index.append(
                {
                    "time": t,
                    "object": "gemini",
                    "value": (
                        f"emotion={r.get('gemini_emotion')};"
                        f"arousal={r.get('gemini_arousal')};"
                        f"valence={r.get('gemini_valence')}"
                    ),
                    "signal_tier": "interpreted",
                }
            )
        ex_raw = r.get("exuberance")
        ar_raw = r.get("sympathetic_arousal")
        try:
            ex_f = float(ex_raw) if ex_raw is not None and ex_raw == ex_raw else 0.5
        except (TypeError, ValueError):
            ex_f = 0.5
        try:
            ar_f = float(ar_raw) if ar_raw is not None and ar_raw == ar_raw else 0.5
        except (TypeError, ValueError):
            ar_f = 0.5
        # Prefer Gemini valence when present for Plutchik map
        sent = float(r.get("text_sentiment") or 0.0)
        if r.get("gemini_valence") is not None:
            try:
                sent = float(r.get("gemini_valence"))
            except (TypeError, ValueError):
                pass
        if r.get("gemini_arousal") is not None:
            try:
                ar_f = float(r.get("gemini_arousal"))
            except (TypeError, ValueError):
                pass
        segs = map_affect_to_segments(sent, ex_f, ar_f)
        for s in segs:
            emotional_index.append(
                {
                    "time": t,
                    "word": s["segment_id"].split("_")[-1],
                    "phrase": s["segment_id"],
                    "relevance": s["relevance"],
                    "signal_tier": "interpreted" if r.get("signal_tier_gemini") else "measured",
                }
            )

    audio_n = sum(1 for r in fused_rows if r.get("modality_present", {}).get("audio"))
    vision_n = sum(1 for r in fused_rows if r.get("modality_present", {}).get("vision"))
    text_n = sum(1 for r in fused_rows if r.get("modality_present", {}).get("text"))
    gemini_n = sum(1 for r in fused_rows if r.get("modality_present", {}).get("gemini"))
    total = max(1, audio_n + vision_n + text_n + gemini_n)
    modality_contributions = {
        "audio": audio_n / total,
        "vision": vision_n / total,
        "text": text_n / total,
        "gemini": gemini_n / total,
        "note": (
            "Coverage-weighted placeholder including interpreted Gemini track; "
            "replace with SHAP/attention weights when model trained."
        ),
        "literature_sanity": {"microexpressions_share": 0.35, "pitch_variation_share": 0.28},
    }

    return {
        "schema_version": "1.1",
        "video_id": video_id,
        "player_id": player_id,
        "summary": [
            {
                "time": 0,
                "keywords": ["fused_multimodal", "congruence", "gemini_interpreted", player_id],
                "phrases": [
                    f"overall_congruence={cross.get('overall_congruence')}",
                    f"modality_divergence_rate={cross.get('modality_divergence_rate')}",
                ],
            }
        ],
        "full_index": full_index,
        "emotional_index": emotional_index,
        "story_arcs": arcs,
        "crossmodal": cross,
        "modality_contributions": modality_contributions,
        "fused_rows": fused_rows,
        "advertising_categories": [],
        "disclaimer": DISCLAIMER,
        "not_for_employment_use": True,
        "fusion_design": {
            "baseline": "late_fusion",
            "tracks": ["measured", "interpreted"],
            "reference_architecture": "SVC2026 hybrid MLP-Mixer + self-attention cross-modal",
            "stretch": "ImageBind-style joint embedding",
        },
    }


def write_fused_index(index: dict[str, Any], path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index, indent=2), encoding="utf-8")
    return path
