#!/usr/bin/env python3
"""Fail if hosted-commercial product markers leak into the OSS package tree.

Research features (predictions, quant, fusion, affect, RiskFactor sensors) are
first-class OSS. Hosted billing, trial credits, and multi-tenant gallery paths
must stay in commercial overlays.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "verityngn"

# Path/name tokens that indicate hosted commercial product code
FORBIDDEN_NAME_SUBSTR = (
    "stripe",
    "dr_credits",
    "trial_credits",
    "verityindex_commercial",
    "billing_webhook",
    "sendgrid_api",
)

# Content markers (light scan of .py under services/)
FORBIDDEN_CONTENT = (
    "stripe.api_key",
    "dr_credits_remaining",
    "trial_credits_remaining",
    "gs://verityindex_commercial/",
    "verityngn_backend_commercial",
)


def main() -> int:
    if not PKG.is_dir():
        print(f"missing package: {PKG}", file=sys.stderr)
        return 2
    hits: list[str] = []
    for path in PKG.rglob("*"):
        if path.is_dir() or "__pycache__" in path.parts:
            continue
        lower = path.name.lower()
        for tok in FORBIDDEN_NAME_SUBSTR:
            if tok in lower:
                hits.append(f"name:{path.relative_to(ROOT)}")
        if path.suffix == ".py" and "services" in path.parts:
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for tok in FORBIDDEN_CONTENT:
                if tok in text:
                    hits.append(f"content:{path.relative_to(ROOT)}:{tok}")
    if hits:
        print("FAIL: commercial product markers in OSS package:", file=sys.stderr)
        for h in hits:
            print(f"  {h}", file=sys.stderr)
        return 1
    print("OK: open-core boundary scrub clean (commercial markers absent)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
