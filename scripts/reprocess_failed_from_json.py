#!/usr/bin/env python3
"""
Reprocess failed videos using updated test_videos.json.

This script reads test_videos.json and submits videos that were previously
failed or are still processing, using the updated video IDs.
"""

import json
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any
import requests

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.batch_process_test_videos import submit_video_to_api, DEFAULT_API_URL


def load_test_videos(test_videos_file: Path) -> Dict[str, Any]:
    """Load test_videos.json file."""
    with open(test_videos_file, 'r') as f:
        return json.load(f)


def get_failed_test_ids(batch_file: Path) -> set:
    """Get set of test IDs that failed or are processing from batch tracking."""
    with open(batch_file, 'r') as f:
        batch_data = json.load(f)
    
    failed_test_ids = set()
    for video in batch_data.get("videos", []):
        status = video.get("status", "unknown")
        if status in ["failed", "processing"]:
            test_id = video.get("test_id")
            if test_id is not None:
                failed_test_ids.add(test_id)
    
    return failed_test_ids


def main():
    parser = argparse.ArgumentParser(description="Reprocess failed videos from test_videos.json")
    parser.add_argument(
        "--batch-file",
        type=str,
        required=True,
        help="Path to batch_tracking.json file (to identify failed videos)"
    )
    parser.add_argument(
        "--test-videos",
        type=str,
        default="test_videos.json",
        help="Path to test_videos.json (default: test_videos.json)"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default=None,
        help="API URL (default: http://localhost:8080)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be reprocessed without actually submitting"
    )
    
    args = parser.parse_args()
    
    batch_file = Path(args.batch_file)
    test_videos_file = Path(args.test_videos)
    
    if not batch_file.exists():
        print(f"❌ Batch file not found: {batch_file}")
        sys.exit(1)
    
    if not test_videos_file.exists():
        print(f"❌ Test videos file not found: {test_videos_file}")
        sys.exit(1)
    
    # Load data
    print(f"📂 Loading batch file: {batch_file}")
    failed_test_ids = get_failed_test_ids(batch_file)
    
    print(f"📂 Loading test videos: {test_videos_file}")
    test_data = load_test_videos(test_videos_file)
    
    # Find videos to reprocess (match by test_id)
    videos_to_reprocess = []
    for video in test_data.get("test_videos", []):
        test_id = video.get("id")
        if test_id in failed_test_ids:
            videos_to_reprocess.append(video)
    
    if not videos_to_reprocess:
        print("✅ No failed videos found in test_videos.json!")
        return
    
    print(f"\n📊 Found {len(videos_to_reprocess)} videos to reprocess:")
    for video in videos_to_reprocess:
        video_id = video.get("video_id", "unknown")
        title = video.get("title", "Unknown")
        youtube_url = video.get("youtube_url", "")
        print(f"  • {video_id}: {title[:50]}")
        print(f"    URL: {youtube_url}")
    
    if args.dry_run:
        print("\n🔍 Dry run mode - no videos will be submitted")
        return
    
    # Get API URL
    api_url = args.api_url or DEFAULT_API_URL
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
    print(f"\n🚀 Reprocessing {len(videos_to_reprocess)} videos...")
    successful = []
    failed = []
    
    for video in videos_to_reprocess:
        video_id = video.get("video_id", "unknown")
        youtube_url = video.get("youtube_url", "")
        title = video.get("title", "Unknown")
        
        if not youtube_url:
            print(f"  ⚠️  Skipping {video_id}: No YouTube URL")
            failed.append({"video_id": video_id, "reason": "No YouTube URL"})
            continue
        
        print(f"\n  📹 Processing: {video_id}")
        print(f"     Title: {title[:60]}")
        print(f"     URL: {youtube_url}")
        
        try:
            result = submit_video_to_api(api_url, youtube_url)
            if result and result.get("task_id"):
                task_id = result["task_id"]
                print(f"     ✅ Submitted successfully (task_id: {task_id})")
                successful.append({"video_id": video_id, "task_id": task_id, "title": title})
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
            print(f"  • {item['video_id']}: {item['title'][:50]}")
            print(f"    Task ID: {item['task_id']}")
    
    if failed:
        print(f"\n❌ Failed videos:")
        for item in failed:
            print(f"  • {item['video_id']}: {item['reason']}")


if __name__ == "__main__":
    main()

