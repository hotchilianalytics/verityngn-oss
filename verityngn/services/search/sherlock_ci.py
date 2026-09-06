"""
Sherlock CI (Counter Intelligence) Module using Google Search Grounding.
"""
import logging
import json
from typing import Dict, Any
from verityngn.utils.llm_utils import invoke_json_prompt_with_fallback

logger = logging.getLogger(__name__)

def generate_sherlock_ci_report(
    video_title: str, 
    video_description: str, 
    claims: list,
    context: str = ""
) -> Dict[str, Any]:
    """
    Generate a JSON Counter-Intelligence report using Gemini Flash with Google Search Grounding.
    """
    logger.info("🕵️‍♂️ [SHERLOCK CI] Initiating Google Search Grounded CI analysis...")
    
    try:
        from verityngn.config.settings import PROJECT_ID, AGENT_MODEL_NAME
        
        try:
            from google import genai
            from google.genai import types
        except ImportError as e:
            logger.warning(f"❌ [SHERLOCK CI] google.genai not available for grounding: {e}")
            return {}

        # Construct the prompt
        claims_text = "\n".join([f"- {c}" for c in claims[:10]]) if claims else "None provided."
        
        prompt = f"""
You are an expert Counter-Intelligence investigator. Your job is to search the web for external evidence regarding the claims made in the following video.
Bypass the video's own claims and find what OTHERS are saying across the open web (Reddit, TrustPilot, BBB, news articles, FDA warnings, fact-checks, YouTube debunks).

Video Title: {video_title}
Video Description: {video_description}
Key Claims:
{claims_text}
Additional Context: {context}

INSTRUCTIONS:
1. Search for complaints, debunks, BBB ratings, scam reports, OR positive reviews/evidence validating the topic.
2. Determine the overall sentiment of the external research. 
   CRITICAL GUIDELINES FOR SCAM VS MIXED CLASSIFICATION:
   - If > 12% of the discussed claims or external reviews have definitively negative or FALSE findings, classify the sentiment as "MIXED".
   - If > 20% of the discussed claims or external reviews have definitively negative, FALSE findings, or expose fraud, classify it as "SCAM".
   - Otherwise, classify as "POSITIVE" or "NEUTRAL".
3. Return the results strictly as a JSON object matching this schema:
{{
  "executive_summary": "A 2-3 paragraph summary of the external consensus and findings.",
  "sentiment": "POSITIVE|NEUTRAL|MIXED|SCAM",
  "key_findings": ["Finding 1", "Finding 2"],
  "sources": [
    {{"url": "https://...", "title": "Source Title"}}
  ]
}}

IMPORTANT: Ensure the output is valid JSON.
"""
        
        # We pass grounding natively via config tools
        ci_report, result_text, meta, response = invoke_json_prompt_with_fallback(
            primary_model=AGENT_MODEL_NAME or "gemini-3.8-flash",
            prompt=prompt,
            project_id=PROJECT_ID,
            preferred_tokens=2048,
            temperature=0.2,
            tools=[{"google_search": {}}],
            logger=logger,
        )
        result_text = result_text.strip()
        logger.info(
            "sherlock_ci backend_selected=%s model_selected=%s location_selected=%s fallback_hops=%s",
            meta.get("backend_selected"),
            meta.get("model_selected"),
            meta.get("location_selected"),
            meta.get("fallback_hops"),
        )
        
        # Strip markdown if model ignored the instruction
        if result_text.startswith("```json"):
            result_text = result_text.replace("```json", "").replace("```", "").strip()
            
        if not ci_report:
            ci_report = json.loads(result_text)
        
        # Attempt to map Google Search sources if the LLM didn't format them,
        # using the raw grounding metadata from the response!
        try:
            if not ci_report.get("sources"):
                grounding_sources = []
                for cand in response.candidates:
                    meta = getattr(cand, "grounding_metadata", None)
                    if meta:
                        chunks = getattr(meta, "grounding_chunks", None) or getattr(meta, "grounding_supports", None)
                        if chunks:
                            for chunk in chunks:
                                web = getattr(chunk, "web", None)
                                if web and hasattr(web, "uri") and web.uri:
                                    from verityngn.services.reputation.url_safety import is_safe_url
                                    if not is_safe_url(web.uri):
                                        continue
                                    grounding_sources.append({
                                        "url": web.uri,
                                        "title": getattr(web, "title", "Google Search Context")
                                    })
                if grounding_sources:
                    ci_report["sources"] = grounding_sources[:5]
        except Exception as source_e:
            logger.warning(f"Failed to parse native grounding chunks: {source_e}")

        logger.info(f"✅ [SHERLOCK CI] Successfully generated grounded CI report (Sentiment: {ci_report.get('sentiment')})")
        return ci_report
        
    except Exception as e:
        logger.error(f"❌ [SHERLOCK CI] Failed to generate CI report: {e}", exc_info=True)
        return {}
