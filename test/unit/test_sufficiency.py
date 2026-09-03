"""Unit tests for sufficiency routing metrics (T-ABL-007)."""
from __future__ import annotations

from verityngn.services.ablation.sufficiency import (
    caption_coverage,
    citation_density,
    compare_sufficiency,
    parse_vtt_cue_coverage,
    preflight_features,
    quality_floor_escalation,
    risk_recall_at_k,
    route_decision,
    token_set_ratio,
)


def test_token_set_ratio_partial():
    assert token_set_ratio("FDA approved clinical trial", "clinical trial FDA approved") > 0.8


def test_parse_vtt_cue_coverage():
    vtt = """WEBVTT

00:00:00.000 --> 00:00:05.000
Hello world

00:00:05.000 --> 00:00:10.000
More text
"""
    cov = parse_vtt_cue_coverage(vtt)
    assert cov["n_cues"] == 2
    assert abs(cov["cue_duration_sec"] - 10.0) < 0.01
    assert caption_coverage(10.0, 20.0) == 0.5


def test_preflight_and_route_light():
    vtt = "WEBVTT\n\n00:00:00.000 --> 00:15:00.000\n" + ("talk " * 200)
    feats = preflight_features(
        duration_sec=1200,
        transcript_chars=8000,
        caption_source="cached_vtt",
        vtt_text=vtt,
        title="Quarterly earnings analysis",
    )
    assert feats["caption_kind"] == "cached"
    assert feats["genre_hint"] == "earnings"
    decision = route_decision(feats, tau_cov=0.5, tau_vis=0.5, tau_dur=900)
    assert decision["route"] == "light"


def test_route_full_when_no_captions():
    feats = preflight_features(
        duration_sec=2000,
        transcript_chars=0,
        caption_source="none",
        vtt_text="",
    )
    decision = route_decision(feats)
    assert decision["route"] == "full"


def test_risk_recall_and_compare():
    claims = [
        {"claim_text": f"Harvard researchers published clinical trial number {i} with FDA review", "source_type": "spoken"}
        for i in range(12)
    ]
    brief = (
        "# Risk\n\nHarvard researchers published clinical trial number 0 with FDA review "
        "[Reference: https://ex.com]\n"
        "Harvard researchers published clinical trial number 1 with FDA review "
        "[Reference: Currently Claim is Unverified]\n"
    )
    rr = risk_recall_at_k(claims, brief, k=10)
    assert rr["n_material"] == 10
    assert rr["risk_recall"] >= 0.1
    assert "material_miss_list" in rr
    assert citation_density(brief) > 0
    cmp = compare_sufficiency(
        full_claims=claims,
        light_brief_md=brief,
        full_elapsed=100,
        light_elapsed=20,
        full_usd=1.0,
        light_usd=0.1,
    )
    assert cmp["latency_speedup"] == 5.0
    assert cmp["cost_speedup"] == 10.0


def test_quality_floor_escalation():
    thin = "short"
    assert quality_floor_escalation(thin)["escalated"] is True
    fat = (
        "# Risk\n\n"
        + ("evidence grounded claim with detail. " * 40)
        + "".join(f"\n[Reference: https://ex.com/{i}]" for i in range(12))
    )
    floor = quality_floor_escalation(fat)
    assert floor["escalated"] is False, floor
