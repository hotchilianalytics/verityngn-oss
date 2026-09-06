# services/report/markdown_generator.py
import html
import logging
import os
import pathlib
import re
from typing import List, Dict, Tuple, Any, Union, Literal

ReportTier = Literal["public", "private", "original"]
from urllib.parse import urlparse
from datetime import datetime
from pathlib import Path

from verityngn.models.workflow import InitialAnalysisState
from verityngn.models.report import VerityReport, Claim
from verityngn.services.report.category_mappings import (
    ensure_category_mappings,
    claim_verdict_display_label,
    VERDICT_BUCKET_LABELS,
    LLM_PLATFORM_VISIBLE_NOTICE,
    VERDICT_KEY_TO_LABEL,
    _verdict_counts,
    compute_overall_verdict_label,
)
from verityngn.services.report.display_labels import (
    claim_modality_display_label,
    is_visual_only_claim,
)

from verityngn.config.settings import OUTPUTS_DIR, COMPARE_DIR, DOWNLOADS_DIR, DEBUG_OUTPUTS
from verityngn.utils.third_party_logging import configure_third_party_loggers
from verityngn.services.reputation.url_safety import filter_safe_urls, is_safe_url

configure_third_party_loggers()


def _esc(text: Any) -> str:
    """HTML-escape user/LLM-derived text for raw HTML blocks."""
    if text is None:
        return ""
    return html.escape(str(text), quote=True)


def _safe_source_link(url: str, title: str) -> str:
    """Return an escaped <a> tag or plain escaped title if URL is unsafe."""
    title_esc = _esc(title or url or "Source")
    if url and is_safe_url(url):
        return f'<a href="{_esc(url)}" target="_blank" rel="noopener noreferrer">{title_esc}</a>'
    return title_esc if title_esc else ""


def _scrub_public_craap_explanation(text: str) -> str:
    """Remove digit-percent patterns from CRAAP explanations (public report; JSON unchanged)."""
    if not text:
        return text
    out = str(text)
    out = re.sub(r"\b\d{1,3}\.\d+\s*%", "[rate omitted]", out)
    out = re.sub(r"\b\d{1,3}\s*%(?![A-Za-z])", "[rate omitted]", out)
    out = re.sub(r"\b\d+\s+of\s+\d+\b", "[proportion omitted]", out, flags=re.I)
    out = re.sub(r"\(\d+\s+out\s+of\s+\d+\)", "(proportion omitted)", out, flags=re.I)
    out = re.sub(
        r"\b\d+\s+(claim|claims|sources?|videos?|releases?)\b",
        "[count omitted]",
        out,
        flags=re.I,
    )
    out = re.sub(r"\((?:HIGHLY_)?LIKELY_(?:TRUE|FALSE)\s*\(\d+\)\)", "(verdict)", out, flags=re.I)
    return out


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
    """Summarize counter-intelligence impact in narrative form (no percentages)."""
    if not counter_intel_boosts:
        return ""

    summaries = []
    for boost in counter_intel_boosts:
        adjustment = boost.get("probability_adjustment", 0)
        boost_type = boost.get("type", "unknown")
        if abs(adjustment) > 0.1:
            if boost_type == "youtube_counter":
                summaries.append("YouTube counter-evidence materially reduced confidence in this claim")
            elif boost_type == "press_release_counter":
                summaries.append("Press-release style counter-evidence materially reduced confidence in this claim")

    return ". ".join(summaries) + "." if summaries else ""

def explain_confidence_level(prob_dist, sources):
    """Explain the confidence level based on probabilities (no source counts)."""
    if not prob_dist:
        return ""

    true_prob = prob_dist.get("TRUE", 0.0) * 100
    false_prob = prob_dist.get("FALSE", 0.0) * 100

    if max(true_prob, false_prob) > 70:
        confidence_level = "high"
    elif max(true_prob, false_prob) > 50:
        confidence_level = "moderate"
    else:
        confidence_level = "low"

    if true_prob > false_prob:
        return f"Assessment shows {confidence_level} confidence in claim validity based on cited evidence."
    return f"Assessment shows {confidence_level} confidence that the claim is problematic based on cited evidence."

def generate_source_quality_indicators(sources):
    """Qualitative source signal only (no counts)."""
    if not sources:
        return "No sources"

    scientific_count = count_scientific_sources(sources)
    medical_count = count_medical_sources(sources)
    government_count = count_government_sources(sources)
    news_present = educational_present = 0
    for source in sources:
        if isinstance(source, str):
            source_lower = source.lower()
        else:
            url = getattr(source, "url", "") or ""
            source_type = getattr(source, "source_type", "") or ""
            source_lower = str(url + " " + source_type).lower()
        if any(
            term in source_lower
            for term in ["reuters.com", "apnews.com", "bbc.", "nytimes.", "wsj.", "cnn.", "news"]
        ):
            news_present += 1
        elif any(term in source_lower for term in [".edu", "university", "academic"]):
            educational_present += 1

    tags = []
    if scientific_count > 0:
        tags.append("Scientific or research-oriented sources present")
    if medical_count > 0:
        tags.append("Clinical or medical-domain sources present")
    if government_count > 0:
        tags.append("Government or official sources present")
    if educational_present > 0:
        tags.append("Academic-domain sources present")
    if news_present > 0:
        tags.append("News-media sources present")

    total_sources = len(sources)
    high_signal = scientific_count + medical_count + government_count + educational_present
    quality_ratio = high_signal / total_sources if total_sources > 0 else 0
    if quality_ratio > 0.7:
        quality_badge = "Strong institutional signal"
    elif quality_ratio > 0.4:
        quality_badge = "Mixed institutional and general web signal"
    else:
        quality_badge = "Mostly general web signal"

    if tags:
        return f"{quality_badge}<br>{' • '.join(tags)}"
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


def _format_probability_cell(verification_result: dict) -> str:
    """Compact probability column for private per-claim tables."""
    if not verification_result or not isinstance(verification_result, dict):
        return "—"
    prob_dist = verification_result.get("probability_distribution") or {}
    if not prob_dist:
        return str(verification_result.get("result", "—"))
    parts = []
    for outcome in ("TRUE", "FALSE", "UNCERTAIN"):
        val = prob_dist.get(outcome)
        if val is not None:
            try:
                parts.append(f"{outcome} {float(val) * 100:.0f}%")
            except (TypeError, ValueError):
                continue
    return " · ".join(parts) if parts else str(verification_result.get("result", "—"))


def format_tier_breakdown_and_badges(
    verification_result: dict,
    *,
    tier: ReportTier = "public",
) -> Tuple[str, str]:
    """
    Tier summary for claim context. Public: qualitative only. Private: includes shares.
    Returns (tier_summary_md, badge_md). Empty strings if no tier_breakdown.
    """
    if not verification_result or not isinstance(verification_result, dict):
        return "", ""
    breakdown = verification_result.get("tier_breakdown") or {}
    t1 = breakdown.get("tier_1", 0) or 0
    t2 = breakdown.get("tier_2", 0) or 0
    t3 = breakdown.get("tier_3", 0) or 0
    t4 = breakdown.get("tier_4", 0) or 0
    t5 = breakdown.get("tier_5", 0) or 0
    total = t1 + t2 + t3 + t4 + t5
    if total == 0:
        return "", ""
    if tier in ("private", "original"):
        summary = (
            f"T1 {t1 / total * 100:.0f}% · T2 {t2 / total * 100:.0f}% · "
            f"T3 {t3 / total * 100:.0f}% · T4 {t4 / total * 100:.0f}% · T5 {t5 / total * 100:.0f}%"
        )
        return summary, ""
    share_top = (t1 + t2) / total
    share_t5 = t5 / total
    summary = "Mixed evidence tiers"
    if share_top >= 0.4:
        summary = "Mostly higher-tier (academic and official) sources"
    elif share_t5 >= 0.6:
        summary = "Evidence skews toward lower-tier or uncategorized web sources"
    badge = ""
    if share_top >= 0.4:
        badge = " **Stronger institutional sourcing**"
    elif share_t5 >= 0.6:
        badge = " **Weaker evidence base**"
    return summary, badge


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
    
    # 1. Evidence strength overview (no source totals)
    if sources:
        scientific_sources = count_scientific_sources(sources)
        medical_sources = count_medical_sources(sources)
        government_sources = count_government_sources(sources)
        evidence_overview = "Verification drew on multiple external references"
        flavor = []
        if scientific_sources > 0:
            flavor.append("research-oriented material")
        if medical_sources > 0:
            flavor.append("clinical or health-domain material")
        if government_sources > 0:
            flavor.append("official or government material")
        if flavor:
            evidence_overview += ", including " + ", ".join(flavor) + "."
        else:
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
    """Clean explanation for public reports — no extracted counts, percentages, or view totals."""
    if not explanation or explanation == "No explanation provided.":
        return "No verification details available."

    cleaned = re.sub(r"<[^>]+>", "", explanation)
    cleaned = re.sub(r"[📺📰🔬🌐🎬📋🚫→🕵️]{2,}", "", cleaned)
    cleaned = re.sub(
        r"youtube counter-intelligence:.*?(?=\s*🔬|\s*📰|\s*🌐|\s*$)",
        "",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )
    cleaned = re.sub(
        r"press release counter-intelligence:.*?(?=\s*🔬|\s*📰|\s*🌐|\s*$)",
        "",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    core = extract_core_finding(cleaned)
    if core:
        core = re.sub(r"\b\d+\s*%\b", "", core)
        core = re.sub(r"\b\d+\s+of\s+\d+\b", "", core, flags=re.I)
        core = re.sub(r"\s+", " ", core).strip()

    parts = []
    if core:
        parts.append(core)
    el = explanation.lower()
    if "counter" in el or "contradict" in el:
        parts.append("Independent counter-evidence contributed to this assessment.")
    elif "support" in el or "confirm" in el:
        parts.append("Some cited material supports the claim’s factual basis.")
    elif not parts:
        parts.append("Verification analysis completed; see cited sources in Section 7.")

    ci_links = []
    if claim_index is not None and video_id and ("counter" in el or "youtube" in el):
        ci_links.append(f"[Counter-intelligence detail](claim/claim_{claim_index}/counter_intel.html)")
    if ci_links:
        parts.append(ci_links[0])

    return "<br>".join(parts)


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
    content = "# 🕵️ Counter-Intelligence Analysis for Claim\n\n"
    content += f"**Claim ID:** {getattr(claim, 'claim_id', 'N/A')}\n\n"
    content += f"**Timestamp:** {claim.timestamp}\n\n"
    content += f"**Speaker:** {claim.speaker}\n\n"
    content += f"**Claim:** {claim.claim_text}\n\n"
    content += f"**Initial Assessment:** {claim.initial_assessment}\n\n"

    explanation = str(claim.explanation or "")

    # YouTube Counter-Intelligence Section (no view counts, confidence %, or “found N” tallies)
    content += "## 📺 YouTube Counter-Intelligence\n\n"

    youtube_videos = counter_intel_data.get("youtube_videos", [])
    if youtube_videos:
        for i, video in enumerate(youtube_videos):
            content += f"### Video {i+1}: {video.get('title', 'Unknown Title')}\n\n"
            content += f"**URL:** [{video.get('url', '#')}]({video.get('url', '#')})\n\n"
            content += f"**Channel:** {video.get('channel_title', 'Unknown Channel')}\n\n"
            content += f"**Stance:** {video.get('stance', 'Unknown')}\n\n"

            key_points = video.get("key_points", [])
            if key_points:
                content += "**Key Counter-Arguments:**\n\n"
                for point in key_points[:3]:
                    content += f"- {point}\n"
                content += "\n"

            vid = video.get("id", "")
            if vid:
                content += f"**Detailed Analysis:** [View summary JSON](counter_intelligence/{vid}/summary.json)\n\n"

            content += "---\n\n"
    else:
        content += "No YouTube counter-intelligence linked for this claim.\n\n"

    content += "## Press Release Counter-Intelligence\n\n"

    press_releases = counter_intel_data.get("press_releases", [])
    if press_releases:
        for i, release in enumerate(press_releases):
            content += f"### Press Release {i+1}: {release.get('title', 'Unknown Title')}\n\n"
            content += f"**URL:** [{release.get('url', '#')}]({release.get('url', '#')})\n\n"
            content += f"**Source:** {release.get('source', 'Unknown Source')}\n\n"
            content += f"**Date:** {release.get('date', 'Unknown Date')}\n\n"
            cred_impact = release.get("credibility_impact", "Unknown")
            if isinstance(cred_impact, str) and "%" not in cred_impact:
                content += f"**Credibility Impact:** {cred_impact}\n\n"

            key_findings = release.get("key_findings", [])
            if key_findings:
                content += "**Key Findings:**\n\n"
                for finding in key_findings[:3]:
                    content += f"- {finding}\n"
                content += "\n"

            content += "---\n\n"
    else:
        content += "No press release counter-intelligence linked for this claim.\n\n"

    content += "## Counter-Intelligence Impact Summary\n\n"
    if youtube_videos or press_releases:
        content += (
            "**Assessment:** Counter-intelligence material was reviewed and factored into the editorial "
            "reliability judgment for this claim.\n\n"
        )
    else:
        content += "**Assessment:** No counter-intelligence package was associated with this claim.\n\n"
    
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


def _claim_source_items(claim) -> list:
    """Normalized evidence list for a claim (safe URLs only).

    Prefer verification_result.sources; fall back to claim.evidence and
    nested evidence blobs so Section 7 is not empty when cite-only was soft.
    """
    claim_evidence = []
    vr = claim.verification_result if claim.verification_result else None
    if isinstance(vr, dict):
        claim_evidence = list(vr.get("sources") or [])
        if not claim_evidence:
            # Nested evidence list (dicts with url) from verification_result
            nested = vr.get("evidence")
            if isinstance(nested, list):
                claim_evidence = nested
            elif isinstance(nested, str) and "http" in nested:
                # Pull bare URLs out of the evidence summary text as last resort
                import re

                claim_evidence = re.findall(r"https?://[^\s\\)\"]+", nested)[:8]
    if not claim_evidence and isinstance(claim.evidence, list):
        claim_evidence = claim.evidence
    return filter_safe_urls(claim_evidence)


def _source_dict(source) -> tuple[str, str, str]:
    """Return (url, title, text) from a source entry."""
    if isinstance(source, str):
        return source, source, ""
    if isinstance(source, dict):
        url = source.get("url", "")
        title = source.get("title", source.get("source_name", url or "Source Detail"))
        text = source.get("text", source.get("snippet", ""))
        return url, title, text
    url = getattr(source, "url", "") or ""
    title = getattr(source, "title", "") or getattr(source, "source_name", "") or url or "Source Detail"
    text = getattr(source, "text", "") or getattr(source, "snippet", "") or ""
    return url, title, text


def _build_sources_section_lines(report: VerityReport) -> List[str]:
    """Section 7 accordion HTML for standard reports."""
    lines: List[str] = ["## 7. Sources"]
    if not report.claims_breakdown:
        lines.append("No claims were analyzed, so no specific sources are listed.")
        lines.append("")
        return lines

    for i, claim in enumerate(report.claims_breakdown):
        claim_evidence = _claim_source_items(claim)
        source_html = "<ul>"
        if not claim_evidence:
            source_html += "<li>No evidence sources were provided for this claim.</li>"
        else:
            for source in claim_evidence:
                url, title, text = _source_dict(source)
                if url and is_safe_url(url):
                    item = _safe_source_link(url, title)
                elif title:
                    item = _esc(title)
                else:
                    continue
                if text:
                    item += f"<br><em>{_esc(text)}</em>"
                source_html += f"<li>{item}</li>"
        source_html += "</ul>"

        details_style = "border: 1px solid #e1e4e8; border-radius: 6px; padding: 0; margin-bottom: 16px; background-color: #fff;"
        summary_style = "cursor: pointer; padding: 12px 16px; background-color: #f6f8fa; border-radius: 6px; font-weight: 600; outline: none; list-style: none;"
        content_style = "padding: 16px; border-top: 1px solid #e1e4e8;"
        claim_text_esc = _esc(claim.claim_text)
        ts_esc = _esc(claim.timestamp)

        lines.append(f"""
<details id="sources-for-claim-{i+1}" style="{details_style}">
<summary style="{summary_style}">▶ Claim {i+1} Sources <span style="font-weight: normal; color: #586069;">({ts_esc})</span></summary>
<div style="{content_style}">
<p><strong>Claim:</strong> {claim_text_esc}</p>
{source_html}
</div>
</details>
""")
    lines.append("")
    return lines


def generate_sources_appendix(report: VerityReport) -> str:
    """
    Markdown appendix of per-claim sources (for combined reports).
    Uses anchor ids matching in-report #sources-for-claim-N links.
    """
    lines = ["## Appendix: Sources", ""]
    if not report.claims_breakdown:
        lines.append("_No claims were analyzed, so no sources are listed._")
        return "\n".join(lines)

    for i, claim in enumerate(report.claims_breakdown):
        claim_evidence = _claim_source_items(claim)
        ts = claim.timestamp or "—"
        lines.append(f'<a id="sources-for-claim-{i+1}"></a>')
        lines.append(f"### Claim {i+1} — {ts}")
        lines.append("")
        lines.append(f"**Claim:** {claim.claim_text}")
        lines.append("")
        if not claim_evidence:
            lines.append("_No evidence sources were provided for this claim._")
        else:
            for source in claim_evidence:
                url, title, text = _source_dict(source)
                if url and is_safe_url(url):
                    lines.append(f"- [{title}]({url})")
                elif title:
                    lines.append(f"- {title}")
                else:
                    continue
                if text:
                    lines.append(f"  - _{text}_")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _build_original_header(report: VerityReport) -> List[str]:
    """Pre-compliance header: title, thumbnail embed, and YouTube description."""
    media = report.media_embed
    video_id = media.video_id if media else "unknown_id"
    title = (media.title if media and media.title else None) or report.title or f"Video {video_id}"
    video_url = (media.video_url if media and media.video_url else None) or f"https://www.youtube.com/watch?v={video_id}"
    thumbnail = (
        (media.thumbnail_url if media and media.thumbnail_url else None)
        or f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
    )
    description = (media.description if media and media.description else None) or report.description or ""
    desc_html = html.escape(description).replace("\n", "<br>")

    return [
        f"# {title}",
        "",
        '<div class="video-embed">',
        f'    <a href="{video_url}" target="_blank">',
        f'        <img src="{thumbnail}" alt="Video thumbnail for {html.escape(title)}" width="560" style="max-width: 100%; height: auto;" />',
        "    </a>",
        f"    <p>Video ID: {video_id}</p>",
        "</div><!-- VIDEO_CONTAINER_END -->",
        "",
        "## Internal YouTube Description",
        "",
        desc_html,
        "",
    ]


def _build_original_executive_summary(report: VerityReport) -> List[str]:
    """Numeric executive summary for user-controlled original reports."""
    claims = report.claims_breakdown or []
    total = len(claims)
    vc = _verdict_counts(claims)
    lines = ["## Executive Summary", "", f"Total Claims: {total}"]

    for key, label in VERDICT_KEY_TO_LABEL.items():
        if key == "UNVERIFIABLE":
            continue
        count = vc.get(key, 0)
        lines.append(f"- {label}: {count}")

    pr_count = getattr(report, "press_release_count", 0) or 0
    yt_count = getattr(report, "youtube_response_count", 0) or 0
    lines.extend(
        [
            "",
            f"Claims with Press Release/Newswire Evidence: {pr_count}",
            f"Claims with YouTube Counter-Intelligence Evidence: {yt_count}",
            "",
        ]
    )
    return lines


def _build_verdict_percentage_table(claims: List[Claim]) -> List[str]:
    """Overall claim-risk count/percentage table for original reports."""
    total = len(claims)
    if total == 0:
        return ["| Category | Count | Percentage |", "|:---------|:-----:|:----------:|", "| Total Claims | 0 | 100% |", ""]

    vc = _verdict_counts(claims)
    lines = [
        "| Category | Count | Percentage |",
        "|:---------|:-----:|:----------:|",
        f"| Total Claims | {total} | 100% |",
    ]
    for key, label in VERDICT_KEY_TO_LABEL.items():
        if key == "UNVERIFIABLE":
            continue
        count = vc.get(key, 0)
        pct = count / total * 100
        lines.append(f"| {label} | {count} | {pct:.1f}% |")
    lines.append("")
    return lines


def generate_markdown_report(
    report: VerityReport,
    *,
    tier: ReportTier = "private",
) -> Tuple[str, Dict[str, str], Dict[str, str]]:
    """
    Generate the complete markdown report with embedded claim sources and counter-intelligence.
    Returns main content. Separate file dictionaries are returned empty as content is now embedded.

    tier=private: full CRAAP text, per-claim probability column (persisted user reports).
    tier=public: scrubbed CRAAP and no probability column (legacy public markdown path).
    """
    logger = logging.getLogger(__name__)
    try:
        # Generate the main report content with embedded sources
        main_content = generate_main_report_content(report, tier=tier)

        # Return empty dicts for separate files as they are now embedded
        # We keep the signature for compatibility
        return main_content, {}, {}

    except Exception as e:
        logger.error(f"Error generating markdown report: {e}", exc_info=True)
        # Return minimal content in case of error during generation
        error_content = f"# Report Generation Error\n\nAn error occurred: {e}\n\nGenerated by VerityNgn on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        return error_content, {}, {}

def generate_main_report_content(report: VerityReport, *, tier: ReportTier = "private", omit_video_header: bool = False, omit_sources: bool = False) -> str:
    """
    Generate the main report content in memory.
    
    Args:
        report (VerityReport): The report containing claims and report data
        
    Returns:
        str: Markdown content for the main report
    """
    logger = logging.getLogger(__name__)
    report_content = []
    cm = ensure_category_mappings(report)
    narrative = cm.get("narrative") or {}
    overall_verdict = cm.get("overall_verdict_label") or "Undetermined (No Claims)"
    disclaimer = cm.get("independent_research_disclaimer") or (
        "This assessment is independent editorial research by HotChili Analytics, LLC. "
        "It is not provided, endorsed, or calculated by YouTube or Google."
    )
    llm_notice = cm.get("llm_platform_visible_notice") or LLM_PLATFORM_VISIBLE_NOTICE
    user_controlled_notice = None
    if tier == "original":
        from verityngn.services.report.notices import PRIVATE_IN_REPORT_NOTICE

        user_controlled_notice = PRIVATE_IN_REPORT_NOTICE
    elif tier == "private":
        from verityngn.services.report.notices import PRIVATE_IN_REPORT_NOTICE

        user_controlled_notice = PRIVATE_IN_REPORT_NOTICE
    if not report.claims_breakdown:
        logger.warning("No claims found in the report for markdown generation.")

    # --- Build Report Sections ---

    media_embed = report.media_embed
    video_id = media_embed.video_id if media_embed else "unknown_id"
    source_info_hash = report.source_info_hash or "(unavailable)"
    report_generated_at = report.report_generated_at or "(unavailable)"
    claims_breakdown_list = report.claims_breakdown or []

    if tier == "original":
        if not omit_video_header:
            report_content.extend(_build_original_header(report))
        if user_controlled_notice:
            report_content.append(f"> **Notice:** {user_controlled_notice}")
            report_content.append("")
        report_content.extend(_build_original_executive_summary(report))
        overall_verdict = compute_overall_verdict_label(claims_breakdown_list)
        report_content.append(f"## 2. Overall Claim Risk Assessment: {overall_verdict}")
        report_content.extend(_build_verdict_percentage_table(claims_breakdown_list))
    else:
        notice_block = f"> **Notice:** {llm_notice}\n\n"
        if user_controlled_notice and tier == "private":
            notice_block += f"> **Private report:** {user_controlled_notice}\n\n"
        report_content.append(f"""# Verity Report

{notice_block}| Field | Value |
|---|---|
| Video ID | `{video_id}` |
| Source Info Hash | `{source_info_hash}` |
| Report Generated | `{report_generated_at}` |

""")

        # --- Section 1: Executive Summary (narrative only; numerics live in JSON) ---
        report_content.append("## Executive Summary")
        report_content.append("")
        report_content.append(narrative.get("executive_paragraph") or "")
        report_content.append("")

        # --- 2. Overall Claim Risk Assessment ---
        report_content.append(f"## 2. Overall Claim Risk Assessment: {overall_verdict}")
        report_content.append(f"_{disclaimer}_")
        report_content.append("")
        report_content.append(narrative.get("overall_assessment_sentence") or "")
        report_content.append("")

    # --- 3. Summary of Key Findings --- (qualitative descriptors from category_mappings)
    report_content.append("## 3. Summary of Key Findings")
    report_content.append("| Category | Description (qualitative) | Impact |")
    report_content.append("|:---------|:--------------------------|:-------|")
    report_content.append(
        f"| Overall Assessment | {overall_verdict} | Provides context for the overall message reliability. |"
    )
    report_content.append(
        f"| Evidence Quality | {narrative.get('evidence_quality', 'Mixed')} | "
        f"Affects the confidence level of verification results. |"
    )
    report_content.append(
        f"| Verification Status | {narrative.get('verification_status', 'Most claims assessed')} | "
        f"Indicates whether a determinative assessment was reached for each claim. |"
    )
    report_content.append(
        f"| Source Diversity | {narrative.get('source_diversity', 'Multiple categories')} | "
        f"Broader diversity can enhance reliability. |"
    )
    report_content.append(
        f"| Time Distribution | {narrative.get('time_distribution', 'Across the video runtime')} | "
        f"Helps identify pattern and concentration of claims. |"
    )
    report_content.append("")

    # --- 4. Key Findings Identified --- (Specific findings generated by agent/logic)
    report_content.append("## 4. Key Findings Identified")
    if report.key_findings:
        report_content.append("| Category | Description |")
        report_content.append("|:---------|:------------|")
        for finding in report.key_findings:
            # Prepare cell content separately, escaping pipes and using <br> for newlines
            category_cell = str(finding.category or "N/A").replace("|", "\\|").replace("\n", "<br>")
            desc_raw = str(finding.description or "N/A")
            if tier == "public":
                desc_raw = _scrub_public_craap_explanation(desc_raw)
            description_cell = desc_raw.replace("|", "\\|").replace("\n", "<br>")
            report_content.append(f"| {category_cell} | {description_cell} |")
        report_content.append("")
    else:
        report_content.append("No specific key findings were generated for this report.")
        report_content.append("")

    # --- 5. Evidence Summary --- (category list only; no counts)
    report_content.append("## 5. Evidence Summary")
    report_content.append("### Source categories cited in this report")
    cats = cm.get("evidence_categories_present") or []
    if not cats:
        report_content.append(
            "No external source categories were cataloged for this run; see Section 7 for any cited references."
        )
    else:
        if len(cats) == 1:
            cat_line = cats[0]
        elif len(cats) == 2:
            cat_line = f"{cats[0]} and {cats[1]}"
        else:
            cat_line = ", ".join(cats[:-1]) + f", and {cats[-1]}"
        report_content.append(
            f"Evidence cited in this report draws from the following source categories: {cat_line}. "
            "Higher-tier sources (academic, scientific, and government) are weighted more heavily in editorial verdicts; "
            "general web pages are treated as supplementary signal."
        )
    report_content.append("")

    # --- 6. Claims Breakdown with Verification Results --- (Renumbered)
    # Fix 5: Split out unverifiable (pre-filtered) claims for a separate subsection
    def _claim_result(c):
        vr = getattr(c, "verification_result", None) if hasattr(c, "verification_result") else None
        if vr is None and isinstance(c, dict):
            vr = c.get("verification_result")
        return (vr or {}).get("result") if isinstance(vr, dict) else None

    claims_breakdown_list = report.claims_breakdown or []
    unverifiable_claims = [c for c in claims_breakdown_list if _claim_result(c) == "UNVERIFIABLE"]

    report_content.append("## 6. Claims Breakdown with Verification Results")
    report_content.append(
        "*This section shows primary video analysis claims. Counter-intelligence context appears in Section 8.*"
    )
    report_content.append("")
    if not report.claims_breakdown:
        report_content.append("No claims were available for breakdown.")
    else:
        # --- 6.0 Grouped narrative (verdict buckets) ---
        report_content.append("### 6.0 Findings Grouped by Verdict")
        report_content.append("")
        buckets = cm.get("verdict_buckets") or {}
        by_id = {c.claim_id: c for c in claims_breakdown_list}
        for label in VERDICT_BUCKET_LABELS:
            ids = buckets.get(label) or []
            if not ids:
                continue
            report_content.append(f"#### {label}")
            for cid in sorted(ids):
                c = by_id.get(cid)
                if not c:
                    continue
                ts = str(c.timestamp or "-").strip()
                txt = str(c.claim_text or "").strip()
                report_content.append(f"- ({ts}) {txt}")
            report_content.append("")

        # --- 6.1 Per-claim detail ---
        report_content.append("### 6.1 Per-Claim Detail")
        report_content.append("")
        visual_only_n = sum(
            1
            for c in claims_breakdown_list
            if is_visual_only_claim(getattr(c, "source_type", None))
        )
        if visual_only_n:
            report_content.append(
                f"*Multimodal: **{visual_only_n}** claim(s) sourced from on-screen text, charts, or demos "
                f"(not spoken in transcript alone).*"
            )
            report_content.append("")
        if tier in ("private", "original"):
            report_content.append("| # | Time | Modality | Verdict | Probability | Claim | Sources |")
            report_content.append("|:--:|:----:|:---------|:--------|:------------|:------|:--------|")
        else:
            report_content.append("| # | Time | Modality | Verdict | Claim | Sources |")
            report_content.append("|:--:|:----:|:---------|:--------|:------|:--------|")
        for orig_idx, claim in enumerate(claims_breakdown_list):
            time_cell = str(claim.timestamp or "-").replace("|", "\\|").replace("\n", " ")
            claim_text_cell = str(claim.claim_text or "N/A").replace("|", "\\|").replace("\n", " ")
            verdict_cell = claim_verdict_display_label(claim).replace("|", "\\|")
            modality_cell = claim_modality_display_label(getattr(claim, "source_type", None)).replace("|", "\\|")
            source_link = f"[Sources](#sources-for-claim-{orig_idx+1})"
            vr = getattr(claim, "verification_result", None) or {}
            if tier in ("private", "original"):
                prob_cell = _format_probability_cell(vr if isinstance(vr, dict) else {}).replace("|", "\\|")
                report_content.append(
                    f"| {orig_idx + 1} | {time_cell} | {modality_cell} | {verdict_cell} | {prob_cell} | {claim_text_cell} | {source_link} |"
                )
            else:
                report_content.append(
                    f"| {orig_idx + 1} | {time_cell} | {modality_cell} | {verdict_cell} | {claim_text_cell} | {source_link} |"
                )
        report_content.append("")
        report_content.append(
            "*Each claim was assessed against external sources cited in Section 7.*"
        )
        report_content.append("")

        # Claims Noted But Not Independently Verifiable (pre-filtered; no web research)
        if unverifiable_claims:
            report_content.append("")
            report_content.append("#### 6.2 Claims Noted But Not Independently Verifiable")
            report_content.append("The following claims were not independently verified (promotional, anecdotal, or product-name type). They are listed for completeness only.")
            report_content.append("")
            report_content.append("| Time | Claim | Initial Assessment | Reason |")
            report_content.append("|:----:|:------|:-------------------|:-------|")
            for c in unverifiable_claims:
                ts = getattr(c, "timestamp", None) or (c.get("timestamp") if isinstance(c, dict) else None)
                text = getattr(c, "claim_text", None) or (c.get("claim_text") if isinstance(c, dict) else None)
                assess = getattr(c, "initial_assessment", None) or (c.get("initial_assessment") if isinstance(c, dict) else None)
                vr = getattr(c, "verification_result", None) or (c.get("verification_result") if isinstance(c, dict) else None)
                reason = (vr.get("explanation", "Pre-filtered") if isinstance(vr, dict) else "Pre-filtered")[:80]
                time_cell = str(ts or "-").replace("|", "\\|").replace("\n", " ")
                claim_cell = str(text or "N/A")[:200].replace("|", "\\|").replace("\n", " ")
                assess_cell = str(assess or "N/A")[:100].replace("|", "\\|").replace("\n", " ")
                reason_cell = str(reason or "N/A").replace("|", "\\|").replace("\n", " ")
                report_content.append(f"| {time_cell} | {claim_cell} | {assess_cell} | {reason_cell} |")
            report_content.append("")

    report_content.append("")

    # --- 7. Sources --- (Embedded details; skippable for combined-report appendix)
    if not omit_sources:
        report_content.extend(_build_sources_section_lines(report))

    # --- 8. Counter-Intelligence Analysis (narrative; no view counts or tallies) ---
    report_content.append("## 8. Counter-Intelligence Analysis")

    youtube_counter_intel = getattr(report, "youtube_counter_intelligence", []) or []
    press_release_counter = getattr(report, "press_release_counter_intelligence", []) or []
    claims = getattr(report, "claims_breakdown", []) or []

    youtube_evidence_count = 0
    press_release_evidence_count = 0
    for claim in claims:
        if hasattr(claim, "explanation") and claim.explanation:
            explanation_text = str(claim.explanation).lower()
            if "youtube counter-intelligence" in explanation_text or "youtube counter" in explanation_text:
                youtube_evidence_count += 1
            if "press release" in explanation_text or "press release counter" in explanation_text:
                press_release_evidence_count += 1

    if youtube_counter_intel or press_release_counter or youtube_evidence_count > 0 or press_release_evidence_count > 0:
        report_content.append("### Analysis Summary")
        report_content.append("")
        ci_summary = cm.get("counter_intelligence_summary") or ""
        if tier == "public":
            ci_summary = _scrub_public_craap_explanation(ci_summary)
        report_content.append(ci_summary)
        report_content.append("")

        if youtube_counter_intel:
            report_content.append("#### Independent YouTube sources reviewed")
            report_content.append("")
            for video in youtube_counter_intel:
                if not isinstance(video, dict):
                    continue
                title = video.get("title", "Video")
                url = video.get("url", "")
                if not url or not is_safe_url(url):
                    continue
                channel = video.get("channel_title", video.get("channel", ""))
                ch = f" — *{_esc(channel)}*" if channel else ""
                report_content.append(f"- [{_esc(title)}]({url}){ch}")
            report_content.append("")

            yt_rows = ""
            for video in youtube_counter_intel:
                if isinstance(video, dict):
                    title = video.get("title", "Unknown")
                    url = video.get("url", "")
                    if not url or not is_safe_url(url):
                        continue
                    channel = video.get("channel_title", video.get("channel", "Unknown"))
                    yt_rows += (
                        f"<tr><td>{_safe_source_link(url, title)}</td>"
                        f"<td>{_esc(channel)}</td></tr>"
                    )

            if yt_rows:
                details_style = "border: 1px solid #e1e4e8; border-radius: 6px; padding: 0; margin-bottom: 16px; background-color: #fff;"
                summary_style = "cursor: pointer; padding: 12px 16px; background-color: #f6f8fa; border-radius: 6px; font-weight: 600; outline: none; list-style: none;"
                content_style = "padding: 16px; border-top: 1px solid #e1e4e8;"
                report_content.append(f"""
<details style="{details_style}">
<summary style="{summary_style}">▶ YouTube Counter-Intelligence — Details</summary>
<div style="{content_style}">
<table>
<thead><tr><th>Video</th><th>Channel</th></tr></thead>
<tbody>
{yt_rows}
</tbody>
</table>
</div>
</details>
""")

        if press_release_counter:
            report_content.append("#### Promotional or press-style documents reviewed")
            report_content.append("")
            for pr in press_release_counter:
                if not isinstance(pr, dict):
                    continue
                title = pr.get("title", "Document")
                url = pr.get("url", "")
                if not url or not is_safe_url(url):
                    continue
                report_content.append(f"- [{_esc(title)}]({url})")
            report_content.append("")

            pr_rows = ""
            for pr in press_release_counter:
                if isinstance(pr, dict):
                    title = pr.get("title", "Unknown")
                    url = pr.get("url", "")
                    if not url or not is_safe_url(url):
                        continue
                    source = pr.get("source", "Unknown")
                    pr_rows += (
                        f"<tr><td>{_safe_source_link(url, title)}</td>"
                        f"<td>{_esc(source)}</td></tr>"
                    )

            if pr_rows:
                details_style = "border: 1px solid #e1e4e8; border-radius: 6px; padding: 0; margin-bottom: 16px; background-color: #fff;"
                summary_style = "cursor: pointer; padding: 12px 16px; background-color: #f6f8fa; border-radius: 6px; font-weight: 600; outline: none; list-style: none;"
                content_style = "padding: 16px; border-top: 1px solid #e1e4e8;"
                report_content.append(f"""
<details style="{details_style}">
<summary style="{summary_style}">▶ Press Release Counter-Intelligence — Details</summary>
<div style="{content_style}">
<table>
<thead><tr><th>Title</th><th>Source</th></tr></thead>
<tbody>
{pr_rows}
</tbody>
</table>
</div>
</details>
""")

    else:
        report_content.append("No counter-intelligence analysis data was available for this report.")
        report_content.append("")

    # --- AI & Authenticity Assessment ---
    report_content.append("## 8.5 AI & Authenticity Assessment")
    report_content.append("")
    metadata = getattr(report, "metadata", None) or {}
    ai_disclosure = metadata.get("ai_disclosure", False)
    ai_indicators_detected = metadata.get("ai_indicators_detected", False)
    ai_indicators = metadata.get("ai_indicators", []) or []
    if ai_disclosure:
        report_content.append("**Platform AI disclosure**: This content is labeled by the platform as altered or synthetic.")
        report_content.append("")
    if ai_indicators_detected and ai_indicators:
        report_content.append("**AI artifacts observed**: " + "; ".join(str(x) for x in ai_indicators[:15]))
        report_content.append("")
    if not ai_disclosure and not ai_indicators_detected:
        report_content.append("No AI indicators were detected for this video.")
        report_content.append("")

    # Unverifiable Authority (credential red flags)
    credential_red_flag_claims = []
    for c in getattr(report, "claims_breakdown", []) or []:
        vr = getattr(c, "verification_result", None)
        if isinstance(vr, dict) and vr.get("credential_red_flag"):
            text = getattr(c, "claim_text", None) or (c.get("claim_text", "") if isinstance(c, dict) else "") or ""
            speaker = (getattr(c, "speaker", None) or "") or ""
            credential_red_flag_claims.append((speaker or "Unknown", text[:120] + ("..." if len(text) > 120 else "")))
    if credential_red_flag_claims:
        report_content.append("### Unverifiable Authority")
        report_content.append("")
        report_content.append("The following claims involve speakers who present as Dr./medical authorities but **could not be verified** in professional registries (e.g. healthgrades.com, doximity.com, or official .gov listings). This is a significant red flag for credibility.")
        report_content.append("")
        for speaker, snippet in credential_red_flag_claims:
            report_content.append(f"- **{speaker}**: \"{snippet}\"")
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
             level_str = level.value if hasattr(level, "value") else (level or "N/A")
             level_cell = str(level_str).replace("|", "\\|").replace("\n", "<br>")
             raw_explanation = str(explanation or "N/A")
             if tier == "public":
                 raw_explanation = _scrub_public_craap_explanation(raw_explanation)
             explanation_cell = raw_explanation.replace("|", "\\|").replace("\n", "<br>")
             report_content.append(f"| {criterion_cell} | {level_cell} | {explanation_cell} |")
    else:
         report_content.append("CRAAP analysis data is not available or in the expected format for this report.")

    report_content.append("")

    # --- 9. Recommendations --- (Renumbered)
    report_content.append("## 10. Recommendations")
    
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
        # Synthesize recommendations from verified claim verdicts when none provided
        claims_breakdown = getattr(report, "claims_breakdown", None) or (report.get("claims_breakdown") if isinstance(report, dict) else None)
        synthesized = []
        if claims_breakdown:
            any_false_leaning = False
            any_uncertain = False
            for c in claims_breakdown:
                vr = getattr(c, "verification_result", None) if not isinstance(c, dict) else c.get("verification_result")
                if not vr:
                    continue
                res = (getattr(vr, "result", None) or (vr.get("result") if isinstance(vr, dict) else "")) or ""
                res = str(res).upper()
                if res in ("LIKELY_FALSE", "HIGHLY_LIKELY_FALSE"):
                    any_false_leaning = True
                elif res == "UNCERTAIN":
                    any_uncertain = True
            if any_false_leaning:
                synthesized.append(
                    "Several statements in this video were rated likely or highly likely false under editorial review — "
                    "cross-check key statistics and study citations with primary sources (e.g. published studies, official health bodies)."
                )
            if any_uncertain:
                synthesized.append(
                    "Some statements could not be sufficiently verified — seek independent expert or fact-checker coverage before relying on them."
                )
            synthesized.append("Verify information from reputable sources before making decisions.")
            synthesized.append("Be cautious of claims that seem too good to be true.")
            synthesized.append("Cross-reference information with multiple independent sources.")
        else:
            synthesized = [
                "Verify information from reputable sources before making decisions",
                "Consult experts in the field for professional advice",
                "Be cautious of claims that seem too good to be true",
                "Cross-reference information with multiple independent sources",
            ]
        report_content.append("")
        for i, rec in enumerate(synthesized[:5], 1):
            rec_text = str(rec or "N/A").replace("|", "\\|").replace("\n", "<br>")
            report_content.append(f"{i}. {rec_text}")
        report_content.append("")

    # NOTE: Removed end-of-report redundant evidence and verdict sections per product request.

    # Reporting Guidance when content may warrant reporting (e.g. high PR count, scam indicators)
    pr_count = getattr(report, "press_release_count", 0)
    metadata = getattr(report, "metadata", None) or {}
    ai_disclosure = metadata.get("ai_disclosure", False)
    ai_indicators = metadata.get("ai_indicators_detected", False)
    if pr_count > 2 or ai_disclosure or ai_indicators:
        report_content.append("## How to Report This Content")
        report_content.append("")
        report_content.append("- **FTC** (false advertising, unsubstantiated health claims): https://reportfraud.ftc.gov/")
        report_content.append("- **FDA** (unapproved medical products): https://www.fda.gov/safety/report-problem-fda/reporting-unlawful-sales-medical-products-internet")
        report_content.append("- **YouTube**: Use the Report button on the video (e.g. Medical misinformation).")
        report_content.append("")

    # Join all parts with single newlines
    return "\n".join(report_content)



# (No example usage needed here, it's called by other modules) 