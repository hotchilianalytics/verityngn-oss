#!/usr/bin/env python3
"""Render papers/figures/platform_layers.png — L0–L5 stack."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "papers" / "figures" / "platform_layers.png"

LAYERS = [
    ("L5  Apps / services", "ClearFactor disclosure review · sponsor readiness · bespoke", "#0f766e", "#ecfdf5"),
    ("L4  Control plane", "verityindex.com — workspaces, runs, gallery, billing, BYOC", "#115e59", "#f0fdfa"),
    ("L3  Agent surface", "CLI · Python SDK · MCP · Agent Plugin skills", "#1e3a5f", "#eff6ff"),
    ("L2  Domain sleeves", "CRAAP · SIFT · CEO sensors · disclosure rfkit · brand safety", "#1e40af", "#eef2ff"),
    ("L1  Engine (OSS)", "Extract · six claim kinds · verify · counter-intel · Deep Research", "#0f172a", "#f8fafc"),
    ("L0  Signals", "Video, audio, OCR, EDGAR, press, YouTube counter-intel", "#44403c", "#fafaf9"),
]


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10.2, 6.4), dpi=160)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7.2)
    ax.axis("off")
    fig.patch.set_facecolor("#ffffff")
    ax.set_title("VerityNgn 3.0 — platform layers", loc="left", fontsize=14, pad=8, color="#0f172a")

    y = 6.15
    for title, subtitle, edge, face in LAYERS:
        box = FancyBboxPatch(
            (0.45, y - 0.85),
            9.1,
            0.95,
            boxstyle="round,pad=0.02,rounding_size=0.08",
            linewidth=1.4,
            edgecolor=edge,
            facecolor=face,
        )
        ax.add_patch(box)
        ax.text(0.7, y - 0.28, title, fontsize=11, fontweight="bold", color=edge, va="center")
        ax.text(0.7, y - 0.58, subtitle, fontsize=8.5, color="#44403c", va="center")
        y -= 1.08

    ax.text(
        0.45,
        0.22,
        "Apache OSS = L0–L3 (engine, sleeves, agent). Hosted = L4. Paid apps/services = L5.\n"
        "Risk platform, not a lie detector. No crawl / surveillance layer.",
        fontsize=8,
        color="#57534e",
    )
    fig.tight_layout()
    fig.savefig(OUT, bbox_inches="tight")
    plt.close()
    print(f"Wrote {OUT} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
