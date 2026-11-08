"""Insert real-run example slides into the Perplexity VerityNgn 3.0.0 release deck.

New slides are numbered 08A and 12A–12C so the slide numbers used in the
Perplexity legal brief's presenter notes stay valid.

    python scripts/decks/add_oss_examples.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

from pptx import Presentation
from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).parent))
import charts  # noqa: E402
from slidekit import (  # noqa: E402
    Slide, Theme, html_to_pdf, move_slide, promote_paragraph_defaults, render_html, render_pptx_slide,
)

SOFFICE_CANDIDATES = (
    "soffice",
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    "/opt/homebrew/bin/soffice",
)


def _soffice() -> str:
    for candidate in SOFFICE_CANDIDATES:
        path = shutil.which(candidate) if "/" not in candidate else candidate
        if path and Path(path).exists():
            return path
    raise SystemExit(
        "LibreOffice (soffice) is required to convert the example deck PPTX to PDF. "
        "Install with: brew install --cask libreoffice"
    )


def pptx_to_pdf(pptx_path: Path, pdf_path: Path) -> None:
    """Convert a PPTX to PDF with LibreOffice headless (no Keynote)."""
    out_dir = pdf_path.parent
    subprocess.run(
        [_soffice(), "--headless", "--convert-to", "pdf", "--outdir", str(out_dir), str(pptx_path)],
        check=True,
        capture_output=True,
        timeout=300,
    )
    produced = out_dir / f"{pptx_path.stem}.pdf"
    if produced.resolve() != pdf_path.resolve():
        produced.replace(pdf_path)

ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / "docs/launch/perplexity_review_2026-10-27"
OUT = ROOT / "docs/launch/decks"
BUILD = OUT / "_build"
BATTERY = ROOT / "outputs/release_v3_battery_2026-10-18"
CF_PACK = Path.home() / "proj/ajjax/downloads/rfkit/consulting/packs/MSFT/MSFT_committee_pack.json"

TAG = "https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0"
MSFT_8K = "https://www.sec.gov/Archives/edgar/data/789019/000119312524011295/d708866d8k.htm"
MSFT_10K = "https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm"

THEME = Theme(footer="VERITYNGN OSS  /  3.0.0")
ROWS_3_10 = ["V7mYWOzdhpc", "ijRuuaaM6XM", "cP8pfCJTw4Q", "dRgPbNJ5RJc",
             "lb_ZJylekWo", "tSdWpsj1Cyo", "7MXE1kDCY-k", "RuinHdlpXvE"]
SUPPORTED = {"HIGHLY_LIKELY_TRUE", "LIKELY_TRUE", "LEANING_TRUE"}
CONTESTED = {"HIGHLY_LIKELY_FALSE", "LIKELY_FALSE", "LEANING_FALSE"}


def _result(c):
    r = c.get("verification_result")
    return r.get("result") if isinstance(r, dict) else r


def _claims(video_id):
    """Verified claims for one battery row.

    The report JSON is the canonical artifact. When it has been cleaned out of
    the local run directory, the checkpoint's completed claims are the same set.
    """
    report = BATTERY / video_id / f"{video_id}_report.json"
    if report.exists():
        claims = json.loads(report.read_text())["claims_breakdown"]
    else:
        checkpoint = BATTERY / video_id / f"{video_id}_checkpoint.json"
        claims = json.loads(checkpoint.read_text())["completed_claims"]
    for i, claim in enumerate(claims, start=1):
        claim.setdefault("claim_id", i)
    return claims


def _at(video_id, timestamp, kind=None):
    for claim in _claims(video_id):
        start = str(claim.get("timestamp") or "").split(" - ")[0].strip()
        if start == timestamp and (kind is None or claim.get("claim_kind") == kind):
            return claim
    raise SystemExit(f"no {kind or 'claim'} at {timestamp} in {video_id}")


def _label(result):
    if result in SUPPORTED:
        return "Supported"
    if result in CONTESTED:
        return "Contested"
    if result == "OPINION":
        return "Not scored"
    return "Unresolved"


def battery_counts():
    kinds, labels = Counter(), Counter()
    for vid in ROWS_3_10:
        for c in _claims(vid):
            kinds[c.get("claim_kind") or "source_backed_fact"] += 1
            labels[_label(_result(c))] += 1
    assert sum(kinds.values()) == 263, sum(kinds.values())
    return kinds, labels


def slide_8a():
    pack = json.loads(CF_PACK.read_text())
    pair = pack["disclosure"]["findings"][0]
    hedge = pair["hedged"]["text"]
    event = pair["event"]["text"].replace("Material Cybersecurity Incidents ", "")
    s = Slide(THEME)
    s.chrome(
        "GC / companion — public-record example",
        "Example: the pair a junior would catch",
        "Microsoft, public EDGAR filings only. The companion found this pair, then set it aside.",
        f"Sources: MSFT 10-K filed 29 Jul 2026 (Item 1A); 8-K Item 1.05 filed 19 Jan 2024. Quotes shortened. Phase 1 companion run, not core v3.0.0.",
        "08A",
    )
    s.card(0.64, 2.86, 5.92, 1.98, label="10-K Item 1A · filed 29 Jul 2026",
           body="“" + hedge[:236].rsplit(" ", 1)[0] + "…”", body_size=14)
    s.card(6.75, 2.86, 5.92, 1.98, label="8-K Item 1.05 · filed 19 Jan 2024", label_color=THEME.amber,
           body="“" + event[:236].rsplit(" ", 1)[0] + "…”", body_size=14)
    s.card(0.64, 4.98, 12.03, 0.88, label="Illustrative edit — for counsel to change, not to file",
           body="State the disclosed event with its date. Keep any residual forward-looking risk in a separate sentence.",
           body_size=14)
    s.band("Junior gate: 3 pairs found, 0 kept. Item 1A already states the event; the edit is style—split past fact from forward risk.",
           y=6.0, h=0.5)
    s.notes_with_sources(
        """This is what the Phase 1 disclosure companion does on public filings only. The matcher pairs a risk-factor sentence with a dated sentence from the company's own 8-K. Here, Microsoft's current 10-K already describes the January 2024 nation-state incident in the past tense; only the continuing risk is hedged, in the same sentence. A junior reviewer holding both documents would catch this, so the companion moves it to a hygiene appendix instead of leading with it. The illustrative counsel edit is to split the sentence: state the disclosed event with its date, then keep any residual forward-looking risk separately. This is not an allegation of misleading disclosure. Materiality and drafting remain counsel's decisions. The companion is a separate rfkit checkout and is not part of a core-only v3.0.0 install.""",
        [MSFT_10K, MSFT_8K, f"{TAG}/docs/platform/RFKIT_OSS_EXTRACT.md", f"{TAG}/docs/platform/DOMAIN_PACKS.md"],
    )
    return s


def slide_12a(kinds, labels):
    kind_png, label_png = BUILD / "oss_kind_mix.png", BUILD / "oss_label_mix.png"
    order = [("source_backed_fact", "Source-backed fact"), ("data_derived_inference", "Data-derived inference"),
             ("causal_analytical", "Causal / analytical"), ("reasoned_opinion", "Reasoned opinion"),
             ("prediction", "Prediction"), ("unverified_assertion", "Unverified assertion")]
    charts.hbar(kind_png, [n for _, n in order], [kinds.get(k, 0) for k, _ in order],
                ["a", "b", "b", "b", "b", "b"], figsize=(5.6, 3.05), xmax=310)
    lab_order = ["Supported", "Unresolved", "Contested", "Not scored"]
    charts.hbar(label_png, lab_order, [labels.get(k, 0) for k in lab_order],
                ["a", "grey", "warn", "b"], figsize=(5.6, 3.05), xmax=170)
    s = Slide(THEME)
    s.chrome(
        "Release evidence / what the runs produced",
        "263 claims, sorted into lanes",
        "Primary-10 rows 3–10: eight live videos. Counts come straight from the report JSON.",
        "Source: BATTERY_RESULTS_v3.md; per-row *_report.json in the local battery run. Project-reported; labels are research aids, not ground truth.",
        "12A",
    )
    s.rect(0.64, 2.86, 5.92, 3.02, THEME.card, THEME.line, round=True)
    s.text(0.86, 2.98, 5.5, 0.28, "CLAIM KIND", 10.5, THEME.accent, bold=True)
    s.image(kind_png, 0.74, 3.25, 5.72, 2.55)
    s.rect(6.75, 2.86, 5.92, 3.02, THEME.card, THEME.line, round=True)
    s.text(6.97, 2.98, 5.5, 0.28, "ASSESSMENT LABEL", 10.5, THEME.accent, bold=True)
    s.image(label_png, 6.85, 3.25, 5.72, 2.55)
    s.band(f"{labels['Unresolved']} of 263 stayed Unresolved instead of being forced to true or false.", y=6.0, h=0.5)
    s.notes_with_sources(
        f"""These are the raw counts behind the 263 claims on the release-evidence slide. Almost all extracted claims in these eight videos were source-backed facts: {kinds['source_backed_fact']}. The rest were {kinds.get('prediction', 0)} predictions, {kinds.get('data_derived_inference', 0)} data-derived inferences, and {kinds.get('reasoned_opinion', 0)} reasoned opinion. On the right, Supported groups the true-leaning labels, Contested groups the false-leaning labels, and Unresolved is the engine declining to decide. {labels['Unresolved']} unresolved claims is a feature to talk about: the engine leaves a claim open when evidence is thin. None of this is an accuracy measurement. It describes what the pipeline emitted on public videos.""",
        [f"{TAG}/docs/launch/BATTERY_RESULTS_v3.md", f"{TAG}/verityngn/workflows/claim_kind.py",
         "Local run artifacts: outputs/release_v3_battery_2026-10-18/<video_id>/<video_id>_report.json (not in the public repo)"],
    )
    return s


def slide_12b():
    picks = [
        ("20:34", "prediction", "Prediction", "$4.10M life-care cost", "Present value under an 18-year life-expectancy scenario ending 2040."),
        ("19:46", "prediction", "Prediction", "$3.58M life-care cost", "Present value under a 15-year life-expectancy scenario ending 2037."),
        ("15:18", "data_derived_inference", "Data-derived inference", "$1.07M lost wages", "Present value under Scenario 1, assuming a high-school diploma."),
    ]
    s = Slide(THEME)
    s.chrome(
        "Example / public deposition (row 9)",
        "A forecast stays a forecast.",
        "Expert economic testimony from the Butler Kahn deposition fixture. Real extracted claims; no witness is scored.",
        "Source: claims 18, 19, 23 from the row-9 report JSON (local run artifact). Values rounded. Not legal analysis.",
        "12B",
    )
    for i, (ts, kind, lane, head, body) in enumerate(picks):
        c = _at("7MXE1kDCY-k", ts, kind)
        x = 0.64 + i * 4.06
        s.card(x, 2.92, 3.87, 2.95, label=f"{lane} · {c['timestamp']}", heading=head, body=body,
               edge=THEME.accent if lane == "Prediction" else THEME.accent2, heading_size=21)
        s.text(x + 0.2, 5.2, 3.47, 0.5, f"Unresolved · residual reliance: {c.get('residual_reliance_risk') or 'n/a'}",
               11, THEME.foot)
    s.band("Scenario projections get their own lanes. They never count as “false facts.”", y=6.0, h=0.5)
    s.notes_with_sources(
        """This comes from the public deposition fixture in the release battery. An expert gives present-value projections under different life-expectancy scenarios. A transcript-only fact checker would try to mark these true or false. VerityNgn routes them to the prediction or data-derived-inference lanes, keeps the scenario assumptions visible, and leaves them Unresolved for counsel. That is exactly the review a litigator needs: what is assumed, over what horizon, and what record supports the inputs. We deliberately do not show any claim about the witness personally, and the engine does not score credibility. Values are rounded from the report: 4,101,000; 3,581,865; 1,068,811.""",
        [f"{TAG}/verityngn/workflows/claim_kind.py", f"{TAG}/docs/launch/BATTERY_RESULTS_v3.md",
         "Local run artifact: outputs/release_v3_battery_2026-10-18/7MXE1kDCY-k/7MXE1kDCY-k_report.json"],
    )
    return s


def slide_12c():
    rows = [["TIME", "CLAIM (AS EXTRACTED, SHORTENED)", "LANE", "STATUS"]]
    for ts, short in [
        ("01:05", "OpenAI APIs remain exclusive to Microsoft Azure going forward."),
        ("01:18", "Microsoft and OpenAI maintain revenue-sharing arrangements."),
        ("03:49", "Microsoft is investing $80 billion a year, largely for cloud and AI."),
        ("00:58", "Microsoft will serve as a technology partner to the Stargate project."),
        ("00:43", "Microsoft acted essentially as a seed investor for OpenAI."),
    ]:
        c = _at("lb_ZJylekWo", ts)
        rows.append([c["timestamp"].split(" - ")[0], short, "Fact", _label(_result(c))])

    def style(r, c, v):
        if c == 3:
            return (THEME.card, THEME.accent if v == "Supported" else THEME.body, True)
        if c == 0:
            return (THEME.card, THEME.accent2, True)
        return None

    s = Slide(THEME)
    s.chrome(
        "Example / executive interview (row 7)",
        "One interview, nineteen claims.",
        "Satya Nadella on Squawk Box about Stargate. Every claim keeps its timestamp and evidence trail.",
        "Source: row-7 report JSON (local run artifact). Status groups the engine's labels; research aid, not a verdict on the speaker.",
        "12C",
    )
    s.table(0.64, 2.86, [1.1, 7.6, 1.35, 1.98], rows, row_h=0.5, size=13.5, cell_style=style)
    s.band("In the ClearFactor companion, the matcher found no Item 1A factor for any of these 19 claims.", y=6.0, h=0.5)
    s.notes_with_sources(
        """A public CEO interview becomes a list of timestamped, typed claims. Five of the nineteen are shown. Supported means the engine found corroborating sources; Unresolved means it did not find enough to decide, which is common for forward-looking partnership statements. This is the bridge to the disclosure companion: those same nineteen claims become the "own voice" input, and the Phase 1 matcher found no Item 1A risk factor that maps to them. That is a question for the disclosure committee, not a finding of wrongdoing. Do not present these labels as a judgement of the speaker's honesty.

Presenter caution on currency: this run also labeled Nadella's right-of-first-refusal claim Supported. Microsoft's own Ex-99.2 of 28 October 2025 says Microsoft no longer has a right of first refusal to be OpenAI's compute provider. The claim was accurate when spoken and has since been superseded. That row is left off the slide; labels reflect the evidence the engine found, and a reviewer still checks currency.""",
        [f"{TAG}/docs/launch/BATTERY_RESULTS_v3.md", f"{TAG}/docs/platform/COMMERCIAL_MAP.md",
         "https://www.sec.gov/Archives/edgar/data/789019/000119312525256310/msft-ex99_2.htm",
         "Local run artifact: outputs/release_v3_battery_2026-10-18/lb_ZJylekWo/lb_ZJylekWo_report.json"],
    )
    return s


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    BUILD.mkdir(parents=True, exist_ok=True)
    kinds, labels = battery_counts()
    examples = {8: [slide_8a()], 12: [slide_12a(kinds, labels), slide_12b(), slide_12c()]}

    prs = Presentation(str(REVIEW / "VerityNgn_3_Release.pptx"))
    promoted = promote_paragraph_defaults(prs)
    rendered = {after: [render_pptx_slide(prs, spec) for spec in specs] for after, specs in examples.items()}
    offset = 0
    for after in sorted(rendered):
        for i, slide in enumerate(rendered[after]):
            move_slide(prs, slide, after + offset + i)
        offset += len(rendered[after])
    pptx_out = OUT / "VerityNgn_3_Release_with_examples.pptx"
    prs.save(str(pptx_out))

    ex_specs = examples[8] + examples[12]
    html_path = BUILD / "oss_examples.html"
    html_path.write_text(render_html(ex_specs, "VerityNgn 3.0.0 example slides"), encoding="utf-8")
    ex_pdf = OUT / "VerityNgn_3_example_slides.pdf"
    html_to_pdf(html_path, ex_pdf)

    pdf_out = OUT / "VerityNgn_3_Release_with_examples.pdf"
    pptx_to_pdf(pptx_out, pdf_out)
    page_count = len(PdfReader(str(pdf_out)).pages)
    print(f"runs promoted: {promoted}; slides: {len(prs.slides)}; pdf pages: {page_count}")
    print(pptx_out, pdf_out, ex_pdf, sep="\n")


if __name__ == "__main__":
    main()
