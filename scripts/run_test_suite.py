#!/usr/bin/env python3
"""
Comprehensive test suite runner.

Orchestrates the entire test workflow: batch processing, monitoring,
and optional gallery import.

Usage:
    # Process all videos
    python scripts/run_test_suite.py --process-all

    # Process and auto-import
    python scripts/run_test_suite.py --process-all --auto-import

    # Process specific category
    python scripts/run_test_suite.py --category "Health & Medicine" --limit 5

    # Monitor existing batch
    python scripts/run_test_suite.py --monitor --batch-file test_results/batch_.../batch_tracking.json
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_command(cmd: list, description: str):
    """Run a command and handle errors."""
    print(f"\n{'='*80}")
    print(f"🚀 {description}")
    print(f"{'='*80}")
    print(f"Command: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd, cwd=project_root)
    
    if result.returncode != 0:
        print(f"\n❌ Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive test suite runner for VerityNgn"
    )
    
    # Processing options
    parser.add_argument(
        "--process-all",
        action="store_true",
        help="Process all videos from test_videos.json"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Process only first N videos"
    )
    parser.add_argument(
        "--category",
        type=str,
        help="Process only specific category"
    )
    parser.add_argument(
        "--video-id",
        type=str,
        help="Process single video by video_id"
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip videos that already have results"
    )
    
    # Monitoring options
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Monitor batch progress"
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch mode (continuous monitoring)"
    )
    parser.add_argument(
        "--batch-file",
        type=str,
        help="Use specific batch tracking file"
    )
    
    # Import options
    parser.add_argument(
        "--auto-import",
        action="store_true",
        help="Automatically import completed videos to gallery"
    )
    parser.add_argument(
        "--import-only",
        action="store_true",
        help="Only import (skip processing)"
    )
    parser.add_argument(
        "--min-claims",
        type=int,
        help="Minimum claims count for import"
    )
    parser.add_argument(
        "--verdict-match",
        action="store_true",
        help="Only import if verdict matches expected"
    )
    
    # Other options
    parser.add_argument(
        "--api-url",
        type=str,
        help="API URL (default: from VERITYNGN_API_URL env or http://localhost:8080)"
    )
    
    args = parser.parse_args()
    
    # Determine workflow
    if args.import_only:
        # Import only workflow
        if not args.batch_file:
            print("❌ --batch-file required for --import-only")
            sys.exit(1)
        
        cmd = ["python", "scripts/import_test_results_to_gallery.py", "--batch-file", args.batch_file]
        
        if args.min_claims:
            cmd.extend(["--min-claims", str(args.min_claims)])
        if args.verdict_match:
            cmd.append("--verdict-match")
        if args.category:
            cmd.extend(["--category", args.category])
        
        run_command(cmd, "Importing results to gallery")
        
    elif args.monitor:
        # Monitor only workflow
        cmd = ["python", "scripts/monitor_batch_progress.py"]
        
        if args.batch_file:
            cmd.extend(["--batch-file", args.batch_file])
        if args.watch:
            cmd.append("--watch")
        if args.api_url:
            cmd.extend(["--api-url", args.api_url])
        
        run_command(cmd, "Monitoring batch progress")
        
    elif args.process_all or args.limit or args.category or args.video_id:
        # Processing workflow
        cmd = ["python", "scripts/batch_process_test_videos.py"]
        
        if args.process_all:
            pass  # Process all is default
        if args.limit:
            cmd.extend(["--limit", str(args.limit)])
        if args.category:
            cmd.extend(["--category", args.category])
        if args.video_id:
            cmd.extend(["--video-id", args.video_id])
        if args.skip_existing:
            cmd.append("--skip-existing")
        if args.api_url:
            cmd.extend(["--api-url", args.api_url])
        
        result = run_command(cmd, "Processing test videos")
        
        # If auto-import requested, find the batch file and import
        if args.auto_import:
            # The batch file path should be in the output, but we can find the latest
            from scripts.monitor_batch_progress import find_latest_batch_file
            
            batch_file = find_latest_batch_file()
            if batch_file:
                print(f"\n📂 Found batch file: {batch_file}")
                
                # First, monitor until complete
                print("\n⏳ Waiting for videos to complete...")
                monitor_cmd = ["python", "scripts/monitor_batch_progress.py", "--batch-file", str(batch_file), "--watch"]
                if args.api_url:
                    monitor_cmd.extend(["--api-url", args.api_url])
                
                run_command(monitor_cmd, "Monitoring until completion")
                
                # Then import
                import_cmd = ["python", "scripts/import_test_results_to_gallery.py", "--batch-file", str(batch_file)]
                
                if args.min_claims:
                    import_cmd.extend(["--min-claims", str(args.min_claims)])
                if args.verdict_match:
                    import_cmd.append("--verdict-match")
                if args.category:
                    import_cmd.extend(["--category", args.category])
                
                run_command(import_cmd, "Importing to gallery")
            else:
                print("⚠️  Could not find batch file for auto-import")
        
    else:
        parser.print_help()
        print("\n💡 Examples:")
        print("  # Process all videos")
        print("  python scripts/run_test_suite.py --process-all")
        print("\n  # Process and auto-import")
        print("  python scripts/run_test_suite.py --process-all --auto-import")
        print("\n  # Process specific category")
        print("  python scripts/run_test_suite.py --category 'Health & Medicine' --limit 5")
        print("\n  # Monitor existing batch")
        print("  python scripts/run_test_suite.py --monitor --watch")
        print("\n  # Import only")
        print("  python scripts/run_test_suite.py --import-only --batch-file test_results/batch_.../batch_tracking.json")


if __name__ == "__main__":
    main()

