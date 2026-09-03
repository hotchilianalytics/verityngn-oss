"""Compare transcript-only vs multimodal claim inventories."""
from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List, Optional, Set

from verityngn.services.report.display_labels import is_visual_only_claim


_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)
_WS_RE = re.compile(r"\s+")


def normalize_claim_text(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace for set matching."""
    if not text:
        return ""
    s = str(text).lower().strip()
    s = _PUNCT_RE.sub(" ", s)
    s = _WS_RE.sub(" ", s).strip()
    return s


def _claim_text(claim: Any) -> str:
    if isinstance(claim, dict):
        return str(claim.get("claim_text") or claim.get("text") or "").strip()
    return str(claim or "").strip()


def _source_type(claim: Any) -> str:
    if isinstance(claim, dict):
        return str(claim.get("source_type") or "unknown").strip().lower() or "unknown"
    return "unknown"


def _indexed(claims: List[Any]) -> Dict[str, Dict[str, Any]]:
    """Map normalized text → first original claim dict (with claim_text)."""
    out: Dict[str, Dict[str, Any]] = {}
    for c in claims or []:
        raw = _claim_text(c)
        key = normalize_claim_text(raw)
        if not key or key in out:
            continue
        if isinstance(c, dict):
            item = dict(c)
            item.setdefault("claim_text", raw)
        else:
            item = {"claim_text": raw, "source_type": "unknown"}
        out[key] = item
    return out


def compare_claim_inventories(
    transcript_claims: Optional[List[Any]],
    multimodal_claims: Optional[List[Any]],
    *,
    unique_mm_share_threshold: float = 0.15,
) -> Dict[str, Any]:
    """
    Claim-level Jaccard + only_transcript / only_multimodal / both lists.

    decision_hint:
      - multimodal_adds_unique if only_multimodal share of union ≥ threshold
      - inventories_align if overlap high and few unique-to-MM
      - insufficient_pair if either side missing
    """
    tx = _indexed(transcript_claims or [])
    mm = _indexed(multimodal_claims or [])
    tx_keys: Set[str] = set(tx)
    mm_keys: Set[str] = set(mm)

    if not transcript_claims and not multimodal_claims:
        return {
            "n_transcript": 0,
            "n_multimodal": 0,
            "n_both": 0,
            "n_only_transcript": 0,
            "n_only_multimodal": 0,
            "claim_jaccard": None,
            "only_transcript": [],
            "only_multimodal": [],
            "both": [],
            "multimodal_source_type_histogram": {},
            "only_multimodal_share_of_union": None,
            "visual_only_multimodal_count": 0,
            "visual_only_multimodal_share": None,
            "only_multimodal_visual_count": 0,
            "decision_hint": "insufficient_pair",
        }

    both_keys = tx_keys & mm_keys
    only_tx = tx_keys - mm_keys
    only_mm = mm_keys - tx_keys
    union = tx_keys | mm_keys
    jaccard = (len(both_keys) / len(union)) if union else 1.0
    only_mm_share = (len(only_mm) / len(union)) if union else 0.0

    mm_hist = Counter(_source_type(c) for c in (multimodal_claims or []))
    visual_only_mm = sum(1 for c in (multimodal_claims or []) if is_visual_only_claim(_source_type(c)))
    visual_only_share = (visual_only_mm / len(mm_keys)) if mm_keys else 0.0
    only_mm_visual = sum(1 for k in only_mm if is_visual_only_claim(mm[k].get("source_type")))

    if not transcript_claims or not multimodal_claims:
        hint = "insufficient_pair"
    elif only_mm_share >= unique_mm_share_threshold:
        hint = "multimodal_adds_unique"
    elif jaccard >= 0.7:
        hint = "inventories_align"
    else:
        hint = "partial_overlap"

    def _list(keys: Set[str], src: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [src[k] for k in sorted(keys, key=lambda x: src[x].get("claim_text", x))]

    both_rows = []
    for k in sorted(both_keys, key=lambda x: tx[x].get("claim_text", x)):
        both_rows.append(
            {
                "claim_text": tx[k].get("claim_text"),
                "transcript": tx[k],
                "multimodal": mm[k],
            }
        )

    return {
        "n_transcript": len(tx_keys),
        "n_multimodal": len(mm_keys),
        "n_both": len(both_keys),
        "n_only_transcript": len(only_tx),
        "n_only_multimodal": len(only_mm),
        "claim_jaccard": round(jaccard, 4),
        "only_transcript": _list(only_tx, tx),
        "only_multimodal": _list(only_mm, mm),
        "both": both_rows,
        "multimodal_source_type_histogram": dict(mm_hist),
        "only_multimodal_share_of_union": round(only_mm_share, 4),
        "visual_only_multimodal_count": visual_only_mm,
        "visual_only_multimodal_share": round(visual_only_share, 4),
        "only_multimodal_visual_count": only_mm_visual,
        "decision_hint": hint,
    }


def evaluate_genre_sleeve_gate(
    compare_result: Dict[str, Any],
    *,
    visual_only_share_threshold: float = 0.25,
) -> Dict[str, Any]:
    """
    T-ABL-004 gate: sleeve validated when visual-only share is high enough
    on genre-appropriate seeds (not talky VSLs).
    """
    share = compare_result.get("visual_only_multimodal_share")
    hint = compare_result.get("decision_hint")
    passed = (
        share is not None
        and float(share) >= visual_only_share_threshold
        and hint in ("multimodal_adds_unique", "partial_overlap")
    )
    return {
        "visual_only_share_threshold": visual_only_share_threshold,
        "visual_only_multimodal_share": share,
        "sleeve_validated": passed,
        "recommendation": "validate_sleeve" if passed else "audit_path_only",
    }
