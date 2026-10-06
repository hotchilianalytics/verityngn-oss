#!/usr/bin/env python3
"""Score S15 disclosure risk on local files (EDGAR extract or Qin & Yang dump)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from verityngn.services.text_risk.extract import score_disclosure_risk
from verityngn.services.text_risk.edgar import extract_risk_section, qin_yang_loader


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--text-file", type=Path, default=None)
    ap.add_argument("--qin-yang-root", type=Path, default=None)
    ap.add_argument("--ticker", default="")
    ap.add_argument("--out", type=Path, default=ROOT / "data" / "predictions" / "text" / "s15_scores.jsonl")
    args = ap.parse_args()
    rows = []
    if args.text_file:
        raw = args.text_file.read_text(encoding="utf-8", errors="replace")
        rows.append(score_disclosure_risk(extract_risk_section(raw), doc_id=args.text_file.name, ticker=args.ticker))
    if args.qin_yang_root:
        for rec in qin_yang_loader(args.qin_yang_root):
            rows.append(score_disclosure_risk(rec["text"], doc_id=rec["path"], ticker=rec.get("ticker") or args.ticker, asof=rec.get("event_date")))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(f"wrote {args.out} n={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
