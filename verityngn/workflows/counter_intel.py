"""
VerityNgn Counter Intelligence Module

This module searches for contradictory evidence and alternative perspectives
on YouTube to detect potential scams, misinformation, or biased content.

It uses:
1. Deep web search with LLM-driven query generation
2. YouTube-specific search for reviews, debunks, and warnings
3. Channel expansion to find topic-related videos
4. Deduplication and relevance filtering
5. ENHANCED: Transcript analysis of counter-evidence videos

The counter-intelligence results are used to balance the verification
process and provide alternative viewpoints.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Import enhanced transcript analysis
try:
    from verityngn.config.enhanced_settings import (
        YOUTUBE_TRANSCRIPT_ANALYSIS_ENABLED,
        YOUTUBE_TRANSCRIPT_MAX_VIDEOS,
    )
except ImportError:
    YOUTUBE_TRANSCRIPT_ANALYSIS_ENABLED = True
    YOUTUBE_TRANSCRIPT_MAX_VIDEOS = 3


def _is_file_upload_state(state: Dict[str, Any]) -> bool:
    if state.get("ingest_source") == "file_upload":
        return True
    url = state.get("video_url") or ""
    return isinstance(url, str) and url.startswith("upload://")


def run_counter_intel_once(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run YouTube counter-intelligence search once after initial analysis.

    This function searches for contradictory evidence about the video,
    including:
    - Review videos
    - Scam warnings
    - Debunk videos
    - Alternative perspectives

    Uses the video's title, description, tags, and initial analysis as context
    to generate relevant search queries.

    Args:
        state: Workflow state containing:
            - video_id: YouTube video ID
            - video_info: Video metadata (title, description, tags)
            - initial_report: Results from initial analysis
            - claims: Extracted claims (if available)

    Returns:
        Updated state with counter-intelligence results in state['ci_once']

    The results are stored as a list of dictionaries with:
    - url: Link to counter-intelligence source
    - title: Title of the source
    - source_type: Type of source (youtube_counter_intelligence, web, etc.)
    """
    if state.get("video_availability") in ["Not Available", "Not Processed"] or not state.get("claims"):
        logger.info("⏭️ Skipping counter-intelligence due to empty claims or unavailability.")
        state["ci_once"] = []
        return state

    is_file_upload = _is_file_upload_state(state)

    video_id = state.get("video_id", "")
    video_info = state.get("video_info") or {}
    title = (video_info.get("title") or state.get("upload_title") or "").strip()

    logger.info(f"🔎 Running counter-intelligence for video: {video_id}")

    # Get initial report for context
    initial = state.get("initial_report") or {}
    initial_text = (initial.get("initial_report") or initial.get("summary") or "")[
        :4000
    ]

    # Fetch video metadata if not already available (YouTube only)
    if not title and not is_file_upload:
        try:
            # Try private repo module first
            from verityngn.services.video.metadata import fetch_video_metadata

            meta = fetch_video_metadata(video_id)
            title = meta.get("title") or title
            desc = meta.get("description", "")
            tags = meta.get("tags", [])
            if not initial_text:
                initial_text = (desc + "\n" + " ".join(tags))[:4000]
        except ImportError:
            # Fallback: Use video_info if available
            if video_info and video_info.get("title"):
                title = video_info.get("title")
            logger.debug("Using video_info for metadata (private module not available)")
        except Exception as e:
            logger.warning(f"Could not fetch video metadata: {e}")

    # Build context for search
    video_desc = video_info.get("description", "") or ""
    tags_list = video_info.get("tags", []) or []

    # Extract claims for additional context
    claims = []
    try:
        claims = [
            c.get("claim_text", "")
            for c in (state.get("claims") or [])
            if isinstance(c, dict)
        ]
    except Exception:
        claims = []

    # Prepare search context
    search_context = {
        "title": title or f"Video {video_id}",
        "video_id": video_id,
        "description": video_desc,
        "tags": tags_list,
        "initial_report": initial_text,
        "summary_report": (initial.get("summary") or ""),
        "claims": claims,
    }

    sherlock_links = []
    try:
        from verityngn.config.settings import USE_SHERLOCK_CI
    except ImportError:
        USE_SHERLOCK_CI = False

    if USE_SHERLOCK_CI:
        logger.info("🕵️‍♂️ [SHERLOCK CI] Running new Web Grounded LLM Counter-Intelligence...")
        from verityngn.services.search.sherlock_ci import generate_sherlock_ci_report
        
        ci_report = generate_sherlock_ci_report(
            video_title=search_context["title"],
            video_description=search_context["description"],
            claims=search_context["claims"],
            context=search_context["initial_report"]
        )
        
        state["sherlock_ci_report"] = ci_report
        
        # Map sources to ci_once for downstream compatibility
        if ci_report and isinstance(ci_report.get("sources"), list):
            for src in ci_report.get("sources", []):
                sherlock_links.append({
                    "url": src.get("url", ""),
                    "title": src.get("title", ""),
                    "source_type": "web",
                    "text": ci_report.get("executive_summary", "")[:200]
                })
                
        logger.info(f"✅ Sherlock CI mapped {len(sherlock_links)} links for later merging.")

    # Track YouTube and Google searches for metrics
    _youtube_searches = 0

    # Run deep counter-intelligence search (primary method)
    deep_links = []
    try:
        # Try private repo deep CI module
        from verityngn.services.search.deep_ci import deep_counter_intel_search

        deep_links = deep_counter_intel_search(search_context, max_links=4)
        logger.info(f"✅ Deep CI found {len(deep_links)} links")
    except ImportError:
        # OSS version: use Google CSE as fallback when deep_ci is unavailable
        logger.info("Deep CI module not available (private repo feature); using Google web search fallback")
        deep_links = _oss_google_ci_fallback(search_context)
    except Exception as e:
        logger.warning(f"Deep CI search failed: {e}")
        deep_links = []

    # Fallback to YouTube API search (YouTube sources only)
    api_results = []
    if not is_file_upload:
        try:
            from verityngn.config.settings import YOUTUBE_API_ENABLED

            if YOUTUBE_API_ENABLED:
                try:
                    # Try private repo module first
                    from verityngn.services.search.youtube_api import (
                        search_counter_intelligence,
                    )

                    _youtube_searches += 1
                    api_results = search_counter_intelligence(
                        title or f"Video {video_id}",
                        context=initial_text or None,
                        video_id=video_id,
                        max_results=4,
                    )
                    logger.info(
                        f"✅ YouTube API (private) found {len(api_results)} additional results"
                    )
                except ImportError:
                    # OSS FALLBACK: Use public youtube_search module
                    logger.info(
                        "📦 Using OSS YouTube search (private module not available)"
                    )
                    try:
                        from verityngn.services.search.youtube_search import (
                            search_youtube_counter_intelligence_with_context,
                        )

                        _youtube_searches += 1
                        api_results = search_youtube_counter_intelligence_with_context(
                            video_title=title or f"Video {video_id}",
                            initial_review_text=initial_text or None,
                            video_id=video_id,
                            max_results=4,
                        )
                        logger.info(
                            f"✅ OSS YouTube search found {len(api_results)} counter-intel results"
                        )
                    except Exception as oss_error:
                        logger.error(f"❌ OSS YouTube search also failed: {oss_error}")
                        api_results = []
        except Exception as e:
            logger.warning(f"YouTube API search failed: {e}")

    # Expand YouTube channel URLs to specific videos
    expanded_links = []
    try:
        # Extract topic terms for targeted channel expansion
        topic_terms = _extract_topic_terms(title, video_desc, tags_list)
        generic_terms = ["review", "scam", "debunk", "warning"]
        search_terms = (topic_terms + generic_terms)[:6]

        for link in deep_links:
            url = link.get("url", "")
            if not url:
                continue

            # Check if this is a channel URL
            if any(
                pattern in url
                for pattern in [
                    "youtube.com/@",
                    "youtube.com/channel/",
                    "youtube.com/user/",
                ]
            ):
                # Expand channel to specific videos
                from verityngn.services.search.channel_expand import (
                    expand_channel_to_videos,
                )

                videos = expand_channel_to_videos(url, search_terms, max_results=3)

                if videos:
                    for v in videos:
                        expanded_links.append(
                            {
                                "url": v.get("url", ""),
                                "title": v.get("title", ""),
                                "source_type": "youtube_counter_intelligence",
                            }
                        )
                else:
                    # Keep original channel link if expansion fails
                    expanded_links.append(link)
            else:
                # Keep non-channel links as-is
                expanded_links.append(link)

    except Exception as e:
        logger.warning(f"Channel expansion failed: {e}")
        expanded_links = deep_links

    # Merge and deduplicate results
    merged_results = []
    seen_urls = set()

    # Add Sherlock CI results first
    for result in sherlock_links:
        url = result.get("url", "")
        if url and url not in seen_urls:
            merged_results.append(result)
            seen_urls.add(url)

    # Add API results next (if any)
    for result in api_results:
        url = result.get("url", "")
        if url and url not in seen_urls:
            merged_results.append(result)
            seen_urls.add(url)

    # Add expanded links
    for link in expanded_links:
        url = link.get("url", "")
        if url and url not in seen_urls:
            merged_results.append(link)
            seen_urls.add(url)

    # Store results in state
    from verityngn.services.reputation.url_safety import filter_safe_evidence

    state["ci_once"] = filter_safe_evidence(merged_results)
    state["_metrics_youtube_searches"] = state.get("_metrics_youtube_searches", 0) + _youtube_searches

    if len(merged_results) == 0:
        logger.warning(
            f"⚠️  Counter-intelligence found ZERO results for video {video_id}. "
            "This may indicate:\n"
            "   1. Private repo modules not available (expected for OSS)\n"
            "   2. YouTube API key not configured (check .env)\n"
            "   3. Google Search API key not configured (check .env)\n"
            "   4. Network/API errors occurred\n"
            "Check logs above for specific errors."
        )
    else:
        logger.info(
            f"✅ Counter-intelligence complete: {len(merged_results)} total links"
        )
        logger.info(f"   Sources: {'API + ' if api_results else ''}Deep Search")

    # ENHANCED: Analyze transcripts of counter-videos if enabled
    if YOUTUBE_TRANSCRIPT_ANALYSIS_ENABLED and merged_results:
        try:
            logger.info(
                "🎯 ENHANCED: Analyzing transcripts of top "
                f"{YOUTUBE_TRANSCRIPT_MAX_VIDEOS} counter-videos"
            )
            from verityngn.workflows.youtube_transcript_analysis import (
                enhance_youtube_counter_intelligence,
            )
            import asyncio

            # Run transcript analysis
            enhanced_results = asyncio.run(
                enhance_youtube_counter_intelligence(
                    counter_videos=merged_results,
                    max_videos_to_analyze=YOUTUBE_TRANSCRIPT_MAX_VIDEOS,
                )
            )

            state["ci_once"] = enhanced_results
            logger.info(f"✅ Enhanced counter-intelligence with transcript analysis")
        except Exception as e:
            logger.warning(
                f"⚠️  Transcript analysis failed: {e}. Continuing with basic CI."
            )

    return state


def _generate_ci_search_queries_oss(search_context: Dict[str, Any]) -> List[str]:
    """Generate 3-5 counter-intelligence search queries (OSS fallback when deep_ci unavailable)."""
    title = (search_context.get("title") or "").strip() or "video"
    initial = (search_context.get("initial_report") or "")[:2000]
    claims_preview = " ".join((search_context.get("claims") or [])[:5])[:500]
    try:
        from langchain_google_vertexai import ChatVertexAI
        from langchain_core.prompts import ChatPromptTemplate
        from verityngn.config.settings import AGENT_MODEL_NAME, PROJECT_ID, VERTEX_LOCATION

        llm = ChatVertexAI(
            model_name=AGENT_MODEL_NAME,
            temperature=0.2,
            max_output_tokens=1024,
            project=PROJECT_ID,
            location=VERTEX_LOCATION,
        )
        prompt = ChatPromptTemplate.from_template(
            "Generate exactly 3 to 5 short search queries to find counter-evidence, reviews, debunks, or fact-checks about this video. "
            "Use only the video title and context below. Return one query per line, no numbering or bullets.\n\n"
            "Title: {title}\n\nContext: {context}\n\nQueries (one per line):"
        )
        response = llm.invoke(
            prompt.format(title=title, context=(initial or "") + " " + (claims_preview or ""))
        )
        text = (response.content or "").strip()
        queries = [q.strip() for q in text.split("\n") if q.strip()][:5]
        if queries:
            return queries
    except Exception as e:
        logger.debug("LLM CI query generation failed, using heuristic: %s", e)
    # Heuristic fallback
    return [
        f"{title} review",
        f"{title} fact check",
        f"{title} debunk",
        f"{title} scam warning",
        f"{title} controversy",
    ][:5]


def _oss_google_ci_fallback(search_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """When deep_ci is unavailable, use Google Custom Search for counter-intelligence (OSS)."""
    try:
        from verityngn.config.settings import ENABLE_GOOGLE_SEARCH
        from verityngn.services.search.web_search import (
            GoogleSearchAPIError,
            search_for_evidence,
        )
    except ImportError:
        return []
    if not ENABLE_GOOGLE_SEARCH:
        logger.info("Google search disabled; skipping OSS CI web fallback")
        return []
    queries = _generate_ci_search_queries_oss(search_context)
    seen_urls = set()
    deep_links = []
    for q in queries:
        if not q:
            continue
        try:
            results = search_for_evidence(q, num_results=5)
        except GoogleSearchAPIError as api_err:
            logger.warning(
                "CI search unavailable (API access): %s. Check Custom Search API setup.",
                api_err,
            )
            break
        except Exception as e:
            logger.warning("OSS CI search failed for query %r: %s", q[:50], e)
            continue
        for r in results:
            url = r.get("url") or r.get("link") or ""
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            deep_links.append({
                "url": url,
                "title": r.get("title") or r.get("source_name") or "",
                "source_type": "web",
            })
    logger.info("OSS Google CI fallback found %s web links", len(deep_links))
    return deep_links


def _extract_topic_terms(title: str, description: str, tags: List[str]) -> List[str]:
    """
    Extract topic-specific terms from video metadata for targeted search.

    Args:
        title: Video title
        description: Video description
        tags: Video tags

    Returns:
        List of topic terms (max 3)
    """
    import re

    # Prefer provided tags
    if tags:
        topic_terms = []
        for tag in tags[:5]:
            if isinstance(tag, str) and tag.strip():
                topic_terms.append(tag.strip().lower())
        if topic_terms:
            return topic_terms[:3]

    # Extract from title/description
    text = (title or "").lower()
    if not text:
        text = (description or "").lower()

    # Tokenize
    tokens = re.findall(r"[a-z0-9][a-z0-9\-\_]{2,}", text)

    # Filter out common stop words
    stop_words = {
        "the",
        "and",
        "for",
        "with",
        "this",
        "that",
        "your",
        "you",
        "are",
        "was",
        "were",
        "have",
        "has",
        "had",
        "from",
        "into",
        "over",
        "under",
        "about",
        "very",
        "more",
        "most",
        "less",
        "least",
        "best",
        "worst",
        "exclusive",
        "interview",
        "real",
        "way",
        "quickly",
        "better",
        "health",
        "video",
        "watch",
        "learn",
        "today",
        "secret",
        "trick",
        "hack",
    }

    # Extract meaningful terms
    topic = []
    for token in tokens:
        if token in stop_words:
            continue
        if token.isdigit():
            continue
        if token not in topic:
            topic.append(token)
        if len(topic) >= 3:
            break

    return topic
