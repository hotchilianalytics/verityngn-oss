#!/usr/bin/env python3
"""Build / validate docs/predictions/events/{lane}/{entity}.json catalogs.

Converts legacy per-player video catalogs into the shared event schema,
or validates an existing tree.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EVENTS_ROOT = ROOT / "docs" / "predictions" / "events"


def _as_events_from_legacy(raw: dict[str, Any]) -> dict[str, Any]:
    items = list(raw.get("existing_corpus") or []) + list(raw.get("run_five") or [])
    events = []
    ticker = raw.get("ticker") or ""
    speaker = raw.get("player_id") or raw.get("speaker_id") or ""
    for item in items:
        vid = item.get("video_id")
        events.append(
            {
                "event_id": f"{ticker.lower()}-{item.get('next_print')}-{vid}",
                "event_date": item.get("next_print"),
                "kind": "earnings",
                "window": item.get("window"),
                "source_id": vid,
                "source_url": item.get("source") or (f"https://www.youtube.com/watch?v={vid}" if vid else ""),
                "recorded": item.get("recorded"),
                "print_label": item.get("print_label"),
                "outcome_kind": "equity_car",
                "title": item.get("title"),
            }
        )
    return {
        "schema_version": "1.0",
        "lane": "video",
        "speaker_id": speaker,
        "ticker": ticker,
        "events": events,
    }


def validate(doc: dict[str, Any]) -> list[str]:
    errs = []
    if not doc.get("speaker_id") and not doc.get("ticker"):
        errs.append("need speaker_id or ticker")
    for i, ev in enumerate(doc.get("events") or []):
        if not ev.get("event_date"):
            errs.append(f"events[{i}] missing event_date")
        if not ev.get("kind"):
            errs.append(f"events[{i}] missing kind")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--from-legacy", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--validate-tree", action="store_true")
    args = ap.parse_args()
    if args.from_legacy:
        raw = json.loads(args.from_legacy.read_text(encoding="utf-8"))
        doc = _as_events_from_legacy(raw)
        errs = validate(doc)
        if errs:
            print("INVALID", errs)
            return 1
        out = args.out or (EVENTS_ROOT / "video" / f"{doc['speaker_id']}.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {out} n_events={len(doc['events'])}")
        return 0
    if args.validate_tree:
        n = 0
        for p in EVENTS_ROOT.rglob("*.json"):
            doc = json.loads(p.read_text(encoding="utf-8"))
            errs = validate(doc)
            n += 1
            print(p.relative_to(ROOT), "OK" if not errs else errs)
        print(f"checked {n} catalogs")
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
