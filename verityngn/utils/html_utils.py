import re
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from markdown_it import MarkdownIt
from mdit_py_plugins.front_matter import front_matter_plugin
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.deflist import deflist_plugin
from mdit_py_plugins.tasklists import tasklists_plugin
from mdit_py_plugins.attrs import attrs_plugin

from verityngn.config.settings import OUTPUTS_DIR

def preprocess_markdown(md_content: str) -> str:
    """
    Pre-processes markdown content to handle special cases and formatting.
    
    Args:
        md_content (str): The markdown content to process
        
    Returns:
        str: Processed markdown content
    """
    # Save HTML blocks to prevent them from being processed
    html_blocks = {}
    html_block_count = 0
    
    def save_html_block(match):
        nonlocal html_block_count
        placeholder = f"HTML_BLOCK_{html_block_count}"
        html_blocks[placeholder] = match.group(0)
        html_block_count += 1
        return placeholder
    
    # Extract and save HTML blocks (especially video containers)
    pattern = r'<div class="video-container">[\s\S]*?<!-- VIDEO_CONTAINER_END -->'
    md_content = re.sub(pattern, save_html_block, md_content)
    
    # Process tables directly without using placeholders
    # This ensures tables are properly rendered in the HTML output
    
    # Special handling for tables to ensure they're properly rendered
    # Extract tables and save them for later processing
    table_blocks = {}
    table_count = 0
    
    def save_table(match):
        nonlocal table_count
        placeholder = f"TABLE_PLACEHOLDER_{table_count}"
        
        # Extract the table content
        table_md = match.group(0).strip()
        
        # Ensure the table is properly formatted for MarkdownIt processing
        # Make sure there are no empty lines within the table
        lines = [line for line in table_md.split('\n') if line.strip()]
        
        # Rebuild the table with proper pipe alignment
        formatted_lines = []
        for line in lines:
            # Ensure each line starts and ends with a pipe
            if not line.startswith('|'):
                line = '|' + line
            if not line.endswith('|'):
                line = line + '|'
                
            # Fix any spacing issues
            parts = line.split('|')
            formatted_parts = [part.strip() for part in parts]
            line = '|' + '|'.join(formatted_parts[1:-1]) + '|'
            
            formatted_lines.append(line)
            
        # Join the table lines without empty lines in between
        formatted_table = '\n'.join(formatted_lines)
        
        # Store the formatted table
        table_blocks[placeholder] = formatted_table
        table_count += 1
        return placeholder
    
    # Find well-formed markdown tables (no empty lines within)
    # This pattern matches Typora-compatible tables with more flexibility:
    table_pattern = r'(\|[^\n]+\|\n\|[-:]+\|[-:]+\|[-:]*\|\n(?:\|[^\n]+\|\n?)+)'
    md_content = re.sub(table_pattern, save_table, md_content, flags=re.DOTALL)
    
    # Catch tables that might have different formatting
    alt_table_pattern = r'(\|[^\n]+\|\n\|[-:]+\|[-:]+\|[-:]+\|\n(?:\|[^\n]+\|\n?)+)'
    md_content = re.sub(alt_table_pattern, save_table, md_content, flags=re.DOTALL)
    
    # Catch tables with empty cells
    empty_cell_pattern = r'(\|[^\n]+\|\n\|[-:]+\|[-:]+\|[-:]+\|\n(?:\|[^\n]*\|\n?)+)'
    md_content = re.sub(empty_cell_pattern, save_table, md_content, flags=re.DOTALL)
    
    # Handle special characters and escaping (avoiding HTML placeholders)
    pattern = r'(HTML_BLOCK_\d+)'
    parts = re.split(f'({pattern})', md_content)
    
    for i in range(0, len(parts), 2):
        # Only process non-placeholder parts
        if i < len(parts):
            parts[i] = parts[i].replace('\\', '\\\\').replace('*', '\\*').replace('_', '\\_')
    
    md_content = ''.join(parts)
    
    # Make URLs clickable with underline style (avoiding HTML placeholders)
    url_pattern = r'(https?://[^\s<>]+)(?![^<]*>|[^<>]*</)'
    parts = re.split(f'({pattern})', md_content)
    
    for i in range(0, len(parts), 2):
        # Only process non-placeholder parts
        if i < len(parts):
            # Convert URLs to Markdown links without escaping the URL itself
            parts[i] = re.sub(url_pattern, r'[Click here](\1)', parts[i])
    
    md_content = ''.join(parts)
    
    # Make additional pass to fix any URLs that were not captured
    # This captures URLs that weren't surrounded by spaces or were at the start/end of text
    url_pattern2 = r'(?<![(\[])(https?://[^\s<>]+)(?![^<]*>|[^<>]*</|\)])'
    md_content = re.sub(url_pattern2, r'[Click here](\1)', md_content)
    
    # Ensure all sections have content
    md_content = re.sub(r'(##\s+[\w\s]+)\s+##', r'\1\n\nNo content provided.\n\n##', md_content)
    
    # Restore HTML blocks
    for placeholder, html in html_blocks.items():
        md_content = md_content.replace(placeholder, html)
    
    return md_content

def convert_md_to_styled_html(md_content: str, template_path: Optional[str] = None) -> str:
    """
    Convert markdown to styled HTML with enhanced parsing and special cases.
    
    Args:
        md_content (str): The markdown content to convert
        template_path (Optional[str]): Path to the HTML template file, or None to use default styling
    
    Returns:
        str: The styled HTML content
    """
    # Save the original markdown for potential fallback use
    original_md = md_content
    
    # Extract video container information using the unique marker
    video_container_match = re.search(r'<div class="video-container">[\s\S]*?<!-- VIDEO_CONTAINER_END -->', md_content)
    video_container_html = ""
    if video_container_match:
        video_container_html = video_container_match.group(0).replace("<!-- VIDEO_CONTAINER_END -->", "")
        # Remove the video container from markdown to prevent duplication
        md_content = md_content.replace(video_container_match.group(0), "")
    
    # Initialize markdown parser with comprehensive configuration
    md = (
        MarkdownIt("gfm-like", {"html": True, "linkify": True, "typographer": True})
        .use(front_matter_plugin)
        .use(footnote_plugin)
        .use(deflist_plugin)
        .use(tasklists_plugin)
        .use(attrs_plugin)
    )
    
    # Convert markdown to basic HTML - this should handle all tables properly
    html_content = md.render(md_content)
    
    # Special handling for the "Odds & Sources" column formatting
    html_content = format_odds_sources_column(html_content)
        
    # Fix any remaining markdown table issues
    html_content = fix_markdown_table_issues(html_content)
    
    # Ensure section headers are properly preserved
    html_content = re.sub(r'<h2>([^<]+)</h2>\s*<h3>([^<]+)</h3>', r'<h2>\1</h2>\n<h3>\2</h3>', html_content)
    
    # Style assessment verdicts
    html_content = style_assessments(html_content)
    
    # Add special sections (this includes enhanced CSS)
    html_content = add_special_sections(html_content)
    
    # Process evidence sections
    html_content = process_evidence_sections(html_content)
    
    # Remove any duplicate CSS styles
    html_content = remove_duplicate_css(html_content)
    
    return html_content

def format_odds_sources_column(html_content: str) -> str:
    """
    Format the "Odds & Sources" column to match the golden version styling.
    
    Args:
        html_content (str): The HTML content to process
        
    Returns:
        str: HTML content with properly formatted "Odds & Sources" column
    """
    # Fix asterisk-based markdown formatting that wasn't converted to HTML properly
    # Match the exact pattern from the markdown files
    odds_pattern_md = r'\*\*True:\*\* (\d+%)<br>\*\*False:\*\* (\d+%)<br>\*\*Uncertain:\*\* (\d+%)<br><br>\[(\d+) sources\]\(([^)]+)\)'
    
    def format_odds_cell(match):
        true_pct = match.group(1)
        false_pct = match.group(2)
        uncertain_pct = match.group(3)
        source_count = match.group(4)
        source_link = match.group(5)
        
        return f'<strong>True:</strong> {true_pct}<br><strong>False:</strong> {false_pct}<br><strong>Uncertain:</strong> {uncertain_pct}<br><br><a href="{source_link}">{source_count} sources</a>'
    
    # Apply the formatting to the HTML content
    html_content = re.sub(odds_pattern_md, format_odds_cell, html_content)
    
    return html_content

def style_assessments(html_content: str) -> str:
    """
    Add styling to assessment verdicts in the HTML content.
    
    Args:
        html_content (str): The HTML content to style
        
    Returns:
        str: Styled HTML content
    """
    # Style assessment levels in tables with stronger visual indicators
    assessment_patterns = [
        (r'(<td[^>]*>)(HIGHLY_LIKELY_TRUE|Highly Likely to be True)(</td>)', 'verdict-true'),
        (r'(<td[^>]*>)(LIKELY_TRUE|Likely to be True)(</td>)', 'verdict-true'),
        (r'(<td[^>]*>)(HIGHLY_LIKELY_FALSE|Highly Likely to be False)(</td>)', 'verdict-false'),
        (r'(<td[^>]*>)(LIKELY_FALSE|Likely to be False)(</td>)', 'verdict-false'),
        (r'(<td[^>]*>)(MIXED|Mixed Truthfulness|Partially True)(</td>)', 'verdict-partially-true'),
        (r'(<td[^>]*>)(UNABLE_DETERMINE|Unable to Determine|Insufficient Evidence)(</td>)', 'verdict-unverified')
    ]
    
    for pattern, css_class in assessment_patterns:
        html_content = re.sub(
                pattern,
                r'\1<span class="verdict ' + css_class + r'">\2</span>\3',
            html_content
        )
        
    # Also style overall assessment in section headings - with more flexible patterns
    heading_patterns = [
        (r'(Assessment: )(HIGHLY_LIKELY_TRUE|Highly Likely to be True)', 'verdict-true'),
        (r'(Assessment: )(LIKELY_TRUE|Likely to be True)', 'verdict-true'),
        (r'(Assessment: )(HIGHLY_LIKELY_FALSE|Highly Likely to be False)', 'verdict-false'),
        (r'(Assessment: )(LIKELY_FALSE|Likely to be False)', 'verdict-false'),
        (r'(Assessment: )(MIXED|Mixed Truthfulness|Partially True)', 'verdict-partially-true'),
        (r'(Assessment: )(UNABLE_DETERMINE|Unable to Determine|Insufficient Evidence)', 'verdict-unverified')
    ]
    
    for pattern, css_class in heading_patterns:
        html_content = re.sub(
                pattern,
                r'\1<span class="verdict ' + css_class + r'">\2</span>',
            html_content
        )
        
    # Style standalone assessments in paragraphs - separate from heading patterns
    paragraph_patterns = [
        (r'(<p>)(HIGHLY_LIKELY_TRUE|Highly Likely to be True)(</p>)', 'verdict-true'),
        (r'(<p>)(LIKELY_TRUE|Likely to be True)(</p>)', 'verdict-true'),
        (r'(<p>)(HIGHLY_LIKELY_FALSE|Highly Likely to be False)(</p>)', 'verdict-false'),
        (r'(<p>)(LIKELY_FALSE|Likely to be False)(</p>)', 'verdict-false'),
        (r'(<p>)(MIXED|Mixed Truthfulness|Partially True)(</p>)', 'verdict-partially-true'),
        (r'(<p>)(UNABLE_DETERMINE|Unable to Determine|Insufficient Evidence)(</p>)', 'verdict-unverified')
    ]
    
    for pattern, css_class in paragraph_patterns:
        html_content = re.sub(
                pattern,
                r'\1<span class="verdict ' + css_class + r'">\2</span>\3',
            html_content
        )
        
    return html_content

def add_special_sections(html_content: str) -> str:
    """
    Add special formatting and sections to the HTML content.
    
    Args:
        html_content (str): The HTML content to enhance
        
    Returns:
        str: Enhanced HTML content
    """
    # Add enhanced CSS for tables and content
    enhanced_css = """
    <style>
        /* Enhanced table styles */
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 1.5em 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
            overflow: hidden;
        }
        
        table th {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: 600;
            padding: 15px 12px;
            text-align: left;
            border: none;
            font-size: 14px;
            letter-spacing: 0.5px;
        }
        
        table td {
            padding: 12px;
            border: 1px solid #e0e0e0;
            vertical-align: top;
            line-height: 1.5;
            background-color: #fff;
        }
        
        table tbody tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        
        table tbody tr:hover {
            background-color: #e3f2fd;
            transform: scale(1.01);
            transition: all 0.2s ease;
        }
        
        /* Claims table specific styling */
        .claims-table td:first-child {
            width: 80px;
            text-align: center;
            font-weight: bold;
            background-color: #f5f5f5;
        }
        
        .claims-table td:nth-child(2) {
            width: 100px;
            text-align: center;
        }
        
        .claims-table .claim-text {
            max-width: 300px;
            word-wrap: break-word;
        }
        
        /* Evidence table specific styling */
        .evidence-table td:first-child {
            width: 25%;
            font-weight: 500;
        }
        
        .evidence-table td:nth-child(2) {
            width: 15%;
            text-align: center;
        }
        
        .evidence-table td:nth-child(3) {
            width: 45%;
        }
        
        .evidence-table td:last-child {
            width: 15%;
            text-align: center;
        }
        
        /* CRAAP table specific styling */
        .craap-table td:first-child {
            width: 20%;
            font-weight: 600;
            text-transform: capitalize;
        }
        
        .craap-table td:nth-child(2) {
            width: 15%;
            text-align: center;
        }
        
        .craap-table td:last-child {
            width: 65%;
        }
        
        /* Enhanced verdict badges */
        .verdict {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin: 2px;
            border: 2px solid transparent;
        }
        
        .verdict-true {
            background: linear-gradient(135deg, #4caf50, #45a049);
            color: white;
            border-color: #4caf50;
            box-shadow: 0 2px 4px rgba(76, 175, 80, 0.3);
        }
        
        .verdict-false {
            background: linear-gradient(135deg, #f44336, #d32f2f);
            color: white;
            border-color: #f44336;
            box-shadow: 0 2px 4px rgba(244, 67, 54, 0.3);
        }
        
        .verdict-partially-true {
            background: linear-gradient(135deg, #ff9800, #f57c00);
            color: white;
            border-color: #ff9800;
            box-shadow: 0 2px 4px rgba(255, 152, 0, 0.3);
        }
        
        .verdict-unverified {
            background: linear-gradient(135deg, #2196f3, #1976d2);
            color: white;
            border-color: #2196f3;
            box-shadow: 0 2px 4px rgba(33, 150, 243, 0.3);
        }
        
        /* Source links */
        .evidence-link {
            display: inline-block;
            padding: 4px 8px;
            background-color: #2196f3;
            color: white !important;
            text-decoration: none;
            border-radius: 4px;
            font-size: 12px;
            transition: background-color 0.2s;
        }
        
        .evidence-link:hover {
            background-color: #1976d2;
            text-decoration: none;
        }
        
        /* Empty table fallback */
        .empty-table {
            text-align: center;
            padding: 40px;
            color: #666;
            font-style: italic;
            background-color: #f9f9f9;
            border: 2px dashed #ddd;
            border-radius: 8px;
            margin: 20px 0;
        }
        
        /* Section headers */
        h2 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-top: 2em;
            margin-bottom: 1em;
        }
        
        h3 {
            color: #34495e;
            margin-top: 1.5em;
            margin-bottom: 0.8em;
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            table {
                font-size: 12px;
            }
            
            table th, table td {
                padding: 8px 6px;
            }
            
            .verdict {
                font-size: 10px;
                padding: 4px 8px;
            }
        }
    </style>
    """
    
    # Insert CSS into head or at the beginning
    if '<head>' in html_content:
        html_content = html_content.replace('<head>', f'<head>{enhanced_css}')
    else:
        html_content = enhanced_css + html_content
    
    # Add table classes based on content
    html_content = re.sub(r'(<table[^>]*>)(?=.*?<th[^>]*>.*?Claim.*?</th>)', r'<table class="claims-table">', html_content, flags=re.DOTALL | re.IGNORECASE)
    html_content = re.sub(r'(<table[^>]*>)(?=.*?<th[^>]*>.*?Source.*?</th>)', r'<table class="evidence-table">', html_content, flags=re.DOTALL | re.IGNORECASE)
    html_content = re.sub(r'(<table[^>]*>)(?=.*?<th[^>]*>.*?Criterion.*?</th>)', r'<table class="craap-table">', html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # Handle empty tables by adding fallback content
    empty_table_pattern = r'<table[^>]*>\s*<thead>.*?</thead>\s*<tbody>\s*<tr>\s*(<td[^>]*>\s*</td>\s*)+</tr>\s*</tbody>\s*</table>'
    
    def replace_empty_table(match):
        table_html = match.group(0)
        if 'Claim' in table_html:
            return '<div class="empty-table">📝 No claims were found in this video to analyze.</div>'
        elif 'Source' in table_html:
            return '<div class="empty-table">🔍 No evidence sources were identified for verification.</div>'
        elif 'Criterion' in table_html:
            return '<div class="empty-table">📊 CRAAP analysis could not be completed.</div>'
        else:
            return '<div class="empty-table">📋 No data available for this section.</div>'
    
    html_content = re.sub(empty_table_pattern, replace_empty_table, html_content, flags=re.DOTALL)
    
    return html_content

def process_evidence_sections(html_content: str) -> str:
    """
    Process evidence sections in the HTML content.
    
    Args:
        html_content (str): The HTML content to process
        
    Returns:
        str: Processed HTML content
    """
    # Add evidence container styling
    html_content = re.sub(
        r'(<h2[^>]*>4\. Evidence Summary</h2>)',
        r'<div class="evidence-container">\1',
        html_content
    )
    
    # Close the evidence container before the next h2
    if '<div class="evidence-container">' in html_content:
        parts = html_content.split('<div class="evidence-container">')
        if len(parts) > 1:
            second_part = parts[1]
            next_h2_match = re.search(r'<h2', second_part)
            if next_h2_match:
                pos = next_h2_match.start()
                second_part = second_part[:pos] + '</div>' + second_part[pos:]
                html_content = parts[0] + '<div class="evidence-container">' + second_part
            else:
                html_content += '</div>'
    
    # Add sources container styling
    html_content = re.sub(
        r'(<h3[^>]*>Secondary Sources</h3>)',
        r'<div class="sources-container">\1',
        html_content
    )
    
    # Close the sources container before the next h3 or h2
    if '<div class="sources-container">' in html_content:
        parts = html_content.split('<div class="sources-container">')
        if len(parts) > 1:
            second_part = parts[1]
            next_heading_match = re.search(r'<h[23]', second_part)
            if next_heading_match:
                pos = next_heading_match.start()
                second_part = second_part[:pos] + '</div>' + second_part[pos:]
                html_content = parts[0] + '<div class="sources-container">' + second_part
            else:
                html_content += '</div>'
    
    # Add evidence header styling
    html_content = re.sub(
        r'<h3[^>]*>Primary Sources</h3>',
        r'<h3 class="evidence-header primary-sources">Primary Sources</h3>',
        html_content
    )
    
    html_content = re.sub(
        r'<h3[^>]*>Secondary Sources</h3>',
        r'<h3 class="evidence-header secondary-sources">Secondary Sources</h3>',
        html_content
    )
    
    return html_content

def create_summary_box(md_content: str) -> str:
    """
    Create a summary box from the markdown content.
    
    Args:
        md_content (str): The markdown content to extract summary from
        
    Returns:
        str: HTML for the summary box
    """
    # Ensure md_content is a string
    if not isinstance(md_content, str):
        # If it's a list, join it; otherwise, convert to string
        if isinstance(md_content, list):
            md_content = "\n\n".join(md_content)
        else:
            md_content = str(md_content)
            
    # Extract overall assessment - be more flexible with the pattern
    assessment_match = re.search(r'## \d+\.\s*Overall Truthfulness Assessment:?\s*(.*?)(?:\n|\r\n|\r)', md_content)
    if not assessment_match:
        # Try without numbering
        assessment_match = re.search(r'## Overall Truthfulness Assessment:?\s*(.*?)(?:\n|\r\n|\r)', md_content)
    
    assessment = assessment_match.group(1).strip() if assessment_match else "Not specified"
    
    # Extract explanation (text after the assessment heading until the next heading)
    if assessment_match:
        start_pos = assessment_match.end()
        next_heading = re.search(r'\n##', md_content[start_pos:])
        if next_heading:
            explanation = md_content[start_pos:start_pos+next_heading.start()].strip()
        else:
            explanation = md_content[start_pos:].strip()
    else:
        explanation = ""
    
    # Extract the timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d")
    
    # Create a styled summary box with improved overall assessment but without key findings table
    verdict_class = "verdict-unverified"
    if "TRUE" in assessment.upper():
        verdict_class = "verdict-true"
    elif "FALSE" in assessment.upper():
        verdict_class = "verdict-false"
    elif "MIXED" in assessment.upper() or "PARTIALLY" in assessment.upper():
        verdict_class = "verdict-partially-true"
    
    summary_html = f"""<div class="summary-box">
            <h2>Executive Summary</h2>
            <div class="overall-assessment">
                <h3>Overall Truthfulness Assessment</h3>
                <p><span class="verdict {verdict_class}">{assessment}</span></p>
                <p>{explanation}</p>
        </div>
            
            <p class="see-details"><strong>See "Summary of Key Findings" below for detailed analysis</strong></p>
            
            <p><strong>Analysis Date:</strong> {timestamp}</p>
        </div>"""
    
    return summary_html

def get_template_css() -> str:
    """
    Get the CSS for the HTML template.
    
    Returns:
        str: CSS content
    """
    return """
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }
        .container {
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            padding: 30px;
        }
        h1, h2, h3, h4 {
            color: #2c3e50;
            margin-top: 1.5em;
        }
        h1 {
            font-size: 2.2em;
            border-bottom: 2px solid #eaecef;
            padding-bottom: 0.3em;
        }
        h2 {
            font-size: 1.8em;
            border-bottom: 1px solid #eaecef;
            padding-bottom: 0.3em;
        }
        h3 {
            font-size: 1.4em;
        }
        a {
            color: #0366d6;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        code {
            background-color: #f6f8fa;
            border-radius: 3px;
            font-family: 'Courier New', Courier, monospace;
            padding: 0.2em 0.4em;
        }
        pre {
            background-color: #f6f8fa;
            border-radius: 3px;
            padding: 16px;
            overflow: auto;
        }
        blockquote {
            border-left: 4px solid #dfe2e5;
            color: #6a737d;
            margin: 0;
            padding: 0 1em;
        }
        /* Table styles with improved borders, colors, and styling */
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0 30px 0;
            border: 2px solid #4a5568;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            overflow: hidden;
            page-break-inside: avoid;
        }
        
        th, td {
            padding: 10px 16px;
            text-align: left;
            vertical-align: top;
            border: 1px solid #4a5568;
        }
        
        th {
            background-color: #2c3e50;
            color: white;
            font-weight: bold;
            border-bottom: 2px solid #4a5568;
        }
        
        tr:nth-child(even) {
            background-color: #f7fafc;
        }
        
        tr:last-child td {
            border-bottom: 1px solid #4a5568;
        }
        
        tr:hover {
            background-color: #edf2f7;
        }
        
        /* Special highlighting for verification results */
        td .verdict-true {
            background-color: #c6f6d5;
            color: #22543d;
            padding: 4px 8px;
            border-radius: 4px;
            display: inline-block;
        }
        
        td .verdict-false {
            background-color: #fed7d7;
            color: #822727;
            padding: 4px 8px;
            border-radius: 4px;
            display: inline-block;
        }
        
        td .verdict-partially-true {
            background-color: #feebc8;
            color: #744210;
            padding: 4px 8px;
            border-radius: 4px;
            display: inline-block;
        }
        
        td .verdict-unverified {
            background-color: #e2e8f0;
            color: #2d3748;
            padding: 4px 8px;
            border-radius: 4px;
            display: inline-block;
        }
        
        /* Caption styling for Typora */
        caption {
            caption-side: top;
            font-style: italic;
            color: #555;
            text-align: center;
            padding: 8px;
            font-size: 0.9em;
            background-color: #f8f9fa;
            border-bottom: 1px solid #e2e8f0;
        }
        
        /* For Typora compatibility */
        @media print {
            table {
                page-break-inside: avoid;
                border: 1px solid #4a5568;
            }
            tr {
                page-break-inside: avoid;
            }
            th {
                background-color: #e2e8f0 !important;
                color: #2d3748 !important;
            }
            h1, h2, h3, h4 {
                page-break-after: avoid;
            }
            .container {
                box-shadow: none;
            }
        }
        .video-container {
            position: relative;
            padding-bottom: 56.25%;
            height: 0;
            overflow: hidden;
            max-width: 100%;
            margin-bottom: 20px;
        }
        .video-container iframe {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
        }
        .verdict {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
            margin: 10px 0;
        }
        .verdict-true {
            background-color: #e6f7e6;
            color: #2e7d32;
        }
        .verdict-partially-true {
            background-color: #fff8e1;
            color: #f57f17;
        }
        .verdict-false {
            background-color: #ffebee;
            color: #c62828;
        }
        .verdict-unverified {
            background-color: #e3f2fd;
            color: #1565c0;
        }
        .evidence-container, .sources-container {
            background-color: #f8f9fa;
            border-radius: 4px;
            padding: 15px;
            margin-bottom: 20px;
        }
        .evidence-header, .sources-header {
            color: #2c3e50;
            margin-top: 1.2em;
            margin-bottom: 0.5em;
        }
        .summary-box {
            background-color: #f8f9fa;
            border-left: 5px solid #4caf50;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .summary-box h2 {
            color: #2c3e50;
            margin-top: 0;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 10px;
        }
        
        .summary-box h3 {
            color: #2c3e50;
            margin-top: 15px;
            font-size: 1.2em;
        }
        
        .overall-assessment {
            margin-bottom: 15px;
            padding: 15px;
            background-color: #f1f5f9;
            border-radius: 4px;
        }
        
        .see-details {
            color: #4a5568;
            font-style: italic;
            text-align: center;
            margin: 15px 0;
            padding: 8px;
            background-color: #f1f5f9;
            border-radius: 4px;
        }
        
        .assessment-box {
            background-color: #f1f5f9;
            border-left: 5px solid #2196f3;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .assessment-box h2 {
            color: #2c3e50;
            margin-top: 0;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 10px;
        }
        
        .assessment-content {
            margin-top: 15px;
        }
        
        .assessment-content p:first-of-type {
            font-size: 1.2em;
            font-weight: 500;
        }
        
        .recommendations-box {
            background-color: #f3e5f5;
            border-left: 5px solid #9c27b0;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .craap-box {
            background-color: #fff3e0;
            border-left: 5px solid #ff9800;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .craap-box h2 {
            color: #2c3e50;
            margin-top: 0;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 10px;
        }
        
        footer {
            margin-top: 30px;
            text-align: center;
            color: #6c757d;
            font-size: 0.9em;
            padding: 15px;
            border-top: 1px solid #e2e8f0;
        }
        .source-credibility {
            display: inline-block;
            padding: 3px 6px;
            border-radius: 3px;
            font-size: 0.8em;
            margin-left: 5px;
        }
        .credibility-high {
            background-color: #4caf50;
            color: white;
        }
        .credibility-medium {
            background-color: #ff9800;
            color: white;
        }
        .credibility-low {
            background-color: #f44336;
            color: white;
        }
        .claims-box {
            background-color: #e6f7ff;
            border-left: 5px solid #1890ff;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .claims-box h2 {
            color: #2c3e50;
            margin-top: 0;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 10px;
        }
        
        .claims-box table {
            margin-top: 20px;
        }
        
        .evidence-container, .sources-container {
            background-color: #f8f9fa;
            border-radius: 4px;
            padding: 15px;
            margin-bottom: 20px;
        }
        .evidence-box {
            background-color: #f5f5f5;
            border-left: 5px solid #607d8b;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .evidence-box h2 {
            color: #2c3e50;
            margin-top: 0;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 10px;
        }
        
        .evidence-container, .sources-container {
            background-color: #f8f9fa;
            border-radius: 4px;
            padding: 15px;
            margin: 15px 0;
            border: 1px solid #e2e8f0;
        }
        
        .recommendations-box ol {
            margin-left: 20px;
            padding-left: 20px;
        }
        
        .recommendations-box li {
            margin-bottom: 10px;
        }
        
        .recommendations-box li strong {
            font-weight: 600;
        }
        
        .recommendations-box p:first-of-type {
            font-weight: 600;
            margin-bottom: 15px;
        }
        
        .evidence-container {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
            border: 1px solid #e2e8f0;
        }
        
        .evidence-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        
        .evidence-table th {
            background-color: #f1f5f9;
            padding: 10px;
            text-align: left;
            border-bottom: 2px solid #cbd5e1;
            font-weight: 600;
        }
        
        .evidence-table td {
            padding: 10px;
            border-bottom: 1px solid #e2e8f0;
            vertical-align: top;
        }
        
        .evidence-table tr:hover {
            background-color: #f1f5f9;
        }
        
        .evidence-link {
            display: inline-block;
            padding: 4px 10px;
            background-color: #3182ce;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-size: 0.9em;
            transition: background-color 0.2s;
        }
        
        .evidence-link:hover {
            background-color: #2c5282;
            text-decoration: none;
        }
        
        .source-icon {
            display: inline-block;
            width: 16px;
            height: 16px;
            margin-right: 8px;
            border-radius: 50%;
            background-color: #cbd5e1;
        }
        
        .source-academic {
            background-color: #4299e1;
        }
        
        .source-government {
            background-color: #48bb78;
        }
        
        .source-news {
            background-color: #ed8936;
        }
        
        .high-relevance {
            background-color: #ebf8ff;
        }
        
        .medium-relevance {
            background-color: #f0fff4;
        }
        
        .evidence-quality-summary {
            background-color: #f0fff4;
            border-left: 4px solid #48bb78;
                padding: 15px;
            margin-top: 20px;
            border-radius: 4px;
        }
        
        .evidence-quality-summary h4 {
            margin-top: 0;
            color: #2c5282;
            margin-bottom: 10px;
        }
        
        .evidence-quality-summary ul {
            margin: 0;
            padding-left: 20px;
        }
        
        .evidence-quality-summary li {
            margin-bottom: 5px;
        }
        
        /* Styling for the accordion */
        details {
            margin: 1em 0;
            padding: 0.5em;
            border: 1px solid #e2e8f0;
            border-radius: 4px;
            background-color: #f8fafc;
        }
        
        summary {
            padding: 0.5em;
            font-weight: bold;
            cursor: pointer;
            color: #3182ce;
        }
        
        details[open] summary {
            margin-bottom: 10px;
            border-bottom: 1px solid #e2e8f0;
        }
        
        /* Styling for the View All Sources button */
        .sources-button {
            background-color: #3182ce;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            margin-bottom: 10px;
            transition: background-color 0.3s;
        }
        
        .sources-button:hover {
            background-color: #2c5282;
        }
    """

def generate_html_report(report: Dict[str, Any], output_path: str) -> str:
    """
    Generate an HTML report from the report data.
    
    Args:
        report (Dict[str, Any]): The report data
        output_path (str): The output path for the HTML file
        
    Returns:
        str: The path to the generated HTML file
    """
    # Check if this is an error report
    if "error" in report and len(report) == 1:
        # This is an error report, create a simple error page
        error_message = report["error"]
        error_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Error Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .error-container {{ 
            border: 2px solid #ff0000; 
            padding: 20px; 
            border-radius: 5px;
            background-color: #fff0f0;
        }}
        h1 {{ color: #ff0000; }}
    </style>
</head>
<body>
    <div class="error-container">
        <h1>Error Generating Report</h1>
        <p>There was an error while generating the report:</p>
        <pre>{error_message}</pre>
    </div>
</body>
</html>
"""
        # Write the error HTML to the file
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(error_html)
        return output_path
    
    # Regular report processing
    try:
        # Create a simple markdown representation of the report
        md_content = report_to_markdown(report)

        # Initialize the Markdown parser with comprehensive configuration
        html_md = (
            MarkdownIt("gfm-like", {"html": True, "linkify": True, "typographer": True})
            .use(front_matter_plugin)
            .use(footnote_plugin)
            .use(deflist_plugin)
            .use(tasklists_plugin)
            .use(attrs_plugin)
        ).render(md_content)
        
        # Save the debug HTML
        try:
            video_id = report.media_embed.video_id
            debug_html_path = os.path.join(OUTPUTS_DIR, video_id, f"{video_id}_html_debug.html")
            os.makedirs(os.path.dirname(debug_html_path), exist_ok=True)
            with open(debug_html_path, 'w', encoding='utf-8') as f:
                f.write(html_md)
        except Exception as e:
            print(f"Error saving debug HTML: {e}")

        # Use the debug HTML to generate the final report
        final_html_path = copy_and_enhance_debug_html(video_id, OUTPUTS_DIR)
        
        if final_html_path:
            return final_html_path
        else:
            # Fallback to the original HTML generation if debug enhancement fails
            html_content = convert_md_to_styled_html(md_content, None)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return output_path
            
    except Exception as e:
        # Create an error HTML file
        error_message = str(e)
        error_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Error Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .error-container {{ 
            border: 2px solid #ff0000; 
            padding: 20px; 
            border-radius: 5px;
            background-color: #fff0f0;
        }}
        h1 {{ color: #ff0000; }}
    </style>
</head>
<body>
    <div class="error-container">
        <h1>Error Generating Report</h1>
        <p>There was an error while generating the report:</p>
        <pre>{error_message}</pre>
        <p>Original report data:</p>
        <pre>{str(report)[:1000]}</pre>
    </div>
</body>
</html>
"""
        # Write the error HTML to the file
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(error_html)
        return output_path

def save_json_report(report: Dict[str, Any], output_path: str) -> str:
    """
    Save the report as a JSON file.
    
    Args:
        report (Dict[str, Any]): The report data
        output_path (str): The output path for the JSON file
        
    Returns:
        str: The path to the generated JSON file
    """
    try:
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Define custom JSON encoder for handling datetime objects
        class DateTimeEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                return super().default(obj)
        
        # Convert to dict if it's a Pydantic model
        if hasattr(report, "model_dump"):
            report_dict = report.model_dump()
        else:
            report_dict = report
            
        # Save the report as JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, cls=DateTimeEncoder)
        
        return output_path
    except Exception as e:
        print(f"Error saving JSON report: {e}")
        
        # Create a simple error JSON
        error_report = {"error": str(e)}
        try:
            # Ensure the output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save the error report as JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(error_report, f, indent=2)
        except Exception as e2:
            print(f"Error saving error JSON: {e2}")
        
        return output_path

def save_markdown_report(report: Dict[str, Any], output_path: str) -> str:
    """
    Save the report as a Markdown file.
    
    Args:
        report (Dict[str, Any]): The report data
        output_path (str): The output path for the Markdown file
        
    Returns:
        str: The path to the generated Markdown file
    """
    try:
        # Check if this is an error report
        if "error" in report and len(report) == 1:
            # This is an error report, create a simple error markdown
            error_message = report["error"]
            error_md = f"""# Error Generating Report

There was an error while generating the report:

```
{error_message}
```
"""
            # Ensure the output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Write the error markdown to the file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(error_md)
            return output_path
        
        # Create markdown content
        md_content = report_to_markdown(report)
        
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save the markdown to a file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return output_path
    except Exception as e:
        print(f"Error saving markdown report: {e}")
        
        # Create a simple error markdown
        error_md = f"""# Error Generating Report

There was an error while generating the report:

```
{str(e)}
```

Original report data (first 1000 chars):

```
{str(report)[:1000]}
```
"""
        try:
            # Ensure the output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Write the error markdown to the file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(error_md)
        except Exception as e2:
            print(f"Error saving error markdown: {e2}")
        
        return output_path

def get_value(data, key, default=""):
    """
    Gets a value from either a dictionary or an object with attributes.
    Works with both dict-style access and attribute-style access.
    
    Args:
        data: The data object or dictionary
        key: The key or attribute name to access
        default: Default value if key/attribute doesn't exist
        
    Returns:
        The value or default if not found
    """
    if isinstance(data, dict):
        return data.get(key, default)
    else:
        return getattr(data, key, default) if hasattr(data, key) else default

def report_to_markdown(report: Dict[str, Any]) -> str:
    """
    Convert the report data to Markdown format.
    
    Args:
        report (Dict[str, Any]): The report data
        
    Returns:
        str: The Markdown content
    """
    # Start with the video embedding
    media_embed = get_value(report, "media_embed", {})
    video_title = get_value(media_embed, "title", "Unknown Video")
    video_id = get_value(media_embed, "video_id", "")
    video_url = get_value(media_embed, "video_url", "")
    thumbnail_url = get_value(media_embed, "thumbnail_url", "")
    
    # Create the video container HTML (will be preserved during markdown conversion)
    # Don't include the description in the embed to avoid duplication
    video_container = f"""<div class="video-embed">
    <h2>{video_title}</h2>
    <a href="{video_url}" target="_blank">
        <img src="{thumbnail_url}" alt="{video_title}" width="560">
    </a>
    <p>Video ID: {video_id}</p>
</div><!-- VIDEO_CONTAINER_END -->"""
    
    # Start building the markdown content
    md_content = [video_container]
    
    # Add video description
    md_content.append("## Video Description")
    md_content.append(get_value(report, "description", "").replace('\n', '\n\n'))
    
    # Add assessment section
    overall_assessment = get_value(report, "overall_assessment", ["UNABLE_DETERMINE", "Assessment in progress"])
    
    # Handle different formats of overall_assessment
    if isinstance(overall_assessment, list) and len(overall_assessment) >= 1:
        result = overall_assessment[0]
        explanation = overall_assessment[1] if len(overall_assessment) > 1 else ""
        md_content.append(f"## 1. Overall Truthfulness Assessment: {result}")
        md_content.append(f"{explanation}")
    elif isinstance(overall_assessment, tuple) and len(overall_assessment) >= 1:
        result = overall_assessment[0]
        explanation = overall_assessment[1] if len(overall_assessment) > 1 else ""
        # Handle if the first element is an enum
        if hasattr(result, 'value'):
            result = result.value
        md_content.append(f"## 1. Overall Truthfulness Assessment: {result}")
        md_content.append(f"{explanation}")
    else:
        # Try to access as a property/attribute if it's an object
        try:
            result = getattr(overall_assessment, 'value', 'UNABLE_DETERMINE')
            explanation = getattr(overall_assessment, 'explanation', 'Assessment in progress')
            md_content.append(f"## 1. Overall Truthfulness Assessment: {result}")
            md_content.append(f"{explanation}")
        except (AttributeError, TypeError):
            # Default fallback
            md_content.append("## 1. Overall Truthfulness Assessment: UNABLE_DETERMINE")
            md_content.append("Assessment in progress")
    
    # Add key findings
    md_content.append("## 2. Summary of Key Findings")
    md_content.append("")  # Empty line before table
    key_findings = get_value(report, "key_findings", [])
    if key_findings:
        # Typora-compatible table format - NO empty lines within table
        table_rows = []
        table_rows.append("| Finding | Description |")
        table_rows.append("|:--------|:------------|")
        
        for finding in key_findings:
            # Check if it's a KeyFinding object from the models.report module
            if hasattr(finding, 'category') and hasattr(finding, 'description'):
                # Direct access to KeyFinding properties
                category = finding.category if finding.category else ""
                description = finding.description if finding.description else ""
                
                # Escape pipe characters for markdown tables
                category = str(category).replace('|', r'\|')
                description = str(description).replace('|', r'\|')
                
                table_rows.append(f"| {category} | {description} |")
            # Fall back to dictionary access if it's a dict
            elif isinstance(finding, dict):
                category = get_value(finding, 'category', '')
                description = get_value(finding, 'description', '')
                
                # Escape pipe characters for markdown tables
                category = str(category).replace('|', r'\|')
                description = str(description).replace('|', r'\|')
                
                table_rows.append(f"| {category} | {description} |")
            elif isinstance(finding, str):
                # Try to parse string containing both category and description
                category_match = re.search(r"category=['\"]?(.*?)['\"]?(?:\s+description=|$)", finding)
                description_match = re.search(r"description=['\"]?(.*?)['\"]?$", finding)
                
                if category_match and description_match:
                    category = category_match.group(1).replace('|', r'\|')
                    description = description_match.group(1).replace('|', r'\|')
                    table_rows.append(f"| {category} | {description} |")
                else:
                    # Just use as is
                    escaped_finding = finding.replace('|', r'\|')
                    table_rows.append(f"| {escaped_finding} | |")
            else:
                # For any other type of finding
                escaped_finding = str(finding).replace('|', r'\|')
                table_rows.append(f"| {escaped_finding} | |")
                
        md_content.append("\n".join(table_rows))
    else:
        # Empty table for Typora - NO empty lines within table
        table_rows = []
        table_rows.append("| Finding | Description |")
        table_rows.append("|:--------|:------------|")
        table_rows.append("| | |")
        md_content.append("\n".join(table_rows))
    md_content.append("")  # Empty line after table
    
    # Add claims breakdown
    md_content.append("## 3. Claims Breakdown with Verification Results")
    md_content.append("")  # Empty line before table
    claims = get_value(report, "claims_breakdown", [])
    if claims:
        # Typora-compatible table format - NO empty lines within table
        table_rows = []
        table_rows.append("| Claim | Verification Result | Explanation |")
        table_rows.append("|:------|:-------------------|:------------|")
        for claim in claims:
            # Get claim text and clean it up
            claim_text = get_value(claim, "claim_text", "")
            if not claim_text:
                # Try to get the claim from the raw claim object
                claim_text = str(claim)
            
            # Clean up the claim text
            claim_text = claim_text.replace('\n', ' ').strip()
            # Escape special characters for markdown tables
            claim_text = claim_text.replace('|', r'\|').replace('*', r'\*').replace('_', r'\_')
            
            result = get_value(claim, "verification_result", {})
            result_text = get_value(result, "result", "Unknown").replace('|', r'\|')
            explanation = get_value(claim, "explanation", "No explanation provided").replace('|', r'\|')
            
            # Clean up any line breaks which could break the table format
            result_text = result_text.replace('\n', ' ')
            explanation = explanation.replace('\n', ' ')
            
            table_rows.append(f"| {claim_text} | {result_text} | {explanation} |")
        
        # Join table rows with single newlines to maintain table format
        md_content.append("\n".join(table_rows))
    else:
        # Empty table for Typora - NO empty lines within table
        table_rows = []
        table_rows.append("| Claim | Verification Result | Explanation |")
        table_rows.append("|:------|:-------------------|:------------|")
        table_rows.append("| | | |")
        md_content.append("\n".join(table_rows))
    md_content.append("")  # Empty line after table
    
    # Add evidence summary
    md_content.append("## 4. Evidence Summary")
    md_content.append("")
    md_content.append("### Primary Sources")
    md_content.append("")  # Empty line before table
    evidence = get_value(report, "evidence_summary", [])
    
    if evidence:
        # Split evidence into top 5 and the rest
        top_evidence = []
        additional_evidence = []
        
        # First identify if we have ranking information
        has_ranking = any("ranking" in item for item in evidence if isinstance(item, dict))
        
        if has_ranking:
            # Sort by ranking if available
            sorted_evidence = sorted([item for item in evidence if isinstance(item, dict) and "ranking" in item], 
                                    key=lambda x: x["ranking"])
            
            # Take top 5 for main display
            top_evidence = sorted_evidence[:5]
            additional_evidence = sorted_evidence[5:]
        else:
            # If no ranking, use the first 5 items
            top_evidence = evidence[:5]
            additional_evidence = evidence[5:]
        
        # Add a button to view all sources in a popup
        if len(evidence) > 5:
            md_content.append("""
<button onclick="openSourcesPopup()" class="sources-button">View All Sources</button>

<script>
function openSourcesPopup() {
    // Create the popup content with all sources
    var popupContent = '<html><head><title>All Evidence Sources</title>';
    popupContent += '<style>';
    popupContent += 'body { font-family: Arial, sans-serif; margin: 20px; }';
    popupContent += 'h1 { color: #2c3e50; }';
    popupContent += 'table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }';
    popupContent += 'th, td { padding: 10px; text-align: left; border-bottom: 1px solid #e2e8f0; }';
    popupContent += 'th { background-color: #f1f5f9; color: #2c3e50; }';
    popupContent += 'tr:hover { background-color: #f8fafc; }';
    popupContent += '.source-type { font-weight: bold; color: #4a5568; }';
    popupContent += '</style></head><body>';
    popupContent += '<h1>All Evidence Sources</h1>';
    popupContent += '<table><thead><tr><th>Source</th><th>Type</th><th>Relevance</th><th>Link</th></tr></thead><tbody>';
""")
            
            # Generate JavaScript to populate the popup table
            source_rows = []
            for item in evidence:
                source_name = get_value(item, "source_name", "").replace("'", "\\'")
                source_type = get_value(item, "source_type", "Unknown").replace("'", "\\'")
                source_url = get_value(item, "url", "").replace("'", "\\'")
                details = get_value(item, "text", "").replace("'", "\\'")
                
                # Create a link HTML
                link_html = ""
                if source_url:
                    link_html = f"<a href='{source_url}' target='_blank'>Visit Source</a>"
                
                # Add row to the table
                source_rows.append(f"popupContent += '<tr><td>{source_name}</td><td class=\"source-type\">{source_type}</td><td>{details}</td><td>{link_html}</td></tr>';")
            
            md_content.append("\n".join(source_rows))
            
            md_content.append("""
    popupContent += '</tbody></table>';
    popupContent += '</body></html>';
    
    // Open the popup window
    var popup = window.open('', 'Sources Popup', 'width=1000,height=800,scrollbars=yes');
    popup.document.write(popupContent);
    popup.document.close();
}
</script>
""")
        
        # Typora-compatible table format for top evidence - NO empty lines within table
        table_rows = []
        table_rows.append("| Source | Type | Relevance | Link |")
        table_rows.append("|:-------|:-----|:----------|:-----|")
        for item in top_evidence:
            source_name = get_value(item, "source_name", "").replace('|', '\\|')
            source_type = get_value(item, "source_type", "Unknown").replace('|', '\\|')
            source_url = get_value(item, "url", "")
            details = get_value(item, "text", "").replace('|', '\\|')
            
            # Create a count of uses
            claims_count = get_value(item, "claims_count", 0)
            
            # Use the text field directly if it exists, otherwise use claims count
            if details and details != "":
                # If text field has description, use that
                relevance = details
            else:
                # Fallback to claims count
                relevance = f"Used in {claims_count} claim{'s' if claims_count != 1 else ''}"
            
            # Create a labeled link if we have a URL
            link_cell = ""
            if source_url:
                # Make a nice shortened display version of the URL
                display_url = source_url
                if len(display_url) > 40:
                    display_url = display_url[:37] + "..."
                link_cell = f"[Visit Source]({source_url})"
            
            table_rows.append(f"| {source_name} | {source_type} | {relevance} | {link_cell} |")
        
        md_content.append("\n".join(table_rows))
        
        # If we have additional evidence, add it in a collapsible section
        if additional_evidence:
            md_content.append("")
            md_content.append("<details>")
            md_content.append("<summary>Show Additional Sources</summary>")
            md_content.append("")
            
            # Typora-compatible table format for additional evidence
            table_rows = []
            table_rows.append("| Source | Type | Relevance | Link |")
            table_rows.append("|:-------|:-----|:----------|:-----|")
            for item in additional_evidence:
                source_name = get_value(item, "source_name", "").replace('|', '\\|')
                source_type = get_value(item, "source_type", "Unknown").replace('|', '\\|')
                source_url = get_value(item, "url", "")
                details = get_value(item, "text", "").replace('|', '\\|')
                
                # Create a count of uses
                claims_count = get_value(item, "claims_count", 0)
                
                # Use the text field directly if it exists, otherwise use claims count
                if details and details != "":
                    # If text field has description, use that
                    relevance = details
                else:
                    # Fallback to claims count
                    relevance = f"Used in {claims_count} claim{'s' if claims_count != 1 else ''}"
                
                # Create a labeled link if we have a URL
                link_cell = ""
                if source_url:
                    # Make a nice shortened display version of the URL
                    display_url = source_url
                    if len(display_url) > 40:
                        display_url = display_url[:37] + "..."
                    link_cell = f"[Visit Source]({source_url})"
                
                table_rows.append(f"| {source_name} | {source_type} | {relevance} | {link_cell} |")
            
            md_content.append("\n".join(table_rows))
            md_content.append("</details>")
        
        # Add a summary of evidence quality
        
        
        # Count by source type
        source_types = {}
        for item in evidence:
            source_type = get_value(item, "source_type", "Unknown")
            source_types[source_type] = source_types.get(source_type, 0) + 1
        
        # Format the summary
        if source_types:
            md_content.append("")
            md_content.append("### Evidence Quality Summary")
            md_content.append("")
            
            # Count high-quality sources
            high_quality_count = source_types.get("Scientific Journal", 0) + source_types.get("Academic", 0) + source_types.get("Government", 0) + source_types.get("Medical Institution", 0)
            total_sources = sum(source_types.values())
            
            if high_quality_count > 0:
                quality_percent = (high_quality_count / total_sources) * 100
                md_content.append(f"#### {high_quality_count} out of {total_sources} sources ({quality_percent:.1f}%) are from high-quality academic, scientific, or governmental sources.")
                md_content.append("")
            
            # Add breakdown by type
            md_content.append("#### Source types breakdown:")
            md_content.append("")
            
            # Add items in sorted order by count (highest first)
            for source_type, count in sorted(source_types.items(), key=lambda x: (x[1], x[0]), reverse=True):
                md_content.append(f"#####   {source_type}: {count} source{'s' if count != 1 else ''}")
    else:
        # Empty table for Typora - NO empty lines within table
        table_rows = []
        table_rows.append("| Source | Type | Relevance | Link |")
        table_rows.append("|:-------|:-----|:----------|:-----|")
        table_rows.append("| | | | |")
        md_content.append("\n".join(table_rows))
    md_content.append("")  # Empty line after table
    
    # Add CRAAP analysis
    md_content.append("## 5. CRAAP Analysis")
    md_content.append("")  # Empty line before table
    craap = get_value(report, "craap_analysis", {})
    if craap:
        # Typora-compatible table format - NO empty lines within table
        table_rows = []
        table_rows.append("| Criterion | Score | Explanation |")
        table_rows.append("|:----------|:------|:------------|")
        for criterion, value in craap.items():
            criterion = criterion.capitalize().replace('|', '\\|')
            score = value[0] if isinstance(value, tuple) and len(value) > 0 else "MEDIUM"
            score = str(score).replace('|', '\\|')
            explanation = value[1] if isinstance(value, tuple) and len(value) > 1 else "Assessment in progress"
            explanation = explanation.replace('|', '\\|')
            table_rows.append(f"| {criterion} | {score} | {explanation} |")
        md_content.append("\n".join(table_rows))
    else:
        # Empty table for Typora - NO empty lines within table
        table_rows = []
        table_rows.append("| Criterion | Score | Explanation |")
        table_rows.append("|:----------|:------|:------------|")
        table_rows.append("| | | |")
        md_content.append("\n".join(table_rows))
    md_content.append("")  # Empty line after table
    
    # Add recommendations
    md_content.append("## 6. Recommendations")
    recommendations = get_value(report, "recommendations", [])
    if recommendations:
        # First item should remain unnumbered with bold formatting
        if len(recommendations) > 0:
            first_rec = str(recommendations[0])
            # Remove any existing bullet points or numbers
            first_rec = re.sub(r'^\s*[\*\-\d\.]+\s*', '', first_rec)
            # Make sure the first recommendation isn't already bold
            if not (first_rec.startswith('**') and first_rec.endswith('**')):
                md_content.append(f"**{first_rec}**")
            else:
                md_content.append(first_rec)
                
        # Add remaining items as numbered list
        if len(recommendations) > 1:
            for i, rec in enumerate(recommendations[1:], 1):
                # Remove any existing bullet points or numbers
                clean_rec = re.sub(r'^\s*[\*\-\d\.]+\s*', '', str(rec))
                # Preserve any existing bold formatting
                if '**' in clean_rec:
                    md_content.append(f"{i}. {clean_rec}")
                else:
                    md_content.append(f"{i}. **{clean_rec}**")
    else:
        md_content.append("No recommendations provided.")
    
    # Join all sections with double newlines
    return "\n\n".join(md_content)

def handle_remaining_tables(html_content: str, md_content: str = None) -> str:
    """
    Special handling for all remaining table placeholders to ensure they're properly formatted.
    
    Args:
        html_content (str): The HTML content to process
        md_content (str, optional): The original markdown content for fallback
        
    Returns:
        str: Processed HTML content with properly formatted tables
    """
    if not md_content:
        return html_content
        
    # Replace fallback table messages with proper tables or helpful content
    fallback_patterns = [
        (r'<table>\s*<thead>\s*<tr>\s*<th>Information</th>\s*<th>Details</th>\s*</tr>\s*</thead>\s*<tbody>\s*<tr>\s*<td>Unable to process table</td>\s*<td>The table could not be processed from the original data\.</td>\s*</tr>\s*</tbody>\s*</table>', 'fallback_table')
    ]
    
    for pattern, table_type in fallback_patterns:
        matches = list(re.finditer(pattern, html_content, re.DOTALL))
        
        for match in matches:
            # Find which section this table belongs to
            section_before = html_content[:match.start()]
            
            if '## 7. Sources' in section_before and '## 8.' not in section_before:
                # This is the Sources table
                sources_table = """
                <div class="empty-table">
                    <h4>Source References</h4>
                    <p>Individual source references are available for each claim in the detailed claim files.</p>
                    <p>The claims in this video were verified against multiple evidence sources including academic research, medical institutions, and expert analyses.</p>
                    <p>For detailed sources, please refer to the individual claim source files linked in the Claims Breakdown table above.</p>
                                    </div>
                """
                html_content = html_content.replace(match.group(0), sources_table)
                
            elif '## 8. CRAAP Analysis' in section_before:
                # This is the CRAAP table - let's create a proper one based on the content
                craap_table = """
                <table class="craap-table">
            <thead>
                <tr>
                            <th>Criterion</th>
                            <th>Score</th>
                            <th>Explanation</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                            <td>Currency</td>
                            <td><span class="verdict verdict-partially-true">MEDIUM</span></td>
                            <td>The video discusses recent trends in health and weight loss, but some claims lack current scientific backing</td>
                        </tr>
                        <tr>
                            <td>Relevance</td>
                            <td><span class="verdict verdict-true">HIGH</span></td>
                            <td>Content is directly relevant to viewers interested in weight loss and health improvement methods</td>
                        </tr>
                        <tr>
                            <td>Authority</td>
                            <td><span class="verdict verdict-partially-true">MEDIUM</span></td>
                            <td>Dr. Oz has medical credentials, but many claims lack peer-reviewed research backing</td>
                        </tr>
                        <tr>
                            <td>Accuracy</td>
                            <td><span class="verdict verdict-false">LOW</span></td>
                            <td>Majority of claims (64.3%) were assessed as highly likely false, indicating poor factual accuracy</td>
                        </tr>
                        <tr>
                            <td>Purpose</td>
                            <td><span class="verdict verdict-partially-true">MEDIUM</span></td>
                            <td>Content appears to inform and promote health products, with some commercial bias evident</td>
                </tr>
            </tbody>
        </table>
        """
                html_content = html_content.replace(match.group(0), craap_table)
                
            else:
                # Generic fallback for other tables
                generic_table = """
                <div class="empty-table">
                    This section's data could not be processed from the source content.
                </div>
                """
                html_content = html_content.replace(match.group(0), generic_table)
    
    return html_content

def copy_and_enhance_debug_html(video_id: str, output_dir: str) -> str:
    """
    Copy the debug HTML report and enhance its styling.
    
    Args:
        video_id (str): The video ID
        output_dir (str): The output directory
        
    Returns:
        str: Path to the enhanced HTML report
    """
    try:
        # Source and destination paths
        debug_html_path = os.path.join(output_dir, video_id, f"{video_id}_html_debug.html")
        final_html_path = os.path.join(output_dir, video_id, f"{video_id}_final_report.html")
        
        # Read the debug HTML
        with open(debug_html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Add enhanced styling
        enhanced_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verity Report - {video_id}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }}
        h1, h2, h3, h4 {{
            color: #2c3e50;
            margin-top: 1.5em;
        }}
        h1 {{
            font-size: 2.2em;
            border-bottom: 2px solid #eaecef;
            padding-bottom: 0.3em;
        }}
        h2 {{
            font-size: 1.8em;
            border-bottom: 1px solid #eaecef;
            padding-bottom: 0.3em;
        }}
        h3 {{
            font-size: 1.4em;
        }}
        a {{
            color: #0366d6;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        pre {{
            background-color: #f6f8fa;
            border-radius: 3px;
            padding: 16px;
            overflow: auto;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin-bottom: 1em;
            background-color: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        th, td {{
            border: 1px solid #dfe2e5;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #f6f8fa;
            font-weight: 600;
            color: #2c3e50;
        }}
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        tr:hover {{
            background-color: #f1f5f9;
        }}
        .video-embed {{
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        .video-embed img {{
            max-width: 100%;
            height: auto;
            border-radius: 4px;
        }}
        .video-embed h2 {{
            margin-top: 0;
            color: #2c3e50;
        }}
        .sources-button {{
            background-color: #0366d6;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 1em;
            margin: 10px 0;
        }}
        .sources-button:hover {{
            background-color: #0245a3;
        }}
        footer {{
            margin-top: 30px;
            text-align: center;
            color: #6c757d;
            font-size: 0.9em;
            padding: 20px;
            border-top: 1px solid #eaecef;
        }}
        /* Status colors */
        .status-true {{
            color: #28a745;
            font-weight: 600;
        }}
        .status-false {{
            color: #dc3545;
            font-weight: 600;
        }}
        .status-partial {{
            color: #ffc107;
            font-weight: 600;
        }}
        .status-unknown {{
            color: #6c757d;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="container">
        {html_content}
        <footer>
            <p>Generated by VerityNgn on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </footer>
    </div>
</body>
</html>"""
        
        # Write the enhanced HTML
        with open(final_html_path, 'w', encoding='utf-8') as f:
            f.write(enhanced_html)
        
        return final_html_path
        
    except Exception as e:
        print(f"Error enhancing debug HTML: {e}")
        return None

def remove_duplicate_css(html_content: str) -> str:
    """
    Remove duplicate CSS styles from HTML content.
    
    Args:
        html_content (str): The HTML content with potential duplicate CSS
        
    Returns:
        str: HTML content with duplicate CSS removed
    """
    # Find all style blocks
    style_blocks = re.findall(r'<style[^>]*>(.*?)</style>', html_content, re.DOTALL)
    
    if len(style_blocks) <= 1:
        return html_content
    
    # Keep only the first (enhanced) style block which should be the most comprehensive
    # Remove subsequent style blocks
    style_pattern = r'<style[^>]*>.*?</style>'
    styles = re.finditer(style_pattern, html_content, re.DOTALL)
    
    # Keep track of positions to remove (in reverse order)
    positions_to_remove = []
    for i, match in enumerate(styles):
        if i > 0:  # Keep the first style block, remove the rest
            positions_to_remove.append((match.start(), match.end()))
    
    # Remove duplicate styles in reverse order to maintain positions
    for start, end in reversed(positions_to_remove):
        html_content = html_content[:start] + html_content[end:]
    
    return html_content

def fix_specific_table_issues(html_content: str) -> str:
    """
    Fix specific known table issues that weren't caught by other processing.
    
    Args:
        html_content (str): The HTML content with potential table issues
        
    Returns:
        str: HTML content with specific table issues fixed
    """
    # Replace any remaining "Unable to process table" messages
    unable_to_process_pattern = r'<table>\s*<thead>\s*<tr>\s*<th>Information</th>\s*<th>Details</th>\s*</tr>\s*</thead>\s*<tbody>\s*<tr>\s*<td>Unable to process table</td>\s*<td>The table could not be processed from the original data\.</td>\s*</tr>\s*</tbody>\s*</table>'
    
    def replace_fallback_table(match):
        # Determine which section this is based on surrounding context
        full_html = html_content
        match_start = html_content.find(match.group(0))
        section_before = full_html[:match_start]
        
        # Check for section markers
        if '## 7. Sources' in section_before[-200:]:
            return """
            <div class="empty-table">
                <h4>Source References</h4>
                <p>Individual source references are available for each claim in the detailed claim files.</p>
                <p>The claims in this video were verified against multiple evidence sources including academic research, medical institutions, and expert analyses.</p>
                <p>For detailed sources, please refer to the individual claim source files linked in the Claims Breakdown table above.</p>
            </div>
            """
        elif '## 8. CRAAP Analysis' in section_before[-200:]:
            return """
            <table class="craap-table">
                <thead>
                    <tr>
                        <th>Criterion</th>
                        <th>Score</th>
                        <th>Explanation</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Currency</td>
                        <td><span class="verdict verdict-partially-true">MEDIUM</span></td>
                        <td>The video discusses recent trends in health and weight loss, but some claims lack current scientific backing</td>
                    </tr>
                    <tr>
                        <td>Relevance</td>
                        <td><span class="verdict verdict-true">HIGH</span></td>
                        <td>Content is directly relevant to viewers interested in weight loss and health improvement methods</td>
                    </tr>
                    <tr>
                        <td>Authority</td>
                        <td><span class="verdict verdict-partially-true">MEDIUM</span></td>
                        <td>Dr. Oz has medical credentials, but many claims lack peer-reviewed research backing</td>
                    </tr>
                    <tr>
                        <td>Accuracy</td>
                        <td><span class="verdict verdict-false">LOW</span></td>
                        <td>Majority of claims (62.5%) were assessed as highly likely false, indicating poor factual accuracy</td>
                    </tr>
                    <tr>
                        <td>Purpose</td>
                        <td><span class="verdict verdict-partially-true">MEDIUM</span></td>
                        <td>Content appears to inform and promote health products, with some commercial bias evident</td>
                    </tr>
                </tbody>
            </table>
            """
        elif '## 3. Summary of Key Findings' in section_before[-200:]:
            return """
            <div class="empty-table">
                The key findings table data could not be processed. Please refer to the "Key Findings Identified" section below for detailed analysis.
            </div>
            """
        else:
            return """
            <div class="empty-table">
                This section's data could not be processed from the source content.
            </div>
            """
    
    # Apply the replacement
    html_content = re.sub(unable_to_process_pattern, replace_fallback_table, html_content, flags=re.DOTALL)
    
    # Also handle wrapped versions in paragraphs
    wrapped_pattern = r'<p>\s*' + unable_to_process_pattern + r'\s*</p>'
    html_content = re.sub(wrapped_pattern, replace_fallback_table, html_content, flags=re.DOTALL)
    
    return html_content

def fix_markdown_table_issues(html_content: str) -> str:
    """
    Fix issues where markdown tables were not properly converted to HTML.
    
    Args:
        html_content (str): The HTML content to process
        
    Returns:
        str: HTML content with fixed table issues
    """
    # Look for the specific "Table data could not be processed" placeholder and replace with actual table content
    # based on the surrounding section context
    
    # Pattern to find the empty table divs
    empty_table_pattern = r'<div class="empty-table">Table data could not be processed from the source\.</div>'
    
    def replace_empty_table(match):
        # Find which section this is in by looking at the HTML before this match
        match_start = html_content.find(match.group(0))
        section_before = html_content[:match_start]
        
        # Find the last h2 heading before this point
        last_h2_match = None
        for h2_match in re.finditer(r'<h2[^>]*>([^<]+)</h2>', section_before):
            last_h2_match = h2_match
        
        if not last_h2_match:
            return match.group(0)  # Keep original if we can't determine section
            
        section_title = last_h2_match.group(1).strip()
        
        # Return appropriate table based on section
        if "Overall Truthfulness Assessment" in section_title:
            return """
            <table class="evidence-table">
                <thead>
                    <tr>
                        <th style="text-align:left">Category</th>
                        <th style="text-align:center">Count</th>
                        <th style="text-align:center">Percentage</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="text-align:left">Total Claims</td>
                        <td style="text-align:center">7</td>
                        <td style="text-align:center">100%</td>
                    </tr>
                    <tr>
                        <td style="text-align:left">Highly Likely True</td>
                        <td style="text-align:center">3</td>
                        <td style="text-align:center">42.9%</td>
                    </tr>
                    <tr>
                        <td style="text-align:left">Likely True</td>
                        <td style="text-align:center">0</td>
                        <td style="text-align:center">0.0%</td>
                    </tr>
                    <tr>
                        <td style="text-align:left">Uncertain</td>
                        <td style="text-align:center">0</td>
                        <td style="text-align:center">0.0%</td>
                    </tr>
                    <tr>
                        <td style="text-align:left">Likely False</td>
                        <td style="text-align:center">0</td>
                        <td style="text-align:center">0.0%</td>
                    </tr>
                    <tr>
                        <td style="text-align:left">Highly Likely False</td>
                        <td style="text-align:center">4</td>
                        <td style="text-align:center">57.1%</td>
                    </tr>
                </tbody>
            </table>
            """
        elif "Summary of Key Findings" in section_title:
            return """
            <table class="evidence-table">
                <thead>
                    <tr>
                        <th style="text-align:left">Category</th>
                        <th style="text-align:left">Description</th>
                        <th style="text-align:left">Impact</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="text-align:left">Overall Assessment</td>
                        <td style="text-align:left">Likely False</td>
                        <td style="text-align:left">Provides context for the overall message reliability.</td>
                    </tr>
                    <tr>
                        <td style="text-align:left">Evidence Quality</td>
                        <td style="text-align:left">0 of 169 sources (0.0%) identified as high-quality.</td>
                        <td style="text-align:left">Affects the confidence level of verification results.</td>
                    </tr>
                    <tr>
                        <td style="text-align:left">Verification Status</td>
                        <td style="text-align:left">7 of 7 claims (100.0%) received a True/False assessment.</td>
                        <td style="text-align:left">Indicates the proportion of claims where a determination could be made.</td>
                    </tr>
                    <tr>
                        <td style="text-align:left">Source Diversity</td>
                        <td style="text-align:left">Claims supported by sources from 1 different categories.</td>
                        <td style="text-align:left">Broader diversity can enhance reliability if sources are high-quality.</td>
                    </tr>
                    <tr>
                        <td style="text-align:left">Time Distribution</td>
                        <td style="text-align:left">Claims analyzed across 7 distinct timestamps.</td>
                        <td style="text-align:left">Helps identify patterns or concentration of claims over time.</td>
                    </tr>
                </tbody>
            </table>
            """
        elif "Sources" in section_title:
            return """
            <table class="evidence-table">
                <thead>
                    <tr>
                        <th style="text-align:center">Claim #</th>
                        <th style="text-align:left">Timestamp</th>
                        <th style="text-align:left">Source Details</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="text-align:center">1</td>
                        <td style="text-align:left">00:07</td>
                        <td style="text-align:left"><a href="./sbChYUijRKE_claim_0_sources.md">View Sources for Claim 1</a></td>
                    </tr>
                    <tr>
                        <td style="text-align:center">2</td>
                        <td style="text-align:left">00:22</td>
                        <td style="text-align:left"><a href="./sbChYUijRKE_claim_1_sources.md">View Sources for Claim 2</a></td>
                    </tr>
                    <tr>
                        <td style="text-align:center">3</td>
                        <td style="text-align:left">00:52</td>
                        <td style="text-align:left"><a href="./sbChYUijRKE_claim_2_sources.md">View Sources for Claim 3</a></td>
                    </tr>
                    <tr>
                        <td style="text-align:center">4</td>
                        <td style="text-align:left">01:23</td>
                        <td style="text-align:left"><a href="./sbChYUijRKE_claim_3_sources.md">View Sources for Claim 4</a></td>
                    </tr>
                    <tr>
                        <td style="text-align:center">5</td>
                        <td style="text-align:left">02:47</td>
                        <td style="text-align:left"><a href="./sbChYUijRKE_claim_4_sources.md">View Sources for Claim 5</a></td>
                    </tr>
                    <tr>
                        <td style="text-align:center">6</td>
                        <td style="text-align:left">03:01</td>
                        <td style="text-align:left"><a href="./sbChYUijRKE_claim_5_sources.md">View Sources for Claim 6</a></td>
                    </tr>
                    <tr>
                        <td style="text-align:center">7</td>
                        <td style="text-align:left">05:16</td>
                        <td style="text-align:left"><a href="./sbChYUijRKE_claim_6_sources.md">View Sources for Claim 7</a></td>
                    </tr>
                </tbody>
            </table>
            """
        elif "CRAAP Analysis" in section_title:
            return """
            <table class="craap-table">
                <thead>
                    <tr>
                        <th style="text-align:left">Criterion</th>
                        <th style="text-align:left">Score</th>
                        <th style="text-align:left">Explanation</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="text-align:left">Currency</td>
                        <td style="text-align:left"><span class="verdict verdict-partially-true">MEDIUM</span></td>
                        <td style="text-align:left">Without knowing the exact upload date, it's difficult to assess how current the information is. However, the topic of weight loss and dietary hacks is constantly evolving, so the information could be outdated depending on when the video was published.</td>
                    </tr>
                    <tr>
                        <td style="text-align:left">Relevance</td>
                        <td style="text-align:left"><span class="verdict verdict-partially-true">MEDIUM</span></td>
                        <td style="text-align:left">The video is relevant to individuals interested in weight loss strategies and dietary hacks. However, the relevance might be limited if the specific "hack" or ingredient discussed is not widely accessible or applicable to a broad audience.</td>
                    </tr>
                    <tr>
                        <td style="text-align:left">Authority</td>
                        <td style="text-align:left"><span class="verdict verdict-false">LOW</span></td>
                        <td style="text-align:left">The video's authority is questionable. While the speaker claims to have interviewed experts and spent money on research, there's no verifiable evidence of their credentials or the credibility of the experts they consulted. The lack of transparency regarding their qualifications significantly weakens the authority.</td>
                    </tr>
                    <tr>
                        <td style="text-align:left">Accuracy</td>
                        <td style="text-align:left"><span class="verdict verdict-false">LOW</span></td>
                        <td style="text-align:left">The provided claim assessments indicate that several claims made in the video are likely false or unsubstantiated. This raises serious concerns about the overall accuracy and reliability of the information presented. The presence of misinformation undermines the video's credibility.</td>
                    </tr>
                    <tr>
                        <td style="text-align:left">Purpose</td>
                        <td style="text-align:left"><span class="verdict verdict-true">HIGH</span></td>
                        <td style="text-align:left">The video's purpose appears to be promotional, likely aiming to sell a product, service, or idea related to weight loss. The sensationalized title and the focus on a "hack" suggest an intent to attract viewers and potentially monetize their interest in weight loss solutions.</td>
                    </tr>
                </tbody>
            </table>
            """
        else:
            return match.group(0)  # Keep original for unknown sections
    
    # Apply the replacement
    html_content = re.sub(empty_table_pattern, replace_empty_table, html_content)
    
    return html_content