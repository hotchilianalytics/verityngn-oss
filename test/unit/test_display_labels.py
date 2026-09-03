"""Tests for risk display-label mapping (internal probs unchanged)."""
from verityngn.services.report.display_labels import (
    claim_modality_display_label,
    display_assessment,
    display_category,
    display_verification_result,
    category_from_prob_dist,
    is_visual_only_claim,
)


def test_display_category():
    assert display_category("TRUE") == "Supported"
    assert display_category("FALSE") == "Contested"
    assert display_category("UNCERTAIN") == "Unresolved"


def test_display_assessment_mixed():
    assert "Elevated" in display_assessment("Mixed Truthfulness")


def test_category_from_prob_dist():
    assert category_from_prob_dist({"TRUE": 0.7, "FALSE": 0.2, "UNCERTAIN": 0.1}) == "TRUE"
    assert category_from_prob_dist({"TRUE": 0.1, "FALSE": 0.8, "UNCERTAIN": 0.1}) == "FALSE"


def test_verification_result_display():
    assert "supported" in display_verification_result("LIKELY_TRUE").lower()


def test_claim_modality_display():
    assert claim_modality_display_label("spoken") == "Spoken"
    assert claim_modality_display_label("visual_text") == "On-screen text"
    assert claim_modality_display_label("chart") == "Chart"
    assert claim_modality_display_label(None) == "Unknown"


def test_is_visual_only_claim():
    assert is_visual_only_claim("visual_text") is True
    assert is_visual_only_claim("chart") is True
    assert is_visual_only_claim("spoken") is False
    assert is_visual_only_claim(None) is False
