import logging
from typing import Dict, Any, Optional
from verityngn.models.report import VerityReport, CredibilityLevel

logger = logging.getLogger(__name__)

def generate_fast_html_report(report: VerityReport, review_text: str) -> str:
    """
    Generate a fast HTML report designed for quick consumption (30-second review).
    
    Includes:
    - Video Thumbnail
    - Video Title
    - ~200 word "Verity Review" of the description/content
    - CRAAP Analysis Table
    """
    
    # Extract data
    video_id = report.media_embed.video_id
    title = report.media_embed.title
    thumbnail_url = report.media_embed.thumbnail_url
    video_url = report.media_embed.video_url
    
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
                
            craap_rows += f"""
            <tr>
                <td class="criterion"><strong>{criterion.capitalize()}</strong></td>
                <td class="level"><span class="badge {color_class}">{level}</span></td>
                <td class="explanation">{explanation}</td>
            </tr>
            """
    else:
        craap_rows = "<tr><td colspan='3'>No CRAAP analysis available.</td></tr>"

    # HTML Template
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verity Fast Report - {title}</title>
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
        
        .media-container {{
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-bottom: 30px;
        }}
        
        .thumbnail {{
            width: 100%;
            max-width: 640px;
            border-radius: var(--border-radius);
            box-shadow: var(--shadow);
            margin-bottom: 15px;
        }}
        
        .video-link {{
            display: inline-block;
            padding: 10px 20px;
            background-color: #ff0000;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-weight: bold;
            font-size: 0.9rem;
        }}
        
        .review-box {{
            background-color: #f0f7ff;
            border-left: 5px solid var(--secondary-color);
            padding: 20px;
            border-radius: 4px;
            margin-bottom: 30px;
        }}
        
        .review-box p {{
            margin: 0;
            font-size: 1.05rem;
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
        <h1>Verity Fast Report</h1>
        
        <div class="media-container">
            <a href="{video_url}" target="_blank">
                <img src="{thumbnail_url}" alt="Thumbnail for {title}" class="thumbnail">
            </a>
            <h3>{title}</h3>
            <a href="{video_url}" target="_blank" class="video-link">Watch on YouTube</a>
        </div>
        
        <h2>📋 Verity Review</h2>
        <div class="review-box">
            <p>{review_text}</p>
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

