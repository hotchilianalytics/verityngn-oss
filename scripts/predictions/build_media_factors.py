#!/usr/bin/env python3
"""Build PIT media-factor panel (hca-qngn-style) from earnings fixtures + synthetic features."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from verityngn.services.quant.factors import build_media_factor_panel, write_panel
from verityngn.services.timeseries.earnings import load_earnings_fixtures
from verityngn.services.timeseries.event_study import _feature_asof_for_event, _synthetic_pre_event_features


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    events = [e.to_dict() for e in load_earnings_fixtures()]
    features = []
    for e in load_earnings_fixtures():
        asof = _feature_asof_for_event(e.event_date)
        feats = _synthetic_pre_event_features(e.ticker, e)
        features.append({"ticker": e.ticker, "asof_available": asof, **feats})

    panel = build_media_factor_panel(events, features)
    write_panel(panel, args.out)
    matched = sum(1 for r in panel if r.get("feature_matched"))
    print(json.dumps({"rows": len(panel), "matched": matched, "out": str(args.out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
