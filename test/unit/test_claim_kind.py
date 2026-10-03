"""Unit tests for analyst claim_kind taxonomy and dual risk metrics."""
from __future__ import annotations

from verityngn.models.report import Claim
from verityngn.services.report.category_mappings import (
    _verdict_counts,
    compute_overall_verdict_label,
)
from verityngn.workflows.claim_kind import (
    ClaimKind,
    annotate_claim_kind,
    classify_claim_kind,
    is_core_factual_claim,
    is_quantitative_method_claim,
    normalize_claim_kind,
)
from verityngn.services.report.analyst_genre import (
    build_sift_method_section,
    infer_report_genre,
)
from verityngn.workflows.reporting import generate_sophisticated_assessment
from verityngn.workflows.verification import _stamp_lane_on_verified_claim


def test_classify_source_backed_fact_date_vote():
    kind = classify_claim_kind(
        "The Oregon Senate passed SB 1507 on February 14, 2026, with a 17–13 vote."
    )
    assert kind == ClaimKind.SOURCE_BACKED_FACT.value


def test_classify_reasoned_opinion():
    kind = classify_claim_kind(
        "In my view policymakers should scrap the bill because it seems to hurt competitiveness."
    )
    assert kind == ClaimKind.REASONED_OPINION.value


def test_classify_causal_analytical_logic_chain():
    kind = classify_claim_kind(
        "Because Oregon uses rolling conformity, this means federal cuts therefore create "
        "automatic state revenue drops conditioned on the placeholder rewrite."
    )
    assert kind == ClaimKind.CAUSAL_ANALYTICAL.value


def test_classify_prediction_not_opinion():
    kind = classify_claim_kind(
        "The LRO forecast is that SB 1507 will raise about $120 million by 2027."
    )
    assert kind == ClaimKind.PREDICTION.value


def test_classify_data_derived_inference_method_quant():
    kind = classify_claim_kind(
        "After MinHash clustering and collapsing copy-paste duplicates, the rate rose "
        "to 42% of distinct individuals with a revenue impact near $18 million."
    )
    assert kind == ClaimKind.DATA_DERIVED_INFERENCE.value
    assert is_quantitative_method_claim(
        "After MinHash clustering, the rate rose to 42% with $18 million impact."
    )


def test_legacy_aliases_normalize():
    assert normalize_claim_kind("factual_sourceable") == ClaimKind.SOURCE_BACKED_FACT.value
    assert normalize_claim_kind("author_proof_candidate") == ClaimKind.CAUSAL_ANALYTICAL.value
    assert normalize_claim_kind("opinion_or_synthesis") == ClaimKind.REASONED_OPINION.value


def test_annotate_and_stamp_dual_metrics_causal():
    claim = annotate_claim_kind(
        {
            "claim_text": (
                "Because Oregon uses rolling conformity, therefore federal cuts "
                "create automatic state revenue drops conditioned on decoupling."
            )
        }
    )
    assert claim["claim_kind"] == ClaimKind.CAUSAL_ANALYTICAL.value
    assert claim["needs_deeper_research"] is True
    stamped = _stamp_lane_on_verified_claim(
        claim,
        {
            "result": "LIKELY_FALSE",
            "sources": [],
            "probability_distribution": {"TRUE": 0.1, "FALSE": 0.8, "UNCERTAIN": 0.1},
            "explanation": "No sources found",
        },
    )
    assert stamped["verification_result"]["result"] == "UNCERTAIN"
    assert stamped["needs_deeper_research"] is True
    assert stamped["verification_result"]["evidence_confidence"] in {"Low", "Medium", "High", "n/a"}
    assert stamped["verification_result"]["residual_reliance_risk"] in {"low", "medium", "high"}
    assert "risk_chip" in stamped["verification_result"]


def test_stamp_prediction_not_likely_false():
    claim = annotate_claim_kind(
        {
            "claim_text": (
                "The revenue forecast is that the bill will raise $200M by 2027."
            )
        }
    )
    assert claim["claim_kind"] == ClaimKind.PREDICTION.value
    stamped = _stamp_lane_on_verified_claim(
        claim,
        {
            "result": "LIKELY_FALSE",
            "sources": [],
            "probability_distribution": {"TRUE": 0.1, "FALSE": 0.8, "UNCERTAIN": 0.1},
            "explanation": "Future event",
        },
    )
    assert stamped["verification_result"]["result"] != "LIKELY_FALSE"
    assert stamped["verification_result"]["plausibility"] == "Unsupported"


def test_stamp_data_derived_no_false_on_empty_sources():
    claim = annotate_claim_kind(
        {
            "claim_text": (
                "After adjusting for MinHash clustering, QSBS bonus depreciation "
                "shows a $45 million LRO revenue impact at 18% of filers."
            )
        }
    )
    assert claim["claim_kind"] == ClaimKind.DATA_DERIVED_INFERENCE.value
    stamped = _stamp_lane_on_verified_claim(
        claim,
        {
            "result": "LIKELY_FALSE",
            "sources": [],
            "probability_distribution": {"TRUE": 0.2, "FALSE": 0.7, "UNCERTAIN": 0.1},
            "explanation": "No academic paper",
        },
    )
    assert stamped["verification_result"]["result"] == "UNCERTAIN"
    assert stamped["needs_deeper_research"] is False


def test_histogram_excludes_non_facts():
    factual = Claim(
        claim_id=1,
        claim_text="SB 1507 passed the Senate 17-13 on February 14, 2026.",
        timestamp="00:10",
        speaker="A",
        initial_assessment="Pending",
        verification_result={"result": "LIKELY_TRUE"},
        claim_kind="source_backed_fact",
    )
    opinion = Claim(
        claim_id=2,
        claim_text="In my view this bill should never have passed.",
        timestamp="00:20",
        speaker="A",
        initial_assessment="Pending",
        verification_result={"result": "LIKELY_FALSE"},
        claim_kind="reasoned_opinion",
    )
    inference = Claim(
        claim_id=3,
        claim_text="After MinHash clustering the rate rose to 42% ($18M).",
        timestamp="00:30",
        speaker="A",
        initial_assessment="Pending",
        verification_result={"result": "LEANING_TRUE"},
        claim_kind="data_derived_inference",
    )
    assert is_core_factual_claim(factual)
    assert not is_core_factual_claim(opinion)
    assert not is_core_factual_claim(inference)
    counts = _verdict_counts([factual, opinion, inference])
    assert counts["LIKELY_TRUE"] == 1
    assert counts["LIKELY_FALSE"] == 0
    assert counts["LEANING_TRUE"] == 0
    assert compute_overall_verdict_label([factual, opinion, inference]) == "Highly Likely True"

    verdict, key_issue, _ = generate_sophisticated_assessment(
        [factual, opinion, inference]
    )
    assert verdict.value == "Likely to be True"


def test_tl_style_factual_ladder_still_core():
    """tL regression: classic checkable facts stay on the TRUE/FALSE histogram."""
    lipozemish = Claim(
        claim_id=10,
        claim_text="Clinical trials showed a 12% reduction in body fat over 90 days.",
        timestamp="01:00",
        speaker="Host",
        initial_assessment="Pending",
        verification_result={"result": "LIKELY_FALSE"},
        claim_kind=classify_claim_kind(
            "Clinical trials showed a 12% reduction in body fat over 90 days."
        ),
    )
    # Pure clinical claim with % but no method verbs → source_backed_fact
    assert lipozemish.claim_kind == ClaimKind.SOURCE_BACKED_FACT.value
    assert is_core_factual_claim(lipozemish)
    counts = _verdict_counts([lipozemish])
    assert counts["LIKELY_FALSE"] == 1
    assert compute_overall_verdict_label([lipozemish]) == "Highly Likely False"


def test_analyst_genre_replaces_craap_section():
    claims = [
        {"claim_kind": "data_derived_inference", "claim_text": "LRO $10M"},
        {"claim_kind": "causal_analytical", "claim_text": "because conformity"},
        {"claim_kind": "prediction", "claim_text": "will publish in spring 2027"},
        {"claim_kind": "source_backed_fact", "claim_text": "SB 1507 passed"},
    ]
    assert infer_report_genre(claims) == "analyst"
    section = "\n".join(build_sift_method_section(claims))
    assert "Method & Reliance Review (SIFT)" in section
    assert "CRAAP" in section  # explained as the bar we are not using
    factual = [{"claim_kind": "source_backed_fact", "claim_text": "passed 17-13"}]
    assert infer_report_genre(factual) == "consumer_factual"
