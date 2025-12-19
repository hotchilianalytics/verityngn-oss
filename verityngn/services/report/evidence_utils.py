import os
import sys
import json
from typing import List, Dict, Any, Tuple
import logging

# Import from our new YouTube search module
from verityngn.services.search.youtube_search import (
    search_youtube_counter_intelligence,
    analyze_youtube_evidence_content,
    youtube_search_service
)

# Remove the old MediaTruthNgn import since we've moved the functionality
# sys.path.append('/Users/ajjc/proj/MediaTruthNgn/utils')

from verityngn.models.report import EvidenceSource, CredibilityLevel

def enhance_source_credibility(sources: List[EvidenceSource]) -> List[EvidenceSource]:
    """Enhance evidence sources with improved metadata and source credibility."""
    enhanced_sources = []
    
    # If evidence_list is empty, return at least some default sources
    if not sources:
        # Return empty list - the _ensure_web_sources method in VerityReport will add default sources
        return []
    
    for source in sources:
        # Handle string URLs (common format from claim verification)
        if isinstance(source, str):
            source_url = source
            source_name = "Referenced Source"
            source_type = "Web"
            title = "External Reference"
            text = "Supporting evidence for video claims"
            credibility = CredibilityLevel.MEDIUM
            
            # Enhance source type detection
            if 'nih.gov' in source_url or 'ncbi.nlm.nih.gov' in source_url or 'pubmed' in source_url:
                source_type = "Scientific Journal"
                source_name = "PubMed/NCBI"
                title = "Scientific Research"
                credibility = CredibilityLevel.HIGH
                text = "Scientific research related to claims in the video"
            elif 'wikipedia.org' in source_url:
                source_type = "Encyclopedia"
                source_name = "Wikipedia" 
                title = "Encyclopedia Article"
                credibility = CredibilityLevel.MEDIUM
                text = "Background information on topics mentioned in the video"
            elif 'mayoclinic.org' in source_url:
                source_type = "Medical Institution"
                source_name = "Mayo Clinic"
                title = "Mayo Clinic Health Information"
                credibility = CredibilityLevel.HIGH
                text = "Authoritative medical information related to health claims"
            elif 'clevelandclinic.org' in source_url:
                source_type = "Medical Institution"
                source_name = "Cleveland Clinic"
                title = "Cleveland Clinic Health Information"
                credibility = CredibilityLevel.HIGH
                text = "Authoritative medical information related to health claims"
            elif 'fda.gov' in source_url:
                source_type = "Government"
                source_name = "FDA"
                title = "FDA Information"
                credibility = CredibilityLevel.HIGH
                text = "Official government information on regulated substances and health claims"
            elif '.gov' in source_url:
                source_type = "Government"
                source_name = "Government Source"
                title = "Government Information"
                credibility = CredibilityLevel.HIGH
                text = "Official government information related to claims in the video"
            elif 'webmd.com' in source_url:
                source_type = "Health Information"
                source_name = "WebMD"
                title = "WebMD Health Information"
                credibility = CredibilityLevel.MEDIUM
                text = "Health information related to claims in the video"
            elif 'healthline.com' in source_url:
                source_type = "Health Information"
                source_name = "Healthline"
                title = "Healthline Health Information"
                credibility = CredibilityLevel.MEDIUM
                text = "Health information related to claims in the video"
            elif 'youtube.com' in source_url or 'youtu.be' in source_url:
                source_type = "Video"
                source_name = "YouTube Video"
                title = "Referenced Video Content"
                credibility = CredibilityLevel.LOW
                text = "Video content related to claims being verified"
            elif '.edu' in source_url:
                source_type = "Academic"
                source_name = "Academic Source"
                title = "Academic Research"
                credibility = CredibilityLevel.HIGH
                text = "Academic research related to claims in the video"
            elif 'amazon.com' in source_url or 'walmart.com' in source_url:
                source_type = "Commercial"
                source_name = "Commercial Source"
                title = "Commercial Product Information"
                credibility = CredibilityLevel.LOW
                text = "Commercial information related to products mentioned in the video"
            # FIX: Check for government sources BEFORE press release detection
            # Government sites should NEVER be classified as press releases
            elif '.gov' in source_url or any(gov_domain in source_url for gov_domain in [
                'fdic.gov', 'sec.gov', 'nih.gov', 'cdc.gov', 'fda.gov', 'epa.gov', 
                'justice.gov', 'treasury.gov', 'state.gov', 'defense.gov', 'dol.gov',
                'ed.gov', 'hhs.gov', 'dhs.gov', 'energy.gov', 'usda.gov', 'doi.gov',
                'dot.gov', 'commerce.gov', 'hud.gov', 'va.gov', 'opm.gov', 'gsa.gov',
                'sba.gov', 'ssa.gov', 'federalreserve.gov', 'ftc.gov', 'fcc.gov',
                'cms.gov', 'leg.state', 'nj.gov', 'ca.gov', 'ny.gov', 'tx.gov'
            ]):
                source_type = "Government"
                source_name = "Government Source"
                title = "Government Publication"
                credibility = CredibilityLevel.HIGH
                text = "Official government document or publication"
            elif any(domain in source_url for domain in [
                'prnewswire.com', 'businesswire.com', 'globenewswire.com', 'prweb.com', 'marketwatch.com', 'newswire.com', 'einnews.com', 'pressrelease.com', 'prlog.org', 'openpr.com', 'pressat.co.uk', 'pressreleases.com', 'pr.com', 'pr-inside.com', 'prurgent.com', 'prfire.co.uk', 'prbuzz.com', 'prnews.biz', 'pressbox.co.uk', 'pressreleasepoint.com', '24-7pressrelease.com', 'abnewswire.com', 'webwire.com', 'sbwire.com', 'releasewire.com', 'prsync.com', 'przoom.com', 'prfree.org', 'prdistribution.com', 'prwire.com.au', 'prwire.co', 'prwirepro.com', 'prwirecenter.com', 'prwireindia.com', 'prwireasia.com', 'prwire360.com', 'prwire.co.nz', 'prwire.com.br', 'prwire.com.mx', 'prwire.com.tr', 'prwire.com.ua', 'prwire.com.vn', 'prwire.com.sg', 'prwire.com.ph', 'prwire.com.my', 'prwire.com.hk', 'prwire.com.cn', 'prwire.com.tw', 'prwire.com.jp', 'prwire.com.kr', 'prwire.com.id', 'prwire.com.th', 'prwire.com.sa', 'prwire.com.eg', 'prwire.com.ng', 'prwire.com.gh', 'prwire.com.ke', 'prwire.com.za', 'prwire.com.au', 'prwire.com.nz', 'prwire.com.sg', 'prwire.com.hk', 'prwire.com.cn', 'prwire.com.tw', 'prwire.com.jp', 'prwire.com.kr', 'prwire.com.id', 'prwire.com.th', 'prwire.com.sa', 'prwire.com.eg', 'prwire.com.ng', 'prwire.com.gh', 'prwire.com.ke', 'prwire.com.za']):
                source_type = "Press Release"
                source_name = "Press Release"
                title = "Press Release"
                credibility = CredibilityLevel.LOW
                text = "Press release or promotional content; informational but not certified."
            else:
                # Extract domain name for unlisted sources
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(source_url).netloc
                    # Clean up domain name
                    if domain.startswith('www.'):
                        domain = domain[4:]
                    source_name = domain.split('.')[0].capitalize()
                    title = f"{source_name} Reference"
                except:
                    source_name = "Web Reference"
                    title = "External Source"
            
            # Create enhanced source from string URL
            enhanced_source = EvidenceSource(
                source_name=source_name,
                source_type=source_type,
                title=title,
                url=source_url,
                text=text
            )
            enhanced_sources.append(enhanced_source)
            continue
            
        if not source or not isinstance(source, dict):
            continue
            
        # Check if we're dealing with the new format or old format
        if 'url' in source:
            # New format with structured data
            source_url = source.get('url', '')
            source_name = source.get('source_name', 'Unknown Source')
            source_type = source.get('source_type', 'Web')
            title = source.get('title', 'Unknown Title')
            text = source.get('text', '')
            
            # Determine credibility based on source type
            credibility = CredibilityLevel.MEDIUM
            if source_type in ["Scientific Journal", "Medical Institution", "Government", "Academic"]:
                credibility = CredibilityLevel.HIGH
            elif source_type in ["Video", "Social Media", "Commercial"]:
                credibility = CredibilityLevel.LOW
                
        else:
            # Old format with just URL
            source_url = source.get('source_url', '')
            source_name = source.get('source_name', 'Unknown Source')
            source_type = "Web"
            title = source.get('title', 'Unknown Title')
            text = source.get('text', '')
            credibility = CredibilityLevel.MEDIUM
            
            # Enhance source type detection
            if 'nih.gov' in source_url or 'ncbi.nlm.nih.gov' in source_url or 'pubmed' in source_url:
                source_type = "Scientific Journal"
                credibility = CredibilityLevel.HIGH
            elif 'wikipedia.org' in source_url:
                source_type = "Encyclopedia"
                credibility = CredibilityLevel.MEDIUM
            elif 'mayoclinic.org' in source_url or 'clevelandclinic.org' in source_url:
                source_type = "Medical Institution"
                credibility = CredibilityLevel.HIGH
            elif 'fda.gov' in source_url or '.gov' in source_url:
                source_type = "Government"
                credibility = CredibilityLevel.HIGH
            elif 'webmd.com' in source_url or 'healthline.com' in source_url:
                source_type = "Health Information"
                credibility = CredibilityLevel.MEDIUM
            elif 'youtube.com' in source_url or 'youtu.be' in source_url:
                source_type = "Video"
                credibility = CredibilityLevel.LOW
            elif '.edu' in source_url:
                source_type = "Academic"
                credibility = CredibilityLevel.HIGH
            elif 'amazon.com' in source_url or 'walmart.com' in source_url:
                source_type = "Commercial"
                credibility = CredibilityLevel.LOW
        
        # Create enhanced source
        enhanced_source = EvidenceSource(
            source_name=source_name,
            source_type=source_type,
            title=title,
            url=source_url,
            text=text
        )
        
        enhanced_sources.append(enhanced_source)
    
    return enhanced_sources 

def generate_youtube_counter_intelligence_file(video_id: str, youtube_counter_sources: List[Dict[str, Any]], output_dir: str) -> Tuple[str, str]:
    """Generate YouTube counter-intelligence reference file similar to claims files."""
    import os
    from pathlib import Path
    from datetime import datetime
    
    # Create markdown content
    content = f"# YouTube Counter-Intelligence Analysis for {video_id}\n\n"
    content += f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    content += f"**Total Counter-Intelligence Videos:** {len(youtube_counter_sources)}\n\n"
    
    if not youtube_counter_sources:
        content += "No YouTube counter-intelligence videos were found for this analysis.\n"
    else:
        content += "## Counter-Intelligence Video Analysis\n\n"
        
        for i, video in enumerate(youtube_counter_sources, 1):
            vid_id = video.get('id') or video.get('video_id') or (video.get('url','').split('v=')[-1] if 'v=' in video.get('url','') else '')
            title = video.get('title', 'Unknown Title')
            url = video.get('url') or (f"https://www.youtube.com/watch?v={vid_id}" if vid_id else '#')
            channel = video.get('uploader') or video.get('channel_title', 'Unknown')

            # Header with thumbnail and link
            thumb = f"https://img.youtube.com/vi/{vid_id}/0.jpg" if vid_id else "https://via.placeholder.com/320x180?text=Video"
            content += f"### {i}. [{title}]({url})\n\n"
            content += f"[![{title}]({thumb})]({url})\n\n"
            content += f"**Channel:** {channel}\n\n"
            
            # Add detailed statistics if available
            if 'detailed_stats' in video:
                stats = video['detailed_stats']
                content += f"**Statistics:**\n"
                content += f"- Views: {stats.get('view_count', 0):,}\n"
                content += f"- Likes: {stats.get('like_count', 0):,}\n"
                content += f"- Comments: {stats.get('comment_count', 0):,}\n"
                content += f"- Duration: {stats.get('duration', 0)} seconds\n"
                content += f"- Upload Date: {stats.get('upload_date', 'Unknown')}\n"
                content += f"- Subscriber Count: {stats.get('subscriber_count', 0):,}\n\n"
            
            # Add counter-intelligence score
            content += f"**Counter-Intelligence Score:** {video.get('counter_intelligence_score', 0):.2f}\n\n"
            
            # Add transcript analysis if available
            if 'transcript_analysis' in video:
                analysis = video['transcript_analysis']
                content += f"**Transcript Analysis:**\n"
                content += f"- Overall Stance: {analysis.get('stance_indicators', {}).get('overall_stance', 'Unknown')}\n"
                content += f"- Counter Signals: {analysis.get('stance_indicators', {}).get('counter_signals', 0)}\n"
                content += f"- Supporting Signals: {analysis.get('stance_indicators', {}).get('supporting_signals', 0)}\n"
                content += f"- Transcript Length: {analysis.get('transcript_length', 0):,} characters\n"
                
                # 🎯 DEMO: Add key critical phrases (enhanced DEMO format)
                key_critical_phrases = analysis.get('key_critical_phrases_found', [])
                key_phrases = analysis.get('key_phrases', [])
                
                if key_critical_phrases:
                    content += f"\n**Key Critical Phrases Found:**\n"
                    for phrase in key_critical_phrases[:5]:  # Limit to top 5
                        content += f"- {phrase}\n"
                elif key_phrases:
                    content += f"\n**Key Critical Phrases Found:**\n"
                    for phrase_data in key_phrases[:5]:  # Fallback to original format
                        content += f"- \"{phrase_data.get('phrase', '')}\": {phrase_data.get('context', '')[:100]}...\n"
                
                # Add credibility signals
                credibility_signals = analysis.get('credibility_signals', [])
                if credibility_signals:
                    content += f"\n**Credibility Signals:** {', '.join(credibility_signals[:10])}\n"
                content += "\n"
            
            # Add description snippet
            description = video.get('description', '')
            if description:
                content += f"**Description:** {description[:200]}...\n\n"
            
            content += "---\n\n"
    
    # Write files
    md_file_path = os.path.join(output_dir, f"{video_id}_youtube_counter_intel.md")
    html_file_path = os.path.join(output_dir, f"{video_id}_youtube_counter_intel.html")
    
    # Write markdown file
    os.makedirs(output_dir, exist_ok=True)
    with open(md_file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Generate HTML version
    try:
        from markdown_it import MarkdownIt
        md_parser = MarkdownIt("gfm-like", {"html": True, "linkify": True, "typographer": True})
        html_body = md_parser.render(content)
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Counter-Intelligence Analysis - {video_id}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }}
        h1, h2, h3 {{
            color: #2c3e50;
            margin-top: 1.5em;
        }}
        h1 {{
            font-size: 2em;
            border-bottom: 2px solid #eaecef;
            padding-bottom: 0.3em;
        }}
        a {{
            color: #0366d6;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        hr {{
            border: none;
            border-top: 1px solid #ddd;
            margin: 2em 0;
        }}
        .back-link {{
            margin-bottom: 20px;
            display: inline-block;
            background-color: #0366d6;
            color: white;
            padding: 8px 16px;
            border-radius: 4px;
            text-decoration: none;
        }}
        .back-link:hover {{
            background-color: #0256cc;
            color: white;
        }}
    </style>
</head>
<body>
    <a href="../../report.html" class="back-link">← Back to Main Report</a>
    {html_body}
</body>
</html>"""
        
        with open(html_file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    except Exception as e:
        # Fallback: create simple HTML
        html_content = f"<html><body><pre>{content}</pre></body></html>"
        with open(html_file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    return md_file_path, html_file_path


def generate_press_release_counter_intelligence_file(video_id: str, press_release_counter_sources: List[Dict[str, Any]], output_dir: str) -> Tuple[str, str]:
    """
    🎯 SHERLOCK ENHANCED: Generate detailed Press Release counter-intelligence analysis file matching DEMO format.

    Args:
        video_id: Main video ID being analyzed
        press_release_counter_sources: List of press release counter-intelligence sources with detailed analysis
        output_dir: Directory to save the files

    Returns:
        Tuple of (markdown_path, html_path)
    """
    import os
    from datetime import datetime

    # 🎯 DEMO: Create content exactly matching DEMO format
    content = f"# 🚀 ENHANCED Press Release Counter-Intelligence Analysis for {video_id}\n\n"
    content += f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    content += f"**Total Press Release Counter-Intelligence:** {len(press_release_counter_sources)}\n\n"
    # Quick stats summary
    if press_release_counter_sources:
        self_refs = sum(1 for pr in press_release_counter_sources if pr.get('self_referential', pr.get('self_referential_score', 0) > 50))
        avg_self_ref = sum(float(pr.get('self_referential_score', 0) or 0) for pr in press_release_counter_sources) / max(1, len(press_release_counter_sources))
        content += "### Summary Statistics\n\n"
        content += f"- Self-Referential Items: {self_refs}/{len(press_release_counter_sources)}\n"
        content += f"- Avg. Self-Referential Score: {avg_self_ref:.1f}%\n\n"
    content += "## Press Release Counter-Intelligence Analysis\n\n"

    if not press_release_counter_sources:
        content += "No press release counter-intelligence sources were found for this analysis.\\n"
    else:
        for i, press_release in enumerate(press_release_counter_sources, 1):
            title = press_release.get('title', 'Unknown Title')
            content += f"### {i}. {title}\n\n"

            source_name = press_release.get('source_name', 'Unknown Source')
            content += f"**Source:** {source_name}\n\n"

            url = press_release.get('url', '#')
            content += f"**URL:** [{source_name}]({url})\n\n"
            if url and 'http' in url:
                content += f"[![{source_name}]({press_release.get('thumbnail_url', 'https://www.google.com/s2/favicons?sz=64&domain_url=' + url)})]({url})\n\n"

            # 🎯 DEMO: Self-referential analysis
            self_referential_score = press_release.get('self_referential_score', 0.0)
            content += f"**Self-Referential Score:** {self_referential_score:.1f}%\n\n"

            validation_power = press_release.get('validation_power', 0.0)
            content += f"**Validation Power:** {validation_power}\n\n"

            # 🎯 DEMO: Analysis section
            analysis = press_release.get('analysis', 'No analysis available.')
            content += f"**Analysis:** {analysis}\n\n"
            if press_release.get('self_referential', False):
                content += "> This appears to be self-referential promotional content and should not be used as independent validation.\n\n"

            # 🎯 DEMO: Publication details
            publish_date = press_release.get('publish_date', 'Unknown')
            if publish_date != 'Unknown':
                content += f"**Publication Date:** {publish_date}\n\n"

            # 🎯 DEMO: Description section
            description = press_release.get('text', press_release.get('description', 'No description available'))
            if len(description) > 200:
                description = description[:200] + "..."
            content += f"**Description:** {description}\n\n"
            content += "---\n\n"

    # Save markdown file
    markdown_path = os.path.join(output_dir, f"{video_id}_press_release_counter_intel.md")
    with open(markdown_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # Generate HTML version (similar approach as YouTube counter-intelligence)
    html_path = os.path.join(output_dir, f"{video_id}_press_release_counter_intel.html")
    
    try:
        from markdown_it import MarkdownIt
        md_parser = MarkdownIt("gfm-like", {"html": True, "linkify": True, "typographer": True})
        html_body = md_parser.render(content)
        
        html_content = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>Press Release Counter-Intelligence Analysis - {video_id}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }}
        h1, h2, h3 {{
            color: #2c3e50;
            margin-top: 1.5em;
        }}
        h1 {{
            font-size: 2em;
            border-bottom: 2px solid #eaecef;
            padding-bottom: 0.3em;
        }}
        a {{
            color: #0366d6;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .back-link {{
            margin-bottom: 20px;
            display: inline-block;
            background-color: #0366d6;
            color: white;
            padding: 8px 16px;
            border-radius: 4px;
            text-decoration: none;
        }}
        .back-link:hover {{
            background-color: #0256cc;
            color: white;
        }}
        .stats {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }}
        hr {{
            border: none;
            border-top: 1px solid #eaecef;
            margin: 2em 0;
        }}
    </style>
</head>
<body>
    <a href=\"../../report.html\" class=\"back-link\">← Back to Main Report</a>
    {html_body}
</body>
</html>"""
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    except Exception as e:
        # Fallback: create simple HTML
        html_content = f"<html><body><pre>{content}</pre></body></html>"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

    return markdown_path, html_path

def generate_press_release_sources_file(video_id: str, press_release_sources: List[Dict[str, Any]], output_dir: str) -> Tuple[str, str]:
    """Generate press release sources reference files in Markdown and HTML formats."""
    if not press_release_sources:
        return None, None
    
    # Generate Markdown content
    md_content = f"# Press Release Sources for {video_id}\n\n"
    md_content += f"Total Press Release Sources Found: {len(press_release_sources)}\n\n"
    md_content += "## Sources List\n\n"
    
    for i, source in enumerate(press_release_sources, 1):
        url = source.get('url', 'N/A')
        title = source.get('title', 'N/A')
        domain = source.get('domain', 'N/A')
        credibility = source.get('credibility_score', 'N/A')
        
        md_content += f"### {i}. {title}\n"
        md_content += f"- **URL:** {url}\n"
        md_content += f"- **Domain:** {domain}\n"
        md_content += f"- **Credibility Score:** {credibility}\n"
        md_content += f"- **Source Type:** Press Release/Newswire\n\n"
    
    # Generate HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Press Release Sources for {video_id}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #d32f2f; }}
            h2 {{ color: #1976d2; }}
            .source {{ margin-bottom: 20px; border-left: 3px solid #ff9800; padding-left: 15px; }}
            .url {{ word-break: break-all; }}
        </style>
    </head>
    <body>
        <h1>Press Release Sources for {video_id}</h1>
        <p><strong>Total Press Release Sources Found:</strong> {len(press_release_sources)}</p>
        <h2>Sources List</h2>
    """
    
    for i, source in enumerate(press_release_sources, 1):
        url = source.get('url', 'N/A')
        title = source.get('title', 'N/A')
        domain = source.get('domain', 'N/A')
        credibility = source.get('credibility_score', 'N/A')
        
        html_content += f"""
        <div class="source">
            <h3>{i}. {title}</h3>
            <p><strong>URL:</strong> <span class="url">{url}</span></p>
            <p><strong>Domain:</strong> {domain}</p>
            <p><strong>Credibility Score:</strong> {credibility}</p>
            <p><strong>Source Type:</strong> Press Release/Newswire</p>
        </div>
        """
    
    html_content += "</body></html>"
    
    # Write files
    md_file = os.path.join(output_dir, f"{video_id}_pr_sources.md")
    html_file = os.path.join(output_dir, f"{video_id}_pr_sources.html")
    
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return md_file, html_file

def generate_youtube_sources_file(video_id: str, youtube_evidence: Dict[str, Any], output_dir: str) -> Tuple[str, str]:
    """Generate YouTube counter-intelligence sources reference files in Markdown and HTML formats."""
    counter_evidence = youtube_evidence.get('counter_evidence', [])
    confirming_evidence = youtube_evidence.get('confirming_evidence', [])
    
    if not counter_evidence and not confirming_evidence:
        return None, None
    
    # Generate Markdown content
    md_content = f"# YouTube Counter-Intelligence Sources for {video_id}\n\n"
    md_content += f"Total YouTube Videos Analyzed: {youtube_evidence.get('total_videos_analyzed', 0)}\n\n"
    
    if counter_evidence:
        md_content += f"## Counter-Evidence Videos ({len(counter_evidence)})\n\n"
        for i, video in enumerate(counter_evidence, 1):
            md_content += f"### {i}. {video['title']}\n"
            md_content += f"- **URL:** {video['url']}\n"
            md_content += f"- **View Count:** {video['view_count']:,}\n"
            md_content += f"- **Stance:** {video['stance']}\n"
            md_content += f"- **Confidence:** {video['confidence']:.2f}\n"
            md_content += f"- **Key Points:**\n"
            for point in video['key_points']:
                md_content += f"  - {point}\n"
            md_content += "\n"
    
    if confirming_evidence:
        md_content += f"## Confirming Evidence Videos ({len(confirming_evidence)})\n\n"
        for i, video in enumerate(confirming_evidence, 1):
            md_content += f"### {i}. {video['title']}\n"
            md_content += f"- **URL:** {video['url']}\n"
            md_content += f"- **View Count:** {video['view_count']:,}\n"
            md_content += f"- **Stance:** {video['stance']}\n"
            md_content += f"- **Confidence:** {video['confidence']:.2f}\n"
            md_content += f"- **Key Points:**\n"
            for point in video['key_points']:
                md_content += f"  - {point}\n"
            md_content += "\n"
    
    # Generate HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>YouTube Counter-Intelligence Sources for {video_id}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #d32f2f; }}
            h2 {{ color: #1976d2; }}
            .counter {{ border-left: 3px solid #f44336; padding-left: 15px; margin-bottom: 20px; }}
            .confirming {{ border-left: 3px solid #4caf50; padding-left: 15px; margin-bottom: 20px; }}
            .url {{ word-break: break-all; }}
            ul {{ margin: 10px 0; }}
        </style>
    </head>
    <body>
        <h1>YouTube Counter-Intelligence Sources for {video_id}</h1>
        <p><strong>Total YouTube Videos Analyzed:</strong> {youtube_evidence.get('total_videos_analyzed', 0)}</p>
    """
    
    if counter_evidence:
        html_content += f"<h2>Counter-Evidence Videos ({len(counter_evidence)})</h2>"
        for i, video in enumerate(counter_evidence, 1):
            html_content += f"""
            <div class="counter">
                <h3>{i}. {video['title']}</h3>
                <p><strong>URL:</strong> <span class="url">{video['url']}</span></p>
                <p><strong>View Count:</strong> {video['view_count']:,}</p>
                <p><strong>Stance:</strong> {video['stance']}</p>
                <p><strong>Confidence:</strong> {video['confidence']:.2f}</p>
                <p><strong>Key Points:</strong></p>
                <ul>
            """
            for point in video['key_points']:
                html_content += f"<li>{point}</li>"
            html_content += "</ul></div>"
    
    if confirming_evidence:
        html_content += f"<h2>Confirming Evidence Videos ({len(confirming_evidence)})</h2>"
        for i, video in enumerate(confirming_evidence, 1):
            html_content += f"""
            <div class="confirming">
                <h3>{i}. {video['title']}</h3>
                <p><strong>URL:</strong> <span class="url">{video['url']}</span></p>
                <p><strong>View Count:</strong> {video['view_count']:,}</p>
                <p><strong>Stance:</strong> {video['stance']}</p>
                <p><strong>Confidence:</strong> {video['confidence']:.2f}</p>
                <p><strong>Key Points:</strong></p>
                <ul>
            """
            for point in video['key_points']:
                html_content += f"<li>{point}</li>"
            html_content += "</ul></div>"
    
    html_content += "</body></html>"
    
    # Write files
    md_file = os.path.join(output_dir, f"{video_id}_yt_sources.md")
    html_file = os.path.join(output_dir, f"{video_id}_yt_sources.html")
    
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return md_file, html_file 