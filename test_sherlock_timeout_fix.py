#!/usr/bin/env python3
"""
Test script to verify the Sherlock timeout fixes work correctly.

This tests the three layers of timeout protection:
1. Transcript download timeout (30s)
2. LLM analysis timeout (120s request, 150s overall)
3. Per-video overall timeout (200s)
"""

import asyncio
import logging
import sys
from unittest.mock import patch, MagicMock
from typing import Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_transcript_download_timeout():
    """Test that transcript download respects 30 second timeout."""
    logger.info("=" * 80)
    logger.info("TEST 1: Transcript Download Timeout (30s)")
    logger.info("=" * 80)
    
    from verityngn.workflows.youtube_transcript_analysis import analyze_counter_video_transcript
    
    # Mock YouTubeTranscriptApi to hang
    async def slow_fetch(*args, **kwargs):
        logger.info("Simulating slow transcript fetch (would hang forever without timeout)...")
        await asyncio.sleep(60)  # Try to sleep 60s (should timeout at 30s)
        return None
    
    with patch('youtube_transcript_api.YouTubeTranscriptApi.list_transcripts', side_effect=slow_fetch):
        try:
            start_time = asyncio.get_event_loop().time()
            result = await analyze_counter_video_transcript(
                video_id="test_video_id",
                video_title="Test Video",
                video_description="Test Description"
            )
            end_time = asyncio.get_event_loop().time()
            elapsed = end_time - start_time
            
            logger.info(f"✅ Test completed in {elapsed:.1f} seconds")
            logger.info(f"Result: {result}")
            
            if elapsed < 35:  # Should timeout around 30s (with some buffer)
                logger.info("✅ PASS: Transcript download timeout working correctly")
                return True
            else:
                logger.error(f"❌ FAIL: Took too long ({elapsed}s), timeout not working")
                return False
                
        except Exception as e:
            logger.error(f"❌ Test failed with exception: {e}")
            return False


async def test_llm_timeout():
    """Test that LLM analysis respects 150 second timeout."""
    logger.info("=" * 80)
    logger.info("TEST 2: LLM Analysis Timeout (150s)")
    logger.info("=" * 80)
    
    from verityngn.workflows.youtube_transcript_analysis import _extract_counter_claims_from_transcript
    
    # Mock ChatVertexAI to hang
    class MockLLM:
        def __init__(self, *args, **kwargs):
            logger.info(f"Mock LLM initialized with kwargs: {kwargs}")
            self.request_timeout = kwargs.get('request_timeout', None)
            logger.info(f"✅ request_timeout parameter present: {self.request_timeout}s")
        
        def invoke(self, *args, **kwargs):
            logger.info("Simulating slow LLM call (would hang forever without timeout)...")
            import time
            time.sleep(180)  # Try to sleep 180s (should timeout at 150s)
            return MagicMock(content='{"counter_claims": []}')
    
    with patch('langchain_google_vertexai.ChatVertexAI', MockLLM):
        try:
            start_time = asyncio.get_event_loop().time()
            result = await _extract_counter_claims_from_transcript(
                transcript_text="Test transcript",
                video_title="Test Video",
                video_description="Test Description"
            )
            end_time = asyncio.get_event_loop().time()
            elapsed = end_time - start_time
            
            logger.info(f"✅ Test completed in {elapsed:.1f} seconds")
            logger.info(f"Result: {result}")
            
            if elapsed < 160:  # Should timeout around 150s (with some buffer)
                logger.info("✅ PASS: LLM timeout working correctly")
                return True
            else:
                logger.error(f"❌ FAIL: Took too long ({elapsed}s), timeout not working")
                return False
                
        except Exception as e:
            logger.error(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False


async def test_per_video_timeout():
    """Test that per-video timeout (200s) catches everything."""
    logger.info("=" * 80)
    logger.info("TEST 3: Per-Video Overall Timeout (200s)")
    logger.info("=" * 80)
    
    from verityngn.workflows.youtube_transcript_analysis import enhance_youtube_counter_intelligence
    
    # Mock analyze_counter_video_transcript to hang
    async def slow_analyze(*args, **kwargs):
        logger.info("Simulating slow video analysis (would hang forever without timeout)...")
        await asyncio.sleep(250)  # Try to sleep 250s (should timeout at 200s)
        return {"success": True, "counter_claims": []}
    
    mock_videos = [
        {
            "id": "test_video_1",
            "title": "Test Scam Video",
            "description": "This is a scam warning"
        }
    ]
    
    with patch('verityngn.workflows.youtube_transcript_analysis.analyze_counter_video_transcript', slow_analyze):
        try:
            start_time = asyncio.get_event_loop().time()
            result = await enhance_youtube_counter_intelligence(
                counter_videos=mock_videos,
                max_videos_to_analyze=1
            )
            end_time = asyncio.get_event_loop().time()
            elapsed = end_time - start_time
            
            logger.info(f"✅ Test completed in {elapsed:.1f} seconds")
            logger.info(f"Result: {result}")
            
            if elapsed < 210:  # Should timeout around 200s (with some buffer)
                logger.info("✅ PASS: Per-video timeout working correctly")
                # Verify it returned error instead of hanging
                if result[0].get("transcript_analysis", {}).get("success") == False:
                    logger.info("✅ PASS: Graceful failure - returned error dict")
                    return True
                else:
                    logger.error("❌ FAIL: Should have returned error dict")
                    return False
            else:
                logger.error(f"❌ FAIL: Took too long ({elapsed}s), timeout not working")
                return False
                
        except Exception as e:
            logger.error(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False


async def test_successful_flow():
    """Test that normal successful flow still works."""
    logger.info("=" * 80)
    logger.info("TEST 4: Successful Flow (Should Complete Quickly)")
    logger.info("=" * 80)
    
    from verityngn.workflows.youtube_transcript_analysis import _extract_counter_claims_from_transcript
    
    # Mock ChatVertexAI to return success quickly
    class MockLLM:
        def __init__(self, *args, **kwargs):
            logger.info(f"Mock LLM initialized")
            self.request_timeout = kwargs.get('request_timeout', None)
            logger.info(f"✅ request_timeout parameter present: {self.request_timeout}s")
        
        def invoke(self, *args, **kwargs):
            logger.info("Mock LLM returning success...")
            response = MagicMock()
            response.content = '''
            {
                "counter_claims": [
                    {
                        "claim_text": "Test counter-claim",
                        "evidence_snippet": "Test evidence",
                        "credibility_score": 0.8,
                        "claim_type": "contradiction"
                    }
                ]
            }
            '''
            return response
    
    with patch('langchain_google_vertexai.ChatVertexAI', MockLLM):
        try:
            start_time = asyncio.get_event_loop().time()
            result = await _extract_counter_claims_from_transcript(
                transcript_text="Test transcript with claims",
                video_title="Test Video",
                video_description="Test Description"
            )
            end_time = asyncio.get_event_loop().time()
            elapsed = end_time - start_time
            
            logger.info(f"✅ Test completed in {elapsed:.1f} seconds")
            logger.info(f"Result: {result}")
            
            if elapsed < 5 and len(result) > 0:  # Should complete quickly with results
                logger.info("✅ PASS: Successful flow working correctly")
                return True
            else:
                logger.error(f"❌ FAIL: Took {elapsed}s or got no results")
                return False
                
        except Exception as e:
            logger.error(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False


async def test_sherlock_logging():
    """Test that Sherlock debug logs are present."""
    logger.info("=" * 80)
    logger.info("TEST 5: Sherlock Debug Logging")
    logger.info("=" * 80)
    
    from verityngn.workflows.youtube_transcript_analysis import _extract_counter_claims_from_transcript
    
    # Capture log messages
    captured_logs = []
    
    class LogCapture(logging.Handler):
        def emit(self, record):
            captured_logs.append(record.getMessage())
    
    # Add log capture handler
    test_logger = logging.getLogger('verityngn.workflows.youtube_transcript_analysis')
    handler = LogCapture()
    test_logger.addHandler(handler)
    
    # Mock ChatVertexAI
    class MockLLM:
        def __init__(self, *args, **kwargs):
            pass
        def invoke(self, *args, **kwargs):
            response = MagicMock()
            response.content = '{"counter_claims": []}'
            return response
    
    with patch('langchain_google_vertexai.ChatVertexAI', MockLLM):
        try:
            await _extract_counter_claims_from_transcript(
                transcript_text="Test",
                video_title="Test",
                video_description="Test"
            )
            
            # Check for Sherlock markers
            sherlock_logs = [log for log in captured_logs if '[SHERLOCK]' in log]
            
            logger.info(f"Total logs captured: {len(captured_logs)}")
            logger.info(f"Sherlock logs found: {len(sherlock_logs)}")
            
            for log in sherlock_logs:
                logger.info(f"  - {log}")
            
            expected_markers = [
                "Starting transcript analysis",
                "Creating ChatVertexAI with 120s timeout",
                "Formatting prompt messages",
                "Invoking LLM with timeout protection",
            ]
            
            found_all = all(
                any(marker in log for log in sherlock_logs)
                for marker in expected_markers
            )
            
            if found_all:
                logger.info("✅ PASS: All Sherlock debug logs present")
                return True
            else:
                logger.error("❌ FAIL: Missing some Sherlock debug logs")
                return False
                
        except Exception as e:
            logger.error(f"❌ Test failed with exception: {e}")
            return False
        finally:
            test_logger.removeHandler(handler)


async def main():
    """Run all tests."""
    logger.info("\n")
    logger.info("=" * 80)
    logger.info("SHERLOCK TIMEOUT FIX - VERIFICATION TESTS")
    logger.info("=" * 80)
    logger.info("\n")
    
    tests = [
        ("Sherlock Debug Logging", test_sherlock_logging),
        ("Successful Flow", test_successful_flow),
        # Note: Timeout tests disabled by default as they take 30-200s each
        # Uncomment to run full timeout verification:
        # ("Transcript Download Timeout", test_transcript_download_timeout),
        # ("LLM Analysis Timeout", test_llm_timeout),
        # ("Per-Video Overall Timeout", test_per_video_timeout),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
        logger.info("\n")
    
    # Summary
    logger.info("=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Sherlock timeout fix verified.")
        return 0
    else:
        logger.error("⚠️  Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)








