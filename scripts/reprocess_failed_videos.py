#!/usr/bin/env python3
"""
Reprocess failed videos from a batch tracking file.

This script identifies videos that failed or are still processing,
and resubmits them to the API for verification.
"""

import json
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any
import requests
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.batch_process_test_videos import get_api_url, submit_video


def load_batch_tracking(batch_file: Path) -> Dict[str, Any]:
    """Load batch tracking JSON file."""
    with open(batch_file, 'r') as f:
        return json.load(f)


def get_failed_videos(batch_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract videos that failed or are still processing."""
    failed = []
    
    for video in batch_data.get("videos", []):
        status = video.get("status", "unknown")
        if status in ["failed", "processing"]:
            failed.append(video)
    
    return failed


def main():
    parser = argparse.ArgumentParser(description="Reprocess failed videos from batch")
    parser.add_argument(
        "--batch-file",
        type=str,
        required=True,
        help="Path to batch_tracking.json file"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default=None,
        help="API URL (default: from batch file or http://localhost:8080)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be reprocessed without actually submitting"
    )
    
    args = parser.parse_args()
    
    batch_file = Path(args.batch_file)
    if not batch_file.exists():
        print(f"❌ Batch file not found: {batch_file}")
        sys.exit(1)
    
    # Load batch data
    print(f"📂 Loading batch file: {batch_file}")
    batch_data = load_batch_tracking(batch_file)
    
    # Get failed videos
    failed_videos = get_failed_videos(batch_data)
    
    if not failed_videos:
        print("✅ No failed or processing videos found!")
        return
    
    print(f"\n📊 Found {len(failed_videos)} videos to reprocess:")
    for video in failed_videos:
        video_id = video.get("video_id", "unknown")
        status = video.get("status", "unknown")
        error = video.get("error_message", "")
        print(f"  • {video_id}: {status}")
        if error:
            print(f"    Error: {error[:100]}")
    
    if args.dry_run:
        print("\n🔍 Dry run mode - no videos will be submitted")
        return
    
    # Get API URL
    api_url = args.api_url or batch_data.get("api_url") or "http://localhost:8080"
    print(f"\n🌐 Using API URL: {api_url}")
    
    # Check API health
    try:
        health_url = f"{api_url.rstrip('/')}/health"
        response = requests.get(health_url, timeout=5)
        if response.status_code != 200:
            print(f"⚠️  API health check failed: {response.status_code}")
            sys.exit(1)
        print("✅ API is healthy")
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        sys.exit(1)
    
    # Reprocess videos
    print(f"\n🚀 Reprocessing {len(failed_videos)} videos...")
    successful = []
    failed = []
    
    for video in failed_videos:
        video_id = video.get("video_id", "unknown")
        youtube_url = video.get("youtube_url", "")
        
        if not youtube_url:
            print(f"  ⚠️  Skipping {video_id}: No YouTube URL")
            failed.append({"video_id": video_id, "reason": "No YouTube URL"})
            continue
        
        print(f"\n  📹 Processing: {video_id}")
        print(f"     URL: {youtube_url}")
        
        try:
            task_id = submit_video(api_url, youtube_url)
            if task_id:
                print(f"     ✅ Submitted successfully (task_id: {task_id})")
                successful.append({"video_id": video_id, "task_id": task_id})
            else:
                print(f"     ❌ Failed to submit")
                failed.append({"video_id": video_id, "reason": "Submission failed"})
        except Exception as e:
            print(f"     ❌ Error: {e}")
            failed.append({"video_id": video_id, "reason": str(e)})
    
    # Summary
    print(f"\n✅ Reprocessing complete!")
    print(f"  Successful: {len(successful)}")
    print(f"  Failed: {len(failed)}")
    
    if successful:
        print(f"\n📋 Successfully submitted videos:")
        for item in successful:
            print(f"  • {item['video_id']}: {item['task_id']}")
    
    if failed:
        print(f"\n❌ Failed videos:")
        for item in failed:
            print(f"  • {item['video_id']}: {item['reason']}")


if __name__ == "__main__":
    main()

