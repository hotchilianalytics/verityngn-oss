#!/usr/bin/env python3
"""Re-categorize sb1507 (or any report JSON) under the analyst risk taxonomy.

Writes a rolling scorecard to outputs/sb1507_risk_taxonomy_loop/scorecard.json.
Exit 0 when all acceptance criteria are green; exit 1 otherwise.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from verityngn.workflows.claim_kind import (  # noqa: E402
    ClaimKind,
    annotate_claim_kind,
    classify_claim_kind,
    is_core_factual_claim,
    is_quantitative_method_claim,
    normalize_claim_kind,
)
from verityngn.workflows.verification import _stamp_lane_on_verified_claim  # noqa: E402


def _load_claims(report_path: Path) -> list:
    data = json.loads(report_path.read_text())
    claims = data.get("claims_breakdown") or data.get("claims") or []
    return [c for c in claims if isinstance(c, dict)]


def build_scorecard(claims: list) -> dict:
    recategorized = []
    kind_counts: dict[str, int] = {}
    quant_total = 0
    quant_inference = 0
    false_opinion = 0
    pred_false = 0
    section_61 = 0
    deeper_generic_uncertain = 0

    for raw in claims:
        text = raw.get("claim_text") or raw.get("claim") or ""
        annotated = annotate_claim_kind(dict(raw))
        # Preserve prior verification result for stamp routing; re-stamp dual metrics
        prior_vr = dict(raw.get("verification_result") or {})
        if not prior_vr.get("result"):
            prior_vr["result"] = "UNCERTAIN"
        stamped = _stamp_lane_on_verified_claim(annotated, prior_vr)
        kind = normalize_claim_kind(stamped.get("claim_kind"))
        kind_counts[kind] = kind_counts.get(kind, 0) + 1
        if is_core_factual_claim(stamped):
            section_61 += 1
        if is_quantitative_method_claim(text):
            quant_total += 1
            if kind == ClaimKind.DATA_DERIVED_INFERENCE.value:
                quant_inference += 1
        result = (stamped.get("verification_result") or {}).get("result", "")
        if kind == ClaimKind.REASONED_OPINION.value and result in {
            "LIKELY_FALSE",
            "HIGHLY_LIKELY_FALSE",
        }:
            false_opinion += 1
        if kind == ClaimKind.PREDICTION.value and result in {
            "LIKELY_FALSE",
            "HIGHLY_LIKELY_FALSE",
        }:
            pred_false += 1
        # §6.3/6.8 should not be dominated by generic UNCERTAIN source_backed facts
        if (
            kind == ClaimKind.SOURCE_BACKED_FACT.value
            and result in {"UNCERTAIN", "UNVERIFIABLE"}
            and stamped.get("needs_deeper_research")
        ):
            deeper_generic_uncertain += 1

        recategorized.append(
            {
                "claim_text": text[:160],
                "claim_kind": kind,
                "result": result,
                "evidence_confidence": (stamped.get("verification_result") or {}).get(
                    "evidence_confidence"
                ),
                "residual_reliance_risk": (stamped.get("verification_result") or {}).get(
                    "residual_reliance_risk"
                ),
                "risk_chip": (stamped.get("verification_result") or {}).get("risk_chip"),
            }
        )

    total = len(claims) or 1
    quant_pct = (quant_inference / quant_total * 100) if quant_total else 100.0
    section_61_half = section_61 <= max(1, len(claims) // 2)

    acceptance = {
        "quant_method_to_inference_pct_ge_60": quant_pct >= 60.0,
        "section_61_le_half_total": section_61_half,
        "section_deeper_not_dominated_by_uncertain_facts": deeper_generic_uncertain
        <= max(2, section_61 // 3),
        "zero_predictions_likely_false": pred_false == 0,
        "false_opinion_rate_zero": false_opinion == 0,
    }
    all_green = all(acceptance.values())

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_claims": len(claims),
        "kind_counts": kind_counts,
        "section_61_fact_rows": section_61,
        "quantitative_method_claims": quant_total,
        "quantitative_in_data_derived_inference": quant_inference,
        "quant_method_to_inference_pct": round(quant_pct, 1),
        "false_opinion_count": false_opinion,
        "predictions_labeled_likely_false": pred_false,
        "deeper_generic_uncertain_facts": deeper_generic_uncertain,
        "acceptance": acceptance,
        "all_green": all_green,
        "claims": recategorized,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--report",
        type=Path,
        default=ROOT / "outputs/finish_smoke_sb1507/3f70063ddbd_report.json",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "outputs/sb1507_risk_taxonomy_loop",
    )
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    claims = _load_claims(args.report)
    scorecard = build_scorecard(claims)
    out = args.out_dir / "scorecard.json"
    out.write_text(json.dumps(scorecard, indent=2))
    # Rolling history append
    hist = args.out_dir / "scorecard_history.jsonl"
    with hist.open("a") as f:
        f.write(
            json.dumps(
                {
                    "generated_at": scorecard["generated_at"],
                    "all_green": scorecard["all_green"],
                    "kind_counts": scorecard["kind_counts"],
                    "acceptance": scorecard["acceptance"],
                    "quant_pct": scorecard["quant_method_to_inference_pct"],
                    "section_61": scorecard["section_61_fact_rows"],
                }
            )
            + "\n"
        )
    print(json.dumps({k: scorecard[k] for k in (
        "total_claims",
        "kind_counts",
        "section_61_fact_rows",
        "quant_method_to_inference_pct",
        "acceptance",
        "all_green",
    )}, indent=2))
    print(f"Wrote {out}")
    return 0 if scorecard["all_green"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
