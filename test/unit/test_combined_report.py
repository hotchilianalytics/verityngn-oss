"""Tests for combined report assembly and deep markdown scrub."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from verityngn.models.report import AssessmentLevel, Claim, MediaEmbed, QuickSummary, VerityReport
from verityngn.services.report.combined_report import build_combined_markdown, _strip_leading_h1
from verityngn.services.reputation.url_safety import sanitize_url_list_in_text

MALICIOUS = (
    "https://www.ncl.ecu.edu/plugins/generic/pdfJsViewer/pdf.js/web/viewer.html"
    "?file=%2Findex.php%2Findex%2Flogin%2FsignOut%3Fsource%3D%2Esu7u%2Eshop%2Fmale%2F"
)
LEGIT = "https://www.nytimes.com/2024/11/10/opinion/wellness-bro-science.html"


def _minimal_report() -> VerityReport:
    claim = Claim(
        claim_id=0,
        claim_text="Test claim",
        timestamp="00:00",
        speaker="Host",
        initial_assessment="Verifiable",
        explanation="x",
        verification_result={"result": "LIKELY_TRUE", "sources": [LEGIT]},
    )
    return VerityReport(
        media_embed=MediaEmbed(
            title="Test Video",
            video_id="vid1",
            thumbnail_url="https://img.youtube.com/vi/vid1/0.jpg",
            video_url="https://youtu.be/vid1",
            description="d",
        ),
        title="Test Video",
        description="",
        quick_summary=QuickSummary(
            verdict=AssessmentLevel.MIXED,
            key_issue="Supplement claims",
            main_concerns=["Overstated efficacy"],
        ),
        overall_assessment=(AssessmentLevel.MIXED, "Mixed evidence"),
        key_findings=[],
        claims_breakdown=[claim],
        evidence_summary=[],
    )


def test_combined_markdown_section_order():
    report = _minimal_report()
    tldr = "**Bottom line:** Mixed / Uncertain — key hook."
    deep = "# Deep Title\n\nForensic paragraph."
    md = build_combined_markdown(report, deep, tldr, tier="original")
    assert md.index("# Test Video") < md.index("# TL;DR / Bottom Line")
    assert "![Video thumbnail" in md
    assert md.index("# TL;DR / Bottom Line") < md.index("## Deep Research Forensic Summary")
    assert md.index("## Deep Research Forensic Summary") < md.index("## Full VerityIndex Report")
    assert md.index("## Full VerityIndex Report") < md.index("## Appendix: Sources")
    assert "sources-for-claim-1" in md
    assert "## 7. Sources" not in md
    assert "Bottom line" in md
    assert "Forensic paragraph" in md
    assert "# Deep Title" not in md


def test_combined_html_renders_thumbnail_and_appendix():
    from verityngn.services.report.combined_report import render_combined_markdown_to_html

    report = _minimal_report()
    md = build_combined_markdown(report, "Deep body.", "**Bottom line:** hook.", tier="original")
    html = render_combined_markdown_to_html(md, "vid1", display_title="Test Video")
    assert "img.youtube.com" in html or "img src=" in html
    assert "Test Video" in html
    assert "Appendix: Sources" in html
    assert "sources-for-claim-1" in html
    assert "<details" not in html or "Claim 1" in html


def test_strip_leading_h1():
    assert _strip_leading_h1("# Title\n\nBody") == "Body"
    assert _strip_leading_h1("No title") == "No title"


def test_deep_markdown_scrub_removes_poisoned_urls():
    text = f"See {LEGIT} and {MALICIOUS} in references."
    cleaned = sanitize_url_list_in_text(text)
    assert LEGIT in cleaned
    assert MALICIOUS not in cleaned
    assert "pdfJsViewer" not in cleaned
