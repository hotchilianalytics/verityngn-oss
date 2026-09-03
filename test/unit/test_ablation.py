"""Unit tests for ablation compare + offline direct + claims modality arms."""
from __future__ import annotations

import json
from pathlib import Path

from verityngn.services.ablation.claim_compare import (
    compare_claim_inventories,
    evaluate_genre_sleeve_gate,
    normalize_claim_text,
)
from verityngn.services.ablation.compare import compare_arms, jaccard_overlap
from verityngn.services.ablation.direct import build_direct_payload, run_dr_direct
from verityngn.services.ablation.runner import run_claims_ablation


def test_jaccard_identical():
    assert jaccard_overlap("alpha beta gamma", "alpha beta gamma") == 1.0


def test_jaccard_disjoint():
    assert jaccard_overlap("alpha beta", "zeta theta") == 0.0


def test_build_direct_payload_empty_claims():
    p = build_direct_payload(video_id="tLJC8hkK-ao", title="Lipozem")
    assert p["claims_breakdown"] == []
    assert p["ablation_arm"] == "dr_direct"


def test_run_dr_direct_offline(tmp_path: Path):
    out = run_dr_direct(
        out_dir=str(tmp_path),
        video_id="tLJC8hkK-ao",
        title="Lipozem interview",
        use_live_llm=False,
    )
    assert out["status"] == "completed"
    assert out["n_claims_in_payload"] == 0
    assert Path(out["markdown_path"]).is_file()
    assert Path(out["sanitized_path"]).is_file()
    payload = json.loads(Path(out["sanitized_path"]).read_text())
    assert payload["claims_breakdown"] == []


def test_compare_arms(tmp_path: Path):
    a = tmp_path / "a.md"
    b = tmp_path / "b.md"
    a.write_text(
        "# Risk\n\nLipozem clinical trial claim contested "
        "[Reference: https://example.com/a]\n" + ("word " * 80)
    )
    b.write_text(
        "# Risk\n\nLipozem clinical trial claim contested "
        "[Reference: https://example.com/b]\n" + ("word " * 80)
    )
    cmp = compare_arms(
        {"markdown_path": str(a), "elapsed_sec": 1.0},
        {"markdown_path": str(b), "elapsed_sec": 0.5},
    )
    assert cmp["topic_jaccard"] is not None
    assert cmp["topic_jaccard"] > 0.3


def test_normalize_claim_text():
    assert normalize_claim_text("Harvard Researchers!") == normalize_claim_text(
        "harvard  researchers"
    )


def test_compare_claim_inventories_multimodal_unique():
    tx = [
        {"claim_text": "Clinically tested formula", "source_type": "spoken"},
        {"claim_text": "Harvard validated it", "source_type": "spoken"},
    ]
    mm = [
        {"claim_text": "Clinically tested formula", "source_type": "spoken"},
        {"claim_text": "Harvard validated it", "source_type": "spoken"},
        {
            "claim_text": "On-screen graphic shows 97% success",
            "source_type": "visual_text",
        },
        {"claim_text": "Chart labeled FDA approved", "source_type": "chart"},
    ]
    cmp = compare_claim_inventories(tx, mm)
    assert cmp["n_both"] == 2
    assert cmp["n_only_multimodal"] == 2
    assert cmp["n_only_transcript"] == 0
    assert cmp["decision_hint"] == "multimodal_adds_unique"
    assert cmp["multimodal_source_type_histogram"].get("visual_text") == 1
    assert cmp["claim_jaccard"] is not None
    assert cmp["claim_jaccard"] < 0.7
    assert cmp["visual_only_multimodal_count"] == 2
    assert cmp["visual_only_multimodal_share"] == 0.5
    gate = evaluate_genre_sleeve_gate(cmp)
    assert gate["sleeve_validated"] is True
    assert gate["recommendation"] == "validate_sleeve"


def test_evaluate_genre_sleeve_gate_fails_low_visual():
    cmp = {
        "visual_only_multimodal_share": 0.1,
        "decision_hint": "multimodal_adds_unique",
    }
    gate = evaluate_genre_sleeve_gate(cmp)
    assert gate["sleeve_validated"] is False
    assert gate["recommendation"] == "audit_path_only"


def test_run_claims_ablation_offline(tmp_path: Path):
    result = run_claims_ablation(
        out_dir=str(tmp_path),
        arms="both",
        video_id="tLJC8hkK-ao",
        youtube_url="https://www.youtube.com/watch?v=tLJC8hkK-ao",
        title="Lipozem",
        use_live_llm=False,
    )
    assert Path(result["compare_path"]).is_file()
    assert (tmp_path / "transcript" / "claims_transcript.json").is_file()
    assert (tmp_path / "multimodal" / "claims_multimodal.json").is_file()
    cmp = result["compare"]
    assert cmp["decision_hint"] == "multimodal_adds_unique"
    assert cmp["n_only_multimodal"] >= 1
    payload = json.loads(Path(result["compare_path"]).read_text())
    assert payload["mode"] == "claims"


def test_infer_source_type_from_visual_text_speaker():
    from verityngn.services.ablation.multimodal_arm import _infer_source_type, _normalize_claims

    assert _infer_source_type({"speaker": "Visual Text", "source_type": "unknown"}) == "visual_text"
    assert _infer_source_type({"speaker": "On-Screen Graphics", "source_type": ""}) == "graphic"
    assert _infer_source_type({"speaker": "Paul", "source_type": "chart"}) == "chart"
    norms = _normalize_claims(
        [{"claim_text": "Disclaimer on screen", "speaker": "Visual Text", "source_type": "unknown"}]
    )
    assert norms[0]["source_type"] == "visual_text"


def test_validate_preserves_source_type():
    from verityngn.workflows.analysis import validate_and_normalize_json_result
    import logging

    result = validate_and_normalize_json_result(
        {
            "initial_report": "ok",
            "video_analysis_summary": "ok",
            "claims": [
                {
                    "claim_text": "On-screen success rate of ninety seven percent shown",
                    "timestamp": "01:00",
                    "speaker": "Visual Text",
                    "source_type": "unknown",
                    "initial_assessment": "OCR",
                }
            ],
        },
        logging.getLogger("test"),
    )
    assert result["claims"][0]["source_type"] == "visual_text"


def test_direct_payload_uses_full_transcript_not_12k():
    long_tx = "word " * 5000  # ~25k chars
    p = build_direct_payload(video_id="abc12345678", transcript=long_tx)
    assert p["transcript_chars_fetched"] == len(long_tx)
    assert p["transcript_chars_used"] == len(long_tx)
    assert p["transcript_truncated"] is False
    assert len(p["transcript_excerpt"]) == len(long_tx)


def test_run_dr_direct_writes_arm_cost(tmp_path: Path):
    out = run_dr_direct(
        out_dir=str(tmp_path),
        video_id="offlineStub01",
        title="Stub interview",
        use_live_llm=False,
        duration_sec=100.0,
    )
    assert out["status"] == "completed"
    assert out.get("arm_cost_path")
    assert Path(out["arm_cost_path"]).is_file()
    cost = json.loads(Path(out["arm_cost_path"]).read_text())
    assert "usd_estimate" in cost
    assert cost["arm"] == "dr_direct"
    assert "transcript_chars_used" in out