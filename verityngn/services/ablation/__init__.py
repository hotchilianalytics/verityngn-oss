"""Ablation: DR full vs direct, and transcript vs multimodal claim inventories."""
from __future__ import annotations

from verityngn.services.ablation.claim_compare import (
    compare_claim_inventories,
    normalize_claim_text,
)
from verityngn.services.ablation.compare import compare_arms, jaccard_overlap
from verityngn.services.ablation.direct import run_dr_direct
from verityngn.services.ablation.multimodal_arm import run_multimodal_claims_arm
from verityngn.services.ablation.runner import run_ablation, run_claims_ablation
from verityngn.services.ablation.sufficiency import (
    compare_sufficiency,
    preflight_features,
    route_decision,
)
from verityngn.services.ablation.transcript_arm import run_transcript_claims_arm

__all__ = [
    "run_ablation",
    "run_claims_ablation",
    "run_dr_direct",
    "run_transcript_claims_arm",
    "run_multimodal_claims_arm",
    "compare_arms",
    "compare_claim_inventories",
    "compare_sufficiency",
    "preflight_features",
    "route_decision",
    "jaccard_overlap",
    "normalize_claim_text",
]
