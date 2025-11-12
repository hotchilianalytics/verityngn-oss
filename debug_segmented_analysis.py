#!/usr/bin/env python
"""
Debug script to test segmented YouTube URL analysis directly.
This will show us exactly why the segmented analysis is failing.
"""

import logging
import os
import sys

# Setup verbose logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_segmented_vertex_analysis():
    """Test segmented Vertex AI analysis directly."""
    
    video_id = "tLJC8hkK-ao"
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    # Mock video info with known duration
    video_info = {
        "id": video_id,
        "title": "[LIPOZEM] Exclusive Interview with Dr. Julian Ross",
        "duration": 1998,  # 33 minutes in seconds
        "upload_date": "20240810"
    }
    
    logger.info("="*80)
    logger.info("🔍 DEBUG: Segmented Vertex YouTube Analysis")
    logger.info("="*80)
    logger.info(f"Video ID: {video_id}")
    logger.info(f"Video URL: {video_url}")
    logger.info(f"Duration: {video_info['duration']}s (~{video_info['duration']//60} minutes)")
    logger.info("")
    
    # Check environment
    logger.info("🔧 Checking environment...")
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID")
    location = os.getenv("LOCATION", "us-central1")
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    logger.info(f"   PROJECT_ID: {project_id}")
    logger.info(f"   LOCATION: {location}")
    logger.info(f"   CREDENTIALS: {creds_path}")
    
    if not project_id:
        logger.error("❌ GOOGLE_CLOUD_PROJECT or PROJECT_ID not set!")
        logger.error("   Set with: export GOOGLE_CLOUD_PROJECT=your-project-id")
        return False
    
    if not creds_path or not os.path.exists(creds_path):
        logger.error("❌ GOOGLE_APPLICATION_CREDENTIALS not found!")
        return False
    
    logger.info("✅ Environment OK")
    logger.info("")
    
    # Test Vertex AI initialization
    logger.info("🚀 Initializing Vertex AI...")
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel, Part, GenerationConfig
        
        vertexai.init(project=project_id, location=location)
        logger.info("✅ Vertex AI initialized")
        
        model_name = "gemini-2.5-flash"
        model = GenerativeModel(model_name)
        logger.info(f"✅ Model loaded: {model_name}")
        
    except Exception as e:
        logger.error(f"❌ Vertex AI initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    logger.info("")
    logger.info("🎬 Testing segmented YouTube URL analysis...")
    logger.info("")
    
    # Test a single segment (first 30 seconds)
    test_duration = 30
    logger.info(f"📍 Testing FIRST SEGMENT: 0s to {test_duration}s")
    logger.info("")
    
    try:
        # Create YouTube URL part
        logger.info(f"🔗 Creating YouTube URL part: {video_url}")
        
        # Try to create Part with video metadata (if supported)
        try:
            video_part = Part.from_uri(
                video_url,
                mime_type="video/*"
            )
            logger.info("✅ Created video part from URI")
        except Exception as e:
            logger.warning(f"⚠️  Could not create Part with video metadata: {e}")
            logger.info("   Trying basic Part.from_uri...")
            video_part = Part.from_uri(video_url, mime_type="video/*")
            logger.info("✅ Created basic video part")
        
        # Create prompt
        prompt = """Extract 3-5 verifiable claims from this video segment.
        
        Return as valid JSON:
        {
            "claims": [
                {
                    "claim_text": "specific claim text",
                    "timestamp": "MM:SS",
                    "speaker": "speaker name or Visual Text",
                    "source_type": "spoken|visual_text",
                    "initial_assessment": "brief assessment"
                }
            ]
        }
        """
        
        logger.info("📝 Sending request to Gemini...")
        logger.info("   This may take 10-30 seconds...")
        logger.info("")
        
        # Generate content
        generation_config = GenerationConfig(
            max_output_tokens=8192,
            temperature=0.2,
        )
        
        response = model.generate_content(
            [video_part, prompt],
            generation_config=generation_config
        )
        
        # Check response
        logger.info("="*80)
        logger.info("📨 RESPONSE RECEIVED")
        logger.info("="*80)
        
        if hasattr(response, 'text') and response.text:
            response_text = response.text
            logger.info(f"✅ Response length: {len(response_text)} characters")
            logger.info("")
            logger.info("📄 Response preview (first 500 chars):")
            logger.info("-"*80)
            logger.info(response_text[:500])
            logger.info("-"*80)
            logger.info("")
            logger.info("🎉 SUCCESS! Segmented YouTube analysis is working!")
            return True
        else:
            logger.error("❌ Response has no text!")
            logger.error(f"   Response object: {response}")
            
            # Check for finish reason
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                finish_reason = getattr(candidate, 'finish_reason', None)
                logger.error(f"   Finish reason: {finish_reason}")
                
                # Check safety ratings
                safety_ratings = getattr(candidate, 'safety_ratings', None)
                if safety_ratings:
                    logger.error(f"   Safety ratings: {safety_ratings}")
            
            return False
            
    except Exception as e:
        logger.error("")
        logger.error("="*80)
        logger.error("❌ ERROR DURING ANALYSIS")
        logger.error("="*80)
        logger.error(f"Error: {e}")
        logger.error("")
        
        import traceback
        logger.error("Full traceback:")
        traceback.print_exc()
        
        # Check if it's a rate limit error
        error_str = str(e).lower()
        if '429' in error_str or 'resource exhausted' in error_str:
            logger.error("")
            logger.error("💡 This is a RATE LIMIT error (429)")
            logger.error("   Vertex AI is throttling requests")
            logger.error("   This is why the workflow hangs - it's retrying indefinitely")
        elif '503' in error_str or 'unavailable' in error_str:
            logger.error("")
            logger.error("💡 This is a SERVICE UNAVAILABLE error (503)")
            logger.error("   Vertex AI service is temporarily down or overloaded")
        elif 'auth' in error_str or 'permission' in error_str:
            logger.error("")
            logger.error("💡 This is an AUTHENTICATION error")
            logger.error("   Check your service account permissions")
        
        return False


if __name__ == "__main__":
    logger.info("")
    logger.info("🔬 VerityNgn - Segmented Analysis Debug")
    logger.info("")
    
    import asyncio
    success = asyncio.run(test_segmented_vertex_analysis())
    
    logger.info("")
    if success:
        logger.info("✅ DEBUG TEST PASSED")
        logger.info("   Segmented YouTube analysis is working!")
        logger.info("   The full workflow should work now.")
        sys.exit(0)
    else:
        logger.error("❌ DEBUG TEST FAILED")
        logger.error("   This is why the workflow is hanging.")
        logger.error("   Fix the issue above before running the full workflow.")
        sys.exit(1)


















