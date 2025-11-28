# services/report/markdown_generator.py
import logging
import os
import pathlib
from typing import List, Dict, Tuple, Any, Union
from urllib.parse import urlparse
from datetime import datetime
from collections import defaultdict # Added for counting evidence types
from pathlib import Path

from verityngn.models.workflow import InitialAnalysisState
from verityngn.models.report import VerityReport, Claim, map_probabilities_to_verification_result

from verityngn.config.settings import OUTPUTS_DIR, COMPARE_DIR, DOWNLOADS_DIR, DEBUG_OUTPUTS

# Helper functions for enhanced explanation generation
def count_scientific_sources(sources):
    """Count scientific/research sources."""
    if not sources:
        return 0
    count = 0
    for source in sources:
        if isinstance(source, str):
            source_lower = source.lower()
        else:
            # Handle Pydantic EvidenceSource objects
            url = getattr(source, 'url', '') or ''
            source_type = getattr(source, 'source_type', '') or ''
            source_lower = str(url + ' ' + source_type).lower()
        
        if any(term in source_lower for term in ['pubmed', 'ncbi', 'doi.org', 'scholar.google', 'research', 'study', 'clinical', 'journal']):
            count += 1
    return count

def count_medical_sources(sources):
    """Count medical/health sources."""
    if not sources:
        return 0
    count = 0
    for source in sources:
        if isinstance(source, str):
            source_lower = source.lower()
        else:
            # Handle Pydantic EvidenceSource objects
            url = getattr(source, 'url', '') or ''
            source_type = getattr(source, 'source_type', '') or ''
            source_lower = str(url + ' ' + source_type).lower()
        
        if any(term in source_lower for term in ['harvard.edu', 'mayoclinic', 'clevelandclinic', 'nih.gov', 'cdc.gov', 'webmd', 'healthline']):
            count += 1
    return count

def count_government_sources(sources):
    """Count government sources."""
    if not sources:
        return 0
    count = 0
    for source in sources:
        if isinstance(source, str):
            source_lower = source.lower()
        else:
            # Handle Pydantic EvidenceSource objects
            url = getattr(source, 'url', '') or ''
            source_type = getattr(source, 'source_type', '') or ''
            source_lower = str(url + ' ' + source_type).lower()
        
        if any(term in source_lower for term in ['.gov', 'fda.', 'usda.', 'who.int']):
            count += 1
    return count

def extract_core_finding(explanation):
    """Extract the core finding from LLM explanation while preserving reasoning."""
    if not explanation:
        return ""
    
    # Remove excessive technical jargon but preserve core meaning
    import re
    
    # Split into sentences and find the most substantive ones
    sentences = re.split(r'[.!?]+', explanation)
    core_sentences = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 20 and not sentence.lower().startswith(('however', 'additionally', 'furthermore')):
            # Keep sentences that contain verification reasoning
            if any(term in sentence.lower() for term in ['evidence', 'sources', 'research', 'study', 'analysis', 'findings', 'supports', 'contradicts', 'indicates']):
                core_sentences.append(sentence)
    
    if core_sentences:
        # Take the first 2 most relevant sentences
        return '. '.join(core_sentences[:2]) + '.'
    else:
        # Fallback to first substantial sentence
        substantial_sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
        return substantial_sentences[0] + '.' if substantial_sentences else ""

def assess_evidence_quality(sources):
    """Assess and describe evidence quality."""
    if not sources:
        return ""
    
    scientific_count = count_scientific_sources(sources)
    medical_count = count_medical_sources(sources)
    government_count = count_government_sources(sources)
    total_count = len(sources)
    
    quality_descriptors = []
    
    # Determine overall quality
    high_quality_count = scientific_count + medical_count + government_count
    quality_ratio = high_quality_count / total_count if total_count > 0 else 0
    
    if quality_ratio > 0.7:
        quality_descriptors.append("Evidence quality is high with authoritative sources")
    elif quality_ratio > 0.4:
        quality_descriptors.append("Evidence quality is moderate with some authoritative sources")
    else:
        quality_descriptors.append("Evidence quality is mixed with limited authoritative sources")
    
    return '. '.join(quality_descriptors) + '.' if quality_descriptors else ""

def summarize_counter_intelligence_impact(counter_intel_boosts):
    """Summarize counter-intelligence impact in narrative form."""
    if not counter_intel_boosts:
        return ""
    
    summaries = []
    for boost in counter_intel_boosts:
        adjustment = boost.get('probability_adjustment', 0)
        boost_type = boost.get('type', 'unknown')
        
        if abs(adjustment) > 0.1:  # Only mention significant adjustments
            if boost_type == 'youtube_counter':
                summaries.append(f"YouTube counter-evidence reduces confidence by {abs(adjustment)*100:.0f}%")
            elif boost_type == 'press_release_counter':
                summaries.append(f"Press release counter-evidence reduces confidence by {abs(adjustment)*100:.0f}%")
    
    return '. '.join(summaries) + '.' if summaries else ""

def explain_confidence_level(prob_dist, sources):
    """Explain the confidence level based on probabilities and evidence."""
    if not prob_dist:
        return ""
    
    true_prob = prob_dist.get('TRUE', 0.0) * 100
    false_prob = prob_dist.get('FALSE', 0.0) * 100
    uncertain_prob = prob_dist.get('UNCERTAIN', 0.0) * 100
    
    # Determine confidence explanation
    if max(true_prob, false_prob) > 70:
        confidence_level = "high"
    elif max(true_prob, false_prob) > 50:
        confidence_level = "moderate"
    else:
        confidence_level = "low"
    
    source_count = len(sources) if sources else 0
    
    if true_prob > false_prob:
        return f"Assessment shows {confidence_level} confidence in claim validity based on {source_count} sources."
    else:
        return f"Assessment shows {confidence_level} confidence that claim is problematic based on {source_count} sources."

def generate_source_quality_indicators(sources):
    """Generate quality indicators for the odds & sources column."""
    if not sources:
        return "No sources"
    
    scientific_count = count_scientific_sources(sources)
    medical_count = count_medical_sources(sources)
    government_count = count_government_sources(sources)
    
    # Count source types for better categorization
    news_count = 0
    educational_count = 0
    general_count = 0
    
    for source in sources:
        if isinstance(source, str):
            source_lower = source.lower()
        else:
            # Handle Pydantic EvidenceSource objects
            url = getattr(source, 'url', '') or ''
            source_type = getattr(source, 'source_type', '') or ''
            source_lower = str(url + ' ' + source_type).lower()
        
        if any(term in source_lower for term in ['reuters.com', 'apnews.com', 'bbc.', 'nytimes.', 'wsj.', 'cnn.', 'news']):
            news_count += 1
        elif any(term in source_lower for term in ['.edu', 'university', 'academic']):
            educational_count += 1
        else:
            general_count += 1
    
    # Build quality indicator string (no icons)
    indicators = []
    
    if scientific_count > 0:
        indicators.append(f"{scientific_count} scientific")
    if medical_count > 0:
        indicators.append(f"{medical_count} medical")
    if government_count > 0:
        indicators.append(f"{government_count} government")
    if educational_count > 0:
        indicators.append(f"{educational_count} academic")
    if news_count > 0:
        indicators.append(f"{news_count} news")
    if general_count > 0:
        indicators.append(f"{general_count} general")
    
    # Determine overall quality assessment
    total_sources = len(sources)
    high_quality_sources = scientific_count + medical_count + government_count + educational_count
    quality_ratio = high_quality_sources / total_sources if total_sources > 0 else 0
    
    if quality_ratio > 0.7:
        quality_badge = "High Quality"
    elif quality_ratio > 0.4:
        quality_badge = "Good Quality"
    else:
        quality_badge = "Mixed Quality"
    
    if indicators:
        return f"{quality_badge}<br>{' • '.join(indicators)}"
    else:
        return quality_badge

def _get_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        domain = urlparse(url).netloc
        # Basic cleaning, can be expanded
        domain = domain.replace("www.", "").replace("m.", "").split(':')[0]
        return domain
    except Exception as e:
        # Log the error for debugging
        # logging.warning(f"Could not parse URL '{url}': {e}")
        return "invalid_url" # Return a specific string for invalid URLs

def _map_source_type(source_type: str, url: str) -> str:
    """Maps raw source type or URL domain to standardized categories for the Evidence Summary."""
    source_type_lower = source_type.lower() if source_type else ''
    domain = _get_domain(url)

    if "academic" in source_type_lower or any(ending in domain for ending in [".edu"]):
        return "Academic Research"
    if "government" in source_type_lower or any(ending in domain for ending in [".gov", ".mil", "whitehouse.gov", "cdc.gov", "nih.gov", "fda.gov"]):
        return "Government Publications"
    if "journal" in source_type_lower or any(kw in domain for kw in ["ncbi.nlm.nih", "pubmed", "nejm.", "jamanetwork.", "thelancet.", "nature.com", "science.org", "pnas.org"]):
        return "Scientific Journals"
    if "expert" in source_type_lower: # This is less reliable, needs context
        return "Expert Opinions"
    if "fact-check" in source_type_lower or any(kw in domain for kw in ["factcheck.org", "politifact.", "snopes.", "reuters.com/fact-check", "apnews.com/ap-fact-check", "factcheck.afp.com"]):
        return "Fact-checking Organizations"
    if "news" in source_type_lower or any(kw in domain for kw in ["reuters.com", "apnews.com", "bbc.", "nytimes.", "wsj.", "cnn."]): # Add more reputable news domains
        return "News Articles"
    # Default to Web Page if not matched
    return "Web Pages/Blogs"


def generate_enhanced_explanation(verification_result: dict, claim_text: str, claim_index: int = None, video_id: str = None) -> str:
    """Generate comprehensive, narrative explanations instead of bullet points."""
    if not verification_result:
        return "No verification details available."
    
    # Extract key components
    sources = verification_result.get("sources", [])
    explanation = verification_result.get("explanation", "")
    prob_dist = verification_result.get("probability_distribution", {})
    counter_intel_boosts = verification_result.get("counter_intelligence_boosts", [])
    
    # Build narrative explanation parts
    narrative_parts = []
    
    # 1. Evidence strength overview
    if sources:
        source_count = len(sources)
        scientific_sources = count_scientific_sources(sources)
        medical_sources = count_medical_sources(sources)
        government_sources = count_government_sources(sources)
        
        evidence_overview = f"Analysis of {source_count} sources"
        quality_indicators = []
        if scientific_sources > 0:
            quality_indicators.append(f"{scientific_sources} scientific/research")
        if medical_sources > 0:
            quality_indicators.append(f"{medical_sources} medical")
        if government_sources > 0:
            quality_indicators.append(f"{government_sources} government")
        
        if quality_indicators:
            evidence_overview += f", including {', '.join(quality_indicators)} sources"
        evidence_overview += "."
        narrative_parts.append(evidence_overview)
    
    # 2. Core verification finding (preserve LLM reasoning)
    if explanation:
        core_finding = extract_core_finding(explanation)
        if core_finding:
            narrative_parts.append(core_finding)
    
    # 3. Evidence quality assessment
    if sources:
        evidence_quality = assess_evidence_quality(sources)
        if evidence_quality:
            narrative_parts.append(evidence_quality)
    
    # 4. Counter-intelligence impact (if significant)
    if counter_intel_boosts:
        ci_impact = summarize_counter_intelligence_impact(counter_intel_boosts)
        if ci_impact:
            narrative_parts.append(ci_impact)
    
    # 5. Confidence reasoning
    if prob_dist:
        confidence_reasoning = explain_confidence_level(prob_dist, sources)
        if confidence_reasoning:
            narrative_parts.append(confidence_reasoning)
    
    # Combine into coherent narrative
    if narrative_parts:
        return " ".join(narrative_parts)
    else:
        return "Verification analysis completed with limited detail available."

def optimize_explanation_format(explanation: str, claim_index: int = None, video_id: str = None) -> str:
    """Legacy function maintained for compatibility - now calls enhanced explanation when possible."""
    if not explanation or explanation == "No explanation provided.":
        return "No verification details available."
    
    # Try to preserve more content while still cleaning
    import re
    
    # Remove only HTML tags and excessive emoji
    cleaned = re.sub(r'<[^>]+>', '', explanation)
    cleaned = re.sub(r'[📺📰🔬🌐🎬📋🚫→🕵️]{2,}', '', cleaned)  # Only remove multiple emojis
    
    # 🎯 SHERLOCK: Extract and deduplicate counter-intelligence information
    counter_intel_points = []
    
    # Extract YouTube counter-intelligence data
    youtube_patterns = [
        r'(\d+)\s*youtube\s*videos.*?(\d+)\s*total\s*views',
        r'youtube\s*counter.*?(\d+)\s*sources',
        r'(\d+)\s*youtube\s*videos.*?contradict',
        r'youtube\s*reviews.*?reduced.*?(\d+)%',
        r'(\d+)\s*youtube\s*videos.*?(\d+)\s*views'
    ]
    
    for pattern in youtube_patterns:
        matches = re.findall(pattern, cleaned, re.IGNORECASE)
        for match in matches:
            if len(match) == 2:
                sources, views = match
                counter_intel_points.append(f"• YouTube counter-evidence: {sources} videos ({views} views)")
            elif len(match) == 1:
                value = match[0]
                if '%' in pattern:
                    counter_intel_points.append(f"• YouTube credibility reduction: {value}%")
                else:
                    counter_intel_points.append(f"• YouTube counter-sources: {value} videos")
    
    # Extract press release counter-intelligence data
    press_patterns = [
        r'(\d+)\s*press\s*release.*?contradict',
        r'press\s*release.*?(\d+)\s*sources',
        r'press\s*release.*?reduced.*?(\d+)%'
    ]
    
    for pattern in press_patterns:
        matches = re.findall(pattern, cleaned, re.IGNORECASE)
        for match in matches:
            if '%' in pattern:
                counter_intel_points.append(f"• Press release credibility reduction: {match[0]}%")
            else:
                counter_intel_points.append(f"• Press release counter-sources: {match[0]} releases")
    
    # 🎯 SHERLOCK: Extract scientific and independent evidence
    evidence_points = []
    
    # Scientific evidence extraction
    scientific_patterns = [
        r'(\d+)\s*scientific\s*sources.*?(\d+)\s*supporting',
        r'(\d+)\s*scientific\s*studies.*?support',
        r'scientific\s*evidence.*?(\d+)\s*sources',
        r'scientific\s*support:\s*(\d+)/(\d+)\s*sources',
        r'(\d+)/(\d+)\s*sources\s*support'
    ]
    
    for pattern in scientific_patterns:
        matches = re.findall(pattern, cleaned, re.IGNORECASE)
        for match in matches:
            if len(match) == 2:
                if 'support' in pattern.lower():
                    supporting, total = match
                else:
                    total, supporting = match
                evidence_points.append(f"• Scientific support: {supporting}/{total} sources")
            elif len(match) == 1:
                evidence_points.append(f"• Scientific evidence: {match[0]} sources")
    
    # Independent evidence extraction
    independent_patterns = [
        r'(\d+)\s*independent\s*sources',
        r'independent\s*research.*?(\d+)\s*sources',
        r'(\d+)\s*independent\s*studies',
        r'independent\s*research:\s*(\d+)\s*sources'
    ]
    
    for pattern in independent_patterns:
        matches = re.findall(pattern, cleaned, re.IGNORECASE)
        for match in matches:
            if match[0].isdigit():
                evidence_points.append(f"• Independent research: {match[0]} sources")
    
    # 🎯 SHERLOCK: Extract probability and verification data
    probability_points = []
    
    prob_patterns = [
        r'probability.*?(\d+\.?\d*)%',
        r'(\d+\.?\d*)%\s*probability',
        r'confidence.*?(\d+\.?\d*)%'
    ]
    
    for pattern in prob_patterns:
        matches = re.findall(pattern, cleaned, re.IGNORECASE)
        for match in matches:
            probability_points.append(f"• Confidence: {match[0]}%")
    
    # 🎯 SHERLOCK: Remove counter-intelligence blocks to clean remaining text
    cleaned = re.sub(r'youtube counter-intelligence:.*?(?=\s*🔬|\s*📰|\s*🌐|\s*$)', '', cleaned, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r'press release counter-intelligence:.*?(?=\s*🔬|\s*📰|\s*🌐|\s*$)', '', cleaned, flags=re.IGNORECASE | re.DOTALL)
    
    # Clean multiple spaces and line breaks
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # Remove common redundant phrases
    redundant_phrases = [
        "This claim is", "The claim that", "Based on the evidence", "According to our analysis",
        "The verification shows", "Our findings indicate", "The research suggests", "Evidence suggests that",
        "Analysis reveals that", "It appears that", "It seems that", "No conclusion available",
        "multiple youtube videos", "independent reviewers with", "total views provide", "contradictory evidence",
        "verification analysis", "comprehensive review", "mixed evidence", "contradictory sources"
    ]
    
    for phrase in redundant_phrases:
        cleaned = cleaned.replace(phrase, "").strip()
    
    # 🎯 SHERLOCK: Combine all extracted points with deduplication
    all_points = []
    
    # Add counter-intelligence points first (most important)
    all_points.extend(counter_intel_points[:2])  # Limit to 2 counter-intel points
    
    # Add evidence points
    all_points.extend(evidence_points[:2])  # Limit to 2 evidence points
    
    # Add probability points
    all_points.extend(probability_points[:1])  # Limit to 1 probability point
    
    # Extract remaining meaningful content
    if len(cleaned) > 30:
        sentences = [s.strip() for s in cleaned.replace('. ', '.|').split('|') if s.strip()]
        for sentence in sentences[:2]:  # Limit to 2 additional points
            if len(sentence) > 20 and not any(kp in sentence.lower() for kp in ["scientific", "independent", "youtube", "press"]):
                clean_sentence = sentence.strip(' .,').capitalize()
                if not clean_sentence.endswith('.'):
                    clean_sentence += '.'
                all_points.append(f"• {clean_sentence}")
    
    # 🎯 SHERLOCK: Add counter-intelligence file links if available
    ci_links = []
    
    # Check for counter-intelligence and add appropriate links
    # Use relative paths for standalone viewing compatibility
    if counter_intel_points and claim_index is not None and video_id:
        ci_links.append(f"[🕵️ CI Analysis](claim/claim_{claim_index}/counter_intel.html)")
    
    # Add YouTube counter-intelligence link if detected
    if any("youtube" in point.lower() for point in counter_intel_points):
        if claim_index is not None and video_id:
            ci_links.append(f"[📺 YouTube CI](claim/claim_{claim_index}/youtube_ci.html)")
    
    # Add press release counter-intelligence link if detected  
    if any("press" in point.lower() for point in counter_intel_points):
        if claim_index is not None and video_id:
            ci_links.append(f"[Press CI](claim/claim_{claim_index}/press_ci.html)")
    
    # 🎯 SHERLOCK: Final fallback if no meaningful points extracted
    if not all_points:
        if "counter" in explanation.lower() or "contradict" in explanation.lower():
            all_points.append("• Counter-evidence detected from multiple sources")
        elif "support" in explanation.lower() or "confirm" in explanation.lower():
            all_points.append("• Supporting evidence found from verification")
        else:
            all_points.append("• Verification analysis completed with mixed results")
    
    # 🎯 SHERLOCK: Deduplicate and limit to 4 bullet points maximum
    seen_points = set()
    final_points = []
    counter_intel_added = 0
    other_added = 0
    
    for point in all_points:
        # Create a key for deduplication (remove numbers to avoid exact duplicates)
        point_key = re.sub(r'\d+', 'N', point.lower())
        
        if point_key not in seen_points:
            seen_points.add(point_key)
            
            if "counter" in point.lower() and counter_intel_added < 2:
                final_points.append(point)
                counter_intel_added += 1
            elif other_added < 2:
                final_points.append(point)
                other_added += 1
            
            if len(final_points) >= 4:
                break
    
    # 🎯 SHERLOCK: Add counter-intelligence links at the end if space allows
    if ci_links and len(final_points) < 4:
        for link in ci_links[:4-len(final_points)]:
            final_points.append(f"• {link}")
    
    return "<br>".join(final_points)


def create_counter_intelligence_claim_file(claim: Claim, counter_intel_data: Dict[str, Any], file_path: pathlib.Path) -> str:
    """
    Create a markdown string containing counter-intelligence analysis for a specific claim.
    
    Args:
        claim (Claim): Claim data object
        counter_intel_data (Dict[str, Any]): Counter-intelligence data (YouTube videos, press releases)
        file_path (pathlib.Path): Path to save the CI file (currently unused for in-memory generation)
        
    Returns:
        str: Markdown content for the counter-intelligence analysis
    """
    content = f"# 🕵️ Counter-Intelligence Analysis for Claim\n\n"
    content += f"**Claim ID:** {getattr(claim, 'claim_id', 'N/A')}\n\n"
    content += f"**Timestamp:** {claim.timestamp}\n\n"
    content += f"**Speaker:** {claim.speaker}\n\n"
    content += f"**Claim:** {claim.claim_text}\n\n"
    content += f"**Initial Assessment:** {claim.initial_assessment}\n\n"
    
    # Extract counter-intelligence from explanation
    explanation = str(claim.explanation or "")
    youtube_count = 0
    press_count = 0
    
    # Count counter-intelligence references in explanation
    if 'youtube counter' in explanation.lower():
        import re
        youtube_matches = re.findall(r'(\d+)\s*youtube', explanation.lower())
        if youtube_matches:
            youtube_count = int(youtube_matches[0])
    
    if 'press release' in explanation.lower():
        import re
        press_matches = re.findall(r'(\d+)\s*press\s*release', explanation.lower())
        if press_matches:
            press_count = int(press_matches[0])
    
    # YouTube Counter-Intelligence Section
    content += "## 📺 YouTube Counter-Intelligence\n\n"
    
    youtube_videos = counter_intel_data.get('youtube_videos', [])
    if youtube_videos and youtube_count > 0:
        content += f"**Found:** {youtube_count} YouTube videos providing counter-evidence\n\n"
        
        for i, video in enumerate(youtube_videos[:youtube_count]):
            content += f"### Video {i+1}: {video.get('title', 'Unknown Title')}\n\n"
            content += f"**URL:** [{video.get('url', '#')}]({video.get('url', '#')})\n\n"
            content += f"**Channel:** {video.get('channel_title', 'Unknown Channel')}\n\n"
            content += f"**Views:** {video.get('view_count', 'N/A'):,}\n\n"
            content += f"**Stance:** {video.get('stance', 'Unknown')}\n\n"
            content += f"**Confidence:** {video.get('confidence', 0):.2%}\n\n"
            
            key_points = video.get('key_points', [])
            if key_points:
                content += "**Key Counter-Arguments:**\n\n"
                for point in key_points[:3]:  # Limit to top 3 points
                    content += f"- {point}\n"
                content += "\n"
            
            # Link to detailed analysis if available (use relative path)
            video_id = video.get('id', '')
            if video_id:
                content += f"**Detailed Analysis:** [View {video_id}.summary.json](counter_intelligence/{video_id}/summary.json)\n\n"
            
            content += "---\n\n"
    else:
        content += "No YouTube counter-intelligence found for this claim.\n\n"
    
    # Press Release Counter-Intelligence Section
    content += "## Press Release Counter-Intelligence\n\n"
    
    press_releases = counter_intel_data.get('press_releases', [])
    if press_releases and press_count > 0:
        content += f"**Found:** {press_count} press releases providing counter-evidence\n\n"
        
        for i, release in enumerate(press_releases[:press_count]):
            content += f"### Press Release {i+1}: {release.get('title', 'Unknown Title')}\n\n"
            content += f"**URL:** [{release.get('url', '#')}]({release.get('url', '#')})\n\n"
            content += f"**Source:** {release.get('source', 'Unknown Source')}\n\n"
            content += f"**Date:** {release.get('date', 'Unknown Date')}\n\n"
            content += f"**Credibility Impact:** {release.get('credibility_impact', 'Unknown')}\n\n"
            
            key_findings = release.get('key_findings', [])
            if key_findings:
                content += "**Key Findings:**\n\n"
                for finding in key_findings[:3]:  # Limit to top 3 findings
                    content += f"- {finding}\n"
                content += "\n"
            
            content += "---\n\n"
    else:
        content += "No press release counter-intelligence found for this claim.\n\n"
    
    # Summary Impact Section
    content += "## Counter-Intelligence Impact Summary\n\n"
    
    total_ci_sources = youtube_count + press_count
    if total_ci_sources > 0:
        content += f"**Total Counter-Intelligence Sources:** {total_ci_sources}\n\n"
        content += f"- YouTube Videos: {youtube_count}\n"
        content += f"- Press Releases: {press_count}\n\n"
        
        # Extract credibility impact from explanation
        import re
        credibility_matches = re.findall(r'reduced.*?(\d+)%', explanation.lower())
        if credibility_matches:
            reduction = credibility_matches[0]
            content += f"**Estimated Credibility Reduction:** {reduction}%\n\n"
        
        content += "**Assessment:** This claim has significant counter-intelligence that challenges its reliability.\n\n"
    else:
        content += "**Assessment:** No significant counter-intelligence found for this claim.\n\n"
    
    content += f"\n---\n\n*Generated by VerityNgn Counter-Intelligence Analysis • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
    
    return content

def create_rolled_up_source_file(claim: Claim, evidence: List[Union[str, Dict]], file_path: pathlib.Path) -> str:
    """
    Create a markdown string containing all sources for a claim.
    
    Args:
        claim (Claim): Claim data object
        evidence (List[Union[str, Dict]]): List of evidence items (URLs or dicts)
        file_path (pathlib.Path): Path to save the source file (currently unused for in-memory generation)
        
    Returns:
        str: Markdown content for the claim sources
    """
    content = f"# Sources for Claim ID: {claim.claim_id}\n\n" # Use claim_id if available
    content += f"**Timestamp:** {claim.timestamp}\n\n"
    content += f"**Speaker:** {claim.speaker}\n\n"
    content += f"**Claim:** {claim.claim_text}\n\n"
    content += f"**Initial Assessment:** {claim.initial_assessment}\n\n"
    content += f"**Explanation:** {claim.explanation}\n\n"

    # Add sources
    content += "## References\n\n"
    if not evidence:
        content += "No evidence sources were provided for this claim.\n"
    else:
        for i, source in enumerate(evidence):
            # Initialize variables for all paths
            url = ''
            title = ''
            text = ''
            
            if isinstance(source, str):
                # Handle string URLs
                url = source
                title = source
                text = ''
            elif isinstance(source, dict):
                # Handle dictionary sources (like EvidenceSource Pydantic model might be converted to)
                url = source.get('url', '')
                title = source.get('title', source.get('source_name', url or 'Source Detail'))
                text = source.get('text', source.get('snippet', '')) # Prioritize text/snippet
            else:
                # Handle Pydantic EvidenceSource objects or any other type
                url = getattr(source, 'url', '') or ''
                title = getattr(source, 'title', '') or getattr(source, 'source_name', '') or url or 'Source Detail'
                text = getattr(source, 'text', '') or getattr(source, 'snippet', '') or '' # Prioritize text/snippet

            if url:
                content += f"{i+1}. [{title}]({url})\n"
            else:
                content += f"{i+1}. {title}\n" # If no URL, just list title

            if text:
                # Indent the snippet/text under the source link/title
                content += f"   > {text}\n"

    return content

def generate_markdown_report(report: VerityReport) -> Tuple[str, Dict[str, str], Dict[str, str]]:
    """
    Generate the complete markdown report with embedded claim sources and counter-intelligence.
    Returns main content. Separate file dictionaries are returned empty as content is now embedded.
    """
    logger = logging.getLogger(__name__)
    try:
        # Generate the main report content with embedded sources
        main_content = generate_main_report_content(report)

        # Return empty dicts for separate files as they are now embedded
        # We keep the signature for compatibility
        return main_content, {}, {}

    except Exception as e:
        logger.error(f"Error generating markdown report: {e}", exc_info=True)
        # Return minimal content in case of error during generation
        error_content = f"# Report Generation Error\n\nAn error occurred: {e}\n\nGenerated by VerityNgn on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        return error_content, {}, {}

def generate_main_report_content(report: VerityReport) -> str:
    """
    Generate the main report content in memory.
    
    Args:
        report (VerityReport): The report containing claims and report data
        
    Returns:
        str: Markdown content for the main report
    """
    logger = logging.getLogger(__name__)
    report_content = []
    evidence_counts_by_type = defaultdict(int)
    verdict_counts = defaultdict(int)
    all_evidence_sources = [] # Collect all sources for summary

    # --- Pre-process data ---
    total_claims = 0
    if report.claims_breakdown:
        total_claims = len(report.claims_breakdown)
        for claim in report.claims_breakdown:
            # Use the same probability-based calculation as Table 6 for consistency
            verdict = "UNCERTAIN"
            if isinstance(claim.verification_result, dict):
                prob_dist = claim.verification_result.get("probability_distribution")
                if isinstance(prob_dist, dict):
                    # Use the same mapping function as Table 6
                    from verityngn.models.report import map_probabilities_to_verification_result
                    verdict = map_probabilities_to_verification_result(prob_dist)
                else:
                    # Fallback to stored result if no probability distribution
                    verdict = claim.verification_result.get("result", "UNCERTAIN")
            elif isinstance(claim.verification_result, str):
                verdict = claim.verification_result

            # Normalize verdicts slightly if needed, e.g., map UNABLE_DETERMINE
            if verdict == "UNABLE_DETERMINE": verdict = "UNCERTAIN"
            verdict_counts[verdict] += 1

            # Collect evidence sources from verification_result.sources (the actual location)
            sources_to_process = []
            
            # First try to get sources from verification_result.sources
            if claim.verification_result and isinstance(claim.verification_result, dict):
                sources_from_verification = claim.verification_result.get("sources", [])
                if sources_from_verification:
                    sources_to_process.extend(sources_from_verification)
            
            # Also check claim.evidence if it exists (for compatibility)
            if isinstance(claim.evidence, list) and claim.evidence:
                sources_to_process.extend(claim.evidence)
            
            # Process all collected sources
            if sources_to_process:
                all_evidence_sources.extend(sources_to_process)
                for item in sources_to_process:
                    source_type = None
                    url = None
                    if isinstance(item, str): # Simple URL string
                        url = item
                    elif isinstance(item, dict): # Dictionary-like source
                        url = item.get('url')
                        source_type = item.get('source_type')

                    # Standardize type based on URL if type is missing or generic
                    if url:
                         standardized_type = _map_source_type(source_type, url)
                         evidence_counts_by_type[standardized_type] += 1
                    elif source_type: # If no URL but type exists
                         evidence_counts_by_type[source_type] += 1
                    else:
                         evidence_counts_by_type["Unknown/Other"] += 1 # Count sources without URL or type
    else:
        logger.warning("No claims found in the report for markdown generation.")

    # Calculate overall truthfulness based on specific verdict keys
    # Align these keys with the actual values used in your verification results
    false_count = verdict_counts.get("LIKELY_FALSE", 0) + verdict_counts.get("HIGHLY_LIKELY_FALSE", 0)
    true_count = verdict_counts.get("LIKELY_TRUE", 0) + verdict_counts.get("HIGHLY_LIKELY_TRUE", 0)
    uncertain_count = verdict_counts.get("UNCERTAIN", 0) # Include UNCERTAIN

    # Determine overall verdict string
    if total_claims > 0:
        if false_count / total_claims >= 0.6: # Threshold for highly likely false
             overall_verdict = "Highly Likely False"
        elif false_count > true_count:
             overall_verdict = "Likely False"
        elif true_count / total_claims >= 0.6: # Threshold for highly likely true
             overall_verdict = "Highly Likely True"
        elif true_count >= false_count:
             overall_verdict = "Likely True"
        else: # Default to mixed/uncertain if no clear majority
             overall_verdict = "Mixed/Uncertain"
    else:
         overall_verdict = "Undetermined (No Claims)"


    # Calculate percentages safely
    verdict_percentages = {k: (v / total_claims * 100) if total_claims > 0 else 0 for k, v in verdict_counts.items()}

    # --- Build Report Sections ---

    # --- Video Embed and Description (Not Numbered) ---
    media_embed = report.media_embed
    video_title = media_embed.title if media_embed else "Video Title Unavailable"
    thumbnail_url = media_embed.thumbnail_url if media_embed else ""
    video_url = media_embed.video_url if media_embed else ""
    video_id = media_embed.video_id if media_embed else "unknown_id"
    video_description = report.description or "No description provided."

    # Escape potentially problematic characters in title/description for Markdown/HTML
    safe_title = video_title.replace("<", "&lt;").replace(">", "&gt;")
    # Correctly replace actual newlines \n with <br>
    safe_description = video_description.replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")

    # Add video title at the very top
    report_content.append(f"""# {safe_title}

<div class="video-embed">
    <a href="{video_url}" target="_blank">
        <img src="{thumbnail_url}" alt="Video thumbnail for {safe_title}" width="560" style="max-width: 100%; height: auto;">
    </a>
    <p>Video ID: {video_id}</p>
</div><!-- VIDEO_CONTAINER_END -->

## Internal YouTube Description

{safe_description}

""")

    # --- Section 1: Executive Summary ---
    # Apply quantum mapping to all claims and collect verdicts
    verdict_counts = {
        "HIGHLY_LIKELY_TRUE": 0,
        "LIKELY_TRUE": 0,
        "LEANING_TRUE": 0,
        "UNCERTAIN": 0,
        "LEANING_FALSE": 0,
        "LIKELY_FALSE": 0,
        "HIGHLY_LIKELY_FALSE": 0
    }
    press_release_claims = 0
    youtube_counter_claims = 0
    
    # Count Press Release and YouTube Review/Response sources
    press_release_count = 0
    youtube_response_count = 0
    
    for claim in report.claims_breakdown:
        # Use consistent verdict calculation logic (same as Table 6)
        verdict = "UNCERTAIN"
        if isinstance(claim.verification_result, dict):
            prob_dist = claim.verification_result.get("probability_distribution")
            if isinstance(prob_dist, dict):
                # Use the same mapping function as Table 6
                from verityngn.models.report import map_probabilities_to_verification_result
                verdict = map_probabilities_to_verification_result(prob_dist)
            else:
                # Fallback to stored result if no probability distribution
                verdict = claim.verification_result.get("result", "UNCERTAIN")
        elif isinstance(claim.verification_result, str):
            verdict = claim.verification_result
        
        # Normalize verdicts slightly if needed
        if verdict == "UNABLE_DETERMINE": 
            verdict = "UNCERTAIN"
        verdict_counts[verdict] += 1
        
        # Count press release and YouTube evidence using new separated fields
        if hasattr(claim, 'pr_sources') and claim.pr_sources:
            press_release_claims += 1
            press_release_count += len(claim.pr_sources)
            
        if hasattr(claim, 'youtube_counter_sources') and claim.youtube_counter_sources:
            youtube_counter_claims += 1
            youtube_response_count += len(claim.youtube_counter_sources)
    # Section 1: Add claim verdict summary
    report_content.append("## Executive Summary")
    report_content.append("")
    report_content.append(f"Total Claims: {len(report.claims_breakdown)}")
    for verdict, count in verdict_counts.items():
        report_content.append(f"- {verdict.replace('_', ' ').title()}: {count}")
    report_content.append("")
    report_content.append(f"Claims with Press Release/Newswire Evidence: {press_release_claims}")
    report_content.append(f"Claims with YouTube Counter-Intelligence Evidence: {youtube_counter_claims}")
    report_content.append("")

    # --- 2. Overall Truthfulness Assessment ---
    report_content.append(f"## 2. Overall Truthfulness Assessment: {overall_verdict}")
    report_content.append("| Category | Count | Percentage |")
    report_content.append("|:---------|:-----:|:----------:|")
    report_content.append(f"| Total Claims | {total_claims} | 100% |")
    for v_key, v_name in [
        ("HIGHLY_LIKELY_TRUE", "Highly Likely True"),
        ("LIKELY_TRUE", "Likely True"),
        ("LEANING_TRUE", "Leaning True"),
        ("UNCERTAIN", "Uncertain"),
        ("LEANING_FALSE", "Leaning False"),
        ("LIKELY_FALSE", "Likely False"),
        ("HIGHLY_LIKELY_FALSE", "Highly Likely False")
    ]: # Use the same display order as Executive Summary
        count = verdict_counts.get(v_key, 0)
        percent = verdict_percentages.get(v_key, 0)
        report_content.append(f"| {v_name} | {count} | {percent:.1f}% |")

    # Generate contextual summary based on the calculated overall_verdict
    overall_assessment_summary = ""
    if total_claims > 0:
         if overall_verdict == "Highly Likely False":
              summary_status = "significant credibility issues, with a strong majority of claims assessed as false."
         elif overall_verdict == "Likely False":
              summary_status = "credibility concerns, with more claims assessed as false than true."
         elif overall_verdict == "Highly Likely True":
              summary_status = "generally reliable content, with a strong majority of claims assessed as true."
         elif overall_verdict == "Likely True":
              summary_status = "mostly reliable content, with more claims assessed as true than false."
         else: # Mixed/Uncertain
              summary_status = "mixed reliability, containing a blend of verifiable and questionable claims, requiring viewer caution."
         overall_assessment_summary = f"Based on the analysis of {total_claims} claims, this video demonstrates {summary_status}"
    else:
        overall_assessment_summary = "No claims were analyzed, so truthfulness could not be assessed."

    report_content.append("")
    report_content.append(overall_assessment_summary)
    report_content.append("")

    # --- 3. Summary of Key Findings --- (Meta-analysis of the report itself)
    report_content.append("## 3. Summary of Key Findings")
    report_content.append("| Category | Description | Impact |")
    report_content.append("|:---------|:------------|:-------|")

    # --- Calculate metrics for this table using pre-calculated/derived values ---
    high_quality_source_count_meta = 0
    total_sources_meta = len(all_evidence_sources)
    unique_source_types_meta = set()

    for source in all_evidence_sources:
        source_type = None
        url = None
        quality_flag = False

        if isinstance(source, str):
            url = source
        elif isinstance(source, dict):
            url = source.get('url')
            source_type = source.get('source_type')
        else:
            # Handle Pydantic EvidenceSource objects
            url = getattr(source, 'url', None)
            source_type = getattr(source, 'source_type', None)

        standardized_type = "Unknown/Other"
        if url:
            standardized_type = _map_source_type(source_type, url)
        elif source_type:
            standardized_type = source_type # Use provided type if no URL

        unique_source_types_meta.add(standardized_type)

        # Define high-quality types for this section
        if standardized_type in ['Academic Research', 'Scientific Journals', 'Government Publications', 'Fact-checking Organizations']:
            high_quality_source_count_meta += 1

    quality_percentage_meta = (high_quality_source_count_meta / total_sources_meta * 100) if total_sources_meta > 0 else 0

    # Use previously calculated counts for verification status
    uncertain_claim_count = verdict_counts.get("UNCERTAIN", 0)
    verified_claims_meta = total_claims - uncertain_claim_count
    verification_percentage_meta = (verified_claims_meta / total_claims * 100) if total_claims > 0 else 0

    distinct_timestamps_count = len(set(c.timestamp for c in report.claims_breakdown if c and c.timestamp)) if report.claims_breakdown else 0

    # --- Append rows for Section 3 table ---
    report_content.append(f"| Overall Assessment | {overall_verdict} | Provides context for the overall message reliability. |")
    report_content.append(f"| Evidence Quality | {high_quality_source_count_meta} of {total_sources_meta} sources ({quality_percentage_meta:.1f}%) identified as high-quality. | Affects the confidence level of verification results. |")
    report_content.append(f"| Verification Status | {verified_claims_meta} of {total_claims} claims ({verification_percentage_meta:.1f}%) received a True/False assessment. | Indicates the proportion of claims where a determination could be made. |")
    report_content.append(f"| Source Diversity | Claims supported by sources from {len(unique_source_types_meta)} different categories. | Broader diversity can enhance reliability if sources are high-quality. |")
    report_content.append(f"| Time Distribution | Claims analyzed across {distinct_timestamps_count} distinct timestamps. | Helps identify patterns or concentration of claims over time. |")
    report_content.append("")

    # --- 4. Key Findings Identified --- (Specific findings generated by agent/logic)
    report_content.append("## 4. Key Findings Identified")
    if report.key_findings:
        report_content.append("| Category | Description |")
        report_content.append("|:---------|:------------|")
        for finding in report.key_findings:
            # Prepare cell content separately, escaping pipes and using <br> for newlines
            category_cell = str(finding.category or "N/A").replace("|", "\\|").replace("\n", "<br>")
            description_cell = str(finding.description or "N/A").replace("|", "\\|").replace("\n", "<br>")
            report_content.append(f"| {category_cell} | {description_cell} |")
        report_content.append("")
    else:
        report_content.append("No specific key findings were generated for this report.")
        report_content.append("")

    # --- 5. Evidence Summary --- (Breakdown by source type counts) (Renumbered)
    report_content.append("## 5. Evidence Summary")
    report_content.append("### Evidence Types Used in Verification")
    if not evidence_counts_by_type:
        report_content.append("No evidence sources were categorized.")
    else:
        report_content.append("| Category                    | Count | Potential Reliability | Notes                                           |")
        report_content.append("| :-------------------------- | :---: | :------------------ | :---------------------------------------------- |")
        evidence_categories = {
            "Academic Research": ("High", "Peer-reviewed studies and academic publications"),
            "Government Publications": ("High", "Official government documents and reports"),
            "Scientific Journals": ("High", "Professional scientific publications"),
            "Expert Opinions": ("Medium", "Analysis from subject matter experts"),
            "Fact-checking Organizations": ("High", "Professional fact-checking services"),
            "News Articles": ("Medium", "Reputable news outlets"),
            "Web Pages/Blogs": ("Low", "General web content, may vary in reliability"),
        }
        for category, (reliability, notes) in evidence_categories.items():
            count = evidence_counts_by_type.get(category, 0)
            report_content.append(f"| {category:<27} | {count:>5} | {reliability:<11} | {notes:<47} |")
    report_content.append("")

    # --- 6. Claims Breakdown with Verification Results --- (Renumbered)
    report_content.append("## 6. Claims Breakdown with Verification Results")
    report_content.append("*This section shows primary video analysis claims. Counter-intelligence claims are reported separately in Section 8.*")
    report_content.append("")
    if not report.claims_breakdown:
         report_content.append("No claims were available for breakdown.")
    else:
        report_content.append("| Time | Speaker | Claim | Initial Assessment | Verification Result | Explanation | Odds & Sources |")
        report_content.append("|:----:|:--------|:------|:------------------|:-------------------|:------------|:---------------|")
        for i, claim in enumerate(report.claims_breakdown):
            # Prepare cell content safely
            time_cell = str(claim.timestamp or "-").replace("|", "\\|").replace("\n", " ")
            speaker_cell = str(claim.speaker or "Unknown").replace("|", "\\|").replace("\n", " ")
            claim_text_cell = str(claim.claim_text or "N/A").replace("|", "\\|").replace("\n", " ")
            initial_assessment_cell = str(claim.initial_assessment or "N/A").replace("|", "\\|").replace("\n", " ")

            verification_result_data = claim.verification_result
            explanation_str = str(claim.explanation or "No explanation provided.")
            
            # --- Use quantum/human mapping for Verification Result ---
            probabilities = {'TRUE': 0.0, 'FALSE': 0.0, 'UNCERTAIN': 1.0}
            if isinstance(verification_result_data, dict):
                probs_raw = verification_result_data.get("probability_distribution")
                if isinstance(probs_raw, dict):
                    probs_normalized = {k.upper(): float(v) for k, v in probs_raw.items() if isinstance(v, (int, float))}
                    probabilities['TRUE'] = probs_normalized.get('TRUE', 0.0)
                    probabilities['FALSE'] = probs_normalized.get('FALSE', 0.0)
                    uncertain_prob = probs_normalized.get('UNCERTAIN', 1.0 - probabilities['TRUE'] - probabilities['FALSE'])
                    probabilities['UNCERTAIN'] = max(0.0, min(1.0, uncertain_prob))
                    
                # 🚀 ENHANCED: Extract explanation from verification result and optimize ALL sources
                verification_explanation = verification_result_data.get("explanation", "")
                if verification_explanation and verification_explanation != explanation_str:
                    explanation_str = str(verification_explanation)
                    
            elif isinstance(verification_result_data, str):
                if verification_result_data == "UNABLE_DETERMINE":
                    result_str = "UNCERTAIN"
                    
            # Compute Verification Result using mapping
            result_str = map_probabilities_to_verification_result(probabilities)
            result_cell = result_str.replace("|", "\\|").replace("\n", " ")
            
            # 🚀 ENHANCED: Use enhanced explanation generation for better narrative format
            if isinstance(verification_result_data, dict):
                explanation_cell = generate_enhanced_explanation(verification_result_data, claim.claim_text, claim_index=i, video_id=video_id).replace("|", "\\|")
            else:
                explanation_cell = optimize_explanation_format(explanation_str, claim_index=i, video_id=video_id).replace("|", "\\|")

            # Enhanced odds and sources display with quality indicators
            verification_sources = []
            if isinstance(verification_result_data, dict):
                verification_sources = verification_result_data.get("sources", [])
            
            # Fallback to claim evidence if verification sources not available
            if not verification_sources and isinstance(claim.evidence, list):
                verification_sources = claim.evidence
            
            num_sources = len(verification_sources)
            prob_true_pct = probabilities.get('TRUE', 0.0) * 100
            prob_false_pct = probabilities.get('FALSE', 0.0) * 100
            prob_uncertain_pct = probabilities.get('UNCERTAIN', 0.0) * 100

            # Generate quality indicators for sources
            quality_indicators = generate_source_quality_indicators(verification_sources)
            
            claim_id_str_for_link = f"claim_{i}"
            # Use anchor link to embedded sources
            source_link = f"[{num_sources} sources](#sources-for-claim-{i+1})"
            
            # Enhanced display with quality indicators
            odds_sources_raw = f"**True:** {prob_true_pct:.0f}%<br>**False:** {prob_false_pct:.0f}%<br>**Uncertain:** {prob_uncertain_pct:.0f}%<br><br>{quality_indicators}<br>{source_link}"
            odds_sources_cell = odds_sources_raw.replace("|", "\\|")

            report_content.append(
                f"| {time_cell} | {speaker_cell} | {claim_text_cell} | {initial_assessment_cell} | {result_cell} | {explanation_cell} | {odds_sources_cell} |"
            )

    report_content.append("")

    # --- 7. Sources --- (Embedded details)
    report_content.append("## 7. Sources")
    if not report.claims_breakdown:
         report_content.append("No claims were analyzed, so no specific sources are listed.")
    else:
        for i, claim in enumerate(report.claims_breakdown):
            # Get evidence
            claim_evidence = []
            if claim.verification_result and isinstance(claim.verification_result, dict):
                claim_evidence = claim.verification_result.get("sources", [])
            if not claim_evidence and isinstance(claim.evidence, list):
                claim_evidence = claim.evidence

            # Generate source content
            source_html = "<ul>"
            if not claim_evidence:
                source_html += "<li>No evidence sources were provided for this claim.</li>"
            else:
                for src_idx, source in enumerate(claim_evidence):
                    url = ''
                    title = ''
                    text = ''
                    
                    if isinstance(source, str):
                        url = source
                        title = source
                    elif isinstance(source, dict):
                        url = source.get('url', '')
                        title = source.get('title', source.get('source_name', url or 'Source Detail'))
                        text = source.get('text', source.get('snippet', ''))
                    else:
                        url = getattr(source, 'url', '') or ''
                        title = getattr(source, 'title', '') or getattr(source, 'source_name', '') or url or 'Source Detail'
                        text = getattr(source, 'text', '') or getattr(source, 'snippet', '') or ''

                    if url:
                        item = f'<a href="{url}" target="_blank">{title}</a>'
                    else:
                        item = f'{title}'
                    
                    if text:
                        item += f'<br><em>{text}</em>'
                    
                    source_html += f"<li>{item}</li>"
            source_html += "</ul>"

            report_content.append(f"""
<details id="sources-for-claim-{i+1}">
<summary><strong>Claim {i+1} Sources</strong> ({claim.timestamp})</summary>
<br>
<strong>Claim:</strong> {claim.claim_text}
<br><br>
{source_html}
</details>
<br>
""")

    report_content.append("")

    # --- 8. Counter-Intelligence Analysis --- (SHERLOCK ENHANCED - Embedded)
    report_content.append("## 8. Counter-Intelligence Analysis")
    
    # 🎯 SHERLOCK: Enhanced counter-intelligence data extraction
    youtube_counter_intel = getattr(report, 'youtube_counter_intelligence', [])
    press_release_counter = getattr(report, 'press_release_counter_intelligence', [])
    
    # Also check claims for counter-intelligence evidence and get enhanced statistics
    claims = getattr(report, 'claims_breakdown', [])
    youtube_evidence_count = 0
    press_release_evidence_count = 0
    youtube_total_views = 0
    high_credibility_youtube = 0
    
    for claim in claims:
        if hasattr(claim, 'explanation') and claim.explanation:
            explanation_text = str(claim.explanation).lower()
            if 'youtube counter-intelligence' in explanation_text or 'youtube counter' in explanation_text:
                youtube_evidence_count += 1
            if 'press release' in explanation_text or 'press release counter' in explanation_text:
                press_release_evidence_count += 1
    
    # Extract YouTube statistics for analysis summary
    for video in youtube_counter_intel:
        if isinstance(video, dict):
            view_count = video.get('view_count', 0) or video.get('detailed_stats', {}).get('view_count', 0)
            youtube_total_views += view_count
            if view_count > 10000:
                high_credibility_youtube += 1
    
    if youtube_counter_intel or press_release_counter or youtube_evidence_count > 0 or press_release_evidence_count > 0:
        # 🎯 DEMO: Analysis Summary section
        report_content.append("### Analysis Summary")
        report_content.append("")
        
        if total_yt > 0:
            avg_views = youtube_total_views // max(total_yt, 1) if youtube_total_views > 0 else 0
            counter_strong = high_credibility_youtube
            counter_limited = total_yt - high_credibility_youtube
            
            summary_text = f"**YouTube Counter-Intelligence**: {total_yt} independent YouTube videos were analyzed"
            if counter_strong > 0 and counter_limited > 0:
                summary_text += f", with {counter_strong} providing strong counter-evidence and {counter_limited} offering limited supporting evidence"
            elif counter_strong > 0:
                summary_text += f", with {counter_strong} providing strong counter-evidence"
            
            if avg_views > 0:
                summary_text += f". Counter-intelligence videos had an average view count of {avg_views:,}"
            
            if counter_strong >= total_yt * 0.7:  # 70% or more negative
                summary_text += " and consistently identified the content as misleading or fraudulent"
            
            summary_text += "."
            report_content.append(summary_text)
            report_content.append("")
        
        if total_pr > 0:
            pr_summary = f"**Press Release Counter-Intelligence**: {total_pr} press releases were analyzed, "
            if total_pr == 1:
                pr_summary += "identified as self-referential promotional content with zero independent validation value."
            else:
                pr_summary += "both identified as self-referential promotional content with zero independent validation value."
            report_content.append(pr_summary)
            report_content.append("")
        
        # Embed the details tables directly
        
        # YouTube Details
        if total_yt > 0:
            yt_rows = ""
            for i, video in enumerate(youtube_counter_intel):
                if isinstance(video, dict):
                    title = video.get('title', 'Unknown')
                    url = video.get('url', '#')
                    views = video.get('view_count', 0) or video.get('detailed_stats', {}).get('view_count', 0)
                    channel = video.get('channel_title', video.get('channel', 'Unknown'))
                    yt_rows += f"<tr><td><a href='{url}' target='_blank'>{title}</a></td><td>{channel}</td><td>{views:,}</td></tr>"
            
            if yt_rows:
                report_content.append(f"""
<details>
<summary><strong>YouTube Counter-Intelligence Details ({total_yt} Videos)</strong></summary>
<br>
<table>
<thead><tr><th>Video</th><th>Channel</th><th>Views</th></tr></thead>
<tbody>
{yt_rows}
</tbody>
</table>
</details>
<br>
""")

        # Press Release Details
        if total_pr > 0:
            pr_rows = ""
            for i, pr in enumerate(press_release_counter):
                if isinstance(pr, dict):
                    title = pr.get('title', 'Unknown')
                    url = pr.get('url', '#')
                    source = pr.get('source', 'Unknown')
                    pr_rows += f"<tr><td><a href='{url}' target='_blank'>{title}</a></td><td>{source}</td></tr>"
            
            if pr_rows:
                report_content.append(f"""
<details>
<summary><strong>Press Release Counter-Intelligence Details ({total_pr} Releases)</strong></summary>
<br>
<table>
<thead><tr><th>Title</th><th>Source</th></tr></thead>
<tbody>
{pr_rows}
</tbody>
</table>
</details>
<br>
""")

    else:
        report_content.append("No counter-intelligence analysis data was available for this report.")
        report_content.append("")

    # --- 9. CRAAP Analysis --- (Renumbered)
    report_content.append("## 9. CRAAP Analysis")
    if report.craap_analysis and isinstance(report.craap_analysis, dict):
        report_content.append("| Criterion | Score | Explanation |")
        report_content.append("|:----------|:------|:------------|")
        for criterion, analysis_data in report.craap_analysis.items():
             level = "N/A"
             explanation = "N/A"
             if isinstance(analysis_data, (list, tuple)) and len(analysis_data) == 2:
                  level, explanation = analysis_data
             elif isinstance(analysis_data, dict):
                  level = analysis_data.get('level', 'N/A')
                  explanation = analysis_data.get('explanation', 'N/A')

             criterion_cell = str(criterion or "N/A").capitalize().replace("|", "\\|").replace("\n", "<br>")
             level_cell = str(level or "N/A").replace("|", "\\|").replace("\n", "<br>")
             explanation_cell = str(explanation or "N/A").replace("|", "\\|").replace("\n", "<br>")
             report_content.append(f"| {criterion_cell} | {level_cell} | {explanation_cell} |")
    else:
         report_content.append("CRAAP analysis data is not available or in the expected format for this report.")

    report_content.append("")

    # --- 9. Recommendations --- (Renumbered)
    report_content.append("## 9. Recommendations")
    
    # Handle both dictionary and object access patterns
    recommendations = None
    if hasattr(report, 'recommendations'):
        recommendations = report.recommendations
    elif isinstance(report, dict):
        recommendations = report.get("recommendations")
    
    if recommendations and len(recommendations) > 0:
        report_content.append("")
        for i, rec in enumerate(recommendations, 1):
            rec_text = str(rec or "N/A").replace("|", "\\|").replace("\n", "<br>")
            report_content.append(f"{i}. {rec_text}")
        report_content.append("")
    else:
        # Provide default recommendations based on truthfulness assessment
        report_content.append("")
        report_content.append("1. Verify information from reputable sources before making decisions")
        report_content.append("2. Consult experts in the field for professional advice")  
        report_content.append("3. Be cautious of claims that seem too good to be true")
        report_content.append("4. Cross-reference information with multiple independent sources")
        report_content.append("")

    # NOTE: Removed end-of-report redundant evidence and verdict sections per product request.

    # Join all parts with single newlines
    return "\n".join(report_content)



# (No example usage needed here, it's called by other modules) 