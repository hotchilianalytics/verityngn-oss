#!/usr/bin/env python3
"""Factor hygiene gates on a media-factor JSONL panel."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from verityngn.services.quant.hygiene import run_factor_hygiene, write_hygiene


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--panel", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    rows = [json.loads(l) for l in args.panel.read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = [r for r in rows if r.get("prediction") is not None and r.get("y") is not None]

    # Synthetic weekly memberships from tickers present (smoke only)
    by_date = {}
    for r in rows:
        by_date.setdefault(str(r.get("date")), set()).add(str(r.get("ticker")))
    memberships = [by_date[d] for d in sorted(by_date)]

    result = run_factor_hygiene(rows, weekly_memberships=memberships)
    write_hygiene(result, args.out)
    print(json.dumps(result.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
