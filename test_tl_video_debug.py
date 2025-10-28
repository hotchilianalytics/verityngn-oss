#!/usr/bin/env python
"""
Debug version of test script with timeouts and verbose logging.
"""

import logging
import sys
import signal
from pathlib import Path

# Setup verbose logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out!")


def run_tl_video_test_with_timeout():
    """Run complete verification workflow with timeout protection."""
    
    video_id = "tLJC8hkK-ao"
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    logger.info("="*80)
    logger.info("🚀 VERITYNGN DEBUG TEST - tLJC8hkK-ao (LIPOZEM)")
    logger.info("="*80)
    logger.info(f"📹 Video ID: {video_id}")
    logger.info(f"🔗 Video URL: {video_url}")
    logger.info("")
    
    try:
        # Import workflow
        logger.info("📦 Importing verification workflow...")
        from verityngn.workflows.pipeline import run_verification
        logger.info("✅ Modules imported successfully")
        
        # Set up timeout (20 minutes)
        logger.info("")
        logger.info("⏱️  Setting 20-minute timeout...")
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(20 * 60)  # 20 minutes
        
        logger.info("")
        logger.info("🏗️ Starting verification workflow...")
        logger.info("    Monitoring for hangs and timeouts...")
        logger.info("")
        
        # Execute workflow
        final_state, output_dir = run_verification(video_url)
        
        # Cancel timeout
        signal.alarm(0)
        
        logger.info("")
        logger.info("="*80)
        logger.info("✅ WORKFLOW COMPLETED SUCCESSFULLY!")
        logger.info("="*80)
        
        # Display key results
        final_report = final_state.get('final_report', {})
        truthfulness_score = final_report.get('truthfulness_score', 'N/A')
        claims_verified = len(final_state.get('claims', []))
        
        logger.info("")
        logger.info("📊 RESULTS SUMMARY")
        logger.info("-"*80)
        logger.info(f"   Truthfulness Score: {truthfulness_score}")
        logger.info(f"   Claims Verified: {claims_verified}")
        logger.info(f"   Output Directory: {output_dir}")
        logger.info("")
        
        # List generated files
        output_path = Path(output_dir)
        if output_path.exists():
            logger.info("📁 Generated Files:")
            for file in sorted(output_path.glob("*")):
                if file.is_file():
                    size_kb = file.stat().st_size / 1024
                    logger.info(f"   - {file.name} ({size_kb:.1f} KB)")
        
        logger.info("")
        logger.info("🎉 Test completed successfully!")
        logger.info("")
        
        return True
        
    except TimeoutError as e:
        logger.error("")
        logger.error("="*80)
        logger.error("⏱️  TIMEOUT - Process took longer than 20 minutes")
        logger.error("="*80)
        logger.error("The workflow is hung or extremely slow.")
        logger.error("This typically indicates:")
        logger.error("  1. Vertex AI API is not responding")
        logger.error("  2. Video download is stuck")
        logger.error("  3. Network connectivity issues")
        logger.error("  4. Rate limiting from Google APIs")
        logger.error("")
        logger.error("Check the logs above for the last successful operation.")
        return False
        
    except KeyboardInterrupt:
        logger.warning("")
        logger.warning("="*80)
        logger.warning("🛑 INTERRUPTED BY USER")
        logger.warning("="*80)
        logger.warning("Test was cancelled by user (Ctrl+C)")
        return False
        
    except Exception as e:
        logger.error("")
        logger.error("="*80)
        logger.error("❌ WORKFLOW FAILED")
        logger.error("="*80)
        logger.error(f"Error: {e}")
        logger.error("")
        
        import traceback
        logger.error("Full traceback:")
        traceback.print_exc()
        
        return False


if __name__ == "__main__":
    logger.info("")
    logger.info("🔬 VerityNgn Debug Test - LIPOZEM Video (tLJC8hkK-ao)")
    logger.info("🔍 Running with verbose logging and 20-minute timeout")
    logger.info("")
    
    success = run_tl_video_test_with_timeout()
    
    if success:
        logger.info("✅ Test PASSED")
        sys.exit(0)
    else:
        logger.error("❌ Test FAILED or TIMED OUT")
        sys.exit(1)

