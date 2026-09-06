#!/usr/bin/env python3
"""A/B Deep Research models on frozen sb1507 sanitize input.

Usage:
  python scripts/ab_deep_research_models.py \\
    --sanitize outputs/sb1507/3f70063ddbd_deep_sanitized_input.json \\
    --out outputs/sb1507/model_ab
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path


MODELS = [
    "gemini-3.6-flash",
    "gemini-3.8-flash",
]

_REF_RE = re.compile(
    r"\[Reference:\s*(https?://[^\]\s]+|Currently Claim is Unverified)\]",
    re.IGNORECASE,
)


def score_markdown(md: str, grounding_uris: list) -> dict:
    refs = _REF_RE.findall(md or "")
    unverified = sum(1 for r in refs if "unverified" in r.lower())
    url_refs = [r for r in refs if r.lower().startswith("http")]
    uri_set = set(grounding_uris or [])
    in_ground = sum(1 for u in url_refs if u in uri_set)
    return {
        "ref_total": len(refs),
        "ref_unverified": unverified,
        "ref_url": len(url_refs),
        "ref_url_in_grounding": in_ground,
        "pct_unverified": round(100.0 * unverified / max(1, len(refs)), 1),
        "pct_urls_grounded": round(100.0 * in_ground / max(1, len(url_refs)), 1) if url_refs else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sanitize", required=True)
    ap.add_argument("--out", default="outputs/sb1507/model_ab")
    ap.add_argument("--models", nargs="*", default=MODELS)
    args = ap.parse_args()

    # Load dotenv if present
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    sanitize_path = Path(args.sanitize)
    data = json.loads(sanitize_path.read_text(encoding="utf-8"))
    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)

    # Ensure primary pack present (domain-class resolver)
    try:
        from verityngn.services.deepresearch.primary_pack import inject_primary_pack

        data = inject_primary_pack(data)
    except Exception as exc:
        print(f"primary pack skipped: {exc}")

    rows = []
    for model in args.models:
        os.environ["DEEP_RESEARCH_MODEL"] = model
        os.environ["DEEP_RESEARCH_FALLBACK_MODEL"] = model  # isolate — no silent swap
        # Re-import settings/client each time is hard; call generate_content via client helper
        from verityngn.services.deepresearch import client as dr_client

        # Force reload of module-level settings by patching attributes
        dr_client.DEEP_RESEARCH_MODEL = model
        dr_client.DEEP_RESEARCH_FALLBACK_MODEL = model

        t0 = time.time()
        status = "ok"
        err = ""
        result = None
        try:
            result = dr_client.run_deep_research(data)
        except Exception as exc:  # noqa: BLE001
            status = "error"
            err = str(exc)
        elapsed = round(time.time() - t0, 2)

        md = (result.markdown if result else "") or ""
        uris = list(result.grounding_uris if result else []) or []
        queries = list(result.queries if result else []) or []
        scores = score_markdown(md, uris)
        # crude on-topic check vs known primaries
        primary_needles = (
            "olis.oregonlegislature.gov",
            "oregon.gov/dor",
            "ballotpedia.org",
            "capitolchronicle",
            "statesmanjournal",
        )
        on_topic = sum(1 for u in uris if any(n in u.lower() for n in primary_needles))
        on_topic += sum(1 for u in _REF_RE.findall(md) if any(n in u.lower() for n in primary_needles))

        row = {
            "model": model,
            "status": status,
            "error": err[:300],
            "latency_s": elapsed,
            "output_bytes": len(md.encode("utf-8")),
            "grounding_uri_count": len(uris),
            "web_search_queries_count": len(queries),
            "on_topic_hits": on_topic,
            **scores,
        }
        rows.append(row)
        model_dir = out_root / model.replace("/", "_")
        model_dir.mkdir(parents=True, exist_ok=True)
        (model_dir / "report.md").write_text(md, encoding="utf-8")
        (model_dir / "meta.json").write_text(json.dumps(row, indent=2), encoding="utf-8")
        print(json.dumps(row, indent=2))

    summary_path = out_root / "ab_summary.json"
    summary_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"\nWrote {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
