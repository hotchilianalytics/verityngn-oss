#!/usr/bin/env python3
"""Timestamped delivery-risk attribution for the Karp n=7 panel.

Reads local affect + fused_index + claims. Congruence / delivery-risk only —
not a lie detector. Writes markdown next to the corpus report.

Usage:
  PYTHONPATH=. python scripts/write_karp_attribution.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

VIDEO_IDS = [
    "QNkPpVYagRc",
    "dRgPbNJ5RJc",
    "V7mYWOzdhpc",
    "ijRuuaaM6XM",
    "xe84cwQJKaE",
    "WBu9Ai6OX3I",
    "pHu-FarYZlU",
]


def _fmt_ts(sec: float | None) -> str:
    if sec is None:
        return "—"
    s = max(0, int(round(float(sec))))
    return f"{s // 60:02d}:{s % 60:02d}"


def _clip(text: str, n: int = 140) -> str:
    t = " ".join((text or "").split())
    return t if len(t) <= n else t[: n - 1] + "…"


def _claim_text(claim: dict) -> str:
    return str(claim.get("claim_text") or claim.get("text") or "")


def main() -> int:
    os.chdir(ROOT)
    sections: list[str] = []
    summary_rows = []
    for vid in VIDEO_IDS:
        out_dir = ROOT / ".outputs" / f"karp_local_{vid}"
        affect_p = out_dir / f"{vid}_affect.json"
        fused_p = out_dir / f"{vid}_fused_index.json"
        report_p = out_dir / f"{vid}_report_with_delivery.json"
        if not affect_p.exists():
            sections += [f"## `{vid}`", "", "*No affect JSON.*", ""]
            continue
        affect = json.loads(affect_p.read_text(encoding="utf-8"))
        fused = json.loads(fused_p.read_text(encoding="utf-8")) if fused_p.exists() else {}
        report = json.loads(report_p.read_text(encoding="utf-8")) if report_p.exists() else {}
        claims = report.get("claims_breakdown") or report.get("claims") or []
        by_id = {
            c.get("claim_id"): c
            for c in claims
            if isinstance(c, dict) and c.get("claim_id") is not None
        }
        cm = fused.get("crossmodal") or {}
        fused_by = {
            s.get("claim_id"): s
            for s in (cm.get("segments") or [])
            if isinstance(s, dict)
        }
        segs = [s for s in (affect.get("segments") or []) if isinstance(s, dict)]
        srcs = [str(s.get("measured_affect_source") or "") for s in segs]
        asr = str((affect.get("summary") or {}).get("asr_source") or "")
        cong = cm.get("overall_congruence")
        n = len(segs)
        summary_rows.append((vid, n, cong, asr, ",".join(sorted(set(srcs)))))
        block = [
            f"## `{vid}`",
            "",
            f"- n_claims: **{n}**",
            f"- S01 overall_congruence: **{cong:.4f}**" if isinstance(cong, (int, float)) else "- S01: —",
            f"- audio: `{', '.join(sorted(set(srcs))) or '—'}` · ASR: `{asr or '—'}`",
            f"- YouTube: https://www.youtube.com/watch?v={vid}",
            "",
            "| t | claim | A | D | V | exuberance | S01 cong | missing | delivery-risk | excerpt |",
            "|---|-------|---|---|---|---------|----------|---------|---------------|---------|",
        ]
        for s in segs:
            cid = s.get("claim_id")
            t = s.get("timestamp_sec")
            claim = by_id.get(cid) or {}
            fs = fused_by.get(cid) or {}
            miss = ",".join(fs.get("missing_channels") or []) or "—"
            band = fs.get("delivery_risk_band") or "—"
            cong_i = fs.get("congruence")
            a = s.get("measured_arousal")
            d = s.get("measured_dominance")
            v = s.get("measured_valence")
            ex = s.get("exuberance")

            def _n(x):
                try:
                    return f"{float(x):.3f}"
                except (TypeError, ValueError):
                    return "—"

            excerpt = _clip(_claim_text(claim)).replace("|", "/")
            block.append(
                f"| {_fmt_ts(t)} | {cid} | {_n(a)} | {_n(d)} | {_n(v)} | {_n(ex)} | "
                f"{_n(cong_i)} | {miss} | {band} | {excerpt} |"
            )
        block.append("")
        sections.extend(block)

    head = [
        "# Karp delivery-risk attribution (n=7)",
        "",
        "**Trial:** T016 · **promote:** NO_PROMOTE",
        "",
        "Congruence / delivery-risk only. Not a lie detector, clinical diagnosis, or veracity judgment. "
        "Not for employment, HR, or education screening (EU AI Act Art. 5(1)(f)). "
        "Face / rPPG is omitted on every row (never filled with 0.5). S01 is text×voice×interpreted Gemini, renormalized.",
        "",
        "Timestamps are claim marks from the verification report.",
        "",
        "| video | n | S01 | ASR | VAD source |",
        "|-------|---|-----|-----|------------|",
    ]
    for vid, n, c, asr, src in summary_rows:
        cs = f"{c:.4f}" if isinstance(c, (int, float)) else "—"
        head.append(
            f"| [`{vid}`](https://www.youtube.com/watch?v={vid}) | {n} | {cs} | `{asr or '—'}` | `{src}` |"
        )
    head += ["", "---", ""]
    text = "\n".join(head + sections) + "\n"
    dests = [
        ROOT / ".outputs" / "ceo_pltr_karp_corpus" / "karp_delivery_attribution.md",
        ROOT / "docs" / "predictions" / "KARP_DELIVERY_ATTRIBUTION.md",
    ]
    for p in dests:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        print(f"wrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
