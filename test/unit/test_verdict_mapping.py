from __future__ import annotations

from verityngn.models.report import Claim, canonicalize_probability_distribution, map_probabilities_to_verification_result
from verityngn.services.report.category_mappings import compute_overall_verdict_label
from verityngn.workflows.reporting import generate_sophisticated_assessment


def _claim(result: str) -> Claim:
    return Claim(
        claim_id=1,
        claim_text="Example claim",
        timestamp="00:10",
        speaker="Tester",
        initial_assessment="Pending",
        verification_result={"result": result},
        explanation="",
        evidence=None,
    )


def test_canonicalize_probability_distribution_merges_case_and_synonyms():
    canon = canonicalize_probability_distribution(
        {
            "true": 0.10,
            "TRUE": 0.40,
            "mostly_true": 0.10,
            "false": 0.10,
            "FALSE": 0.05,
            "uncertain": 0.10,
            "UNVERIFIABLE": 0.15,
        }
    )
    assert set(canon.keys()) == {"TRUE", "FALSE", "UNCERTAIN"}
    assert abs(sum(canon.values()) - 1.0) < 0.01
    assert canon["TRUE"] > canon["FALSE"]
    assert canon["UNCERTAIN"] > 0.20


def test_high_uncertainty_distribution_does_not_map_to_likely_true():
    verdict = map_probabilities_to_verification_result(
        {"TRUE": 0.46, "FALSE": 0.05, "UNCERTAIN": 0.49}
    )
    assert verdict in {"LEANING_TRUE", "UNCERTAIN"}
    assert verdict != "LIKELY_TRUE"


def test_overall_verdict_label_not_true_by_default_on_leans_and_uncertainty():
    claims = [_claim("LEANING_TRUE") for _ in range(3)] + [_claim("UNCERTAIN") for _ in range(3)]
    assert compute_overall_verdict_label(claims) == "Mixed/Uncertain"


def test_generate_sophisticated_assessment_counts_leaning_buckets():
    claims = [_claim("LEANING_TRUE") for _ in range(7)] + [_claim("LEANING_FALSE") for _ in range(1)]
    verdict, key_issue, _concerns = generate_sophisticated_assessment(claims)
    assert verdict.value == "Likely to be True"
    assert "87.5% of claims appear true or likely true" in key_issue
