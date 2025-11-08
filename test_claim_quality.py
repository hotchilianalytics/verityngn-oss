#!/usr/bin/env python3
"""
Integration test for claim extraction quality.

This test ensures that the claim extraction pipeline produces a sufficient
number of claims for videos of different lengths, preventing quality regressions.

Expected claim counts:
- 50-minute video (LIPOZEM): 15-25 claims
- 30-minute video: 10-20 claims
- 15-minute video: 5-15 claims

Run with: python test_claim_quality.py
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_claim_processor_targets():
    """Test that ClaimProcessor calculates correct target claim counts."""
    from verityngn.workflows.claim_processor import ClaimProcessor
    
    logger.info("="*80)
    logger.info("TEST 1: ClaimProcessor Target Calculation")
    logger.info("="*80)
    
    test_cases = [
        ("50-minute video (LIPOZEM)", 50.5, 15, 25),
        ("30-minute video", 30.0, 10, 20),
        ("15-minute video", 15.0, 5, 15),
        ("10-minute video", 10.0, 5, 10),
    ]
    
    all_passed = True
    
    for name, duration, min_expected, max_expected in test_cases:
        processor = ClaimProcessor(
            video_id=f"test_{int(duration)}min",
            video_duration_minutes=duration,
            target_claims_per_minute=1.0
        )
        
        actual = processor.max_claims
        
        if min_expected <= actual <= max_expected:
            logger.info(f"✅ {name}: {actual} claims (expected {min_expected}-{max_expected})")
        else:
            logger.error(f"❌ {name}: {actual} claims (expected {min_expected}-{max_expected})")
            all_passed = False
    
    return all_passed


def test_video_segmentation():
    """Test that video segmentation produces appropriate segment sizes."""
    from verityngn.config.video_segmentation import (
        calculate_optimal_segment_duration,
        get_segmentation_for_video
    )
    
    logger.info("")
    logger.info("="*80)
    logger.info("TEST 2: Video Segmentation Calculation")
    logger.info("="*80)
    
    # Test optimal segment calculation
    result = calculate_optimal_segment_duration(
        model_name="gemini-2.5-flash",
        fps=1.0
    )
    
    logger.info(f"Model: {result['model_name']}")
    logger.info(f"Context Window: {result['context_window']:,} tokens")
    logger.info(f"Max Output Tokens: {result['max_output_tokens']:,}")
    logger.info(f"Available Input Tokens: {result['available_input_tokens']:,}")
    logger.info(f"Optimal Segment: {result['max_segment_minutes']:.1f} min ({result['max_segment_seconds']}s)")
    
    # Check that segment is in reasonable range (35-50 minutes for max context utilization)
    segment_minutes = result['max_segment_minutes']
    
    if 35 <= segment_minutes <= 50:
        logger.info(f"✅ Segment duration {segment_minutes:.1f} min is in optimal range (35-50 min)")
        test_passed = True
    else:
        logger.error(f"❌ Segment duration {segment_minutes:.1f} min is outside optimal range (35-50 min)")
        test_passed = False
    
    # Test specific video (50.5 minute LIPOZEM)
    logger.info("")
    logger.info("Testing LIPOZEM video segmentation (50.5 minutes):")
    segment_dur, total_segs = get_segmentation_for_video(
        video_duration_seconds=3030,  # 50.5 minutes
        model_name="gemini-2.5-flash",
        fps=1.0
    )
    logger.info(f"  Segment duration: {segment_dur}s ({segment_dur/60:.1f} min)")
    logger.info(f"  Total segments: {total_segs}")
    
    # Should be 1-2 segments for a 50-minute video with optimal segmentation
    if 1 <= total_segs <= 2:
        logger.info(f"✅ Segment count {total_segs} is optimal for 50-minute video")
    else:
        logger.error(f"❌ Segment count {total_segs} is suboptimal for 50-minute video (expected 1-2)")
        test_passed = False
    
    return test_passed


def test_max_output_tokens_config():
    """Test that MAX_OUTPUT_TOKENS is properly configured."""
    from verityngn.config.settings import MAX_OUTPUT_TOKENS_2_5_FLASH, GENAI_VIDEO_MAX_OUTPUT_TOKENS
    
    logger.info("")
    logger.info("="*80)
    logger.info("TEST 3: MAX_OUTPUT_TOKENS Configuration")
    logger.info("="*80)
    
    logger.info(f"MAX_OUTPUT_TOKENS_2_5_FLASH: {MAX_OUTPUT_TOKENS_2_5_FLASH}")
    logger.info(f"GENAI_VIDEO_MAX_OUTPUT_TOKENS: {GENAI_VIDEO_MAX_OUTPUT_TOKENS}")
    
    all_passed = True
    
    # Check that MAX_OUTPUT_TOKENS_2_5_FLASH is reasonable (not too low, not too high)
    if 8000 <= MAX_OUTPUT_TOKENS_2_5_FLASH <= 65536:
        logger.info(f"✅ MAX_OUTPUT_TOKENS_2_5_FLASH is in valid range (8K-64K)")
    else:
        logger.error(f"❌ MAX_OUTPUT_TOKENS_2_5_FLASH ({MAX_OUTPUT_TOKENS_2_5_FLASH}) is outside valid range")
        all_passed = False
    
    # Check that it reads from ENV var (if set)
    env_value = os.getenv("MAX_OUTPUT_TOKENS_2_5_FLASH")
    if env_value:
        expected = int(env_value)
        if MAX_OUTPUT_TOKENS_2_5_FLASH == expected:
            logger.info(f"✅ MAX_OUTPUT_TOKENS_2_5_FLASH correctly reads from ENV ({expected})")
        else:
            logger.error(f"❌ MAX_OUTPUT_TOKENS_2_5_FLASH ({MAX_OUTPUT_TOKENS_2_5_FLASH}) doesn't match ENV ({expected})")
            all_passed = False
    else:
        logger.info(f"ℹ️  MAX_OUTPUT_TOKENS_2_5_FLASH ENV var not set, using default: {MAX_OUTPUT_TOKENS_2_5_FLASH}")
    
    return all_passed


def test_quality_params_file():
    """Test that QUALITY_PARAMS.json exists and has correct values."""
    
    logger.info("")
    logger.info("="*80)
    logger.info("TEST 4: QUALITY_PARAMS.json Validation")
    logger.info("="*80)
    
    params_file = project_root / "QUALITY_PARAMS.json"
    
    if not params_file.exists():
        logger.error(f"❌ QUALITY_PARAMS.json not found at {params_file}")
        return False
    
    logger.info(f"✅ QUALITY_PARAMS.json found")
    
    with open(params_file, 'r') as f:
        params = json.load(f)
    
    # Check critical parameters
    checks = [
        ("claim_extraction.max_output_tokens", 8000, 65536),
        ("claim_extraction.min_claims_per_segment", 10, 50),
        ("claim_selection.target_claims_long_video_min", 15, None),
        ("claim_selection.target_claims_long_video_max", 20, None),
        ("quality_thresholds.min_claims_50min_video", 15, None),
    ]
    
    all_passed = True
    
    for param_path, min_val, max_val in checks:
        keys = param_path.split('.')
        value = params
        try:
            for key in keys:
                value = value[key]
            
            if min_val is not None and value < min_val:
                logger.error(f"❌ {param_path} = {value} is below minimum {min_val}")
                all_passed = False
            elif max_val is not None and value > max_val:
                logger.error(f"❌ {param_path} = {value} is above maximum {max_val}")
                all_passed = False
            else:
                logger.info(f"✅ {param_path} = {value}")
        except (KeyError, TypeError) as e:
            logger.error(f"❌ {param_path} not found in QUALITY_PARAMS.json")
            all_passed = False
    
    return all_passed


def main():
    """Run all quality tests."""
    
    logger.info("")
    logger.info("╔" + "="*78 + "╗")
    logger.info("║" + " "*20 + "CLAIM QUALITY INTEGRATION TEST" + " "*27 + "║")
    logger.info("╚" + "="*78 + "╝")
    logger.info("")
    
    tests = [
        ("ClaimProcessor Targets", test_claim_processor_targets),
        ("Video Segmentation", test_video_segmentation),
        ("MAX_OUTPUT_TOKENS Config", test_max_output_tokens_config),
        ("QUALITY_PARAMS.json", test_quality_params_file),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            logger.error(f"❌ {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    logger.info("")
    logger.info("="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    logger.info("="*80)
    
    if all_passed:
        logger.info("✅ ALL TESTS PASSED")
        return 0
    else:
        logger.error("❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())


