"""
YouTube Counter-Intelligence Transcript Analysis

Downloads and analyzes transcripts from debunking/counter-evidence videos
to extract counter-claims and strengthen verification.
"""

import logging
from typing import Dict, Any, List
import re

logger = logging.getLogger(__name__)


async def analyze_counter_video_transcript(
    video_id: str,
    video_title: str,
    video_description: str = "",
    max_transcript_length: int = 10000,
) -> Dict[str, Any]:
    """
    Download and analyze transcript from a counter-intelligence video.

    Args:
        video_id: YouTube video ID
        video_title: Video title (for context)
        video_description: Video description (for context)
        max_transcript_length: Max characters to analyze

    Returns:
        Dictionary with counter-claims and analysis
    """
    logger.info(f"📝 Analyzing transcript for counter-video: {video_id}")

    try:
        # Try to get transcript using youtube_transcript_api
        from youtube_transcript_api import YouTubeTranscriptApi

        try:
            # Get transcript (prefer English)
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # Try to get English transcript
            transcript = None
            try:
                transcript = transcript_list.find_transcript(["en"]).fetch()
            except Exception:
                # Fall back to auto-generated or first available
                try:
                    transcript = transcript_list.find_generated_transcript(
                        ["en"]
                    ).fetch()
                except Exception:
                    # Get first available transcript
                    for t in transcript_list:
                        transcript = t.fetch()
                        break

            if not transcript:
                logger.warning(f"No transcript available for video {video_id}")
                return {
                    "success": False,
                    "error": "No transcript available",
                    "counter_claims": [],
                }

            # Combine transcript segments
            full_text = " ".join([entry["text"] for entry in transcript])

            # Limit length
            if len(full_text) > max_transcript_length:
                full_text = full_text[:max_transcript_length] + "..."

            logger.info(f"✅ Downloaded transcript: {len(full_text)} characters")

            # Analyze transcript with LLM to extract counter-claims
            counter_claims = await _extract_counter_claims_from_transcript(
                full_text, video_title, video_description
            )

            return {
                "success": True,
                "video_id": video_id,
                "video_title": video_title,
                "transcript_length": len(full_text),
                "transcript_snippet": (
                    full_text[:500] + "..." if len(full_text) > 500 else full_text
                ),
                "counter_claims": counter_claims,
            }

        except Exception as e:
            logger.warning(f"Could not fetch transcript for {video_id}: {e}")
            return {"success": False, "error": str(e), "counter_claims": []}

    except ImportError:
        logger.error(
            "youtube_transcript_api not installed. Install with: pip install youtube-transcript-api"
        )
        return {
            "success": False,
            "error": "youtube_transcript_api not installed",
            "counter_claims": [],
        }


async def _extract_counter_claims_from_transcript(
    transcript_text: str, video_title: str, video_description: str
) -> List[Dict[str, Any]]:
    """
    Extract counter-claims from a debunking video transcript using LLM.

    Args:
        transcript_text: Full transcript text
        video_title: Video title for context
        video_description: Video description for context

    Returns:
        List of counter-claims with credibility scores
    """
    from langchain_google_vertexai import ChatVertexAI
    from langchain_core.prompts import ChatPromptTemplate
    import json

    logger.info("🤖 Using LLM to extract counter-claims from transcript")

    prompt = ChatPromptTemplate.from_template(
        """
You are analyzing a YouTube video that appears to be debunking or warning about a product/claim.

Video Title: {video_title}
Video Description: {video_description}

Transcript (first 10,000 chars):
{transcript}

Extract 3-5 KEY COUNTER-CLAIMS that challenge the original video's assertions.
Focus on:
- Factual contradictions (e.g., "No study by Harvard exists")
- Missing evidence (e.g., "Dr. X has no medical license")
- Exposed fabrications (e.g., "The before/after photos are stock images")
- Credibility issues (e.g., "This person was sued for fraud")

Return ONLY valid JSON (no markdown, no code fences):
{{
  "counter_claims": [
    {{
      "claim_text": "Specific counter-claim extracted from transcript",
      "evidence_snippet": "Quote from transcript supporting this counter-claim",
      "credibility_score": 0.0-1.0,
      "claim_type": "contradiction|missing_evidence|fabrication|credibility"
    }}
  ]
}}
"""
    )

    try:
        llm = ChatVertexAI(
            model_name="gemini-2.0-flash-exp", temperature=0.1, max_output_tokens=2048
        )

        messages = prompt.format_messages(
            video_title=video_title,
            video_description=video_description,
            transcript=transcript_text[:10000],
        )

        response = llm.invoke(messages)
        response_text = response.content.strip()

        # Clean response (remove markdown if present)
        response_text = re.sub(r"^```json\s*", "", response_text)
        response_text = re.sub(r"\s*```$", "", response_text)

        # Parse JSON
        result = json.loads(response_text)
        counter_claims = result.get("counter_claims", [])

        logger.info(
            f"✅ Extracted {len(counter_claims)} counter-claims from transcript"
        )

        return counter_claims

    except Exception as e:
        logger.error(f"Failed to extract counter-claims with LLM: {e}")
        return []


async def enhance_youtube_counter_intelligence(
    counter_videos: List[Dict[str, Any]], max_videos_to_analyze: int = 3
) -> List[Dict[str, Any]]:
    """
    Enhance YouTube counter-intelligence by analyzing transcripts.

    Args:
        counter_videos: List of counter-intelligence video results
        max_videos_to_analyze: Maximum number of transcripts to analyze

    Returns:
        Enhanced counter-intelligence with transcript analysis
    """
    logger.info(f"🎯 Enhancing counter-intelligence for {len(counter_videos)} videos")

    enhanced_results = []
    analyzed_count = 0

    for video in counter_videos:
        video_id = video.get("id") or video.get("video_id")
        if not video_id:
            # Skip if no video ID
            enhanced_results.append(video)
            continue

        # Check if this looks like a debunking/warning video
        title = video.get("title", "").lower()
        description = video.get("description", "").lower()

        is_counter_video = any(
            keyword in title or keyword in description
            for keyword in [
                "scam",
                "fake",
                "fraud",
                "warning",
                "beware",
                "exposed",
                "debunk",
                "review",
                "doesn't work",
                "waste",
            ]
        )

        if is_counter_video and analyzed_count < max_videos_to_analyze:
            logger.info(f"📝 Analyzing transcript for: {video.get('title', video_id)}")

            # Analyze transcript
            transcript_analysis = await analyze_counter_video_transcript(
                video_id=video_id,
                video_title=video.get("title", ""),
                video_description=video.get("description", ""),
            )

            # Add transcript analysis to video data
            video["transcript_analysis"] = transcript_analysis
            video["has_transcript_analysis"] = transcript_analysis.get("success", False)
            video["counter_claims"] = transcript_analysis.get("counter_claims", [])

            analyzed_count += 1

        enhanced_results.append(video)

    logger.info(f"✅ Analyzed {analyzed_count} transcripts")

    return enhanced_results
