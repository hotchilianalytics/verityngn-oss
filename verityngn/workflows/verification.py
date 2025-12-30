import logging
from typing import Dict, Any, List, Optional, Tuple
import time
from verityngn.llm_logging.logger import log_llm_call, log_llm_response

# Removed Pydantic dependency - using dict-based models instead
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_vertexai import ChatVertexAI
from langchain_core.output_parsers import JsonOutputParser
from langgraph.graph import StateGraph, END
from langchain_google_vertexai import VertexAI
import yt_dlp

from verityngn.models.workflow import InitialAnalysisState, ClaimVerificationState
from verityngn.models.report import EvidenceSource
from verityngn.config.prompts import CLAIM_VERIFICATION_PROMPT
from verityngn.config.settings import (
    AGENT_MODEL_NAME,
    GOOGLE_SEARCH_API_KEY,
    CSE_ID,
    MAX_OUTPUT_TOKENS_2_0_FLASH,
)
from verityngn.services.search.web_search import search_for_evidence
from verityngn.tools.search import SearchTool
from verityngn.services.search.youtube_search import (
    analyze_youtube_evidence_content,
    youtube_search_service,
)
from verityngn.services.report.evidence_utils import (
    enhance_source_credibility,
    generate_press_release_sources_file,
    generate_youtube_sources_file,
)
from verityngn.utils.date_utils import get_current_date_context, get_date_context_prompt_section
from verityngn.config.config_loader import get_config

# Dict-based verification result schema (replaces Pydantic model)
VERIFICATION_RESULT_SCHEMA = {
    "evidence_summary": "A single sentence summarizing the key evidence found",
    "conclusion_summary": "A single sentence summarizing the conclusion about the claim's veracity",
    "probability_distribution": "Probability distribution over possible outcomes (TRUE, FALSE, UNCERTAIN), values should sum to 1.0",
    "sources": "List of source URLs or references that support the verification",
}


def get_agent(state):
    """Agent for claim verification, using JsonOutputParser for structured output."""
    # SHERLOCK FIX: Add timeout protection to prevent indefinite hangs
    # Reduced timeout from 120s to 60s and disabled retries to prevent 2202s hangs
    llm = VertexAI(
        model_name=AGENT_MODEL_NAME,
        temperature=0.7,
        max_output_tokens=MAX_OUTPUT_TOKENS_2_0_FLASH,
        request_timeout=60.0,  # Reduced from 120s to 60s
        max_retries=1,  # Limit retries to 1 (was: default unlimited)
    )

    # SHERLOCK FIX: Inject current date context to prevent LLM from treating 2025 sources as "future-dated"
    current_date = get_current_date_context()
    date_context = get_date_context_prompt_section()

    prompt = ChatPromptTemplate.from_template(
        f"""You are an expert fact-checker with a focus on debunking misinformation. Your task is to verify claims by analyzing provided evidence and determining their veracity.

{date_context}

Context:
Video Title: {{video_title}}
Video URL: {{video_url}}
Claim to Verify: {{claim}}

Evidence Found:
{{evidence}}

Guidelines for verification:
1. Review the provided evidence carefully
2. Analyze the credibility and relevance of sources
3. Determine a probability distribution over possible outcomes
4. Provide concise summaries of evidence and conclusions

Key Principles:
- Lack of supporting evidence for extraordinary claims should be treated as a strong indicator that the claim is likely false
- Marketing/promotional content making medical or scientific claims requires strong scientific evidence to be considered true
- Claims about products, treatments, or "secrets" that seem too good to be true should be treated with high skepticism
- Personal anecdotes or testimonials are not sufficient evidence for medical/scientific claims
- Absence of peer-reviewed research or clinical trials for medical claims is a strong indicator of falsehood

Focus on:
- Factual information from credible sources
- Both supporting and contradicting evidence
- Source credibility in assessment
- Specific source citations in evidence summary

Provide a JSON response with the following structure:
{{{{
    "evidence_summary": "A single sentence summarizing the key evidence found",
    "conclusion_summary": "A single sentence summarizing the conclusion about the claim's veracity",
    "probability_distribution": {{{{"TRUE": 0.0, "FALSE": 0.0, "UNCERTAIN": 0.0}}}},
    "sources": ["list of source URLs or references that support the verification"]
}}}}

Example probability distributions:
For a claim with no supporting evidence:
{{{{
    "TRUE": 0.05,
    "FALSE": 0.85,
    "UNCERTAIN": 0.10
}}}}

For a claim with mixed evidence:
{{{{
    "TRUE": 0.30,
    "FALSE": 0.30,
    "UNCERTAIN": 0.40
}}}}

For a claim with strong supporting evidence:
{{{{
    "TRUE": 0.85,
    "FALSE": 0.05,
    "UNCERTAIN": 0.10
}}}}

Analyze the claim and provide your verification result."""
    )

    # Use simple JSON output parser without Pydantic dependency
    output_parser = JsonOutputParser()

    return prompt | llm | output_parser


def search_youtube_counter_intel_standalone(
    video_url: str, video_id: str
) -> List[Dict[str, Any]]:
    """
    Search for YouTube counter-intelligence videos independently of video download.
    This ensures counter-intelligence search always runs regardless of download status.
    """
    logger = logging.getLogger(__name__)
    logger.info(
        f"🎯 [YOUTUBE COUNTER-INTEL] Starting independent search for {video_id}"
    )

    # Try to get video title from URL or use fallback
    video_title = ""
    try:
        # Try to extract from existing .info.json if available
        import os
        import tempfile
        import json

        # Check common output directories for existing video info
        possible_dirs = [
            os.path.join(tempfile.gettempdir(), "verity_outputs", video_id),
            f"/var/tmp/verity_outputs/{video_id}",
            f"outputs/{video_id}",
            f"downloads/{video_id}",
        ]

        for dir_path in possible_dirs:
            info_file = os.path.join(dir_path, f"{video_id}.info.json")
            if os.path.exists(info_file):
                with open(info_file, "r") as f:
                    video_info = json.load(f)
                    video_title = video_info.get("title", "")
                    logger.info(
                        f"Found video title from existing info: {video_title[:50]}..."
                    )
                    break

        # If no title found, extract using yt-dlp --no-download
        if not video_title:
            try:
                import subprocess

                result = subprocess.run(
                    ["yt-dlp", "--no-download", "--print", "%(title)s", video_url],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode == 0 and result.stdout.strip():
                    video_title = result.stdout.strip()
                    logger.info(f"Extracted title via yt-dlp: {video_title[:50]}...")
                else:
                    logger.warning(f"yt-dlp title extraction failed: {result.stderr}")
            except Exception as e:
                logger.warning(f"Failed to extract title via yt-dlp: {e}")

        # Ultimate fallback
        if not video_title:
            video_title = f"Video {video_id}"
            logger.info(f"Using fallback title: {video_title}")

    except Exception as e:
        logger.error(f"Error getting video title: {e}")
        video_title = f"Video {video_id}"

    # YouTube CI now runs once after initial analysis in the workflow; keep this noop to preserve API
    return []


def collect_and_group_evidence(
    all_evidence: List[Dict[str, Any]],
    claim_text: str,
    video_title: str = "",
    video_channel: str = "",
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Collect and group evidence to prevent self-referential press release validation.

    This function:
    1. Groups evidence by type (press releases, scientific, independent web, YouTube counter)
    2. Detects self-referential content by checking for product names and video context
    3. Assigns validation power scores (self-referential press releases get 0.0 validation power)
    4. Ensures press releases cannot validate claims they make themselves

    Args:
        all_evidence: Combined list of all evidence sources
        claim_text: The claim being verified
        video_title: Title of the video being analyzed
        video_channel: Channel name of the video

    Returns:
        Dict with grouped evidence: {
            "independent": [...],     # Independent web sources
            "press_releases": [...],  # Press releases (marked as self-referential if applicable)
            "scientific": [...],      # Scientific/academic sources
            "youtube_counter": [...]  # YouTube counter-intelligence
        }
    """
    logger = logging.getLogger(__name__)

    # Extract product names and key terms from video metadata
    product_names = set()
    key_terms = set()

    if video_title:
        words = [w.lower().strip() for w in video_title.split() if len(w) > 3]
        product_names.update(words)
        key_terms.update(words)

    if video_channel:
        channel_words = [w.lower().strip() for w in video_channel.split() if len(w) > 3]
        key_terms.update(channel_words)

    # Extract key terms from claim text
    if claim_text:
        claim_words = [w.lower().strip() for w in claim_text.split() if len(w) > 3]
        key_terms.update(claim_words)

    logger.info(f"🔍 Grouping evidence with key terms: {list(key_terms)[:5]}...")

    # Initialize evidence groups
    evidence_groups = {
        "independent": [],
        "press_releases": [],
        "scientific": [],
        "youtube_counter": [],
    }

    # Press release domain patterns
    press_release_domains = [
        "prnewswire.com",
        "businesswire.com",
        "globenewswire.com",
        "prweb.com",
        "marketwatch.com",
        "newswire.com",
        "einnews.com",
        "pressrelease.com",
        "prlog.org",
        "openpr.com",
        "pressat.co.uk",
        "pressreleases.com",
        "pr.com",
        "pr-inside.com",
        "prurgent.com",
        "prfire.co.uk",
        "prbuzz.com",
        "prnews.biz",
        "pressbox.co.uk",
        "pressreleasepoint.com",
        "24-7pressrelease.com",
        "abnewswire.com",
        "webwire.com",
        "sbwire.com",
        "releasewire.com",
        "prsync.com",
        "przoom.com",
        "prfree.org",
        "prdistribution.com",
    ]

    # Scientific domain patterns
    scientific_domains = [
        "pubmed.ncbi.nlm.nih.gov",
        "nature.com",
        "science.org",
        "arxiv.org",
        "nih.gov",
        "who.int",
        "fda.gov",
        "cdc.gov",
        "nejm.org",
        "bmj.com",
        "lancet.com",
        "cell.com",
        "pnas.org",
        "jama.jamanetwork.com",
    ]

    for evidence in all_evidence:
        if not isinstance(evidence, dict):
            continue

        source_type = evidence.get("source_type", "").lower()
        url = evidence.get("url", "")
        text = evidence.get("text", "")
        title = evidence.get("title", "")

        # FIX: Check for government sources FIRST - they should NEVER be classified as press releases
        government_domains = [
            '.gov', 'fdic.gov', 'sec.gov', 'nih.gov', 'cdc.gov', 'fda.gov', 'epa.gov',
            'justice.gov', 'treasury.gov', 'state.gov', 'cms.gov', 'leg.state'
        ]
        is_government = any(domain in url for domain in government_domains)
        
        # Detect evidence type
        # Government sources cannot be press releases (FDIC reports, etc.)
        is_press_release = (
            not is_government and 
            (source_type == "press release" or any(
                domain in url for domain in press_release_domains
            ))
        )

        is_youtube_counter = source_type == "youtube_counter_intelligence"

        is_scientific = (
            source_type in ("scientific journal", "academic research", "peer-reviewed")
            or any(domain in url for domain in scientific_domains)
            or url.endswith(".edu")
        )

        # Check for self-referential content
        is_self_referential = False
        validation_power = 1.0

        if is_press_release:
            # Check if press release references the video/product being analyzed
            content_to_check = f"{url} {text} {title}".lower()

            # Self-referential if it contains video channel, product names, or key terms
            if video_channel and video_channel.lower() in content_to_check:
                is_self_referential = True
                validation_power = 0.0
                logger.info(
                    f"🚫 Self-referential press release detected (channel match): {url[:50]}..."
                )
            elif any(term in content_to_check for term in product_names):
                is_self_referential = True
                validation_power = 0.0
                logger.info(
                    f"🚫 Self-referential press release detected (product match): {url[:50]}..."
                )
            elif len(key_terms & set(content_to_check.split())) >= 2:
                # Multiple key term matches suggest self-reference
                is_self_referential = True
                validation_power = 0.2  # Some validation power but heavily reduced
                logger.info(
                    f"⚠️ Likely self-referential press release (term matches): {url[:50]}..."
                )

        # Enhance evidence with validation metadata
        enhanced_evidence = evidence.copy()
        enhanced_evidence.update(
            {
                "self_referential": is_self_referential,
                "validation_power": validation_power,
                "evidence_group": "",  # Will be set below
                "supports_claim": False,  # Will be analyzed separately
            }
        )

        # Analyze claim support for scientific evidence
        if is_scientific and text:
            support_indicators = [
                "effective",
                "significant",
                "proven",
                "benefit",
                "successful",
                "improves",
            ]
            oppose_indicators = [
                "ineffective",
                "no effect",
                "placebo",
                "not significant",
                "failed",
            ]

            text_lower = text.lower()
            if any(indicator in text_lower for indicator in support_indicators):
                enhanced_evidence["supports_claim"] = True
            elif any(indicator in text_lower for indicator in oppose_indicators):
                enhanced_evidence["supports_claim"] = False

        # Group evidence
        if is_press_release:
            enhanced_evidence["evidence_group"] = "press_releases"
            evidence_groups["press_releases"].append(enhanced_evidence)
        elif is_youtube_counter:
            enhanced_evidence["evidence_group"] = "youtube_counter"
            evidence_groups["youtube_counter"].append(enhanced_evidence)
        elif is_scientific:
            enhanced_evidence["evidence_group"] = "scientific"
            evidence_groups["scientific"].append(enhanced_evidence)
        else:
            enhanced_evidence["evidence_group"] = "independent"
            evidence_groups["independent"].append(enhanced_evidence)

    # Log evidence distribution
    logger.info(
        f"📊 Evidence groups: Independent={len(evidence_groups['independent'])}, "
        f"Press releases={len(evidence_groups['press_releases'])}, "
        f"Scientific={len(evidence_groups['scientific'])}, "
        f"YouTube counter={len(evidence_groups['youtube_counter'])}"
    )

    # Log self-referential press releases
    self_ref_count = sum(
        1 for e in evidence_groups["press_releases"] if e.get("self_referential", False)
    )
    if self_ref_count > 0:
        logger.warning(
            f"🚫 Found {self_ref_count} self-referential press releases that cannot validate claims"
        )

    return evidence_groups


def generate_press_release_counter_boost(
    press_release_evidence: List[Dict[str, Any]], claim_text: str
) -> Dict[str, Any]:
    """
    Generate counter-intelligence boost from press release analysis with quotes and explanations.

    Args:
        press_release_evidence: List of press release evidence items
        claim_text: The claim being analyzed

    Returns:
        Dict containing boost information with explanation and quotes
    """
    if not press_release_evidence:
        return None

    # Analyze press release patterns for counter-intelligence
    self_referential_count = sum(
        1 for e in press_release_evidence if e.get("self_referential", False)
    )
    total_pr_count = len(press_release_evidence)

    boost_info = {
        "type": "press_release_counter",
        "probability_adjustment": -0.15,  # Reduce TRUE probability by 15%
        "confidence_factor": 0.8,
        "explanation": "",
        "quotes": [],
        "analysis": "",
    }

    # Generate explanation based on press release analysis
    if self_referential_count > 0:
        boost_info["probability_adjustment"] = (
            -0.25
        )  # Stronger penalty for self-referential
        boost_info["explanation"] = (
            f"Found {self_referential_count}/{total_pr_count} self-referential press releases promoting the same product/service being claimed. This creates circular validation where promotional content supports its own claims."
        )

        # Extract quotes from self-referential press releases
        for pr in press_release_evidence:
            if pr.get("self_referential", False):
                quote_text = pr.get("text", "")[:150]
                source_name = pr.get("source_name", "Press Release")
                boost_info["quotes"].append(
                    {
                        "source": source_name,
                        "quote": f'"{quote_text}..."',
                        "analysis": "Self-promotional content with zero independent validation",
                    }
                )
                if len(boost_info["quotes"]) >= 2:  # Limit quotes for readability
                    break

    elif total_pr_count >= 2:
        boost_info["explanation"] = (
            f"Multiple press releases ({total_pr_count}) found supporting this claim, but press releases are promotional content with inherent bias toward positive claims about products/services."
        )

        # Extract representative quotes
        for i, pr in enumerate(press_release_evidence[:2]):
            quote_text = pr.get("text", "")[:150]
            source_name = pr.get("source_name", f"Press Release {i+1}")
            boost_info["quotes"].append(
                {
                    "source": source_name,
                    "quote": f'"{quote_text}..."',
                    "analysis": "Promotional press release content - inherent positive bias",
                }
            )

    else:
        boost_info["explanation"] = (
            f"Press release evidence found, but press releases are promotional materials with inherent bias toward supporting product claims rather than independent verification."
        )

        if press_release_evidence:
            pr = press_release_evidence[0]
            quote_text = pr.get("text", "")[:150]
            source_name = pr.get("source_name", "Press Release")
            boost_info["quotes"].append(
                {
                    "source": source_name,
                    "quote": f'"{quote_text}..."',
                    "analysis": "Single press release - promotional content, not independent verification",
                }
            )

    boost_info["analysis"] = (
        f"Counter-intelligence analysis: Press releases reduced claim credibility by {abs(boost_info['probability_adjustment'])*100:.0f}% due to promotional bias and lack of independent validation."
    )

    return boost_info


def generate_youtube_counter_boost(
    youtube_evidence: List[Dict[str, Any]], claim_text: str
) -> Dict[str, Any]:
    """
    Generate counter-intelligence boost from YouTube analysis with smart weighting based on actual reach and credibility.

    Args:
        youtube_evidence: List of YouTube counter-intelligence evidence items
        claim_text: The claim being analyzed

    Returns:
        Dict containing boost information with explanation and quotes
    """
    if not youtube_evidence:
        return None

    boost_info = {
        "type": "youtube_counter",
        "probability_adjustment": -0.05,  # Start with minimal adjustment
        "confidence_factor": 0.9,
        "explanation": "",
        "quotes": [],
        "analysis": "",
    }

    negative_videos = []
    high_credibility_videos = []
    total_views = 0
    max_views = 0

    # Analyze YouTube evidence for counter-intelligence patterns
    for video in youtube_evidence:
        title = video.get("title", "").lower()
        description = video.get("description", "").lower()
        view_count = video.get("view_count", 0)
        total_views += view_count
        max_views = max(max_views, view_count)

        # Check for negative sentiment indicators
        negative_keywords = [
            "scam",
            "fake",
            "fraud",
            "doesn't work",
            "waste of money",
            "warning",
            "beware",
            "exposed",
            "debunk",
        ]
        if any(
            keyword in title or keyword in description for keyword in negative_keywords
        ):
            negative_videos.append(video)

        # Check for high credibility (view count, specific analysis)
        if view_count > 10000:  # Lowered threshold but still meaningful
            high_credibility_videos.append(video)

    # Smart weighting based on actual impact
    base_adjustment = 0.0

    # Factor 1: View count impact
    if total_views > 100000:
        base_adjustment += 0.15  # High reach content
    elif total_views > 10000:
        base_adjustment += 0.08  # Moderate reach
    elif total_views > 1000:
        base_adjustment += 0.03  # Low reach
    else:
        base_adjustment += 0.01  # Minimal reach (like the current 0 views case)

    # Factor 2: High credibility videos
    if len(high_credibility_videos) > 0:
        base_adjustment += (
            len(high_credibility_videos) * 0.05
        )  # Additional weight for credible sources

    # Factor 3: Multiple negative videos (but with diminishing returns)
    if len(negative_videos) >= 2:
        negative_boost = min(
            0.08, len(negative_videos) * 0.03
        )  # Max 8% from multiple negatives
        base_adjustment += negative_boost

    # Cap maximum adjustment to prevent over-weighting
    final_adjustment = min(0.20, base_adjustment)  # Maximum 20% reduction

    boost_info["probability_adjustment"] = -final_adjustment

    # Generate more nuanced explanation
    if len(negative_videos) >= 2:
        if total_views > 10000:
            boost_info["explanation"] = (
                f"Multiple YouTube videos ({len(negative_videos)}/{len(youtube_evidence)}) contain negative reviews or warnings about this claim. Independent reviewers with {total_views:,} total views provide contradictory evidence with significant reach."
            )
        else:
            boost_info["explanation"] = (
                f"Multiple YouTube videos ({len(negative_videos)}/{len(youtube_evidence)}) contain negative reviews or warnings about this claim. Independent reviewers with {total_views:,} total views provide contradictory evidence with limited reach."
            )

        # Extract quotes from negative videos
        for i, video in enumerate(negative_videos[:2]):
            title = video.get("title", "")
            view_count = video.get("view_count", 0)
            boost_info["quotes"].append(
                {
                    "source": f"YouTube Review ({view_count:,} views)",
                    "quote": f'Video Title: "{title}"',
                    "analysis": f"Independent reviewer contradicts claim - {view_count:,} viewers exposed to counter-perspective",
                }
            )

    elif len(high_credibility_videos) >= 1:
        boost_info["explanation"] = (
            f"High-credibility YouTube reviews ({len(high_credibility_videos)} videos with {total_views:,} total views) provide counter-intelligence to this claim through independent analysis."
        )

        for video in high_credibility_videos[:2]:
            title = video.get("title", "")
            view_count = video.get("view_count", 0)
            boost_info["quotes"].append(
                {
                    "source": f"YouTube Analysis ({view_count:,} views)",
                    "quote": f'"{title}"',
                    "analysis": f"Independent analysis with significant reach contradicts or questions claim",
                }
            )

    else:
        boost_info["explanation"] = (
            f"YouTube counter-intelligence found {len(youtube_evidence)} videos providing alternative perspectives on this claim, indicating public scrutiny and contradictory viewpoints."
        )

        if youtube_evidence:
            video = youtube_evidence[0]
            title = video.get("title", "")
            view_count = video.get("view_count", 0)
            boost_info["quotes"].append(
                {
                    "source": f"YouTube Review ({view_count:,} views)",
                    "quote": f'"{title}"',
                    "analysis": "Independent perspective provides counter-intelligence to claim",
                }
            )

    boost_info["analysis"] = (
        f"Counter-intelligence analysis: YouTube reviews reduced claim credibility by {abs(boost_info['probability_adjustment'])*100:.0f}% due to independent contradictory evidence from {len(youtube_evidence)} sources with {total_views:,} total views."
    )

    return boost_info


def apply_counter_intelligence_boosts(
    base_prob_dist: Dict[str, float],
    press_release_evidence: List[Dict[str, Any]],
    youtube_evidence: List[Dict[str, Any]],
    claim_text: str,
) -> Tuple[Dict[str, float], List[Dict[str, Any]]]:
    """
    Apply counter-intelligence boosts to probability distribution.

    Args:
        base_prob_dist: Base probability distribution
        press_release_evidence: Press release evidence items
        youtube_evidence: YouTube counter-intelligence evidence items
        claim_text: The claim being analyzed

    Returns:
        Tuple of (enhanced_prob_dist, counter_intel_boosts)
    """
    enhanced_dist = base_prob_dist.copy()
    counter_intel_boosts = []

    # Apply press release counter-intelligence
    if press_release_evidence:
        pr_boost = generate_press_release_counter_boost(
            press_release_evidence, claim_text
        )
        if pr_boost:
            counter_intel_boosts.append(pr_boost)

            # Apply probability adjustment
            adjustment = pr_boost["probability_adjustment"]
            true_reduction = abs(adjustment)

            # Reduce TRUE probability, increase FALSE probability (ENHANCED - Research Path)
            enhanced_dist["TRUE"] = max(
                0.0, enhanced_dist["TRUE"] - true_reduction * 0.6
            )  # Only apply 60% of reduction
            enhanced_dist["FALSE"] = min(
                1.0, enhanced_dist["FALSE"] + true_reduction * 0.4
            )  # 40% goes to FALSE (reduced from 70%)
            enhanced_dist["UNCERTAIN"] = min(
                1.0, enhanced_dist["UNCERTAIN"] + true_reduction * 0.4
            )  # 40% to UNCERTAIN (increased from 30%)

    # Apply YouTube counter-intelligence
    if youtube_evidence:
        youtube_boost = generate_youtube_counter_boost(youtube_evidence, claim_text)
        if youtube_boost:
            counter_intel_boosts.append(youtube_boost)

            # Apply probability adjustment
            adjustment = youtube_boost["probability_adjustment"]
            true_reduction = abs(adjustment)

            # Reduce TRUE probability, increase FALSE probability (ENHANCED - Research Path)
            enhanced_dist["TRUE"] = max(
                0.0, enhanced_dist["TRUE"] - true_reduction * 0.5
            )  # Only apply 50% of reduction
            enhanced_dist["FALSE"] = min(
                1.0, enhanced_dist["FALSE"] + true_reduction * 0.4
            )  # 40% goes to FALSE (reduced from 80%)
            enhanced_dist["UNCERTAIN"] = min(
                1.0, enhanced_dist["UNCERTAIN"] + true_reduction * 0.5
            )  # 50% to UNCERTAIN (increased from 20%)

    # Apply evidence quality boost to counteract over-conservative estimates
    enhanced_dist = apply_evidence_quality_boost(
        enhanced_dist, youtube_evidence, press_release_evidence
    )

    # Normalize probabilities to ensure they sum to 1.0
    total = sum(enhanced_dist.values())
    if total > 0:
        enhanced_dist = {k: v / total for k, v in enhanced_dist.items()}

    return enhanced_dist, counter_intel_boosts


def apply_evidence_quality_boost(
    prob_dist: Dict[str, float],
    youtube_evidence: List[Dict[str, Any]],
    press_release_evidence: List[Dict[str, Any]],
) -> Dict[str, float]:
    """Apply evidence quality boost when counter-intelligence has low impact but primary evidence is strong."""
    boosted_dist = prob_dist.copy()

    # Calculate counter-intelligence reach
    youtube_total_views = (
        sum(video.get("view_count", 0) for video in youtube_evidence)
        if youtube_evidence
        else 0
    )
    press_total_reach = len(press_release_evidence) if press_release_evidence else 0

    # If counter-intelligence has very low reach, boost confidence in primary evidence
    if youtube_total_views < 1000 and press_total_reach < 3:
        confidence_boost = 0.10  # 10% boost when CI has minimal impact

        # Apply boost to the dominant probability
        if boosted_dist["TRUE"] > boosted_dist["FALSE"]:
            boosted_dist["TRUE"] = min(0.95, boosted_dist["TRUE"] + confidence_boost)
            boosted_dist["UNCERTAIN"] = max(
                0.05, boosted_dist["UNCERTAIN"] - confidence_boost * 0.7
            )
            boosted_dist["FALSE"] = max(
                0.05, boosted_dist["FALSE"] - confidence_boost * 0.3
            )
        elif boosted_dist["FALSE"] > boosted_dist["TRUE"]:
            boosted_dist["FALSE"] = min(0.95, boosted_dist["FALSE"] + confidence_boost)
            boosted_dist["UNCERTAIN"] = max(
                0.05, boosted_dist["UNCERTAIN"] - confidence_boost * 0.7
            )
            boosted_dist["TRUE"] = max(
                0.05, boosted_dist["TRUE"] - confidence_boost * 0.3
            )

    return boosted_dist


def verify_claim(state: ClaimVerificationState) -> Dict[str, Any]:
    """Verify a claim using evidence and search results."""
    from verityngn.services.search.youtube_search import (
        search_youtube_counter_intelligence,
    )

    import logging

    logger = logging.getLogger(__name__)

    try:
        from langchain_google_vertexai import ChatVertexAI
        from langchain_core.output_parsers import JsonOutputParser
        from typing import Optional, Dict, Any, List

        # Using dict-based verification result (no Pydantic dependency)
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
        return {
            "result": "UNCERTAIN",
            "explanation": "Unable to import required verification modules",
            "evidence": [],
            "probability_distribution": {"TRUE": 0.0, "FALSE": 0.0, "UNCERTAIN": 1.0},
            "sources": [],
            "pr_sources": [],
            "youtube_counter_sources": [],
        }

    # --- YouTube Counter-Intelligence Search (moved to run_claim_verification) ---
    # YouTube counter-intelligence is now handled at the workflow level to ensure it always runs
    youtube_counter_evidence = getattr(state, "youtube_counter_evidence", [])

    def get_value(data, key, default=""):
        if isinstance(data, dict):
            return data.get(key, default)
        else:
            return getattr(data, key, default) if hasattr(data, key) else default

    if not state.claim:
        return {
            "result": "HIGHLY_LIKELY_FALSE",
            "explanation": "No claim provided - unable to verify non-existent claim",
            "evidence": [],
            "probability_distribution": {"TRUE": 0.0, "FALSE": 0.95, "UNCERTAIN": 0.05},
            "sources": [],
            "pr_sources": [],
            "youtube_counter_sources": [],
        }

    claim_text = get_value(state.claim, "claim_text", "")
    video_url = get_value(state, "video_url", "")
    video_title = get_value(state, "video_title", "")
    video_channel = get_value(getattr(state, "media_embed", {}), "channel", "")

    # Gather evidence if not present
    if not state.evidence:
        try:
            state.evidence = gather_evidence(claim_text)
            logger.info(
                f"Gathered {len(state.evidence)} pieces of evidence for claim: {claim_text[:100]}..."
            )
        except Exception as e:
            logger.error(f"Error gathering evidence: {e}")
            state.evidence = []

    # --- REDESIGNED EVIDENCE COLLECTION ---
    evidence_groups = collect_and_group_evidence(
        all_evidence=list(state.evidence) + youtube_counter_evidence,
        claim_text=claim_text,
        video_title=video_title,
        video_channel=video_channel,
    )

    # Extract grouped evidence
    main_evidence = evidence_groups["independent"]
    press_release_evidence = evidence_groups["press_releases"]
    youtube_review_evidence = evidence_groups["youtube_counter"]
    scientific_evidence = evidence_groups["scientific"]

    # Calculate flags based on grouped evidence
    press_release_found = len(press_release_evidence) > 0
    press_release_associated = any(
        e.get("self_referential", False) for e in press_release_evidence
    )
    youtube_negative_found = len(youtube_review_evidence) > 0
    scientific_evidence_found = len(scientific_evidence) > 0
    scientific_supports = any(
        e.get("supports_claim", False) for e in scientific_evidence
    )
    independent_evidence_found = len(main_evidence) > 0

    # Format evidence for LLM (use only main evidence, not press releases)
    # SHERLOCK FIX: Further limit evidence to prevent rate limiting from large payloads
    evidence_text = ""
    if main_evidence:
        # Prioritize evidence by relevance/quality, limit to top 8 items
        evidence_items = main_evidence[:8]  # Reduced from 10 to 8
        evidence_text = "\n".join(
            [
                f"Source: {item.get('source_name', 'Unknown')}\nURL: {item.get('url', 'N/A')}\nText: {item.get('text', '')[:400]}\n"
                for item in evidence_items  # Also reduced text snippet from 500 to 400 chars
            ]
        )
        logger.info(
            f"📊 [SHERLOCK] Formatted {len(evidence_items)} evidence items for LLM (from {len(main_evidence)} total)"
        )

    try:
        agent = get_agent(state)
        # Use simple JSON output parser without Pydantic dependency
        output_parser = JsonOutputParser()
        agent_input = {
            "claim": claim_text,
            "video_url": video_url,
            "video_title": video_title,
            "evidence": evidence_text or "No relevant evidence found.",
        }

        # SHERLOCK FIX: Add timeout protection to agent.invoke()
        # Reduced timeout from 150s to 90s to fail faster on rate limits
        logger.info(
            f"🔍 [SHERLOCK] Invoking verification agent with 90s timeout for claim: {claim_text[:50]}..."
        )
        from concurrent.futures import (
            ThreadPoolExecutor,
            TimeoutError as FuturesTimeoutError,
        )
        import time
        
        # LLM interaction logging - already imported at top
        start_time = time.time()
        # Extract video_id for logging, assuming it might be in state
        video_id = get_value(state, "video_id", "")

        call_id = log_llm_call(
            operation="verify_claim_agent",
            prompt=str(agent_input),
            model=AGENT_MODEL_NAME,
            video_id=video_id
        )

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(agent.invoke, agent_input)
            try:
                result = future.result(timeout=90.0)  # Reduced from 150s to 90s
                elapsed = time.time() - start_time
                log_llm_response(call_id, result, duration=elapsed)
                logger.info(
                    f"🔍 [SHERLOCK] Agent verification completed successfully in {elapsed:.1f}s"
                )
            except FuturesTimeoutError:
                elapsed = time.time() - start_time
                logger.error(
                    f"🔍 [SHERLOCK] Agent verification timed out after {elapsed:.1f}s for claim: {claim_text[:50]}"
                )
                logger.error(
                    f"⚠️ [SHERLOCK] Possible rate limiting or resource exhaustion after {elapsed:.1f}s"
                )
                # Return uncertain result on timeout with rate limit hint
                return {
                    "result": "UNCERTAIN",
                    "explanation": f"Verification timed out after {elapsed:.1f}s - likely due to rate limiting or resource exhaustion. Unable to complete analysis.",
                    "evidence": main_evidence,
                    "probability_distribution": {
                        "TRUE": 0.2,
                        "FALSE": 0.3,
                        "UNCERTAIN": 0.5,
                    },
                    "sources": [e.get("url", "") for e in main_evidence[:5]],
                    "pr_sources": [e.get("url", "") for e in press_release_evidence],
                    "youtube_counter_sources": [
                        e.get("url", "") for e in youtube_review_evidence
                    ],
                }

        if not isinstance(result, dict):
            # Fallback: attempt to repair/parse JSON from text
            try:
                from verityngn.utils.json_fix import safe_gemini_json_parse
            except Exception:
                safe_gemini_json_parse = None
            text_result = str(result)
            if safe_gemini_json_parse:
                repaired = safe_gemini_json_parse(text_result or "{}")
            else:
                # Minimal fallback: try to extract JSON braces
                import re, json

                m = re.search(r"\{[\s\S]*\}", text_result)
                repaired = json.loads(m.group(0)) if m else {}
            if isinstance(repaired, dict):
                result = repaired
        logger.info(f"Agent verification completed for claim: {claim_text[:100]}...")

        prob_dist = result.get(
            "probability_distribution", {"TRUE": 0.15, "FALSE": 0.50, "UNCERTAIN": 0.35}
        )
        if not isinstance(prob_dist, dict):
            prob_dist = {"TRUE": 0.15, "FALSE": 0.50, "UNCERTAIN": 0.35}

        # --- Enhanced Probability Distribution Logic with Validation Power ---
        def calculate_enhanced_probability_distribution(
            base_dist: Dict[str, float],
            evidence_groups: Dict[str, List[Dict[str, Any]]],
        ) -> Tuple[Dict[str, float], List[str]]:
            """Calculate enhanced probability distribution based on evidence validation power."""

            enhanced_dist = base_dist.copy()
            modifications = []

            # Calculate effective evidence counts based on validation power
            total_validation_power = 0.0
            independent_power = 0.0
            press_release_power = 0.0
            scientific_power = 0.0
            youtube_counter_power = 0.0

            for evidence in evidence_groups["independent"]:
                power = evidence.get("validation_power", 1.0)
                independent_power += power
                total_validation_power += power

            for evidence in evidence_groups["press_releases"]:
                power = evidence.get("validation_power", 1.0)
                press_release_power += power
                total_validation_power += power

            for evidence in evidence_groups["scientific"]:
                power = evidence.get("validation_power", 1.0)
                scientific_power += power
                total_validation_power += power

            for evidence in evidence_groups["youtube_counter"]:
                power = evidence.get("validation_power", 1.0)
                youtube_counter_power += power
                total_validation_power += power

            modifications.append(
                f"Validation power totals: Independent={independent_power:.1f}, Press={press_release_power:.1f}, Scientific={scientific_power:.1f}, YouTube={youtube_counter_power:.1f}"
            )

            # Factor 1: Evidence quality based on validation power
            if total_validation_power > 0:
                quality_factor = min(
                    1.0, total_validation_power / 5
                )  # Scale based on effective evidence
                uncertainty_reduction = (
                    enhanced_dist.get("UNCERTAIN", 0.3) * quality_factor * 0.2
                )
                enhanced_dist["UNCERTAIN"] = max(
                    0.05, enhanced_dist.get("UNCERTAIN", 0.3) - uncertainty_reduction
                )
                modifications.append(
                    f"Evidence quality (power={total_validation_power:.1f}) reduces uncertainty by {uncertainty_reduction:.2f}"
                )

            # Factor 2: Independent vs promotional validation power ratio
            if total_validation_power > 0:
                promotional_power_ratio = press_release_power / total_validation_power
                independent_power_ratio = independent_power / total_validation_power

                if promotional_power_ratio > 0.6:  # Majority promotional power
                    false_boost = min(0.3, promotional_power_ratio * 0.4)
                    enhanced_dist["FALSE"] = min(
                        0.9, enhanced_dist.get("FALSE", 0.3) + false_boost
                    )
                    modifications.append(
                        f"High promotional power ratio ({promotional_power_ratio:.1%}) increases FALSE by {false_boost:.2f}"
                    )
                elif independent_power_ratio > 0.7:  # Majority independent power
                    true_boost = min(0.3, independent_power_ratio * 0.3)
                    enhanced_dist["TRUE"] = min(
                        0.85, enhanced_dist.get("TRUE", 0.3) + true_boost
                    )
                    modifications.append(
                        f"High independent power ratio ({independent_power_ratio:.1%}) increases TRUE by {true_boost:.2f}"
                    )

            # Factor 3: Scientific evidence weighting
            if scientific_power > 0:
                science_weight = min(0.4, scientific_power * 0.2)
                enhanced_dist["TRUE"] = min(
                    0.85, enhanced_dist.get("TRUE", 0.3) + science_weight
                )
                modifications.append(
                    f"Scientific evidence (power={scientific_power:.1f}) increases TRUE by {science_weight:.2f}"
                )

            # Factor 4: YouTube counter-intelligence impact (ENHANCED - Research Path)
            if youtube_counter_power > 0:
                youtube_impact = min(
                    0.20, youtube_counter_power * 0.08
                )  # Reduced from 0.35 and 0.15
                enhanced_dist["FALSE"] = min(
                    0.85, enhanced_dist.get("FALSE", 0.3) + youtube_impact
                )  # Reduced max from 0.9
                modifications.append(
                    f"YouTube counter-intelligence (power={youtube_counter_power:.1f}) increases FALSE by {youtube_impact:.2f}"
                )

            # Factor 5: Self-referential press release penalty
            # Note: This penalty is reduced or skipped for trusted investigators
            is_investigator = getattr(state, "is_trusted_investigator", False)
            self_ref_count = sum(
                1
                for e in evidence_groups["press_releases"]
                if e.get("self_referential", False)
            )
            if self_ref_count > 0 and not is_investigator:
                penalty = min(0.4, self_ref_count * 0.15)
                enhanced_dist["FALSE"] = min(
                    0.9, enhanced_dist.get("FALSE", 0.3) + penalty
                )
                modifications.append(
                    f"Self-referential press releases ({self_ref_count}) penalty increases FALSE by {penalty:.2f}"
                )
            elif self_ref_count > 0 and is_investigator:
                modifications.append(
                    f"Self-referential penalty SKIPPED: trusted investigator channel"
                )
            
            # Factor 6: Source Reputation Boost
            # Boost credibility for content from trusted investigative channels
            channel_reputation = getattr(state, "channel_reputation", 0.5)
            credibility_boost = getattr(state, "credibility_boost", 1.0)
            
            if credibility_boost > 1.0:
                # Trusted source - boost TRUE probability
                reputation_boost = (credibility_boost - 1.0) * 0.5  # 50% of the boost factor
                enhanced_dist["TRUE"] = min(
                    0.9, enhanced_dist.get("TRUE", 0.3) + reputation_boost
                )
                enhanced_dist["FALSE"] = max(
                    0.05, enhanced_dist.get("FALSE", 0.3) - reputation_boost * 0.5
                )
                modifications.append(
                    f"🏆 Source reputation boost (channel={channel_reputation:.2f}, boost={credibility_boost:.2f}x): TRUE +{reputation_boost:.2f}"
                )
            elif credibility_boost < 1.0:
                # Low-credibility source - reduce TRUE probability
                reputation_penalty = (1.0 - credibility_boost) * 0.3
                enhanced_dist["TRUE"] = max(
                    0.05, enhanced_dist.get("TRUE", 0.3) - reputation_penalty
                )
                enhanced_dist["FALSE"] = min(
                    0.9, enhanced_dist.get("FALSE", 0.3) + reputation_penalty * 0.5
                )
                modifications.append(
                    f"⚠️ Low-credibility source (channel={channel_reputation:.2f}): TRUE -{reputation_penalty:.2f}"
                )

            # Normalize to ensure probabilities sum to 1.0
            total = sum(enhanced_dist.values())
            if total > 0:
                enhanced_dist = {
                    k: round(v / total, 3) for k, v in enhanced_dist.items()
                }

            # Ensure minimum thresholds
            for key in ["TRUE", "FALSE", "UNCERTAIN"]:
                enhanced_dist[key] = max(0.001, enhanced_dist.get(key, 0.0))

            # Final normalization
            total = sum(enhanced_dist.values())
            if abs(total - 1.0) > 0.001:
                enhanced_dist = {
                    k: round(v / total, 3) for k, v in enhanced_dist.items()
                }

            return enhanced_dist, modifications

        # Calculate enhanced probability distribution using validation power
        enhanced_prob_dist, prob_modifications = (
            calculate_enhanced_probability_distribution(prob_dist, evidence_groups)
        )

        # Apply counter-intelligence boosts to probability distribution
        final_prob_dist, counter_intel_boosts = apply_counter_intelligence_boosts(
            enhanced_prob_dist,
            press_release_evidence,
            youtube_review_evidence,
            claim_text,
        )

        # Use final distribution after counter-intelligence
        prob_dist = final_prob_dist
        logger.info(f"🎯 Final probability distribution: {prob_dist}")
        for mod in prob_modifications:
            logger.info(f"   📊 {mod}")
        for boost in counter_intel_boosts:
            logger.info(f"   🕵️ Counter-Intel: {boost['analysis']}")

        # --- Enhanced Evidence Analysis with Counter-Intelligence Boosts ---
        explanation_add = []
        assessment_level = "UNCERTAIN"

        # Analyze evidence groups for explanations (use counter-intel boosts already calculated)
        if press_release_found:
            self_ref_count = sum(
                1 for e in press_release_evidence if e.get("self_referential", False)
            )
            total_pr_power = sum(
                e.get("validation_power", 1.0) for e in press_release_evidence
            )

            # Add press release counter-intelligence explanation with quotes
            pr_boosts = [
                b
                for b in counter_intel_boosts
                if b.get("type") == "press_release_counter"
            ]
            if pr_boosts:
                pr_boost = pr_boosts[0]
                explanation_add.append(
                    f"PRESS RELEASE COUNTER-INTELLIGENCE: {pr_boost['explanation']}"
                )

                # Add quotes if available
                for quote in pr_boost.get("quotes", [])[:2]:  # Limit to 2 quotes
                    explanation_add.append(
                        f"   📋 {quote['source']}: {quote['quote']} → {quote['analysis']}"
                    )

            if self_ref_count > 0:
                explanation_add.append(
                    f"🚫 SELF-REFERENTIAL EVIDENCE: {self_ref_count} press releases detected that reference the same product/video being analyzed. These sources have zero validation power for their own claims."
                )

            if total_pr_power < len(press_release_evidence) * 0.5:
                explanation_add.append(
                    f"LIMITED PRESS RELEASE VALIDATION: Press release sources have reduced validation power (total={total_pr_power:.1f}/{len(press_release_evidence)}) due to promotional nature and self-referential content."
                )

        if youtube_negative_found:
            youtube_power = sum(
                e.get("validation_power", 1.0) for e in youtube_review_evidence
            )

            # Add YouTube counter-intelligence explanation with quotes
            youtube_boosts = [
                b for b in counter_intel_boosts if b.get("type") == "youtube_counter"
            ]
            if youtube_boosts:
                youtube_boost = youtube_boosts[0]
                explanation_add.append(
                    f"📺 YOUTUBE COUNTER-INTELLIGENCE: {youtube_boost['explanation']}"
                )

                # Add quotes if available
                for quote in youtube_boost.get("quotes", [])[:2]:  # Limit to 2 quotes
                    explanation_add.append(
                        f"   {quote['source']}: {quote['quote']} → {quote['analysis']}"
                    )
            else:
                explanation_add.append(
                    f"YOUTUBE COUNTER-INTELLIGENCE: Negative/contradictory YouTube evidence found (validation power={youtube_power:.1f}). These reviews provide independent contradictory perspective."
                )

        if scientific_evidence_found:
            scientific_power = sum(
                e.get("validation_power", 1.0) for e in scientific_evidence
            )
            supporting_scientific = sum(
                1 for e in scientific_evidence if e.get("supports_claim", False)
            )
            explanation_add.append(
                f"SCIENTIFIC EVIDENCE: {len(scientific_evidence)} scientific sources (power={scientific_power:.1f}), {supporting_scientific} supporting claim."
            )

        if independent_evidence_found:
            independent_power = sum(
                e.get("validation_power", 1.0) for e in main_evidence
            )
            explanation_add.append(
                f"INDEPENDENT EVIDENCE: {len(main_evidence)} independent sources (validation power={independent_power:.1f}) provide unbiased perspective."
            )

        # --- Quantum/human-like mapping for verdict ---
        t = prob_dist.get("TRUE", 0.0) * 100
        f = prob_dist.get("FALSE", 0.0) * 100
        u = prob_dist.get("UNCERTAIN", 0.0) * 100

        # Enhanced probability mapping with 65% thresholds (from August 22nd analysis)
        false_uncertain_combined = f + u
        true_uncertain_combined = t + u

        if t > 70 and f < 10:
            assessment_level = "HIGHLY_LIKELY_TRUE"
        elif true_uncertain_combined > 65 and f < 35:
            assessment_level = "LIKELY_TRUE"
        elif false_uncertain_combined > 65 and t < 35:
            assessment_level = "LIKELY_FALSE"
        elif f > 75:
            assessment_level = "HIGHLY_LIKELY_FALSE"
        elif t > 50 and f < 20:
            assessment_level = "LIKELY_TRUE"
        elif f > 45 and t < 25:
            assessment_level = "LIKELY_FALSE"
        elif t > 40 and f < 35:
            assessment_level = "LEANING_TRUE"
        elif f > 35 and t < 30:
            assessment_level = "LEANING_FALSE"
        elif abs(t - f) < 10:
            assessment_level = "UNCERTAIN"
        elif t > f:
            assessment_level = "LEANING_TRUE"
        else:
            assessment_level = "LEANING_FALSE"

        explanation = result.get("conclusion_summary", "No conclusion available")
        if explanation_add:
            explanation += "\n\n" + " ".join(explanation_add)

        # Compose evidence summary (only from main evidence, not press releases)
        evidence_summary = result.get(
            "evidence_summary", "No evidence summary available"
        )
        if main_evidence:
            evidence_summary += (
                f"\n\nMain evidence sources used in verification:\n"
                + "\n".join([str(e.get("url", "")) for e in main_evidence])
            )
        if press_release_evidence:
            evidence_summary += (
                f"\n\nPress release/newswire sources used in verification:\n"
                + "\n".join([str(e.get("url", "")) for e in press_release_evidence])
            )
        if youtube_review_evidence:
            evidence_summary += (
                f"\n\nYouTube review/response sources used in verification:\n"
                + "\n".join([str(e.get("url", "")) for e in youtube_review_evidence])
            )

        verification_result = {
            "result": assessment_level,
            "explanation": explanation,
            "evidence": evidence_summary,
            "probability_distribution": prob_dist,
            "sources": list(
                set(
                    result.get("sources", [])
                    + [item.get("url", "") for item in main_evidence if item.get("url")]
                )
            ),
            "pr_sources": press_release_evidence,
            "youtube_counter_sources": youtube_review_evidence,
            "counter_intelligence_boosts": counter_intel_boosts,  # Add counter-intelligence information
        }
        return verification_result
    except Exception as e:
        logger.error(f"Error in claim verification: {str(e)}")
        if state.evidence:
            evidence_summary = "Based on gathered evidence (agent processing failed): "
            evidence_summary += "; ".join(
                [e.get("text", "")[:200] for e in state.evidence[:3] if e.get("text")]
            )
            return {
                "result": "LIKELY_FALSE",
                "explanation": f"Error during verification, and available evidence does not strongly support the claim. Error: {str(e)}",
                "evidence": evidence_summary,
                "probability_distribution": {
                    "TRUE": 0.05,
                    "FALSE": 0.85,
                    "UNCERTAIN": 0.10,
                },
                "sources": [
                    item.get("url", "") for item in state.evidence if item.get("url")
                ],
                "pr_sources": [],
                "youtube_counter_sources": [],
            }
        return {
            "result": "HIGHLY_LIKELY_FALSE",
            "explanation": f"Error during verification and no supporting evidence found: {str(e)}",
            "evidence": [],
            "probability_distribution": {"TRUE": 0.0, "FALSE": 0.95, "UNCERTAIN": 0.05},
            "sources": [],
            "pr_sources": [],
            "youtube_counter_sources": [],
        }


def gather_evidence(claim_text: str) -> List[Dict[str, Any]]:
    """
    Gather evidence for a claim.

    Args:
        claim_text (str): The claim text

    Returns:
        List[Dict[str, Any]]: Evidence for the claim
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Gathering evidence for claim: {claim_text}")

    try:
        # Search for evidence
        evidence = search_for_evidence(claim_text)

        logger.info(f"Found {len(evidence)} pieces of evidence")
        return evidence

    except Exception as e:
        logger.error(f"Error gathering evidence: {e}")
        return []


def build_claim_verification_workflow() -> StateGraph:
    """
    Build the claim verification workflow.

    Returns:
        StateGraph: The workflow graph
    """
    # Create the workflow
    workflow = StateGraph(ClaimVerificationState)

    # Define the nodes
    workflow.add_node("gather_evidence", gather_evidence_node)
    workflow.add_node("verify_claim", verify_claim_node)

    # Define the edges
    workflow.set_entry_point("gather_evidence")
    workflow.add_edge("gather_evidence", "verify_claim")
    workflow.add_edge("verify_claim", END)

    return workflow


def gather_evidence_node(state: ClaimVerificationState) -> ClaimVerificationState:
    """
    Node function to gather evidence for a claim.

    Args:
        state (ClaimVerificationState): Current state

    Returns:
        ClaimVerificationState: Updated state
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Gathering evidence for claim")

    if not state.claim:
        logger.error("Missing claim")
        return state

    # Gather evidence
    evidence = gather_evidence(state.claim.get("claim_text", ""))

    # Update state
    return state.model_copy(update={"evidence": evidence})


def verify_claim_node(state: ClaimVerificationState) -> ClaimVerificationState:
    """
    Node function to verify a claim.

    Args:
        state (ClaimVerificationState): Current state

    Returns:
        ClaimVerificationState: Updated state
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Verifying claim")

    if not state.claim:
        logger.error("Missing claim")
        return state

    # Verify claim - evidence will be gathered inside verify_claim if needed
    try:
        verification_result = verify_claim(state)
        logger.info(
            f"Verification completed with result: {verification_result['result']}"
        )

        # Update state with both verification result and any new evidence
        updates = {"verification_result": verification_result}
        if state.evidence:
            updates["evidence"] = state.evidence

        return state.model_copy(update=updates)

    except Exception as e:
        logger.error(f"Error in verify_claim_node: {e}")
        return state.model_copy(
            update={
                "verification_result": {
                    "result": "UNABLE_DETERMINE",
                    "explanation": f"Error in verification process: {str(e)}",
                    "evidence": [],
                    "probability_distribution": {
                        "TRUE": 0.0,
                        "FALSE": 0.0,
                        "UNCERTAIN": 1.0,
                    },
                    "sources": [],
                }
            }
        )


def process_claims(state: InitialAnalysisState) -> InitialAnalysisState:
    """Process all claims in the initial analysis state."""
    logger = logging.getLogger(__name__)

    # Helper function to get value from either dict or object
    def get_value(data, key, default=""):
        if isinstance(data, dict):
            return data.get(key, default)
        else:
            return getattr(data, key, default) if hasattr(data, key) else default

    if not state.claims:
        logger.warning("No claims to process")
        return state

    updated_claims = []
    aggregated_evidence = []

    for idx, claim in enumerate(state.claims):
        logger.info(
            f"Processing claim {idx + 1}/{len(state.claims)}: {get_value(claim, 'claim_text', '')[:100]}..."
        )

        # Create verification state
        verification_state = ClaimVerificationState(
            claim=claim,
            video_url=state.video_url,
            video_title=(
                get_value(state.media_embed, "title", "") if state.media_embed else ""
            ),
            evidence=[],
        )

        try:
            # First gather evidence
            verification_state = gather_evidence_node(verification_state)
            if not verification_state.evidence:
                logger.warning(f"No evidence found for claim {idx + 1}")

            # Then verify the claim
            verification_state = verify_claim_node(verification_state)

            # Update the claim with verification result
            if isinstance(claim, dict):
                updated_claim = claim.copy()
            else:
                # If claim is an object, convert to dict for consistent handling
                updated_claim = {
                    k: getattr(claim, k)
                    for k in dir(claim)
                    if not k.startswith("_") and not callable(getattr(claim, k))
                }

            # Explicitly copy claim_text to ensure it's preserved
            original_claim_text = get_value(claim, "claim_text", "")
            if original_claim_text:  # Only add if it exists
                updated_claim["claim_text"] = original_claim_text

            # Add the structured evidence gathered earlier
            if verification_state.evidence:
                updated_claim["evidence"] = verification_state.evidence
            else:
                updated_claim["evidence"] = []  # Ensure the key exists even if empty

            if verification_state.verification_result:
                updated_claim["verification_result"] = (
                    verification_state.verification_result
                )
                updated_claim["explanation"] = get_value(
                    verification_state.verification_result, "explanation", ""
                )
            else:
                logger.error(f"No verification result for claim {idx + 1}")
                updated_claim["verification_result"] = {
                    "result": "UNABLE_DETERMINE",
                    "explanation": "Verification process failed to produce a result",
                    "evidence": [],
                    "probability_distribution": {
                        "TRUE": 0.0,
                        "FALSE": 0.0,
                        "UNCERTAIN": 1.0,
                    },
                    "sources": [],
                }
                updated_claim["explanation"] = (
                    "Verification process failed to produce a result"
                )

            updated_claims.append(updated_claim)

            # Add evidence to aggregated evidence
            if verification_state.evidence:
                # Add main verification evidence
                evidence_entry = {
                    "source_name": "Claim Verification Analysis",
                    "source_type": "verification",
                    "title": f"Verification of: {claim.get('claim_text', '')}",
                    "source_url": "",
                    "text": verification_state.verification_result.get(
                        "evidence", "No evidence summary available"
                    ),
                    "credibility_level": "HIGH",
                    "justification": "Direct verification result",
                }
                aggregated_evidence.append(evidence_entry)

                # Add each piece of gathered evidence
                for evidence in verification_state.evidence:
                    if isinstance(evidence, dict) and evidence.get("text"):
                        source_entry = {
                            "source_name": evidence.get(
                                "source_name", "Referenced Source"
                            ),
                            "source_type": evidence.get("source_type", "web"),
                            "title": evidence.get(
                                "title", evidence.get("source_url", "")
                            ),
                            "source_url": evidence.get("source_url", ""),
                            "text": evidence.get("text", ""),
                            "credibility_level": evidence.get(
                                "credibility_level", "MEDIUM"
                            ),
                            "justification": evidence.get(
                                "justification",
                                "External source referenced during verification",
                            ),
                        }
                        aggregated_evidence.append(source_entry)

        except Exception as e:
            logger.error(f"Error processing claim {idx + 1}: {str(e)}")
            updated_claim = claim.copy()
            updated_claim["verification_result"] = {
                "result": "UNABLE_DETERMINE",
                "explanation": f"Error during claim processing: {str(e)}",
                "evidence": [],
                "probability_distribution": {
                    "TRUE": 0.0,
                    "FALSE": 0.0,
                    "UNCERTAIN": 1.0,
                },
                "sources": [],
            }
            updated_claim["explanation"] = f"Error during claim processing: {str(e)}"
            updated_claims.append(updated_claim)

    logger.info(
        f"Processed {len(updated_claims)} claims with {len(aggregated_evidence)} pieces of evidence"
    )

    # Update state with verified claims and evidence (preserve existing keys on dict state)
    if isinstance(state, dict):
        return {
            **state,
            "claims": updated_claims,
            "aggregated_evidence": aggregated_evidence,
        }
    return state.model_copy(
        update={"claims": updated_claims, "aggregated_evidence": aggregated_evidence}
    )


async def run_claim_verification(state: Dict[str, Any]) -> Dict[str, Any]:
    """Verify all claims using the enhanced evidence collection system."""
    from verityngn.services.search.youtube_search import youtube_search_service
    import logging

    logger = logging.getLogger(__name__)

    # SHERLOCK FIX: Circuit breaker to detect and handle rate limiting
    consecutive_timeouts = 0
    max_consecutive_timeouts = 2  # After 2 timeouts, switch to fast-fail mode

    # Do not run independent YouTube CI here; CI-once already produced CI links
    init_rpt = state.get("initial_report") or {}
    initial_review_text = init_rpt.get("initial_report", "") + init_rpt.get(
        "video_analysis_summary", ""
    )

    claims = state.get("claims", [])
    video_url = state.get("video_url", "")
    video_title = state.get("title", "")
    video_id = state.get("video_id", "")
    
    # Get channel info for source reputation scoring
    video_info = state.get("video_info", {})
    channel_name = video_info.get("channel", "") or video_info.get("uploader", "")
    video_description = video_info.get("description", "")
    
    # Calculate source reputation for the video's channel
    try:
        from verityngn.services.reputation import (
            get_channel_reputation,
            is_trusted_investigator,
            calculate_content_credibility_boost,
        )
        
        channel_reputation = get_channel_reputation(channel_name)
        is_investigator = is_trusted_investigator(channel_name)
        credibility_boost, boost_reason = calculate_content_credibility_boost(
            channel_name, video_title, video_description
        )
        
        # Store in state for use in claim verification
        state["channel_reputation"] = channel_reputation
        state["is_trusted_investigator"] = is_investigator
        state["credibility_boost"] = credibility_boost
        state["credibility_boost_reason"] = boost_reason
        
        if is_investigator:
            logger.info(f"🏆 TRUSTED INVESTIGATOR DETECTED: {channel_name}")
            logger.info(f"   Reputation score: {channel_reputation}")
            logger.info(f"   Credibility boost: {credibility_boost}x ({boost_reason})")
        elif channel_reputation != 0.5:
            logger.info(f"📊 Channel reputation for '{channel_name}': {channel_reputation}")
    except ImportError:
        logger.warning("⚠️ Source reputation module not available, using defaults")
        channel_reputation = 0.5
        credibility_boost = 1.0
        state["channel_reputation"] = channel_reputation
        state["credibility_boost"] = credibility_boost

    logger.info(f"🔍 Starting ENHANCED verification for {len(claims)} claims")
    logger.info(f"🎬 Video: {video_title}")
    logger.info(f"🆔 Video ID: {video_id}")

    if not claims:
        logger.warning("⚠️ No claims to verify")
        return {**state, "aggregated_evidence": []}

    # --- USE CI-ONCE COUNTER-INTELLIGENCE EVIDENCE ---
    logger.info("🎯 [YOUTUBE COUNTER-INTEL] Using CI-once Deep CI evidence")
    ci_once = state.get("ci_once", [])
    youtube_counter_evidence = []

    # Process CI-once evidence into counter-intelligence format
    for item in ci_once:
        if isinstance(item, dict):
            # Convert CI-once item to counter-intelligence evidence format
            evidence_item = {
                "url": item.get("url", ""),
                "title": item.get("title", item.get("source_name", "YouTube Source")),
                "text": item.get("text", item.get("description", "")),
                "source_name": item.get("source_name", "YouTube Counter-Intelligence"),
                "source_type": item.get("source_type", "youtube_counter_intelligence"),
                "credibility_level": "MEDIUM",  # Default for counter-intelligence
                "supports_claim": False,  # Counter-intelligence typically contradicts claims
                "self_referential": False,  # Counter-intelligence is independent
            }
            youtube_counter_evidence.append(evidence_item)

    logger.info(
        f"🎯 [COUNTER-INTEL] Processed {len(youtube_counter_evidence)} counter-intelligence sources from CI-once"
    )

    try:
        all_evidence = []
        verified_claims = []

        # Use advanced claim processing with multi-source integration and semantic clustering
        # Extract actual video duration from state or calculate from video metadata
        video_duration_minutes = state.get("video_duration_minutes", 30.0)
        if (
            video_duration_minutes == 30.0
        ):  # Default fallback, try to get actual duration
            try:
                # Try to get duration from video info or media embed
                video_info = state.get("video_info", {})
                media_embed = state.get("media_embed", {})

                # Check multiple possible duration sources
                duration_seconds = (
                    video_info.get("duration")
                    or media_embed.get("duration")
                    or state.get("video_duration_seconds")
                    or 1800  # 30 minutes fallback
                )
                video_duration_minutes = duration_seconds / 60.0
                logger.info(
                    f"📊 Calculated video duration: {video_duration_minutes:.1f} minutes from {duration_seconds} seconds"
                )
            except Exception as e:
                logger.warning(
                    f"Could not calculate video duration: {e}, using 30 minute default"
                )
                video_duration_minutes = 30.0

        output_dir = f"sherlock_analysis_{video_id}"  # Use existing analysis directory

        logger.info(
            f"🚀 [CLAIMS] Starting advanced claim processing for {len(claims)} claims"
        )

        claims_to_process = process_claims_with_advanced_ranking(
            video_analysis_claims=claims,
            video_id=video_id,
            video_title=video_title or "Unknown Video",
            youtube_counter_evidence=youtube_counter_evidence,
            press_release_evidence=None,  # Add press release integration later
            video_duration_minutes=video_duration_minutes,
            output_dir=output_dir,
        )

        logger.info(
            f"✅ Advanced claim processing selected {len(claims_to_process)} claims from {len(claims)} total video analysis claims"
        )

        # Process each claim using the enhanced verification system
        for i, claim in enumerate(claims_to_process):
            claim_text = claim.get("claim_text", "")
            logger.info(
                f"🔎 Verifying claim {i+1}/{len(claims_to_process)}: {claim_text[:100]}..."
            )

            try:
                # Create object wrapper for enhanced system compatibility
                class StateWrapper:
                    def __init__(
                        self, claim, video_url, video_title, video_id, media_embed,
                        channel_reputation=0.5, credibility_boost=1.0,
                        is_trusted_investigator=False
                    ):
                        self.claim = claim
                        self.video_url = video_url
                        self.video_title = video_title
                        self.video_id = video_id
                        self.evidence = []
                        self.media_embed = media_embed
                        # Source reputation fields
                        self.channel_reputation = channel_reputation
                        self.credibility_boost = credibility_boost
                        self.is_trusted_investigator = is_trusted_investigator

                # Extract media_embed info for enhanced system
                media_embed = state.get("media_embed", {})
                if not media_embed and video_title:
                    media_embed = {"title": video_title, "channel": "Unknown"}

                verification_state = StateWrapper(
                    claim=claim,
                    video_url=video_url,
                    video_title=video_title,
                    video_id=video_id,
                    media_embed=media_embed,
                    channel_reputation=state.get("channel_reputation", 0.5),
                    credibility_boost=state.get("credibility_boost", 1.0),
                    is_trusted_investigator=state.get("is_trusted_investigator", False),
                )

                # Add YouTube counter-intelligence to the verification state
                verification_state.youtube_counter_evidence = youtube_counter_evidence

                logger.info(
                    f"🔍 [CLAIM {i+1}] Starting verification for: {claim_text[:80]}..."
                )

                # Use the enhanced verify_claim function
                verification_result = verify_claim(verification_state)

                # SHERLOCK FIX: Circuit breaker - detect consecutive timeouts
                if (
                    verification_result.get("result") == "UNCERTAIN"
                    and "timed out"
                    in verification_result.get("explanation", "").lower()
                ):
                    consecutive_timeouts += 1
                    logger.warning(
                        f"⚠️ [CIRCUIT BREAKER] Timeout detected ({consecutive_timeouts}/{max_consecutive_timeouts})"
                    )

                    if consecutive_timeouts >= max_consecutive_timeouts:
                        logger.error(
                            f"🚨 [CIRCUIT BREAKER] Rate limiting detected after {consecutive_timeouts} consecutive timeouts!"
                        )
                        logger.error(
                            f"🚨 [CIRCUIT BREAKER] Switching to fast-fail mode for remaining {len(claims_to_process) - i - 1} claims"
                        )
                        # Mark remaining claims as uncertain due to rate limiting
                        for remaining_idx in range(i + 1, len(claims_to_process)):
                            remaining_claim = claims_to_process[remaining_idx]
                            verified_claims.append(
                                {
                                    **remaining_claim,
                                    "verification_result": {
                                        "result": "UNCERTAIN",
                                        "explanation": "Skipped due to rate limiting detected on previous claims. API quota likely exhausted.",
                                        "probability_distribution": {
                                            "TRUE": 0.33,
                                            "FALSE": 0.33,
                                            "UNCERTAIN": 0.34,
                                        },
                                        "sources": [],
                                    },
                                    "evidence": [],
                                }
                            )
                        logger.info(
                            f"⏩ [CIRCUIT BREAKER] Skipped {len(claims_to_process) - i - 1} remaining claims"
                        )
                        break  # Exit the claim processing loop
                else:
                    consecutive_timeouts = 0  # Reset on success

                logger.info(
                    f"✅ [CLAIM {i+1}] Verification completed, evidence count: {len(verification_result.get('evidence', []))}"
                )

                # Add rate limiting between claims to avoid API throttling
                import asyncio

                if i < len(claims_to_process) - 1:  # Don't sleep after the last claim
                    # SHERLOCK FIX: Aggressive delays to respect API quotas (10 RPM = 6s minimum)
                    # With 10 RPM default limit: need 6s between requests minimum
                    # We use 8s normally, 15s after timeout for safety margin
                    delay = (
                        8 if consecutive_timeouts == 0 else 15
                    )  # More aggressive delays to respect quotas
                    logger.info(
                        f"⏸️ [QUOTA] Rate limiting: waiting {delay}s before next claim (respecting ~10 RPM API quota)..."
                    )
                    await asyncio.sleep(delay)

                # Fix evidence field - ensure it's a list of EvidenceSource objects, not strings
                raw_evidence = verification_result.get("evidence", [])
                evidence_list = []

                if isinstance(raw_evidence, str):
                    # If evidence is a string, try to extract URLs or use sources
                    if verification_result.get("sources"):
                        # Use sources field (which should be a list of URLs)
                        for source_url in verification_result["sources"]:
                            if isinstance(source_url, str):
                                evidence_list.append(
                                    EvidenceSource(
                                        source_name=f"Source: {source_url.split('/')[-1][:50]}",
                                        source_type="url",
                                        url=source_url,
                                        text=f"Verification source: {source_url}",
                                        title="Verification Source",
                                    )
                                )
                    else:
                        # Try to extract URLs from the string
                        import re

                        urls = re.findall(r"https?://[^\s\n]+", raw_evidence)
                        for url in urls:
                            evidence_list.append(
                                EvidenceSource(
                                    source_name=f"Source: {url.split('/')[-1][:50]}",
                                    source_type="url",
                                    url=url,
                                    text=f"Evidence from verification: {url}",
                                    title="Evidence Source",
                                )
                            )
                elif isinstance(raw_evidence, list):
                    # Convert list items to EvidenceSource objects if needed
                    for item in raw_evidence:
                        if isinstance(item, EvidenceSource):
                            evidence_list.append(item)
                        elif isinstance(item, dict):
                            try:
                                evidence_list.append(EvidenceSource(**item))
                            except Exception as e:
                                logger.warning(
                                    f"Failed to convert dict to EvidenceSource: {e}"
                                )
                        elif isinstance(item, str):
                            evidence_list.append(
                                EvidenceSource(
                                    source_name=f"Source: {item.split('/')[-1][:50] if item.startswith('http') else 'Evidence'}",
                                    source_type=(
                                        "url" if item.startswith("http") else "text"
                                    ),
                                    url=item if item.startswith("http") else None,
                                    text=item,
                                    title="Evidence Source",
                                )
                            )
                else:
                    evidence_list = []

                # Update claim with verification result
                verified_claim = {
                    **claim,
                    "verification_result": verification_result,
                    "evidence": evidence_list,
                }

                verified_claims.append(verified_claim)

                # Add evidence from verification result
                if verification_result.get("sources"):
                    for source_url in verification_result["sources"]:
                        if source_url:  # Only add non-empty sources
                            all_evidence.append(
                                {
                                    "source_name": "Verification Source",
                                    "source_type": "verification",
                                    "url": source_url,
                                    "text": f"Evidence for claim: {claim_text[:100]}...",
                                    "claim_id": i,
                                }
                            )

                result = verification_result.get("result", "UNCERTAIN")
                logger.info(f"✅ Claim {i+1} verified with ENHANCED system: {result}")

                # Log evidence collection details
                if hasattr(
                    verification_result, "pr_sources"
                ) and verification_result.get("pr_sources"):
                    pr_count = len(verification_result["pr_sources"])
                    logger.info(
                        f"📰 Claim {i+1}: Found {pr_count} press release sources"
                    )

                if hasattr(
                    verification_result, "youtube_counter_sources"
                ) and verification_result.get("youtube_counter_sources"):
                    youtube_count = len(verification_result["youtube_counter_sources"])
                    logger.info(
                        f"📺 Claim {i+1}: Found {youtube_count} YouTube counter-intelligence sources"
                    )

            except Exception as e:
                logger.error(
                    f"❌ Failed to verify claim {i+1} with enhanced system: {e}"
                )
                logger.error(f"Claim text: {claim_text}")
                import traceback

                logger.error(traceback.format_exc())

                # Add failed claim with error info
                verified_claims.append(
                    {
                        **claim,
                        "verification_result": {
                            "result": "ERROR",
                            "explanation": f"Enhanced verification failed: {str(e)}",
                            "probability_distribution": {
                                "TRUE": 0.0,
                                "FALSE": 0.0,
                                "UNCERTAIN": 1.0,
                            },
                            "sources": [],
                        },
                        "evidence": [],
                    }
                )

        logger.info(
            f"✅ Completed ENHANCED verification: {len(verified_claims)} claims, {len(all_evidence)} evidence items"
        )

        return {**state, "claims": verified_claims, "aggregated_evidence": all_evidence}

    except Exception as e:
        logger.error(f"❌ Enhanced claim verification failed: {e}")
        import traceback

        logger.error(traceback.format_exc())
        raise


async def search_youtube_reviews(
    claim_text: str, video_title: str, max_results: int = 3
) -> list:
    """Search YouTube for review/response/debunk videos related to the claim."""
    queries = [
        f"{video_title} review",
        f"{video_title} scam",
        f"{video_title} debunk",
        f"{claim_text} review",
        f"{claim_text} scam",
        f"{claim_text} debunk",
        f"{claim_text} response",
    ]
    results = []
    for query in queries:
        try:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,
                "skip_download": True,
                "default_search": "ytsearch",
                "noplaylist": True,
                "max_downloads": max_results,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                search_results = ydl.extract_info(query, download=False)
                for entry in search_results.get("entries", [])[:max_results]:
                    results.append(
                        {
                            "source_name": entry.get("title", "YouTube Review"),
                            "source_type": "YouTube Review",
                            "url": f"https://www.youtube.com/watch?v={entry.get('id', '')}",
                            "text": entry.get("description", ""),
                            "title": entry.get("title", ""),
                            "credibility_level": "LOW",
                            "justification": "YouTube review/response video; may provide contra-claims.",
                        }
                    )
        except Exception as e:
            continue
    return results[:max_results]


async def search_claim_evidence(
    search_tool: SearchTool,
    claim: Dict[str, Any],
    video_url: str,
    video_title: str = "",
) -> List[Dict[str, Any]]:
    """Search for evidence for a specific claim, including YouTube reviews."""
    claim_text = claim.get("claim_text", "")
    logger = logging.getLogger(__name__)
    try:
        # Search for supporting and contradicting evidence
        search_queries = [
            claim_text,
            f"{claim_text} evidence",
            f"{claim_text} fact check",
            f"{claim_text} verify",
        ]
        all_evidence = []
        for query in search_queries[:2]:  # Limit searches
            try:
                results = search_tool.search(query, num_results=5)
                for result in results:
                    evidence_item = {
                        "source_name": result.get("title", "Unknown"),
                        "source_type": "Web",
                        "url": result.get("link", ""),
                        "text": result.get("snippet", ""),
                        "title": result.get("title", ""),
                    }
                    all_evidence.append(evidence_item)
            except Exception as e:
                logger.warning(f"Search failed for query '{query}': {e}")
                continue
        # Add YouTube review/response evidence
        youtube_reviews = await search_youtube_reviews(claim_text, video_title)
        all_evidence.extend(youtube_reviews)
        return all_evidence[:10]
    except Exception as e:
        logger.error(f"Evidence search failed: {e}")
        return []


async def verify_claim_with_evidence(
    claim: Dict[str, Any], evidence: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Verify a claim using the collected evidence."""
    import logging

    logger = logging.getLogger(__name__)

    try:
        from langchain_google_vertexai import ChatVertexAI
        from langchain_core.prompts import ChatPromptTemplate
        from verityngn.config.settings import AGENT_MODEL_NAME

        # SHERLOCK FIX: Add timeout protection
        llm = ChatVertexAI(
            model_name=AGENT_MODEL_NAME,
            temperature=0.1,
            request_timeout=120.0,  # 120 second timeout
        )

        # SHERLOCK FIX: Inject current date context to prevent LLM from treating 2025 sources as "future-dated"
        current_date = get_current_date_context()
        date_context = get_date_context_prompt_section()

        # Format evidence for prompt
        evidence_text = "\n".join(
            [
                f"Source: {item.get('source_name', 'Unknown')}\nURL: {item.get('url', 'N/A')}\nText: {item.get('text', '')[:500]}\n"
                for item in evidence[:5]  # Limit evidence
            ]
        )

        prompt = ChatPromptTemplate.from_template(
            f"""
        {date_context}
        
        Verify this claim using the provided evidence:
        
        Claim: {{claim_text}}
        
        Evidence:
        {{evidence_text}}
        
        Analyze the evidence and determine:
        1. Is the claim TRUE, FALSE, or UNCERTAIN?
        2. Provide a clear explanation
        3. What probability distribution would you assign?
        
        Respond in JSON format:
        {{{{
            "result": "TRUE|FALSE|UNCERTAIN",
            "explanation": "Clear explanation based on evidence",
            "probability_distribution": {{{{"TRUE": 0.0, "FALSE": 0.0, "UNCERTAIN": 0.0}}}},
            "sources": ["url1", "url2"]
        }}}}
        """
        )

        start_time = time.time()
        call_id = log_llm_call(
            operation="verify_claim_with_llm",
            prompt=str(prompt.format(
                claim_text=claim.get("claim_text", ""),
                evidence_text=evidence_text or "No evidence found",
            )),
            model=AGENT_MODEL_NAME,
            video_id=claim.get("video_id") or "unknown"
        )

        response = await llm.ainvoke(
            prompt.format(
                claim_text=claim.get("claim_text", ""),
                evidence_text=evidence_text or "No evidence found",
            )
        )
        duration = time.time() - start_time
        log_llm_response(call_id, response, duration=duration)

        # Parse response - handle different formats
        import json
        import re

        try:
            # Get response content
            response_text = (
                response.content if hasattr(response, "content") else str(response)
            )

            # Try direct JSON parsing first
            try:
                result = json.loads(response_text)
            except json.JSONDecodeError:
                # Extract JSON from markdown code blocks
                json_match = re.search(
                    r"```json\s*\n(.*?)\n```", response_text, re.DOTALL
                )
                if json_match:
                    result = json.loads(json_match.group(1))
                else:
                    # Extract JSON from text
                    json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group(0))
                    else:
                        raise json.JSONDecodeError("No JSON found", response_text, 0)

            # Validate and fix result format
            if not isinstance(result, dict):
                raise ValueError("Result is not a dictionary")

            # Ensure required fields exist
            if "result" not in result:
                result["result"] = "UNCERTAIN"
            if "explanation" not in result:
                result["explanation"] = "No explanation provided"
            if "probability_distribution" not in result:
                result["probability_distribution"] = {
                    "TRUE": 0.1,
                    "FALSE": 0.1,
                    "UNCERTAIN": 0.8,
                }

            # Add source URLs
            result["sources"] = [
                item.get("url", "") for item in evidence if item.get("url")
            ]
            return result

        except Exception as e:
            logger.warning(f"Failed to parse verification result JSON: {e}")
            # Return basic assessment based on evidence availability
            if evidence and len(evidence) > 0:
                return {
                    "result": "UNCERTAIN",
                    "explanation": "Evidence found but parsing failed. Manual review recommended.",
                    "probability_distribution": {
                        "TRUE": 0.3,
                        "FALSE": 0.3,
                        "UNCERTAIN": 0.4,
                    },
                    "sources": [
                        item.get("url", "") for item in evidence if item.get("url")
                    ],
                }
            else:
                return {
                    "result": "LIKELY_FALSE",
                    "explanation": "No supporting evidence found and parsing failed",
                    "probability_distribution": {
                        "TRUE": 0.05,
                        "FALSE": 0.85,
                        "UNCERTAIN": 0.1,
                    },
                    "sources": [],
                }

    except Exception as e:
        logger.error(f"Claim verification failed: {e}")
        return {
            "result": "ERROR",
            "explanation": str(e),
            "probability_distribution": {"TRUE": 0.0, "FALSE": 0.0, "UNCERTAIN": 1.0},
            "sources": [],
        }


from .claim_processor import ClaimProcessor


def process_claims_with_advanced_ranking(
    video_analysis_claims: List[Dict[str, Any]],
    video_id: str,
    video_title: str,
    youtube_counter_evidence: List[Dict[str, Any]] = None,
    press_release_evidence: List[Dict[str, Any]] = None,
    video_duration_minutes: float = 30.0,
    output_dir: str = None,
) -> List[Dict[str, Any]]:
    """
    Process claims using the advanced ClaimProcessor with multi-source integration,
    generalized ranking criteria, semantic clustering, and representative selection.

    Args:
        video_analysis_claims: Claims from multimodal video analysis
        video_id: Video identifier
        video_title: Video title for context
        youtube_counter_evidence: YouTube counter-intelligence claims
        press_release_evidence: Press release counter-intelligence claims
        video_duration_minutes: Video duration in minutes
        output_dir: Directory to save processing reports

    Returns:
        List of processed and ranked claims ready for verification
    """
    logger = logging.getLogger(__name__)

    logger.info(f"🚀 Starting advanced claim processing for video {video_id}")

    # Load configuration
    config = get_config()
    max_claims = config.get('processing.max_claims', 20)
    
    # Initialize the ClaimProcessor
    processor = ClaimProcessor(
        video_id=video_id,
        video_duration_minutes=video_duration_minutes,
        target_claims_per_minute=3.0,  # Target 3 claims per minute (reasonable for dense content analysis)
        max_claims=max_claims,
    )

    # Add video analysis claims
    processor.add_video_analysis_claims(video_analysis_claims)
    ## ajjc: for now, don't add counter-intelligence claims into claims list, as they arent in normal form.
    # # Add YouTube counter-intelligence claims if available
    # if youtube_counter_evidence:
    #     # Convert counter-intelligence evidence to claim format
    #     youtube_claims = []
    #     for i, evidence in enumerate(youtube_counter_evidence):
    #         youtube_claim = {
    #             'claim_id': f"yt_counter_{i}",
    #             'claim_text': evidence.get('text', evidence.get('title', 'YouTube counter-intelligence evidence')),
    #             'timestamp': '00:00',  # Counter-intelligence doesn't have video timestamps
    #             'speaker': 'YouTube Counter-Intelligence',
    #             'initial_assessment': f"Counter-intelligence evidence with credibility level {evidence.get('credibility_level', 'UNKNOWN')}"
    #         }
    #         youtube_claims.append(youtube_claim)
    #     processor.add_youtube_counter_claims(youtube_claims)

    # # Add press release claims if available
    # if press_release_evidence:
    #     # Convert press release evidence to claim format
    #     press_claims = []
    #     for i, evidence in enumerate(press_release_evidence):
    #         press_claim = {
    #             'claim_id': f"pr_counter_{i}",
    #             'claim_text': evidence.get('text', evidence.get('title', 'Press release counter-intelligence evidence')),
    #             'timestamp': '00:00',  # Counter-intelligence doesn't have video timestamps
    #             'speaker': 'Press Release Counter-Intelligence',
    #             'initial_assessment': f"Press release evidence with credibility level {evidence.get('credibility_level', 'UNKNOWN')}"
    #         }
    #         press_claims.append(press_claim)
    #     processor.add_press_release_claims(press_claims)

    # Process all claims through the advanced pipeline
    final_claims = processor.process_all_claims()

    # Save processing report if output directory is provided
    if output_dir:
        try:
            processor.save_claim_processing_report(output_dir)
        except Exception as e:
            logger.warning(f"Failed to save claim processing report: {e}")

    logger.info(
        f"✅ Advanced claim processing complete: {len(final_claims)} claims selected for verification"
    )

    return final_claims
