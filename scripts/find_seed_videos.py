#!/usr/bin/env python3
"""Find duration-stratified YouTube seeds for T-ABL-007 / archive paper.

Usage:
  python scripts/find_seed_videos.py -o evaluation/seed_pool.json
  python scripts/find_seed_videos.py --probe-captions -o evaluation/seed_pool.json
"""
from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

QUERIES = {
    "earnings": [
        "ytsearch8:quarterly earnings analysis charts 12 minutes",
        "ytsearch6:investor presentation slides revenue 20 minutes",
        "ytsearch5:stock earnings walkthrough 8 minutes",
    ],
    "ad": [
        "ytsearch8:supplement review sponsored disclosure 12 minutes",
        "ytsearch6:product comparison on screen labels 10 minutes",
        "ytsearch5:finfluencer stock chart tutorial 15 minutes",
    ],
    "legal": [
        "ytsearch8:congressional hearing exchange 10 minutes",
        "ytsearch6:senate hearing document on screen 15 minutes",
        "ytsearch5:deposition exhibit hearing clip 12 minutes",
    ],
    "vsl": [
        "ytsearch5:weight loss doctor reveals 45 minutes",
        "ytsearch4:health supplement long form review 30 minutes",
    ],
}

STRATA = {
    "S": (0, 600),       # < 10 min
    "M": (600, 900),     # 10–15 min
    "L": (1200, 2400),   # 20–40 min
    "XL": (2400, 100000),  # > 40 min
}


def _gallery_exclusions(repo: Path) -> Set[str]:
    out: Set[str] = {"tLJC8hkK-ao"}  # known VSL exclusion as primary proof
    stats = repo / "papers" / "figures" / "gallery_live_stats.json"
    if stats.is_file():
        data = json.loads(stats.read_text(encoding="utf-8"))
        for r in data.get("reports") or []:
            if r.get("video_id"):
                out.add(r["video_id"])
    seeds = repo / "evaluation" / "genre_ablation_seeds.json"
    if seeds.is_file():
        data = json.loads(seeds.read_text(encoding="utf-8"))
        for s in data.get("seeds") or []:
            if s.get("video_id"):
                out.add(s["video_id"])
    return out


def _yt_search(query: str) -> List[Dict[str, Any]]:
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--print",
        "%(id)s\t%(duration)s\t%(title)s\t%(channel)s",
        query,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=90, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        logger.warning("yt-dlp search failed: %s", exc)
        return []
    rows = []
    for line in (proc.stdout or "").splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        vid, dur_s, title = parts[0].strip(), parts[1].strip(), parts[2].strip()
        channel = parts[3].strip() if len(parts) > 3 else ""
        try:
            dur = int(float(dur_s)) if dur_s and dur_s != "NA" else 0
        except ValueError:
            dur = 0
        if not vid or len(vid) != 11:
            continue
        rows.append(
            {
                "video_id": vid,
                "duration_sec": dur,
                "title": title,
                "channel": channel,
                "url": f"https://www.youtube.com/watch?v={vid}",
            }
        )
    return rows


def _stratum(duration_sec: int) -> Optional[str]:
    for name, (lo, hi) in STRATA.items():
        if lo <= duration_sec < hi:
            return name
    return None


def _probe_captions(video_id: str) -> Dict[str, Any]:
    """Cheap caption presence probe via yt-dlp --list-subs."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    cmd = ["yt-dlp", "--list-subs", "--skip-download", url]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return {"caption_kind": "unknown", "has_subs": None}
    out = (proc.stdout or "") + (proc.stderr or "")
    has = "en" in out.lower() and ("vtt" in out.lower() or "srv3" in out.lower() or "automatic" in out.lower())
    kind = "asr_auto" if "automatic" in out.lower() else ("manual" if has else "none")
    if not has:
        kind = "none"
    return {"caption_kind": kind, "has_subs": has, "list_subs_snippet": out[:400]}


def build_pool(*, probe: bool, per_stratum: int = 4) -> Dict[str, Any]:
    repo = Path(__file__).resolve().parents[1]
    exclude = _gallery_exclusions(repo)
    # Force-include long stress cases
    forced = [
        {
            "video_id": "tLJC8hkK-ao",
            "duration_sec": 3029,
            "title": "Lipozem VSL (known long talky)",
            "channel": "",
            "url": "https://www.youtube.com/watch?v=tLJC8hkK-ao",
            "genre": "vsl",
            "forced": True,
            "notes": "XL stress; exclude as multimodal proof",
        },
        {
            "video_id": "LzExSq9DU9w",
            "duration_sec": 3718,
            "title": "Alphabet 2026 Q2 Earnings Call",
            "channel": "Alphabet Investor Relations",
            "url": "https://www.youtube.com/watch?v=LzExSq9DU9w",
            "genre": "earnings",
            "forced": True,
            "notes": "XL caption-less IR stress (C4)",
        },
        {
            "video_id": "p9nBtboU9KM",
            "duration_sec": 796,
            "title": "Visa quarterly earnings analysis",
            "channel": "Everything Money",
            "url": "https://www.youtube.com/watch?v=p9nBtboU9KM",
            "genre": "earnings",
            "forced": True,
            "notes": "T-ABL-006 G1 reuse",
        },
        {
            "video_id": "Exj5iK_K0Kk",
            "duration_sec": 755,
            "title": "5-Minute Stock Analysis for Beginners",
            "channel": "Let's Talk Money",
            "url": "https://www.youtube.com/watch?v=Exj5iK_K0Kk",
            "genre": "ad",
            "forced": True,
            "notes": "T-ABL-006 G2 reuse",
        },
        {
            "video_id": "2RkQ7mGWMAA",
            "duration_sec": 605,
            "title": "Jack Smith hearing exchange",
            "channel": "The Economic Times",
            "url": "https://www.youtube.com/watch?v=2RkQ7mGWMAA",
            "genre": "legal",
            "forced": True,
            "notes": "T-ABL-006 G3 reuse",
        },
        {
            "video_id": "YJULq4e2pZE",
            "duration_sec": 894,
            "title": "Basler AG Q1 2020 quarterly presentation",
            "channel": "Basler AG",
            "url": "https://www.youtube.com/watch?v=YJULq4e2pZE",
            "genre": "earnings",
            "forced": True,
            "notes": "C4 caption-less official slides",
        },
    ]

    candidates: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    for item in forced:
        seen.add(item["video_id"])
        item["stratum"] = _stratum(int(item["duration_sec"])) or "XL"
        candidates.append(item)

    for genre, queries in QUERIES.items():
        for q in queries:
            for row in _yt_search(q):
                vid = row["video_id"]
                if vid in seen or vid in exclude:
                    continue
                # Skip obvious react/debunk titles
                title_l = (row.get("title") or "").lower()
                if any(x in title_l for x in ("debunk", "reacts to", "exposed scam", "destroyed")):
                    continue
                stratum = _stratum(int(row.get("duration_sec") or 0))
                if not stratum:
                    continue
                row["genre"] = genre
                row["stratum"] = stratum
                row["forced"] = False
                seen.add(vid)
                candidates.append(row)

    # Fill strata
    selected: List[Dict[str, Any]] = []
    by_stratum: Dict[str, List[Dict[str, Any]]] = {k: [] for k in STRATA}
    for c in candidates:
        by_stratum.setdefault(c["stratum"], []).append(c)

    for stratum, rows in by_stratum.items():
        # Prefer forced first
        rows_sorted = sorted(rows, key=lambda r: (not r.get("forced"), r.get("duration_sec") or 0))
        take = rows_sorted[:per_stratum]
        selected.extend(take)

    if probe:
        for s in selected:
            if s.get("forced") and s["video_id"] in ("YJULq4e2pZE", "LzExSq9DU9w"):
                s["caption_probe"] = {"caption_kind": "none", "has_subs": False, "notes": "known C4"}
                continue
            if s.get("forced") and s["video_id"] in ("p9nBtboU9KM", "Exj5iK_K0Kk", "2RkQ7mGWMAA", "tLJC8hkK-ao"):
                s["caption_probe"] = {"caption_kind": "asr_auto", "has_subs": True, "notes": "known captions"}
                continue
            s["caption_probe"] = _probe_captions(s["video_id"])

    counts = {k: sum(1 for s in selected if s.get("stratum") == k) for k in STRATA}
    return {
        "trial_ids": ["T-ABL-007", "T-TX-002"],
        "n": len(selected),
        "per_stratum_target": per_stratum,
        "stratum_counts": counts,
        "excluded_gallery_count": len(exclude),
        "seeds": selected,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build duration-stratified seed pool")
    parser.add_argument("-o", "--output", default="evaluation/seed_pool.json")
    parser.add_argument("--probe-captions", action="store_true")
    parser.add_argument("--per-stratum", type=int, default=4)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    pool = build_pool(probe=args.probe_captions, per_stratum=args.per_stratum)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(pool, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"output": str(out), "n": pool["n"], "stratum_counts": pool["stratum_counts"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
