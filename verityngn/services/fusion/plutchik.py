"""
Plutchik 4-tier emotion taxonomy — ported from Taxonomy_Plutchik.ipynb
and reconciled with Spot Runner `sr_*` segment IDs.

Closure rule (from sr_iris_test_05.py):
  closure([sr_a_b_c]) = [sr_a_b_c, sr_a_b, sr_a]

Tier weights: w(tier_1) < w(tier_2) < w(tier_3) < w(tier_4)
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional
import csv


PRIMARY = ["joy", "trust", "fear", "surprise", "sadness", "disgust", "anger", "anticipation"]

SECONDARY: dict[str, list[str]] = {
    "joy": ["ecstasy", "serenity"],
    "trust": ["admiration", "acceptance"],
    "fear": ["terror", "apprehension"],
    "surprise": ["amazement", "distraction"],
    "sadness": ["grief", "pensiveness"],
    "disgust": ["loathing", "boredom"],
    "anger": ["rage", "annoyance"],
    "anticipation": ["vigilance", "interest"],
}

TERTIARY: dict[str, list[str]] = {
    "ecstasy": ["delight", "excitement"],
    "serenity": ["calm", "contentment"],
    "admiration": ["respect", "awe"],
    "acceptance": ["forgiveness", "familiarity"],
    "terror": ["panic", "horror"],
    "apprehension": ["nervousness", "worry"],
    "amazement": ["shock", "astonishment"],
    "distraction": ["confusion", "perplexity"],
    "grief": ["despair", "sorrow"],
    "pensiveness": ["reflection", "contemplation"],
    "loathing": ["hate", "revulsion"],
    "boredom": ["disinterest", "apathy"],
    "rage": ["wrath", "fury"],
    "annoyance": ["irritation", "frustration"],
    "vigilance": ["alertness", "attention"],
    "interest": ["curiosity", "expectation"],
}

# Tier weights: deeper = stronger
TIER_WEIGHT = {1: 0.25, 2: 0.5, 3: 0.75, 4: 1.0}


@dataclass
class TaxonomyRow:
    segment_type: str
    segment_id: str
    tier_1: str
    tier_2: str
    tier_3: str
    tier_4: str = ""

    def to_list(self) -> list[str]:
        return [
            self.segment_type,
            self.segment_id,
            self.tier_1,
            self.tier_2,
            self.tier_3,
            self.tier_4,
        ]


def build_taxonomy_rows() -> list[TaxonomyRow]:
    """Emit all leaf paths as sr_<t1>_<t2>_<t3> plus intermediate closures as rows."""
    rows: list[TaxonomyRow] = []
    seen: set[str] = set()

    def _add(seg_id: str, t1: str, t2: str = "", t3: str = "", t4: str = "") -> None:
        if seg_id in seen:
            return
        seen.add(seg_id)
        rows.append(
            TaxonomyRow(
                segment_type="Emotion",
                segment_id=seg_id,
                tier_1=t1,
                tier_2=t2,
                tier_3=t3,
                tier_4=t4,
            )
        )

    for t1 in PRIMARY:
        _add(f"sr_{t1}", t1)
        for t2 in SECONDARY[t1]:
            _add(f"sr_{t1}_{t2}", t1, t2)
            for t3 in TERTIARY[t2]:
                _add(f"sr_{t1}_{t2}_{t3}", t1, t2, t3)
    return rows


def write_taxonomy_csv(path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = build_taxonomy_rows()
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Segment Type", "segment_id", "tier_1", "tier_2", "tier_3", "tier_4"])
        for r in rows:
            w.writerow(r.to_list())
    return path


def closure(segment_id: str) -> list[str]:
    """
    Expand a leaf/mid segment to itself plus ancestors.

    Example: sr_joy_ecstasy_delight → [sr_joy_ecstasy_delight, sr_joy_ecstasy, sr_joy]
    """
    if not segment_id.startswith("sr_"):
        return [segment_id]
    parts = segment_id.split("_")[1:]  # drop 'sr'
    out = []
    for i in range(len(parts), 0, -1):
        out.append("sr_" + "_".join(parts[:i]))
    return out


def tier_of(segment_id: str) -> int:
    if not segment_id.startswith("sr_"):
        return 0
    return len(segment_id.split("_")) - 1  # sr + n parts


def tier_weight(segment_id: str) -> float:
    return TIER_WEIGHT.get(tier_of(segment_id), 0.25)


def load_taxonomy(path: Optional[Path] = None) -> list[dict[str, str]]:
    if path is None:
        # Prefer generated CSV next to this package data dir
        default = Path(__file__).resolve().parents[3] / "data" / "taxonomy" / "plutchik_sr.csv"
        path = default if default.exists() else None
    if path is None or not Path(path).exists():
        return [
            {
                "segment_type": r.segment_type,
                "segment_id": r.segment_id,
                "tier_1": r.tier_1,
                "tier_2": r.tier_2,
                "tier_3": r.tier_3,
                "tier_4": r.tier_4,
            }
            for r in build_taxonomy_rows()
        ]
    out = []
    with Path(path).open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize header variants
            sid = row.get("segment_id") or row.get("Segment ID") or ""
            out.append(
                {
                    "segment_type": row.get("Segment Type") or row.get("segment_type") or "Emotion",
                    "segment_id": sid,
                    "tier_1": row.get("tier_1") or "",
                    "tier_2": row.get("tier_2") or "",
                    "tier_3": row.get("tier_3") or "",
                    "tier_4": row.get("tier_4") or "",
                }
            )
    return out


def reconcile_with_spot_runner(spot_csv: Path) -> dict[str, object]:
    """Compare generated IDs to Spot Runner master CSV; return overlap report."""
    ours = {r.segment_id for r in build_taxonomy_rows()}
    theirs: set[str] = set()
    if Path(spot_csv).exists():
        with Path(spot_csv).open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sid = row.get("segment_id") or ""
                if sid.startswith("sr_"):
                    theirs.add(sid)
    return {
        "ours_n": len(ours),
        "theirs_n": len(theirs),
        "intersection_n": len(ours & theirs),
        "only_ours_sample": sorted(ours - theirs)[:10],
        "only_theirs_sample": sorted(theirs - ours)[:10],
        "match_rate": (len(ours & theirs) / max(1, len(ours))),
    }


def map_affect_to_segments(
    text_sentiment: float,
    exuberance: float,
    arousal: float,
) -> list[dict[str, object]]:
    """
    Heuristic map from Tier-1 measured features onto Plutchik leaves.
    Research labeling aid — not a clinical emotion diagnosis.
    """
    hits: list[dict[str, object]] = []
    if exuberance >= 0.6 and text_sentiment >= 0.0:
        seg = "sr_joy_ecstasy_excitement" if exuberance >= 0.75 else "sr_joy_serenity_contentment"
        hits.append({"segment_id": seg, "relevance": int(60 + 40 * exuberance), "closure": closure(seg)})
    if arousal >= 0.65 and text_sentiment < 0.0:
        seg = "sr_fear_apprehension_nervousness"
        hits.append({"segment_id": seg, "relevance": int(50 + 40 * arousal), "closure": closure(seg)})
    if text_sentiment < -0.3:
        seg = "sr_sadness_pensiveness_reflection"
        hits.append({"segment_id": seg, "relevance": int(40 + 40 * abs(text_sentiment)), "closure": closure(seg)})
    if text_sentiment > 0.3 and exuberance < 0.45:
        seg = "sr_trust_acceptance_familiarity"
        hits.append({"segment_id": seg, "relevance": 55, "closure": closure(seg)})
    if not hits:
        seg = "sr_anticipation_interest_curiosity"
        hits.append({"segment_id": seg, "relevance": 40, "closure": closure(seg)})
    return hits
