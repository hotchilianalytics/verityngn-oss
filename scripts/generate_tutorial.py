#!/usr/bin/env python3
"""
Tutorial Video Generator CLI

Generate tutorial videos from Sherlock analysis results, featuring
the best/worst claims with text overlays and verdicts.

Usage:
    python scripts/generate_tutorial.py --video-id sbChYUijRKE
    python scripts/generate_tutorial.py --video-id sbChYUijRKE --top-n-worst 5 --top-n-best 2
    python scripts/generate_tutorial.py --video-id sbChYUijRKE --all-claims --no-overlays
    python scripts/generate_tutorial.py --video-id sbChYUijRKE --from-gcs
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from verityngn.services.video.clip_generator import ClipGenerator, ClipConfig


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Force reconfiguration of root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add new handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    root_logger.addHandler(handler)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate tutorial videos from Sherlock analysis results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate tutorial with top 5 worst claims
  python scripts/generate_tutorial.py --video-id sbChYUijRKE

  # Include best and worst claims
  python scripts/generate_tutorial.py --video-id sbChYUijRKE --top-n-worst 5 --top-n-best 3

  # Generate tutorial with all claims
  python scripts/generate_tutorial.py --video-id sbChYUijRKE --all-claims

  # Skip overlays for faster processing
  python scripts/generate_tutorial.py --video-id sbChYUijRKE --no-overlays

  # Custom output location
  python scripts/generate_tutorial.py --video-id sbChYUijRKE --output my_tutorial.mp4

  # Fetch latest report from GCS (cloud storage)
  python scripts/generate_tutorial.py --video-id sbChYUijRKE --from-gcs

  # List available reports in GCS
  python scripts/generate_tutorial.py --video-id sbChYUijRKE --list-gcs-reports
        """
    )
    
    # Required arguments
    parser.add_argument(
        "--video-id",
        required=True,
        help="YouTube video ID to generate tutorial for"
    )
    
    # Claim selection
    selection = parser.add_argument_group("Claim Selection")
    selection.add_argument(
        "--top-n-worst",
        type=int,
        default=5,
        help="Number of worst (most false) claims to include (default: 5)"
    )
    selection.add_argument(
        "--top-n-best",
        type=int,
        default=0,
        help="Number of best (most true) claims to include (default: 0)"
    )
    selection.add_argument(
        "--all-claims",
        action="store_true",
        help="Include all claims in tutorial"
    )
    
    # Clip settings
    clips = parser.add_argument_group("Clip Settings")
    clips.add_argument(
        "--clip-duration",
        type=float,
        default=12.0,
        help="Duration of each claim clip in seconds (default: 12)"
    )
    clips.add_argument(
        "--padding-before",
        type=float,
        default=2.0,
        help="Seconds before claim timestamp (default: 2)"
    )
    clips.add_argument(
        "--padding-after",
        type=float,
        default=10.0,
        help="Seconds after claim timestamp (default: 10)"
    )
    
    # Overlay options
    overlays = parser.add_argument_group("Overlay Options")
    overlays.add_argument(
        "--no-overlays",
        action="store_true",
        help="Skip adding text overlays (faster)"
    )
    overlays.add_argument(
        "--font-size",
        type=int,
        default=24,
        help="Font size for overlay text (default: 24)"
    )
    
    # Output options
    output = parser.add_argument_group("Output Options")
    output.add_argument(
        "--output",
        "-o",
        help="Output path for tutorial video (default: outputs/<video_id>/<video_id>_tutorial.mp4)"
    )
    output.add_argument(
        "--output-dir",
        help="Output directory (default: outputs/<video_id>)"
    )
    output.add_argument(
        "--save-clips",
        action="store_true",
        default=True,
        help="Save individual claim clips (default: True)"
    )
    output.add_argument(
        "--no-save-clips",
        action="store_true",
        help="Don't save individual claim clips"
    )
    
    # Input options
    input_opts = parser.add_argument_group("Input Options")
    input_opts.add_argument(
        "--claims-file",
        help="Path to claims JSON file (auto-detected if not provided)"
    )
    input_opts.add_argument(
        "--video-url",
        help="YouTube URL (used if video needs to be downloaded)"
    )
    input_opts.add_argument(
        "--title",
        help="Custom title for the tutorial intro"
    )
    
    # GCS options
    gcs_opts = parser.add_argument_group("GCS Options (fetch reports from cloud)")
    gcs_opts.add_argument(
        "--from-gcs",
        action="store_true",
        help="Fetch the latest report from GCS instead of using local files"
    )
    gcs_opts.add_argument(
        "--gcs-bucket",
        help="GCS bucket name (default: from GCS_BUCKET_NAME env var)"
    )
    gcs_opts.add_argument(
        "--gcs-project",
        help="GCP project ID (default: from PROJECT_ID env var)"
    )
    gcs_opts.add_argument(
        "--list-gcs-reports",
        action="store_true",
        help="List available reports in GCS and exit"
    )
    
    # Other options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without generating video"
    )
    
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()
    setup_logging(args.verbose)
    
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("🎬 VerityNgn Tutorial Generator")
    logger.info("=" * 60)
    
    video_id = args.video_id
    
    # Configure clip generator
    config = ClipConfig(
        clip_duration=args.clip_duration,
        padding_before=args.padding_before,
        padding_after=args.padding_after,
        overlay_font_size=args.font_size,
    )
    
    generator = ClipGenerator(config)
    
    # Handle --list-gcs-reports
    if args.list_gcs_reports:
        logger.info("📋 Listing available reports in GCS...")
        reports = ClipGenerator.list_gcs_reports(
            video_id=video_id if video_id != "list" else None,
            bucket_name=args.gcs_bucket,
            project_id=args.gcs_project,
            limit=20
        )
        
        if not reports:
            logger.info("No reports found in GCS")
            return 0
        
        logger.info(f"\nFound {len(reports)} reports:\n")
        for i, report in enumerate(reports, 1):
            logger.info(f"  {i}. {report['video_id']}")
            logger.info(f"     Path: {report['path']}")
            logger.info(f"     Updated: {report['updated']}")
            logger.info(f"     Size: {report['size_bytes']} bytes")
            logger.info("")
        
        return 0
    
    # Find claims file - check GCS first if requested
    claims_file = args.claims_file
    
    if not claims_file and args.from_gcs:
        logger.info(f"☁️ Fetching latest report from GCS for video: {video_id}")
        
        # Determine output directory for GCS download
        output_dir = args.output_dir or os.path.join("outputs", video_id, "tutorial")
        os.makedirs(output_dir, exist_ok=True)
        
        claims_file = ClipGenerator.fetch_report_from_gcs(
            video_id=video_id,
            output_dir=output_dir,
            bucket_name=args.gcs_bucket,
            project_id=args.gcs_project
        )
        
        if not claims_file:
            logger.error(f"Could not fetch report from GCS for video ID: {video_id}")
            logger.info("Use --list-gcs-reports to see available reports")
            return 1
    
    if not claims_file:
        claims_file = ClipGenerator.find_claims_file(video_id)
        if not claims_file:
            logger.error(f"Could not find claims file for video ID: {video_id}")
            logger.info("Searched in: outputs/, sherlock_analysis_<id>/, etc.")
            logger.info("Use --claims-file to specify the path manually")
            logger.info("Or use --from-gcs to fetch from Google Cloud Storage")
            return 1
    
    logger.info(f"📋 Claims file: {claims_file}")
    
    # Load claims
    try:
        claims = ClipGenerator.load_claims_from_file(claims_file)
        logger.info(f"📊 Loaded {len(claims)} claims")
    except Exception as e:
        logger.error(f"Failed to load claims: {e}")
        return 1
    
    if not claims:
        logger.error("No claims found in file")
        return 1
    
    # Determine output directory
    output_dir = args.output_dir
    if not output_dir:
        output_dir = os.path.join("outputs", video_id, "tutorial")
    
    # Dry run - show plan
    if args.dry_run:
        logger.info("\n📝 DRY RUN - Would perform the following:")
        logger.info(f"  Video ID: {video_id}")
        logger.info(f"  Claims file: {claims_file}")
        logger.info(f"  Total claims: {len(claims)}")
        
        if args.all_claims:
            selected_count = len(claims)
        else:
            selected_count = min(args.top_n_worst + args.top_n_best, len(claims))
        
        logger.info(f"  Claims to include: {selected_count}")
        logger.info(f"    - Top worst: {args.top_n_worst if not args.all_claims else 'all'}")
        logger.info(f"    - Top best: {args.top_n_best if not args.all_claims else 'all'}")
        logger.info(f"  Clip duration: {args.clip_duration}s")
        logger.info(f"  Add overlays: {not args.no_overlays}")
        logger.info(f"  Output directory: {output_dir}")
        
        # Show selected claims
        selected = generator.select_claims_for_tutorial(
            claims, 
            args.top_n_worst if not args.all_claims else 0,
            args.top_n_best if not args.all_claims else 0,
            args.all_claims
        )
        
        logger.info("\n📋 Selected claims:")
        for i, claim in enumerate(selected):
            timestamp = claim.get('timestamp', '00:00')
            text = claim.get('claim_text', '')[:60]
            verdict = generator.get_verdict(claim)
            false_prob = generator.get_false_probability(claim)
            logger.info(f"  {i+1}. [{timestamp}] {text}... ({verdict}, FALSE: {false_prob:.1%})")
        
        return 0
    
    # Generate tutorial
    logger.info(f"\n🚀 Generating tutorial for: {video_id}")
    
    result = generator.generate_tutorial(
        video_id=video_id,
        claims=claims,
        output_dir=output_dir,
        video_url=args.video_url,
        title=args.title,
        top_n_worst=args.top_n_worst if not args.all_claims else 0,
        top_n_best=args.top_n_best if not args.all_claims else 0,
        include_all=args.all_claims,
        add_overlays=not args.no_overlays,
        save_individual_clips=not args.no_save_clips
    )
    
    if result["success"]:
        logger.info("\n" + "=" * 60)
        logger.info("✅ Tutorial generation complete!")
        logger.info("=" * 60)
        
        if result["tutorial_path"]:
            logger.info(f"📹 Tutorial video: {result['tutorial_path']}")
        
        if result["clip_paths"]:
            logger.info(f"📂 Individual clips: {len(result['clip_paths'])} clips")
            for clip_path in result["clip_paths"][:3]:
                logger.info(f"    - {clip_path}")
            if len(result["clip_paths"]) > 3:
                logger.info(f"    ... and {len(result['clip_paths']) - 3} more")
        
        if result.get("metadata_path"):
            logger.info(f"📄 Metadata: {result['metadata_path']}")
        
        return 0
    else:
        logger.error(f"\n❌ Tutorial generation failed: {result.get('error', 'Unknown error')}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

