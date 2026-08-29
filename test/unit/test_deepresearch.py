"""Unit tests for Deep Research sanitize + gated pipeline (mocked LLM)."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from verityngn.services.deepresearch.sanitize import count_claims, sanitize_report_data


def _sample_report() -> dict:
    return {
        "video_id": "demo123",
        "title": "Demo",
        "claims_breakdown": [
            {
                "claim": "Claim A",
                "verification_result": {
                    "evidence": [
                        {"url": "https://example.com/a", "self_referential": False},
                        {"url": "https://example.com/pr", "self_referential": True},
                    ]
                },
            },
            {
                "claim": "Claim B",
                "verification_result": {
                    "evidence": [
                        {"url": "https://example.com/b", "self_referential": False},
                    ]
                },
            },
            {
                "claim": "Claim C",
                "verification_result": {"evidence": []},
            },
        ],
    }


def test_sanitize_drops_self_referential():
    cleaned = sanitize_report_data(_sample_report())
    claims = cleaned["claims_breakdown"]
    ev0 = claims[0]["verification_result"]["evidence"]
    assert len(ev0) == 1
    assert ev0[0]["self_referential"] is False


def test_count_claims():
    assert count_claims(_sample_report()) == 3
    assert count_claims({}) == 0


def test_pipeline_gate_too_few_claims(tmp_path: Path):
    from verityngn.services.deepresearch.pipeline import (
        DeepResearchGateError,
        generate_deep_research_report,
    )

    tiny = {"video_id": "x", "claims_breakdown": [{"claim": "only one"}]}
    p = tmp_path / "x_report.json"
    p.write_text(json.dumps(tiny), encoding="utf-8")
    with pytest.raises(DeepResearchGateError):
        asyncio.run(generate_deep_research_report(str(p), str(tmp_path), video_id="x"))


def test_pipeline_mocked_llm(tmp_path: Path):
    from verityngn.services.deepresearch.client import DeepResearchResult
    from verityngn.services.deepresearch.pipeline import generate_deep_research_report

    report = _sample_report()
    p = tmp_path / "demo123_report.json"
    p.write_text(json.dumps(report), encoding="utf-8")

    fake = DeepResearchResult(
        markdown="# Forensic\n\nFinding [Reference: https://example.com/ok].\n" + ("x" * 1200),
        grounding_metadata="{}",
        model_id="mock-model",
        prompt_version="dr_prompt_v1",
        queries=["q1"],
    )

    with patch(
        "verityngn.services.deepresearch.pipeline.run_deep_research",
        return_value=fake,
    ), patch(
        "verityngn.services.deepresearch.pipeline.render_html_to_pdf",
        return_value=True,
    ):
        result = asyncio.run(
            generate_deep_research_report(str(p), str(tmp_path), video_id="demo123")
        )

    assert result["status"] == "completed"
    assert Path(result["markdown_path"]).is_file()
    assert Path(result["grounding_path"]).is_file()
