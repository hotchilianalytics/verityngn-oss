#!/usr/bin/env python3
"""Fail if predictions/quant/Karp/riskfactor product paths appear under verityngn/."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "verityngn"
FORBIDDEN_DIRS = {
    "predictions",
    "quant",
    "players",
    "mediasphere",
    "text_risk",
    "timeseries",
    "fusion",
    "deception",
    "affect",
}
FORBIDDEN_NAME_SUBSTR = (
    "karp_panel",
    "risk_factor_registry",
    "s00_s15",
    "deflated_sharpe",
)


def main() -> int:
    if not PKG.is_dir():
        print(f"missing package: {PKG}", file=sys.stderr)
        return 2
    services = PKG / "services"
    present = {p.name for p in services.iterdir() if p.is_dir()}
    leaked = present & FORBIDDEN_DIRS
    if leaked:
        print(f"FAIL: forbidden overlay dirs in OSS: {sorted(leaked)}", file=sys.stderr)
        return 1
    hits = []
    for path in PKG.rglob("*"):
        if path.is_dir() or "__pycache__" in path.parts:
            continue
        lower = path.name.lower()
        for tok in FORBIDDEN_NAME_SUBSTR:
            if tok in lower:
                hits.append(str(path.relative_to(ROOT)))
    if hits:
        print("FAIL: forbidden tokens in package paths:", file=sys.stderr)
        for h in hits:
            print(f"  {h}", file=sys.stderr)
        return 1
    print("OK: open-core boundary scrub clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
