"""Unit tests for adaptive sampler, exhibit map, brand-safety scores."""
from __future__ import annotations

from pathlib import Path

from verityngn.services.report.brand_safety_scores import compute_brand_safety_scores
from verityngn.services.vision.adaptive_sampler import (
    SCENE_EXHIBIT,
    SCENE_FLASH_OCR,
    SCENE_LECTURE,
    classify_scene,
    effective_segment_fps,
    resolve_sampling_policy,
)
from verityngn.services.vision.exhibit_tracker import build_exhibit_map, persist_exhibit_map


def test_classify_scene_genre_hints():
    assert classify_scene(genre_hint="ad") == SCENE_FLASH_OCR
    assert classify_scene(genre_hint="deposition") == SCENE_EXHIBIT
    assert classify_scene(cut_density_per_min=1.0) == SCENE_LECTURE


def test_resolve_sampling_policy_flash():
    fps, res = resolve_sampling_policy(SCENE_FLASH_OCR)
    assert fps >= 4.0
    assert "HIGH" in res


def test_effective_segment_fps_env_override():
    fps, res, probe = effective_segment_fps(
        "vid",
        env_fps=2.5,
        adaptive_enabled=True,
    )
    assert fps == 2.5
    assert probe.status == "env_override"


def test_build_exhibit_map_visual_only():
    claims = [
        {
            "claim_id": 0,
            "claim_text": "Exhibit 0142 shows fracture at weld",
            "timestamp": "04:12",
            "speaker": "Visual Text",
            "source_type": "visual_text",
            "ocr_snippet": "EXHIBIT 0142",
        },
        {
            "claim_id": 1,
            "claim_text": "I disagree with that figure",
            "timestamp": "04:20",
            "speaker": "Witness",
            "source_type": "spoken",
        },
    ]
    emap = build_exhibit_map("dep001", claims)
    assert emap.n_exhibits == 1
    assert emap.entries[0].bates_guess
    assert "0142" in emap.entries[0].bates_guess or "EXHIBIT" in emap.entries[0].bates_guess.upper()


def test_persist_exhibit_map(tmp_path: Path):
    claims = [
        {
            "claim_text": "On-screen chart: Q3 revenue up 15%",
            "timestamp": "05:20",
            "source_type": "chart",
        }
    ]
    path = persist_exhibit_map("earn01", claims, tmp_path)
    assert path is not None
    assert path.is_file()


def test_brand_safety_visual_only_high_risk():
    claims = [
        {
            "claim_text": "97% success rate shown on graphic",
            "source_type": "visual_text",
            "timestamp": "00:08",
            "verification_result": {"result": "LIKELY_FALSE"},
        },
        {
            "claim_text": "Dr. Ross Johns Hopkins endocrinologist",
            "source_type": "visual_text",
            "timestamp": "00:12",
            "verification_result": {"result": "UNCERTAIN"},
        },
        {
            "claim_text": "#ad Paid Partnership",
            "source_type": "visual_text",
            "timestamp": "00:01",
            "on_screen_ms": 400,
            "verification_result": {"result": "LIKELY_TRUE"},
        },
    ]
    scores = compute_brand_safety_scores("ad01", claims)
    assert scores.visual_only_claim_count == 3
    assert scores.visual_only_high_risk_count >= 1
    assert scores.credential_flash_events
    assert scores.sponsor_read_detected is True
    assert scores.recommended_action in (
        "legal_review_before_spend",
        "reject",
    )
