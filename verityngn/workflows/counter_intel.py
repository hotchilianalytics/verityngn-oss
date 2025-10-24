"""
VerityNgn Counter Intelligence Module

This module searches for contradictory evidence and alternative perspectives
on YouTube to detect potential scams, misinformation, or biased content.

It uses:
1. Deep web search with LLM-driven query generation
2. YouTube-specific search for reviews, debunks, and warnings  
3. Channel expansion to find topic-related videos
4. Deduplication and relevance filtering

The counter-intelligence results are used to balance the verification
process and provide alternative viewpoints.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


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
    video_id = state.get("video_id", "")
    video_info = state.get("video_info") or {}
    title = (video_info.get("title") or "").strip()

    logger.info(f"🔎 Running counter-intelligence for video: {video_id}")
    
    # Get initial report for context
    initial = state.get("initial_report") or {}
    initial_text = (initial.get("initial_report") or initial.get("summary") or "")[:4000]

    # Fetch video metadata if not already available
    if not title:
        try:
            from verityngn.services.video.metadata import fetch_video_metadata
            meta = fetch_video_metadata(video_id)
            title = meta.get("title") or title
            desc = meta.get("description", "")
            tags = meta.get("tags", [])
            if not initial_text:
                initial_text = (desc + "\n" + " ".join(tags))[:4000]
        except Exception as e:
            logger.warning(f"Could not fetch video metadata: {e}")
            pass

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

    # Run deep counter-intelligence search (primary method)
    deep_links = []
    try:
        from verityngn.services.search.deep_ci import deep_counter_intel_search
        deep_links = deep_counter_intel_search(search_context, max_links=4)
        logger.info(f"✅ Deep CI found {len(deep_links)} links")
    except Exception as e:
        logger.warning(f"Deep CI search failed: {e}")
        deep_links = []

    # Fallback to YouTube API search (if configured and needed)
    api_results = []
    has_youtube_links = any(
        isinstance(x, dict) and 'youtube' in (x.get('url', ''))
        for x in deep_links
    )
    
    if not has_youtube_links:
        try:
            from verityngn.config.settings import YOUTUBE_API_ENABLED
            if YOUTUBE_API_ENABLED:
                from verityngn.services.search.youtube_api import search_counter_intelligence
                api_results = search_counter_intelligence(
                    title or f"Video {video_id}",
                    context=initial_text or None,
                    video_id=video_id,
                    max_results=4
                )
                logger.info(f"✅ YouTube API found {len(api_results)} additional results")
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
            if any(pattern in url for pattern in [
                "youtube.com/@",
                "youtube.com/channel/",
                "youtube.com/user/"
            ]):
                # Expand channel to specific videos
                from verityngn.services.search.channel_expand import expand_channel_to_videos
                videos = expand_channel_to_videos(url, search_terms, max_results=3)
                
                if videos:
                    for v in videos:
                        expanded_links.append({
                            "url": v.get("url", ""),
                            "title": v.get("title", ""),
                            "source_type": "youtube_counter_intelligence"
                        })
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
    
    # Add API results first (if any)
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
    state["ci_once"] = merged_results
    
    logger.info(f"✅ Counter-intelligence complete: {len(merged_results)} total links")
    logger.info(f"   Sources: {'API + ' if api_results else ''}Deep Search")
    
    return state


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
        "the", "and", "for", "with", "this", "that", "your", "you",
        "are", "was", "were", "have", "has", "had", "from", "into",
        "over", "under", "about", "very", "more", "most", "less",
        "least", "best", "worst", "exclusive", "interview", "real",
        "way", "quickly", "better", "health", "video", "watch",
        "learn", "today", "secret", "trick", "hack"
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


