"""Claim-kind taxonomy for analyst / deep-data videos (ICD 203 + Full Fact aligned).

Separates source-backed facts from data-derived inferences, causal analysis,
reasoned opinions, predictions, and unverified assertions so reports stay
parseable and Chris-style method claims are not discounted for missing
academic cites.
"""
from __future__ import annotations

import logging
import re
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class ClaimKind(str, Enum):
    # Canonical (v3.1 analyst taxonomy)
    SOURCE_BACKED_FACT = "source_backed_fact"
    DATA_DERIVED_INFERENCE = "data_derived_inference"
    CAUSAL_ANALYTICAL = "causal_analytical"
    REASONED_OPINION = "reasoned_opinion"
    PREDICTION = "prediction"
    UNVERIFIED_ASSERTION = "unverified_assertion"
    # Legacy aliases kept as enum members for one release
    FACTUAL_SOURCEABLE = "factual_sourceable"
    AUTHOR_PROOF_CANDIDATE = "author_proof_candidate"
    OPINION_OR_SYNTHESIS = "opinion_or_synthesis"
    NEW_REPORT_CONCLUSION = "new_report_conclusion"


# Normalize legacy → canonical
KIND_ALIASES: Dict[str, str] = {
    ClaimKind.FACTUAL_SOURCEABLE.value: ClaimKind.SOURCE_BACKED_FACT.value,
    ClaimKind.AUTHOR_PROOF_CANDIDATE.value: ClaimKind.CAUSAL_ANALYTICAL.value,
    ClaimKind.OPINION_OR_SYNTHESIS.value: ClaimKind.REASONED_OPINION.value,
    ClaimKind.NEW_REPORT_CONCLUSION.value: ClaimKind.REASONED_OPINION.value,
}

# Only pure source-backed facts feed the core true/false histogram (§6.1).
CORE_HISTOGRAM_KINDS: Set[str] = {
    ClaimKind.SOURCE_BACKED_FACT.value,
    ClaimKind.FACTUAL_SOURCEABLE.value,  # legacy synonym
}

# Kinds excluded from core truthfulness histogram.
NON_CORE_KINDS: Set[str] = {
    ClaimKind.DATA_DERIVED_INFERENCE.value,
    ClaimKind.CAUSAL_ANALYTICAL.value,
    ClaimKind.REASONED_OPINION.value,
    ClaimKind.PREDICTION.value,
    ClaimKind.UNVERIFIED_ASSERTION.value,
    ClaimKind.AUTHOR_PROOF_CANDIDATE.value,
    ClaimKind.OPINION_OR_SYNTHESIS.value,
    ClaimKind.NEW_REPORT_CONCLUSION.value,
}

KIND_DISPLAY_LABELS: Dict[str, str] = {
    ClaimKind.SOURCE_BACKED_FACT.value: "Source-backed fact",
    ClaimKind.DATA_DERIVED_INFERENCE.value: "Data-derived inference",
    ClaimKind.CAUSAL_ANALYTICAL.value: "Causal / analytical",
    ClaimKind.REASONED_OPINION.value: "Reasoned opinion",
    ClaimKind.PREDICTION.value: "Prediction",
    ClaimKind.UNVERIFIED_ASSERTION.value: "Unverified assertion",
    ClaimKind.FACTUAL_SOURCEABLE.value: "Source-backed fact",
    ClaimKind.AUTHOR_PROOF_CANDIDATE.value: "Causal / analytical",
    ClaimKind.OPINION_OR_SYNTHESIS.value: "Reasoned opinion",
    ClaimKind.NEW_REPORT_CONCLUSION.value: "Reasoned opinion",
}

LANE_BY_KIND: Dict[str, str] = {
    ClaimKind.SOURCE_BACKED_FACT.value: "factual",
    ClaimKind.DATA_DERIVED_INFERENCE.value: "inference",
    ClaimKind.CAUSAL_ANALYTICAL.value: "analytical",
    ClaimKind.REASONED_OPINION.value: "opinion",
    ClaimKind.PREDICTION.value: "prediction",
    ClaimKind.UNVERIFIED_ASSERTION.value: "unverified",
}

VALUE_OPINION_MARKERS = (
    "should ",
    "must ",
    "ought ",
    "i believe",
    "we believe",
    "in my view",
    "in our view",
    "the takeaway",
    "bottom line",
    "my conclusion",
    "our conclusion",
    "reckless",
    "priority should",
    "ought to",
)

PREDICTION_MARKERS = (
    "forecast",
    "will probably",
    "going to be",
    "projected to",
    "is expected to",
    "will raise",
    "will reduce",
    "will cost",
    "next session",
    "in 2027",
    "by 2027",
    "future revenue",
    "would raise",
    "would reduce",
    "project full",
    "timelines project",
    "to publish in spring",
    "actuals in spring",
)

METHOD_INFERENCE_MARKERS = (
    "minhash",
    "clustering",
    "deduplicat",
    "after adjusting",
    "adjusted for",
    "modeling",
    "modelled",
    "modeled",
    "to model",
    "estimate",
    "estimated",
    "calculation",
    "calculated",
    "analysis shows",
    "when collapsing",
    "distinct individuals",
    "unique individuals",
    "non-form letter",
    "form letter",
    "copy-paste",
    "rate rose",
    "rate fell",
    "variance",
    "delta of",
    "bridge",
    "lro ",
    "legislative revenue",
    "revenue impact",
    "revenue forecast",
    "assumed static",
    "static taxpayer",
    "capital flight",
    "capital migration",
    "qsbs",
    "bonus depreciation",
    "section 179",
    "section 168",
    "filtering out",
    "unadjusted",
    "raw counts",
    "on-screen graphic",
    "associated with the decoupling",
    "collapsing",
    "testimony leaves",
    "written testimony",
    "testimony submissions",
)

BIO_OR_COLOR_MARKERS = (
    "generation oregonian",
    "my wife",
    "fourth-generation",
    "fifth-generation",
    "i am a",
    "personally",
)

CAUSAL_MARKERS = (
    "because ",
    "therefore",
    "which means",
    "this means",
    "as a result",
    "thus ",
    "hence ",
    "so that",
    "conditioned on",
    "conditioned upon",
    "due to",
    "caused by",
    "leads to",
    "results in",
    "rolling conformity",
    "decoupl",
    "gut and stuff",
    "placeholder",
    "legislative concept",
)

FACTUAL_ANCHORS = (
    r"\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}\b",
    r"\b(?:19|20)\d{2}\b",
    r"\b(?:sb|hb|hr|s\.?\s*b\.?)\s*\d{2,5}\b",
    r"\bors\s+\d+",
    r"\barticle\s+[ivxlcdm]+\b",
    r"\b\d{1,3}(?:-\d{1,3})?\s+(?:vote|passed|voted)\b",
    r"\b\d+(?:,\d{3})*(?:\.\d+)?%",
    r"\b\$\d",
)


def normalize_claim_kind(kind: Optional[str]) -> str:
    """Map legacy synonyms to canonical kinds."""
    if not kind:
        return ClaimKind.SOURCE_BACKED_FACT.value
    k = str(kind).strip().lower()
    return KIND_ALIASES.get(k, k)


def claim_kind_display_label(kind: Optional[str]) -> str:
    k = normalize_claim_kind(kind)
    return KIND_DISPLAY_LABELS.get(k, k.replace("_", " ").title())


def classify_claim_kind(
    claim_text: str,
    *,
    source_type: Optional[str] = None,
    report_generated: bool = False,
) -> str:
    """Rule-based claim_kind classifier (no LLM). Returns canonical kind strings."""
    text = (claim_text or "").strip()
    if not text:
        return ClaimKind.SOURCE_BACKED_FACT.value

    if report_generated or (source_type or "").lower() in {
        "report_synthesis",
        "report_generated",
        "verityngn_summary",
    }:
        return ClaimKind.REASONED_OPINION.value

    lower = text.lower()

    # Soft biographical / institutional-color statements → unverified (not T/F ladder)
    if sum(1 for m in BIO_OR_COLOR_MARKERS if m in lower) >= 1 and not re.search(
        r"\b(?:sb|hb|ors|passed|signed|vote)\b", lower
    ):
        return ClaimKind.UNVERIFIED_ASSERTION.value
    if re.search(
        r"\b(?:biennial cycle|even-numbered years originally intended|"
        r"fourth-generation|fifth-generation)\b",
        lower,
    ):
        return ClaimKind.UNVERIFIED_ASSERTION.value

    # Predictions before opinion (forecast language is not a value judgment).
    pred_hits = sum(1 for m in PREDICTION_MARKERS if m in lower)
    if pred_hits >= 1 and re.search(
        r"\b(?:will|would|projected|forecast|expected|next|future|by 20\d{2}|spring 20\d{2}|timelines project|to publish)\b",
        lower,
    ):
        # Pure future/policy outcome language
        if not re.search(r"\b(?:passed|signed|voted|introduced on)\b", lower):
            return ClaimKind.PREDICTION.value

    value_hits = sum(1 for m in VALUE_OPINION_MARKERS if m in lower)
    if value_hits >= 1 and not re.search(
        r"\b(?:act|bill|statute|ors|signed|passed|vote|\$|%|percent)\b", lower
    ):
        return ClaimKind.REASONED_OPINION.value
    if value_hits >= 2:
        return ClaimKind.REASONED_OPINION.value

    method_hits = sum(1 for m in METHOD_INFERENCE_MARKERS if m in lower)
    quant = bool(
        re.search(
            r"(?:\$|\d+(?:,\d{3})*(?:\.\d+)?%|\b\d+\s*percent\b|\bzero percent\b|\bn\s*=\s*\d|"
            r"\btwo-thirds\b|\b\d+\s+unique\b|\b\d+\s+total\b|\bcomprised\s+\d+)",
            text,
            re.I,
        )
    )
    # On-screen modeled $ figures and testimony aggregation are inferences even
    # without classic method verbs when quant + analysis framing co-occur.
    analysis_framing = bool(
        re.search(
            r"\b(?:filtering|unadjusted|graphic|decoupling provisions|raw counts|"
            r"leaves \d+|associated with|form letter|non-form|unique individuals|"
            r"testimony submissions|assumed static|capital flight)\b",
            lower,
        )
    )

    # Institutional conformity / model-mandate analytical claims (before method+quant)
    if re.search(
        r"\b(?:automatically (?:connects|conforms)|rolling(?:\s+\w+)?\s+conformity|"
        r"best available models|no equivalent requirement|no requirement on the lro|"
        r"impose no requirement)\b",
        lower,
    ):
        return ClaimKind.CAUSAL_ANALYTICAL.value

    if method_hits >= 1 and quant:
        return ClaimKind.DATA_DERIVED_INFERENCE.value
    if method_hits >= 2:
        return ClaimKind.DATA_DERIVED_INFERENCE.value
    if quant and analysis_framing:
        return ClaimKind.DATA_DERIVED_INFERENCE.value

    factual_hits = sum(1 for pat in FACTUAL_ANCHORS if re.search(pat, text, re.I))
    causal_hits = sum(1 for m in CAUSAL_MARKERS if m in lower)

    if causal_hits >= 2 and factual_hits <= 3:
        return ClaimKind.CAUSAL_ANALYTICAL.value
    if causal_hits >= 1 and factual_hits <= 1 and len(text) > 100:
        return ClaimKind.CAUSAL_ANALYTICAL.value
    if method_hits >= 1 and causal_hits >= 1:
        return ClaimKind.CAUSAL_ANALYTICAL.value
    # Placeholder / conditional legislative drafting is analytical even with date anchors
    if "placeholder" in lower and causal_hits >= 1:
        return ClaimKind.CAUSAL_ANALYTICAL.value

    return ClaimKind.SOURCE_BACKED_FACT.value


def annotate_claim_kind(claim: Dict[str, Any]) -> Dict[str, Any]:
    """Stamp claim_kind, verification_lane, and initial deeper-research flag."""
    if not isinstance(claim, dict):
        return claim
    text = claim.get("claim_text") or claim.get("claim") or ""
    kind = classify_claim_kind(
        text,
        source_type=claim.get("source_type"),
        report_generated=bool(claim.get("report_generated_inference")),
    )
    kind = normalize_claim_kind(kind)
    claim["claim_kind"] = kind
    claim["verification_lane"] = LANE_BY_KIND.get(kind, "factual")
    claim["claim_kind_label"] = claim_kind_display_label(kind)

    if kind == ClaimKind.SOURCE_BACKED_FACT.value:
        claim.setdefault("needs_deeper_research", False)
        claim["source_path_status"] = claim.get("source_path_status") or "pending"
        claim.setdefault("inherent_reliance_risk", "medium")
    elif kind == ClaimKind.DATA_DERIVED_INFERENCE.value:
        claim["needs_deeper_research"] = False
        claim["source_path_status"] = "method_backed"
        claim["inherent_reliance_risk"] = "medium"
    elif kind == ClaimKind.CAUSAL_ANALYTICAL.value:
        claim["needs_deeper_research"] = True
        claim["source_path_status"] = "assumption_sensitive"
        claim["author_logic_detected"] = True
        claim["inherent_reliance_risk"] = "high"
    elif kind == ClaimKind.REASONED_OPINION.value:
        claim["needs_deeper_research"] = False
        claim["source_path_status"] = "not_applicable"
        claim["inherent_reliance_risk"] = "low"
    elif kind == ClaimKind.PREDICTION.value:
        claim["needs_deeper_research"] = False
        claim["source_path_status"] = "forward_looking"
        claim["inherent_reliance_risk"] = "medium"
    else:  # unverified_assertion
        claim["needs_deeper_research"] = True
        claim["source_path_status"] = "incomplete"
        claim["inherent_reliance_risk"] = "high"
    return claim


def annotate_claims_kind(claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for c in claims or []:
        if isinstance(c, dict):
            out.append(annotate_claim_kind(c))
        else:
            out.append(c)
    kinds: Dict[str, int] = {}
    for c in out:
        if isinstance(c, dict):
            k = normalize_claim_kind(c.get("claim_kind", "unknown"))
            kinds[k] = kinds.get(k, 0) + 1
    logger.info("claim_kind distribution: %s", kinds)
    return out


def get_claim_kind(claim: Any) -> str:
    if isinstance(claim, dict):
        return normalize_claim_kind(
            claim.get("claim_kind") or ClaimKind.SOURCE_BACKED_FACT.value
        )
    kind = getattr(claim, "claim_kind", None)
    if kind:
        return normalize_claim_kind(str(kind))
    vr = getattr(claim, "verification_result", None)
    if isinstance(vr, dict) and vr.get("claim_kind"):
        return normalize_claim_kind(str(vr.get("claim_kind")))
    return ClaimKind.SOURCE_BACKED_FACT.value


def is_core_factual_claim(claim: Any) -> bool:
    """True only for source-backed facts (core §6.1 histogram)."""
    return get_claim_kind(claim) in CORE_HISTOGRAM_KINDS


def is_quantitative_method_claim(claim_text: str) -> bool:
    """Chris-style $/%/method claims used by the risk-taxonomy loop scorecard."""
    text = claim_text or ""
    lower = text.lower()
    method_hits = sum(1 for m in METHOD_INFERENCE_MARKERS if m in lower)
    quant = bool(re.search(r"(?:\$|\d+(?:,\d{3})*(?:\.\d+)?%)", text))
    analysis_framing = bool(
        re.search(
            r"\b(?:filtering|unadjusted|graphic|decoupling provisions|raw counts)\b",
            lower,
        )
    )
    return (method_hits >= 1 and quant) or (quant and analysis_framing)


def needs_deeper_research(claim: Any) -> bool:
    """Author-proof / incomplete-path sleeve — not generic UNCERTAIN facts."""
    kind = get_claim_kind(claim)
    if kind in {
        ClaimKind.CAUSAL_ANALYTICAL.value,
        ClaimKind.UNVERIFIED_ASSERTION.value,
    }:
        return True
    if isinstance(claim, dict):
        # Only honor explicit flag when kind is analytical / incomplete path
        if claim.get("needs_deeper_research") and kind != ClaimKind.SOURCE_BACKED_FACT.value:
            return True
        vr = claim.get("verification_result") or {}
        if isinstance(vr, dict) and vr.get("needs_deeper_research"):
            if kind != ClaimKind.SOURCE_BACKED_FACT.value:
                return True
            # factual + incomplete sources still allowed for author-proof sleeve
            if vr.get("source_path_status") in {"incomplete", "assumption_sensitive"}:
                return True
        return False
    if getattr(claim, "needs_deeper_research", False) and kind != ClaimKind.SOURCE_BACKED_FACT.value:
        return True
    return False


def estimate_evidence_confidence(
    *,
    kind: str,
    has_sources: bool,
    supports_count: int = 0,
    method_transparent: bool = False,
) -> str:
    """ICD-style evidence confidence: Low / Medium / High (not paper density)."""
    kind = normalize_claim_kind(kind)
    if kind == ClaimKind.REASONED_OPINION.value:
        return "n/a"
    if kind == ClaimKind.DATA_DERIVED_INFERENCE.value:
        if method_transparent and (has_sources or supports_count > 0):
            return "High"
        if method_transparent:
            return "Medium"
        return "Low" if not has_sources else "Medium"
    if kind == ClaimKind.PREDICTION.value:
        return "Low" if not has_sources else "Medium"
    if kind == ClaimKind.CAUSAL_ANALYTICAL.value:
        if has_sources and supports_count >= 2:
            return "Medium"
        return "Low"
    # source_backed_fact / unverified
    if supports_count >= 2 and has_sources:
        return "High"
    if has_sources:
        return "Medium"
    return "Low"


def estimate_residual_reliance_risk(
    *,
    kind: str,
    result: str,
    evidence_confidence: str,
    inherent: str = "medium",
) -> str:
    """Basel-style residual reliance risk after verification."""
    kind = normalize_claim_kind(kind)
    result = (result or "").upper()
    if kind == ClaimKind.REASONED_OPINION.value:
        return "low"
    if kind == ClaimKind.UNVERIFIED_ASSERTION.value:
        return "high"
    if kind == ClaimKind.PREDICTION.value:
        return "medium"
    if result in {"HIGHLY_LIKELY_TRUE", "LIKELY_TRUE"} and evidence_confidence == "High":
        return "low"
    if result in {"HIGHLY_LIKELY_FALSE", "LIKELY_FALSE"}:
        return "low"  # correctly flagged; reliance on the claim is abated
    if evidence_confidence == "Low" or result in {"UNCERTAIN", "UNVERIFIABLE"}:
        return "high" if inherent == "high" else "medium"
    return "medium"
