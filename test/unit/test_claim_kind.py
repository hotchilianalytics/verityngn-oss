"""Unit tests for claim_kind taxonomy and histogram exclusion."""
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
)
from verityngn.workflows.reporting import generate_sophisticated_assessment
from verityngn.workflows.verification import _stamp_lane_on_verified_claim


def test_classify_factual_date_vote():
    kind = classify_claim_kind(
        "The Oregon Senate passed SB 1507 on February 14, 2026, with a 17–13 vote."
    )
    assert kind == ClaimKind.FACTUAL_SOURCEABLE.value


def test_classify_opinion():
    kind = classify_claim_kind(
        "In my view policymakers should scrap the bill because it seems to hurt competitiveness."
    )
    assert kind == ClaimKind.OPINION_OR_SYNTHESIS.value


def test_classify_author_proof_logic_chain():
    kind = classify_claim_kind(
        "Because Oregon uses rolling conformity, this means federal cuts therefore create "
        "automatic state revenue drops conditioned on the placeholder rewrite."
    )
    assert kind == ClaimKind.AUTHOR_PROOF_CANDIDATE.value


def test_annotate_and_stamp_sets_deeper_research():
    claim = annotate_claim_kind(
        {
            "claim_text": (
                "Because Oregon uses rolling conformity, therefore federal cuts "
                "create automatic state revenue drops conditioned on decoupling."
            )
        }
    )
    assert claim["claim_kind"] == ClaimKind.AUTHOR_PROOF_CANDIDATE.value
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


def test_histogram_excludes_opinion():
    factual = Claim(
        claim_id=1,
        claim_text="SB 1507 passed the Senate 17-13 on February 14, 2026.",
        timestamp="00:10",
        speaker="A",
        initial_assessment="Pending",
        verification_result={"result": "LIKELY_TRUE"},
        claim_kind="factual_sourceable",
    )
    opinion = Claim(
        claim_id=2,
        claim_text="In my view this bill should never have passed.",
        timestamp="00:20",
        speaker="A",
        initial_assessment="Pending",
        verification_result={"result": "LIKELY_FALSE"},
        claim_kind="opinion_or_synthesis",
    )
    assert is_core_factual_claim(factual)
    assert not is_core_factual_claim(opinion)
    counts = _verdict_counts([factual, opinion])
    assert counts["LIKELY_TRUE"] == 1
    assert counts["LIKELY_FALSE"] == 0
    assert compute_overall_verdict_label([factual, opinion]) == "Highly Likely True"

    verdict, key_issue, _ = generate_sophisticated_assessment([factual, opinion])
    assert "false" not in key_issue.lower() or "0.0% false" in key_issue or "predominantly" in key_issue.lower()
    # Opinion false should not dominate — only one factual LIKELY_TRUE
    assert verdict.value == "Likely to be True"
