#!/usr/bin/env python3
"""Build the Chris joint-review package: third (analyst) report + charts + zip.

Does not re-run video analysis. Re-stamps finish_smoke_sb1507 under the
analyst taxonomy and writes a genre report whose source section is SIFT,
not CRAAP.
"""
from __future__ import annotations

import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT))

from verityngn.services.report.analyst_genre import (  # noqa: E402
    build_sift_method_section,
    infer_report_genre,
)
from verityngn.workflows.claim_kind import (  # noqa: E402
    ClaimKind,
    annotate_claim_kind,
    claim_kind_display_label,
    get_claim_kind,
    is_core_factual_claim,
)
from verityngn.workflows.verification import _stamp_lane_on_verified_claim  # noqa: E402

SMOKE = ROOT / "outputs/finish_smoke_sb1507/3f70063ddbd_report.json"
PACK = ROOT / "outputs/chris_review_package"
CHARTS = ROOT / "docs/blog/series/assets"


def restamp(claims: list) -> list:
    out = []
    for raw in claims:
        if not isinstance(raw, dict):
            continue
        annotated = annotate_claim_kind(dict(raw))
        vr = dict(raw.get("verification_result") or {})
        if not vr.get("result"):
            vr["result"] = "UNCERTAIN"
        out.append(_stamp_lane_on_verified_claim(annotated, vr))
    return out


def esc(text: str) -> str:
    return str(text or "").replace("|", "\\|").replace("\n", " ")


def analyst_report_md(claims: list, title: str) -> str:
    genre = infer_report_genre(claims)
    facts = [c for c in claims if is_core_factual_claim(c)]
    lines = [
        f"# Analyst Report — {title}",
        "",
        f"*Third report · genre `{genre}` · generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
        "This is the **video-type report**. The standard report still exists "
        "(`finish_smoke_sb1507` report.html / report.md, rendered 2026-09-23, CRAAP section). "
        "Deep Research is the second report (`deep.html`). This third report is for "
        "**analyst / deep-data** videos: typed claim sections and a **SIFT method review** "
        "in place of CRAAP.",
        "",
        "Likelihoods below are the **original verification results**, re-labeled. "
        "The video was not re-analyzed.",
        "",
        f"Source-backed facts in the core ladder: **{len(facts)}** of **{len(claims)}**.",
        "",
    ]
    lines.extend(build_sift_method_section(claims))
    lines.append("## Typed claims")
    lines.append("")

    def chip(c):
        vr = c.get("verification_result") or {}
        return esc(vr.get("risk_chip") or "")

    sections = [
        (ClaimKind.SOURCE_BACKED_FACT.value, "Source-backed facts (classic ladder)"),
        (ClaimKind.DATA_DERIVED_INFERENCE.value, "Data-derived inferences"),
        (ClaimKind.CAUSAL_ANALYTICAL.value, "Causal / analytical"),
        (ClaimKind.PREDICTION.value, "Predictions"),
        (ClaimKind.REASONED_OPINION.value, "Reasoned opinions"),
        (ClaimKind.UNVERIFIED_ASSERTION.value, "Unverified assertions"),
    ]
    for kind, heading in sections:
        items = [c for c in claims if get_claim_kind(c) == kind]
        if not items:
            continue
        lines.append(f"### {heading} ({len(items)})")
        lines.append("")
        lines.append("| Time | Claim | Risk chip |")
        lines.append("|:----:|:------|:----------|")
        for c in items:
            lines.append(
                f"| {esc(c.get('timestamp'))} | {esc((c.get('claim_text') or '')[:200])} | {chip(c)} |"
            )
        lines.append("")
    return "\n".join(lines)


def md_to_html(md: str, title: str) -> str:
    try:
        import markdown as mdlib

        body = mdlib.markdown(md, extensions=["tables", "fenced_code"])
    except Exception:
        body = "<pre>" + md.replace("&", "&amp;").replace("<", "&lt;") + "</pre>"
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/>
<title>{title}</title>
<style>
body {{ font-family: Georgia, serif; max-width: 920px; margin: 2rem auto; padding: 0 1rem; color: #1c1c1c; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; font-size: 0.92rem; }}
th, td {{ border: 1px solid #ccc; padding: 0.4rem 0.5rem; vertical-align: top; }}
th {{ background: #f4f1ea; text-align: left; }}
h1, h2, h3 {{ font-family: "Helvetica Neue", sans-serif; }}
code {{ font-size: 0.9em; }}
</style></head><body>
{body}
</body></html>
"""


def write_charts() -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    CHARTS.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.size": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.facecolor": "white",
        }
    )

    # History
    fig, ax = plt.subplots(figsize=(10, 4.2))
    milestones = [
        ("2026-08\nOSS 3.0 public\nengine + Deep Research", 1),
        ("2026-09-03\nTiers, captions,\n3.8 local defaults", 2),
        ("2026-09-05\nVertex global\nfallback router", 3),
        ("2026-09-06\nVerdict skew fix\nauthor-proof slice", 4),
        ("2026-09-25\nAnalyst taxonomy\n+ SIFT third report", 5),
    ]
    ax.barh(
        [m[0] for m in milestones][::-1],
        [1, 1, 1, 1, 1],
        color=["#8aa", "#8aa", "#8aa", "#8aa", "#0F6B6B"],
    )
    ax.set_xlabel("Sequence (not a score)")
    ax.set_title("VerityNgn OSS — shipped 3.0.0, then the analyst-genre increment")
    ax.set_xlim(0, 1.2)
    ax.set_xticks([])
    fig.tight_layout()
    fig.savefig(CHARTS / "01_history_timeline.png", dpi=140)
    plt.close()

    # Before / after routing
    fig, ax = plt.subplots(figsize=(8, 4.2))
    labels = ["Before\n(4 thin sleeves)", "After\n(6 kinds)"]
    facts = [26, 13]
    other = [2, 15]
    ax.bar(labels, facts, label="Source-backed facts in §6.1", color="#0F6B6B")
    ax.bar(labels, other, bottom=facts, label="Other typed lanes", color="#c4b8a5")
    ax.set_ylabel("Claims (count)")
    ax.set_title("SB1507: claims on the dense true/false ladder")
    ax.legend(frameon=False)
    ax.set_ylim(0, 32)
    fig.tight_layout()
    fig.savefig(CHARTS / "02_before_after_density.png", dpi=140)
    plt.close()

    # Kind mix
    fig, ax = plt.subplots(figsize=(8, 4.2))
    kinds = [
        "Source-backed\nfact",
        "Data-derived\ninference",
        "Causal /\nanalytical",
        "Prediction",
        "Unverified\nassertion",
    ]
    vals = [13, 7, 4, 2, 2]
    ax.bar(kinds, vals, color="#0F6B6B")
    ax.set_ylabel("Claims (count)")
    ax.set_title("SB1507 claim mix after re-categorization (n=28)")
    fig.tight_layout()
    fig.savefig(CHARTS / "03_kind_mix.png", dpi=140)
    plt.close()

    # Three reports
    fig, ax = plt.subplots(figsize=(8, 3.6))
    names = ["report.html\nstandard", "deep.html\nforensic", "analyst report\nthis genre"]
    ax.barh(names[::-1], [1, 1, 1], color=["#8aa", "#5a7a8a", "#0F6B6B"])
    ax.set_xticks([])
    ax.set_title("Three reports, three jobs")
    fig.tight_layout()
    fig.savefig(CHARTS / "04_three_reports.png", dpi=140)
    plt.close()


def main() -> None:
    PACK.mkdir(parents=True, exist_ok=True)
    data = json.loads(SMOKE.read_text())
    claims = restamp(data.get("claims_breakdown") or [])
    title = (data.get("video_title") or data.get("title") or "SB 1507 / Chris")
    if isinstance(data.get("media_embed"), dict):
        title = data["media_embed"].get("title") or title

    md = analyst_report_md(claims, str(title))
    (PACK / "01_analyst_report.md").write_text(md)
    (PACK / "01_analyst_report.html").write_text(
        md_to_html(md, "Analyst report — SB1507")
    )

    write_charts()
    # copies filled by caller after blogs exist; copy what is already on disk
    series = ROOT / "docs/blog/series"
    if series.exists():
        dest = PACK / "blog_series"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(series, dest)
    diagram = ROOT / "docs/blog/assets/verityngn-claim-classification-diagram.png"
    if diagram.exists():
        shutil.copy(diagram, PACK / "classification_diagram.png")
    score = ROOT / "outputs/sb1507_risk_taxonomy_loop/scorecard.json"
    if score.exists():
        shutil.copy(score, PACK / "scorecard.json")
    typed = ROOT / "outputs/sb1507_risk_taxonomy_loop/chris_review_typed_sections.md"
    if typed.exists():
        shutil.copy(typed, PACK / "02_typed_sections_preview.md")

    start = PACK / "START_HERE.md"
    start.write_text(
        """# Chris joint review — SB1507 package

Open in this order:

1. **`01_analyst_report.html`** — third report for this video type. CRAAP is replaced by a SIFT / method-and-reliance review. Risk chips sit on each typed claim.
2. **`classification_diagram.png`** — how a claim becomes a kind.
3. **`scorecard.json`** — counts and acceptance gates (all green on the offline re-stamp).
4. **`blog_series/`** — three articles (history, value, where the engine is). Charts are in `blog_series/assets/`.

## What this is not

The Sep 23 `report.html` in the smoke folder was rendered **before** this taxonomy. Likelihoods in the analyst report are those original verification results, re-labeled. We did not re-download or re-analyze the video.

## Published version

The PyPI / repo package version is **3.0.0**. There is no tagged **5.0.0**. The analyst report is the new genre path on the `release/v3.0.0` working tree.
"""
    )
    print(f"genre={infer_report_genre(claims)} claims={len(claims)} pack={PACK}")


if __name__ == "__main__":
    main()
