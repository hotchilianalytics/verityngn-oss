import html
import logging
import re
from typing import Dict, Any, Optional
from verityngn.models.report import VerityReport, CredibilityLevel
from verityngn.services.report.category_mappings import LLM_PLATFORM_VISIBLE_NOTICE

logger = logging.getLogger(__name__)


def _sanitize_fast_review_text(text: str, *, preserve_paragraphs: bool = False) -> str:
    """Strip patterns that look like derived metrics from LLM review prose (public fast HTML)."""
    if not text:
        return text
    out = text
    out = re.sub(r"\b\d{1,3}\.\d+\s*%", "[redacted]", out)
    out = re.sub(r"\b\d{1,3}\s*%", "[redacted]", out)
    out = re.sub(r"\b\d+\s+of\s+\d+\b", "[redacted]", out, flags=re.I)
    out = re.sub(r"\bT[1-5]\s*:\s*\d+\s*%?", "[redacted]", out, flags=re.I)
    if preserve_paragraphs:
        return out.strip()
    return re.sub(r"\s+", " ", out).strip()


def _inline_md_bold_to_html(text: str) -> str:
    """Convert **bold** markers to <strong> after html.escape."""
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)


def _format_review_html(text: str) -> str:
    """Render Verity Review prose as HTML paragraphs (not raw markdown in one p tag)."""
    if not text or not text.strip():
        return "<p>No description available to review.</p>"

    cleaned = text.strip()
    cleaned = re.sub(r"^\*?\*?Verity Review:\*?\*?\s*", "", cleaned, flags=re.I)
    cleaned = _sanitize_fast_review_text(cleaned, preserve_paragraphs=True)

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", cleaned) if p.strip()]
    if not paragraphs:
        paragraphs = [cleaned.strip()]

    html_parts = []
    for para in paragraphs:
        escaped = html.escape(para)
        escaped = _inline_md_bold_to_html(escaped)
        html_parts.append(f"<p>{escaped}</p>")
    return "\n            ".join(html_parts)


def generate_fast_html_report(report: VerityReport, review_text: str) -> str:
    """
    Generate a fast HTML report designed for quick consumption (30-second review).
    
    Includes:
    - Video Thumbnail
    - Video Title
    - ~200 word "Verity Review" of the description/content
    - CRAAP Analysis Table
    """
    
    video_id = report.media_embed.video_id
    source_info_hash = html.escape(report.source_info_hash or "(unavailable)")
    report_generated_at = html.escape(report.report_generated_at or "(unavailable)")
    safe_video_id = html.escape(video_id)

    review_html = _format_review_html(review_text)

    # CRAAP Analysis
    craap_rows = ""
    if report.craap_analysis:
        for criterion, (level, explanation) in report.craap_analysis.items():
            # Determine color based on level
            level_str = str(level).upper()
            color_class = "neutral"
            if level_str == "HIGH":
                color_class = "good"
            elif level_str == "LOW":
                color_class = "bad"
            elif level_str == "MEDIUM":
                color_class = "warning"
                
            safe_explanation = _sanitize_fast_review_text(str(explanation or ""))
            craap_rows += f"""
            <tr>
                <td class="criterion"><strong>{criterion.capitalize()}</strong></td>
                <td class="level"><span class="badge {color_class}">{level}</span></td>
                <td class="explanation">{safe_explanation}</td>
            </tr>
            """
    else:
        craap_rows = "<tr><td colspan='3'>No CRAAP analysis available.</td></tr>"

    notice_html = html.escape(LLM_PLATFORM_VISIBLE_NOTICE)

    # HTML Template
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verity Fast Report - {safe_video_id}</title>
    <style>
        :root {{
            --primary-color: #2c3e50;
            --secondary-color: #3498db;
            --accent-color: #e74c3c;
            --bg-color: #f8f9fa;
            --card-bg: #ffffff;
            --text-color: #333333;
            --border-radius: 8px;
            --shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            background-color: var(--bg-color);
            margin: 0;
            padding: 20px;
        }}
        
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background-color: var(--card-bg);
            padding: 30px;
            border-radius: var(--border-radius);
            box-shadow: var(--shadow);
        }}
        
        h1 {{
            color: var(--primary-color);
            margin-top: 0;
            font-size: 1.8rem;
            border-bottom: 2px solid #eee;
            padding-bottom: 15px;
        }}
        
        h2 {{
            color: var(--secondary-color);
            font-size: 1.4rem;
            margin-top: 30px;
        }}
        
        .report-header {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 24px;
            font-size: 0.95rem;
        }}
        .report-header th {{
            text-align: left;
            width: 28%;
            color: var(--primary-color);
        }}
        .report-header td code {{
            word-break: break-all;
            font-size: 0.85rem;
        }}
        .verity-llm-notice {{
            border-left: 4px solid #c0392b;
            background: #fff8f6;
            padding: 12px 16px;
            margin-bottom: 20px;
            font-size: 0.95rem;
            line-height: 1.45;
        }}
        .review-box {{
            background-color: #f0f7ff;
            border-left: 5px solid var(--secondary-color);
            padding: 20px;
            border-radius: 4px;
            margin-bottom: 30px;
        }}
        
        .review-box p {{
            margin: 0 0 1em 0;
            font-size: 1.05rem;
        }}
        .review-box p:last-child {{
            margin-bottom: 0;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        
        th {{
            background-color: #f1f1f1;
            font-weight: bold;
            color: var(--primary-color);
        }}
        
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85rem;
            font-weight: bold;
            color: white;
        }}
        
        .good {{ background-color: #27ae60; }}
        .warning {{ background-color: #f39c12; }}
        .bad {{ background-color: #c0392b; }}
        .neutral {{ background-color: #7f8c8d; }}
        
        .criterion {{ width: 15%; }}
        .level {{ width: 15%; }}
        .explanation {{ width: 70%; font-size: 0.95rem; }}
        
        @media (max-width: 600px) {{
            .container {{ padding: 15px; }}
            th, td {{ display: block; width: 100%; box-sizing: border-box; }}
            tr {{ margin-bottom: 15px; display: block; border-bottom: 2px solid #eee; }}
            td {{ border: none; padding: 5px 10px; }}
            .criterion {{ font-size: 1.1rem; color: var(--secondary-color); }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="verity-llm-notice" role="region" aria-label="YouTube API compliance notice">
            <strong>Notice:</strong> {notice_html}
        </div>
        <h1>Verity Fast Report</h1>
        
        <table class="report-header">
            <tr><th>Video ID</th><td><code>{safe_video_id}</code></td></tr>
            <tr><th>Source Info Hash</th><td><code>{source_info_hash}</code></td></tr>
            <tr><th>Report Generated</th><td>{report_generated_at}</td></tr>
        </table>

        <h2>📋 Verity Review</h2>
        <div class="review-box">
            {review_html}
        </div>
        
        <h2>🔍 CRAAP Analysis</h2>
        <p><em>Evaluation of Currency, Relevance, Authority, Accuracy, and Purpose.</em></p>
        <table>
            <thead>
                <tr>
                    <th>Criterion</th>
                    <th>Rating</th>
                    <th>Assessment</th>
                </tr>
            </thead>
            <tbody>
                {craap_rows}
            </tbody>
        </table>
        
        <div style="margin-top: 40px; text-align: center; color: #7f8c8d; font-size: 0.9rem;">
            <p>Generated by VerityNgn</p>
        </div>
    </div>
</body>
</html>
"""
    return html_content

