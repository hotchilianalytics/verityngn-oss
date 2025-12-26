#!/usr/bin/env python3
"""
VerityNgn Workflow CLI

Run the full verification pipeline for a YouTube video.
Usage: python run_workflow.py "https://www.youtube.com/watch?v=VIDEO_ID"
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# --- BOOTSTRAP: Load secrets before any package imports ---
def setup_secrets():
    """Load secrets from .env file immediately."""
    try:
        # Try loading via ui.secrets_loader if available
        # Need to add project root to path first for package imports
        project_root = Path(__file__).parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
            
        from ui.secrets_loader import load_secrets
        load_secrets()
    except (ImportError, Exception):
        # Fallback to direct dotenv
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass

setup_secrets()
# -----------------------------------------------------------

from verityngn.workflows.pipeline import run_verification

def setup_logging(verbose: bool = False):
    """Setup basic logging to console."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def main():
    parser = argparse.ArgumentParser(description="Run VerityNgn verification workflow on a YouTube video.")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--output", "-o", help="Output directory path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    logger = logging.getLogger("run_workflow")
    
    logger.info(f"🚀 Initializing verification for: {args.url}")
    
    # Verify critical secrets are loaded
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID")
    if not project_id or project_id == "your-project-id":
        logger.warning("⚠️ Warning: GOOGLE_CLOUD_PROJECT is not set or using default. Vertex AI may fail.")
    else:
        logger.info(f"✅ Using Google Cloud Project: {project_id}")
    
    try:
        result = run_verification(args.url, out_dir_path=args.output)
        
        logger.info("=" * 60)
        logger.info("✅ Verification Complete!")
        logger.info(f"📹 Video ID: {result['video_id']}")
        logger.info(f"📊 Claims Processed: {result['claims_count']}")
        logger.info(f"📂 Output Directory: {result['output_dir']}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Workflow failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
