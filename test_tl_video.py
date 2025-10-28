#!/usr/bin/env python
"""
Test script for running verification on tLJC8hkK-ao video (LIPOZEM).

This script runs the complete verification workflow outside of Streamlit,
including:
- Video download
- Multimodal analysis
- Claim extraction
- Counter-intelligence search
- Claim verification
- Report generation

Usage:
    python test_tl_video.py
"""

import logging
import sys
import os
from pathlib import Path

# Load .env file first
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded .env from {env_path}")
    else:
        print(f"⚠️  No .env file found at {env_path}")
except ImportError:
    print("⚠️  python-dotenv not installed, using existing environment variables")

# Ensure critical environment variables are set
required_vars = {
    "GOOGLE_APPLICATION_CREDENTIALS": os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
    "GOOGLE_CLOUD_PROJECT": os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID"),
    "PROJECT_ID": os.getenv("PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT"),
    "LOCATION": os.getenv("LOCATION", "us-central1")
}

# Set derived variables if main ones exist
if required_vars["GOOGLE_CLOUD_PROJECT"]:
    os.environ["GOOGLE_CLOUD_PROJECT"] = required_vars["GOOGLE_CLOUD_PROJECT"]
    os.environ["PROJECT_ID"] = required_vars["GOOGLE_CLOUD_PROJECT"]

if required_vars["LOCATION"]:
    os.environ["LOCATION"] = required_vars["LOCATION"]

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_tl_video_test():
    """Run complete verification workflow for tLJC8hkK-ao video."""
    
    # Video details
    video_id = "tLJC8hkK-ao"
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    logger.info("="*80)
    logger.info("🚀 VERITYNGN WORKFLOW TEST - tLJC8hkK-ao (LIPOZEM)")
    logger.info("="*80)
    logger.info(f"📹 Video ID: {video_id}")
    logger.info(f"🔗 Video URL: {video_url}")
    logger.info("")
    logger.info("⏱️  EXPECTED RUNTIME: 30-60 minutes for 33-minute video")
    logger.info("    (Multimodal analysis is ~8 min per segment, 7 segments total)")
    logger.info("    This is NORMAL - the process is NOT hung if there's no output for 10+ minutes")
    logger.info("")
    
    try:
        # Import workflow
        logger.info("📦 Importing verification workflow...")
        from verityngn.workflows.pipeline import run_verification
        logger.info("✅ Modules imported successfully")
        
        # Run verification
        logger.info("")
        logger.info("🏗️ Starting verification workflow...")
        logger.info("    This will take several minutes to complete.")
        logger.info("")
        logger.info("Pipeline stages:")
        logger.info("  1. 📥 Video Download (download + metadata extraction)")
        logger.info("  2. 🎬 Initial Analysis (multimodal LLM analysis)")
        logger.info("  3. 🔍 Counter-Intelligence (YouTube search for reviews/debunks)")
        logger.info("  4. 📋 Claim Extraction (extract and filter claims)")
        logger.info("  5. ✅ Claim Verification (web search + evidence gathering)")
        logger.info("  6. 📊 Report Generation (truthfulness scoring)")
        logger.info("  7. 💾 Save Reports (JSON + Markdown + HTML)")
        logger.info("")
        logger.info("-"*80)
        
        # Execute workflow
        # The run_verification function will handle all stages automatically
        # Output will be saved to: outputs/{video_id}/
        final_state, output_dir = run_verification(video_url)
        
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
        logger.info(f"📂 View full report at: {output_dir}/report.html")
        logger.info("")
        
        return True
        
    except Exception as e:
        logger.error("")
        logger.error("="*80)
        logger.error("❌ WORKFLOW FAILED")
        logger.error("="*80)
        logger.error(f"Error: {e}")
        logger.error("")
        
        # Print full traceback for debugging
        import traceback
        logger.error("Full traceback:")
        traceback.print_exc()
        
        return False


if __name__ == "__main__":
    logger.info("")
    logger.info("🔬 VerityNgn Test - LIPOZEM Video (tLJC8hkK-ao)")
    logger.info("")
    
    success = run_tl_video_test()
    
    if success:
        logger.info("✅ Test PASSED")
        sys.exit(0)
    else:
        logger.error("❌ Test FAILED")
        sys.exit(1)


