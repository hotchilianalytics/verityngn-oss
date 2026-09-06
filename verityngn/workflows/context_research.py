"""
Video context research: LLM-generated queries + Google CSE to gather
background on the video subject (e.g. CZ/Binance conviction) for verification.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)
from verityngn.utils.llm_utils import invoke_text_prompt_with_fallback


def run_context_research(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    After initial analysis, research the video subject via Google CSE and
    summarize findings into state['context_research'] for verification.
    """
    if state.get("video_availability") in ["Not Available", "Not Processed"] or not state.get("claims"):
        logger.info("⏭️ Skipping context research due to empty claims or unavailability.")
        state["context_research"] = ""
        return state
        
    video_id = state.get("video_id", "")
    video_info = state.get("video_info") or {}
    title = (
        (video_info.get("title") or "").strip()
        or (state.get("upload_title") or "").strip()
    )
    description = (video_info.get("description") or "")[:3000]
    initial = state.get("initial_report") or {}
    if isinstance(initial, str):
        initial_text = initial[:2000]
    elif isinstance(initial, dict):
        initial_text = (
            initial.get("initial_report") or initial.get("summary") or ""
        )[:2000]
    else:
        initial_text = ""

    logger.info("📚 Running context research for video: %s", video_id)

    try:
        from verityngn.config.settings import ENABLE_GOOGLE_SEARCH
    except ImportError:
        state["context_research"] = ""
        return state
    if not ENABLE_GOOGLE_SEARCH:
        logger.info("Google search disabled; skipping context research")
        state["context_research"] = ""
        return state

    queries = _generate_context_queries(title, description, initial_text)
    if not queries:
        state["context_research"] = ""
        return state

    raw_results: List[Dict[str, Any]] = []
    try:
        from verityngn.services.search.web_search import search_for_evidence
    except ImportError:
        state["context_research"] = ""
        return state

    for q in queries[:5]:
        if not q:
            continue
        try:
            results = search_for_evidence(q, num_results=5)
            for r in results:
                raw_results.append({
                    "title": r.get("title") or r.get("source_name", ""),
                    "url": r.get("url") or r.get("link", ""),
                    "text": (
                        (r.get("text") or r.get("snippet", ""))[:600]
                    ),
                })
        except Exception as e:
            logger.warning("Context search failed for %r: %s", q[:50], e)

    if not raw_results:
        state["context_research"] = ""
        return state

    summary = _summarize_context(title, raw_results)
    state["context_research"] = summary
    logger.info("✅ Context research summary length: %s chars", len(summary))
    return state


def _generate_context_queries(
    title: str, description: str, initial_text: str
) -> List[str]:
    """Generate 3-5 search queries about the video subject (LLM or heuristic)."""  # noqa: E501
    context = (
        f"Title: {title}\nDescription: {description[:1500]}\n"
        f"Summary: {initial_text[:1000]}"
    )
    try:
        from verityngn.config.settings import AGENT_MODEL_NAME, PROJECT_ID

        text, meta, _response = invoke_text_prompt_with_fallback(
            primary_model=AGENT_MODEL_NAME,
            prompt=(
                "Generate 3 to 5 short search queries to find authoritative "
                "background on the SUBJECT of this video (e.g. person, company, "
                "event, topic). Goal: find factual context (legal outcomes, "
                "official actions, reputable reporting) to help verify claims. "
                "One query per line, no numbering.\n\n"
                f"{context}\n\nQueries (one per line):"
            ),
            project_id=PROJECT_ID,
            preferred_tokens=1024,
            temperature=0.2,
            logger=logger,
        )
        queries = [q.strip() for q in text.split("\n") if q.strip()][:5]
        if queries:
            return queries
    except Exception as e:
        logger.debug("Context query LLM failed, using heuristic: %s", e)

    # Heuristic: title + topic keywords
    t = (title or "video").strip()
    return [
        f"{t} official",
        f"{t} facts",
        f"{t} news",
    ][:5]


def _summarize_context(
    title: str, raw_results: List[Dict[str, Any]]
) -> str:
    """Summarize search results into short background text for the verifier."""
    if not raw_results:
        return ""
    # Dedupe by url
    seen = set()
    unique = []
    for r in raw_results:
        url = r.get("url", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(r)
    raw_results = unique[:15]

    blocks = []
    for r in raw_results:
        title_s = (r.get("title") or "").strip()
        text_s = (r.get("text") or "").strip()
        if text_s:
            blocks.append(f"[{title_s}]: {text_s}")
    combined = "\n\n".join(blocks)[:8000]

    try:
        from verityngn.config.settings import AGENT_MODEL_NAME, PROJECT_ID

        text, meta, _response = invoke_text_prompt_with_fallback(
            primary_model=AGENT_MODEL_NAME,
            prompt=(
                "Summarize the following search results into a concise background "
                f'note (2-4 short paragraphs) about the video subject: "{title}". '
                "Include only factual, verifiable information that would help a "
                "fact-checker assess claims made in the video. No speculation.\n\n"
                f"Search results:\n{combined}"
            ),
            project_id=PROJECT_ID,
            preferred_tokens=2048,
            temperature=0.2,
            logger=logger,
        )
        return text
    except Exception as e:
        logger.warning("Context summary LLM failed: %s", e)
        return combined[:3000]
