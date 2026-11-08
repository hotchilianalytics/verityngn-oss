"""Matplotlib charts for the decks (dark) and papers (light)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

DARK = dict(bg="#142333", fg="#F6F8FB", muted="#ACC0D0", grid="#2B4054",
            a="#51DFD0", b="#9CBFFF", warn="#FFAE73", amber="#FBBF24", grey="#6C879C")
LIGHT = dict(bg="#FFFFFF", fg="#1C1917", muted="#57534E", grid="#E7E5E4",
             a="#0F766E", b="#2563EB", warn="#C2410C", amber="#B45309", grey="#A8A29E")


def _axes(figsize, pal):
    plt.rcParams["font.family"] = ["DejaVu Sans", "Helvetica", "Arial", "sans-serif"]
    plt.rcParams["axes.unicode_minus"] = False
    fig, ax = plt.subplots(figsize=figsize, dpi=200)
    fig.patch.set_facecolor(pal["bg"])
    ax.set_facecolor(pal["bg"])
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(pal["grid"])
    ax.tick_params(colors=pal["muted"], labelsize=11, length=0)
    return fig, ax


def hbar(path: Path, labels, values, colors, pal=DARK, figsize=(5.6, 3.0), xmax=None,
         title=None, value_fmt="{:,}"):
    fig, ax = _axes(figsize, pal)
    y = range(len(labels))[::-1]
    ax.barh(list(y), values, color=[pal.get(c, c) for c in colors], height=0.62)
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, color=pal["fg"], fontsize=11.5)
    ax.set_xticks([])
    top = xmax or max(values) * 1.18 or 1
    ax.set_xlim(0, top)
    for yi, v in zip(y, values):
        ax.text(v + top * 0.015, yi, value_fmt.format(v), va="center", color=pal["fg"],
                fontsize=12, fontweight="bold")
    if title:
        ax.set_title(title, loc="left", color=pal["muted"], fontsize=11, pad=10)
    fig.tight_layout()
    fig.savefig(path, facecolor=pal["bg"])
    plt.close(fig)


def gate_bars(path: Path, issuers, before, after, pal=DARK, figsize=(5.6, 3.0)):
    fig, ax = _axes(figsize, pal)
    x = range(len(issuers))
    w = 0.36
    ax.bar([i - w / 2 for i in x], before, w, color=pal["grey"], label="Pairs found by matcher")
    ax.bar([i + w / 2 for i in x], after, w, color=pal["a"], label="Left after junior gate")
    for i, (b, a) in enumerate(zip(before, after)):
        ax.text(i - w / 2, b + 0.08, str(b), ha="center", color=pal["fg"], fontsize=13, fontweight="bold")
        ax.text(i + w / 2, a + 0.08, str(a), ha="center", color=pal["a"], fontsize=13, fontweight="bold")
    ax.set_xticks(list(x))
    ax.set_xticklabels(issuers, color=pal["fg"], fontsize=12)
    ax.set_yticks([])
    ax.set_ylim(0, max(before) + 1.2)
    leg = ax.legend(frameon=False, fontsize=10, loc="upper right")
    for t in leg.get_texts():
        t.set_color(pal["muted"])
    fig.tight_layout()
    fig.savefig(path, facecolor=pal["bg"])
    plt.close(fig)


def lag_timeline(path: Path, start: date, end: date, start_label, end_label, pal=DARK,
                 figsize=(11.6, 1.9)):
    fig, ax = _axes(figsize, pal)
    ax.spines["bottom"].set_visible(False)
    days = (end - start).days
    ax.plot([0, days], [0, 0], color=pal["grid"], lw=10, solid_capstyle="round")
    ax.plot([0, days], [0, 0], color=pal["warn"], lw=4, solid_capstyle="round")
    for d, lab, col, ha in ((0, start_label, pal["amber"], "left"), (days, end_label, pal["a"], "right")):
        ax.scatter([d], [0], s=180, color=col, zorder=3, edgecolor=pal["bg"], linewidth=2)
        ax.text(d, -0.55, lab, ha=ha, va="top", color=pal["fg"], fontsize=12, fontweight="bold")
    ax.text(days / 2, 0.35, f"{days} days", ha="center", va="bottom", color=pal["warn"],
            fontsize=20, fontweight="bold")
    ax.set_xlim(-days * 0.02, days * 1.02)
    ax.set_ylim(-1.3, 1.0)
    ax.set_xticks([])
    ax.set_yticks([])
    fig.tight_layout()
    fig.savefig(path, facecolor=pal["bg"])
    plt.close(fig)


def pipeline(path: Path, steps, pal=LIGHT, figsize=(10, 1.8)):
    """Simple left-to-right box diagram for papers."""
    fig, ax = plt.subplots(figsize=figsize, dpi=200)
    plt.rcParams["font.family"] = ["DejaVu Sans", "Helvetica", "Arial", "sans-serif"]
    plt.rcParams["axes.unicode_minus"] = False
    fig.patch.set_facecolor(pal["bg"])
    ax.set_axis_off()
    n = len(steps)
    bw, gap = 1.0, 0.28
    for i, (head, sub) in enumerate(steps):
        x0 = i * (bw + gap)
        ax.add_patch(plt.Rectangle((x0, 0), bw, 1, facecolor=pal["bg"], edgecolor=pal["a"], lw=1.6))
        ax.text(x0 + bw / 2, 0.66, head, ha="center", va="center", fontsize=11, fontweight="bold",
                color=pal["fg"])
        ax.text(x0 + bw / 2, 0.3, sub, ha="center", va="center", fontsize=8.2, color=pal["muted"],
                wrap=True)
        if i < n - 1:
            ax.annotate("", xy=(x0 + bw + gap - 0.03, 0.5), xytext=(x0 + bw + 0.03, 0.5),
                        arrowprops=dict(arrowstyle="->", color=pal["muted"], lw=1.4))
    ax.set_xlim(-0.05, n * (bw + gap) - gap + 0.05)
    ax.set_ylim(-0.05, 1.05)
    fig.tight_layout()
    fig.savefig(path, facecolor=pal["bg"])
    plt.close(fig)
