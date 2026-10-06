#!/usr/bin/env python3
"""Leakage-safe join: pre-print Karp signals → next PLTR surprise / CAR H=1.

Register T010 in docs/trials_ledger.md BEFORE running this against live returns.

Features at video_date t only. Outcome = next print after t (not same-day webcast).
NO_PROMOTE regardless of Spearman sign — n is tiny.
"""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from verityngn.services.timeseries.returns import car as market_car, raw_h1

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_CATALOG = ROOT / "docs" / "karp_pre_earnings_videos.json"
DEFAULT_PLAYER_ID = "ceo_pltr_karp"


def _spearman(xs: list[float], ys: list[float]) -> Optional[float]:
    if len(xs) != len(ys) or len(xs) < 3:
        return None
    rx = _ranks(xs)
    ry = _ranks(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    dy = math.sqrt(sum((b - my) ** 2 for b in ry))
    if dx == 0 or dy == 0:
        return None
    return round(num / (dx * dy), 4)


def _ranks(vals: list[float]) -> list[float]:
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    ranks = [0.0] * len(vals)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _flatten_close(hist: Any) -> Optional[Any]:
    """Return a Close Series even when yfinance returns MultiIndex columns."""
    if hist is None or getattr(hist, "empty", True):
        return None
    cols = hist.columns
    if getattr(cols, "nlevels", 1) > 1:
        # ('Close', 'PLTR') or ('PLTR', 'Close')
        for key in ("Close", "close"):
            try:
                sub = hist[key]
                if hasattr(sub, "columns"):
                    sub = sub.iloc[:, 0]
                return sub
            except Exception:  # noqa: BLE001
                pass
        try:
            return hist.xs("Close", axis=1, level=-1).iloc[:, 0]
        except Exception:  # noqa: BLE001
            return None
    if "Close" not in hist.columns:
        return None
    return hist["Close"]


def _car_h1(ticker: str, event_date: str) -> Optional[float]:
    """Deprecated alias for timeseries.returns.raw_h1 (not a true CAR)."""
    return raw_h1(ticker, event_date)


def _signal_value(report: dict[str, Any], prefix: str) -> Optional[float]:
    for s in report.get("signals") or []:
        if str(s.get("id") or "").startswith(prefix):
            v = s.get("value")
            if isinstance(v, (int, float)):
                return float(v)
    return None


def load_catalog(catalog: Path = DEFAULT_CATALOG) -> dict[str, Any]:
    return json.loads(catalog.read_text(encoding="utf-8"))


def _report_paths(root: Path, player_id: str, video_id: str) -> list[Path]:
    """Prefer player-local dirs; fall back to Karp-era naming."""
    return [
        root / ".outputs" / f"{player_id}_{video_id}" / f"{player_id}_signal_report.json",
        root / ".outputs" / f"karp_local_{video_id}" / f"{player_id}_signal_report.json",
        root / ".outputs" / f"karp_local_{video_id}" / "ceo_pltr_karp_signal_report.json",
    ]


def collect_rows(
    root: Path = ROOT,
    *,
    catalog: Path = DEFAULT_CATALOG,
    player_id: Optional[str] = None,
    trial: str = "T010",
) -> list[dict[str, Any]]:
    cat = load_catalog(catalog)
    pid = player_id or cat.get("player_id") or DEFAULT_PLAYER_ID
    items = list(cat.get("existing_corpus") or []) + list(cat.get("run_five") or [])
    rows = []
    for item in items:
        if item.get("window") != "pre":
            continue
        vid = item["video_id"]
        if item.get("next_print", "").startswith("2024"):
            continue
        report_path = next((p for p in _report_paths(root, pid, vid) if p.exists()), None)
        if report_path is None:
            rows.append({**item, "status": "missing_signals", "features_asof": item.get("recorded")})
            continue
        report = json.loads(report_path.read_text(encoding="utf-8"))
        print_date = item["next_print"]
        if item.get("recorded") >= print_date:
            rows.append({**item, "status": "leakage_skip", "reason": "recorded_on_or_after_print"})
            continue
        car = _car_h1(cat["ticker"], print_date)
        mm = market_car(cat["ticker"], print_date, horizons=(1, 5, 10, 21))
        rows.append(
            {
                "video_id": vid,
                "player_id": pid,
                "ticker": cat.get("ticker"),
                "recorded": item.get("recorded"),
                "next_print": print_date,
                "print_label": item.get("print_label") or item.get("next_print"),
                "window": "pre",
                "s01_congruence": _signal_value(report, "S01"),
                "s05_qa_delta": _signal_value(report, "S05"),
                "s11_derailment": _signal_value(report, "S11"),
                "car_h1": car,
                "raw_h1": car,
                "car_h1_mm": mm.get("car_h1"),
                "car_h5": mm.get("car_h5"),
                "car_h10": mm.get("car_h10"),
                "car_h21": mm.get("car_h21"),
                "beta": mm.get("beta"),
                "features_asof": item.get("recorded"),
                "status": "ok" if car is not None else "ok_no_returns",
                "trial": trial,
                "promote": "NO_PROMOTE",
            }
        )
    return rows


def summarize(rows: list[dict[str, Any]], trial: str = "T010") -> dict[str, Any]:
    ok = [r for r in rows if r.get("status") in {"ok", "ok_no_returns"} and r.get("s01_congruence") is not None]
    with_car = [r for r in ok if r.get("car_h1") is not None]
    ticker = next((r.get("ticker") for r in rows if r.get("ticker")), "TICKER")
    out: dict[str, Any] = {
        "trial": trial,
        "promote": "NO_PROMOTE",
        "n_pre_videos_with_signals": len(ok),
        "n_with_car": len(with_car),
        "hypothesis": (
            f"Pre-print S01/S05/S11 associate with next-print {ticker} CAR H=1. "
            "Registered before peek. n is too small for promote."
        ),
        "spearman": {},
        "verdict": "insufficient_n",
        "limits": (
            "n<10, two videos can share one print, "
            "CAR is raw close-to-close not FF-adjusted, S11 may be Jaccard offline. "
            "Do not treat a signed correlation as an earnings effect. "
            "NO_PROMOTE = risk factor not validated for allocation."
        ),
    }
    if len(with_car) >= 3:
        for key, label in (
            ("s01_congruence", "S01"),
            ("s05_qa_delta", "S05"),
            ("s11_derailment", "S11"),
        ):
            xs = [float(r[key]) for r in with_car if r.get(key) is not None]
            ys = [float(r["car_h1"]) for r in with_car if r.get(key) is not None]
            if len(xs) == len(ys) and len(xs) >= 3:
                out["spearman"][label] = _spearman(xs, ys)
        rhos = [v for v in out["spearman"].values() if v is not None]
        if rhos and max(abs(v) for v in rhos) >= 0.6 and len(with_car) >= 5:
            out["verdict"] = "association_present_underpowered"
        else:
            out["verdict"] = "no_reliable_earnings_effect"
    return out


def write_reports(
    out_dir: Path,
    rows: list[dict[str, Any]],
    summary: dict[str, Any],
    *,
    stem: str = "karp_earnings_effect",
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "rows": rows,
    }
    (out_dir / f"{stem}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    ticker = next((r.get("ticker") for r in rows if r.get("ticker")), "TICKER")
    trial = summary.get("trial") or "T010"
    lines = [
        f"# Pre-earnings → {ticker} CAR ({trial}, NO_PROMOTE)",
        "",
        f"**Verdict:** `{summary.get('verdict')}` · n_signals={summary.get('n_pre_videos_with_signals')} · n_CAR={summary.get('n_with_car')}",
        "",
        f"> {summary.get('limits')}",
        "",
        "## Spearman (feature vs CAR H=1)",
        "",
        json.dumps(summary.get("spearman"), indent=2),
        "",
        "## Rows",
        "",
        "| Video | Recorded | Next print | S01 | S05 | S11 | CAR H=1 | Status |",
        "|-------|----------|------------|-----|-----|-----|---------|--------|",
    ]
    for r in rows:
        lines.append(
            f"| `{r.get('video_id')}` | {r.get('recorded')} | {r.get('next_print')} | "
            f"{r.get('s01_congruence')} | {r.get('s05_qa_delta')} | {r.get('s11_derailment')} | "
            f"{r.get('car_h1')} | {r.get('status')} |"
        )
    (out_dir / f"{stem}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out_dir / f'{stem}.json'}")
    print(f"wrote {out_dir / f'{stem}.md'}")
    print(json.dumps(summary, indent=2))


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    ap.add_argument("--player-id", default=None, help="Override catalog player_id")
    ap.add_argument("--trial", default="T010")
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--stem", default="karp_earnings_effect")
    args = ap.parse_args()

    cat = load_catalog(args.catalog)
    player_id = args.player_id or cat.get("player_id") or DEFAULT_PLAYER_ID
    out_dir = args.out_dir or (ROOT / ".outputs" / f"{player_id}_corpus")
    rows = collect_rows(
        catalog=args.catalog,
        player_id=player_id,
        trial=args.trial,
    )
    summary = summarize(rows, trial=args.trial)
    write_reports(out_dir, rows, summary, stem=args.stem)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
