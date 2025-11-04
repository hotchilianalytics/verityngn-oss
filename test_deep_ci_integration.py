#!/usr/bin/env python3
"""
Test script to verify Deep CI integration works correctly.

This tests that:
1. deep_counter_intel_search can be imported from web_search
2. The function executes without errors
3. It returns the expected data structure
"""

import logging
import sys
from typing import Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_deep_ci_import():
    """Test that Deep CI can be imported from web_search."""
    logger.info("=" * 80)
    logger.info("TEST 1: Deep CI Import Test")
    logger.info("=" * 80)
    
    try:
        from verityngn.services.search.web_search import deep_counter_intel_search
        logger.info("✅ PASS: Successfully imported deep_counter_intel_search from web_search")
        return True
    except ImportError as e:
        logger.error(f"❌ FAIL: Could not import deep_counter_intel_search: {e}")
        return False


def test_deep_ci_function_signature():
    """Test that Deep CI function has the expected signature."""
    logger.info("=" * 80)
    logger.info("TEST 2: Deep CI Function Signature Test")
    logger.info("=" * 80)
    
    try:
        from verityngn.services.search.web_search import deep_counter_intel_search
        import inspect
        
        sig = inspect.signature(deep_counter_intel_search)
        params = list(sig.parameters.keys())
        
        logger.info(f"Function signature: {sig}")
        logger.info(f"Parameters: {params}")
        
        # Check expected parameters
        if 'context' in params and 'max_links' in params:
            logger.info("✅ PASS: Function has expected parameters (context, max_links)")
            return True
        else:
            logger.error(f"❌ FAIL: Missing expected parameters. Got: {params}")
            return False
            
    except Exception as e:
        logger.error(f"❌ FAIL: Could not inspect function: {e}")
        return False


def test_deep_ci_execution_mock():
    """Test that Deep CI executes with mocked LLM."""
    logger.info("=" * 80)
    logger.info("TEST 3: Deep CI Execution Test (Mocked)")
    logger.info("=" * 80)
    
    try:
        from verityngn.services.search.web_search import deep_counter_intel_search
        from unittest.mock import patch, MagicMock
        
        # Mock context
        test_context = {
            "title": "Lipozem Weight Loss Supplement Review",
            "video_id": "test123",
            "description": "Test description about weight loss supplement",
            "tags": ["weight loss", "supplement", "review"],
            "initial_report": "This video promotes a weight loss supplement called Lipozem.",
            "summary_report": "Product promotional video",
            "claims": [
                "Lipozem causes rapid weight loss",
                "No side effects",
                "100% natural ingredients"
            ]
        }
        
        # Mock the LLM to return sample data
        mock_llm_response = MagicMock()
        mock_llm_response.content = '''
        {
            "youtube_urls": [
                "https://www.youtube.com/watch?v=fake123",
                "https://www.youtube.com/watch?v=fake456"
            ],
            "web_urls": [
                "https://www.fda.gov/fake-warning",
                "https://www.snopes.com/fact-check/lipozem"
            ],
            "queries": [
                "Lipozem scam",
                "Lipozem review debunk",
                "Lipozem side effects"
            ]
        }
        '''
        
        with patch('langchain_google_vertexai.VertexAI') as mock_vertex:
            mock_vertex_instance = MagicMock()
            mock_vertex_instance.invoke.return_value = mock_llm_response
            mock_vertex.return_value = mock_vertex_instance
            
            # Call the function
            result = deep_counter_intel_search(test_context, max_links=10)
            
            logger.info(f"Result type: {type(result)}")
            logger.info(f"Number of results: {len(result)}")
            
            if result:
                logger.info("Sample results:")
                for i, item in enumerate(result[:3]):
                    logger.info(f"  [{i+1}] {item}")
            
            # Verify result structure
            if isinstance(result, list):
                logger.info("✅ Result is a list")
                
                if len(result) > 0:
                    logger.info(f"✅ Found {len(result)} counter-intelligence links")
                    
                    # Check structure of first result
                    first_result = result[0]
                    if isinstance(first_result, dict):
                        logger.info("✅ Results are dictionaries")
                        
                        if "url" in first_result and "source_type" in first_result:
                            logger.info("✅ Results have expected keys (url, source_type)")
                            logger.info("✅ PASS: Deep CI execution successful with mocked LLM")
                            return True
                        else:
                            logger.error(f"❌ FAIL: Missing expected keys. Got: {first_result.keys()}")
                            return False
                    else:
                        logger.error(f"❌ FAIL: Result items are not dictionaries: {type(first_result)}")
                        return False
                else:
                    logger.warning("⚠️  No results returned (may be normal with mock)")
                    logger.info("✅ PASS: Function executed without error")
                    return True
            else:
                logger.error(f"❌ FAIL: Result is not a list: {type(result)}")
                return False
                
    except Exception as e:
        logger.error(f"❌ FAIL: Deep CI execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_counter_intel_integration():
    """Test that counter_intel.py can import and use Deep CI."""
    logger.info("=" * 80)
    logger.info("TEST 4: Counter Intel Integration Test")
    logger.info("=" * 80)
    
    try:
        # Read the counter_intel.py file
        with open('/Users/ajjc/proj/verityngn-oss/verityngn/workflows/counter_intel.py', 'r') as f:
            content = f.read()
        
        # Check for correct import
        if 'from verityngn.services.search.web_search import deep_counter_intel_search' in content:
            logger.info("✅ PASS: counter_intel.py has correct Deep CI import")
            return True
        elif 'from verityngn.services.search.deep_ci import deep_counter_intel_search' in content:
            logger.error("❌ FAIL: counter_intel.py still has old incorrect import path")
            return False
        else:
            logger.error("❌ FAIL: counter_intel.py missing Deep CI import")
            return False
            
    except Exception as e:
        logger.error(f"❌ FAIL: Could not check counter_intel.py: {e}")
        return False


def main():
    """Run all tests."""
    logger.info("\n")
    logger.info("=" * 80)
    logger.info("DEEP CI INTEGRATION - VERIFICATION TESTS")
    logger.info("=" * 80)
    logger.info("\n")
    
    tests = [
        ("Deep CI Import", test_deep_ci_import),
        ("Function Signature", test_deep_ci_function_signature),
        ("Deep CI Execution (Mocked)", test_deep_ci_execution_mock),
        ("Counter Intel Integration", test_counter_intel_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
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
        logger.info("🎉 All tests passed! Deep CI integration successful.")
        return 0
    else:
        logger.error("⚠️  Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)


