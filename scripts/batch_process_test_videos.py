#!/usr/bin/env python3
"""
Batch process test videos from test_videos.json.

This script reads test_videos.json and submits all videos to the VerityNgn API
for verification, tracking their progress in a batch tracking file.

Usage:
    # Process all videos
    python scripts/batch_process_test_videos.py

    # Process only first 5 videos
    python scripts/batch_process_test_videos.py --limit 5

    # Process specific category
    python scripts/batch_process_test_videos.py --category "Health & Medicine"

    # Process single video by ID
    python scripts/batch_process_test_videos.py --video-id tLJC8hkK-ao

    # Skip videos that already have results
    python scripts/batch_process_test_videos.py --skip-existing
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests
from urllib.parse import urlparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configuration
TEST_VIDEOS_FILE = project_root / "test_videos.json"
TEST_RESULTS_DIR = project_root / "test_results"
DEFAULT_API_URL = os.getenv("VERITYNGN_API_URL", "http://localhost:8080")


def load_test_videos() -> Dict[str, Any]:
    """Load test videos from test_videos.json."""
    if not TEST_VIDEOS_FILE.exists():
        print(f"❌ Test videos file not found: {TEST_VIDEOS_FILE}")
        sys.exit(1)
    
    with open(TEST_VIDEOS_FILE, 'r') as f:
        return json.load(f)


def check_existing_results(video_id: str) -> bool:
    """Check if video already has results in outputs directory."""
    outputs_dir = project_root / "outputs" / video_id
    if not outputs_dir.exists():
        return False
    
    # Check for any _complete directories
    complete_dirs = list(outputs_dir.glob("*_complete"))
    return len(complete_dirs) > 0


def submit_video_to_api(api_url: str, youtube_url: str) -> Optional[Dict[str, Any]]:
    """Submit a video to the API for verification."""
    try:
        response = requests.post(
            f"{api_url}/api/v1/verification/verify",
            json={"video_url": youtube_url},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"  ❌ API error: {e}")
        return None


def create_batch_tracking_file() -> Path:
    """Create a new batch tracking file."""
    TEST_RESULTS_DIR.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    batch_id = f"batch_{timestamp}"
    batch_dir = TEST_RESULTS_DIR / batch_id
    batch_dir.mkdir(exist_ok=True)
    
    tracking_file = batch_dir / "batch_tracking.json"
    
    return tracking_file, batch_id, batch_dir


def load_batch_tracking(tracking_file: Path) -> Dict[str, Any]:
    """Load existing batch tracking file."""
    if tracking_file.exists():
        with open(tracking_file, 'r') as f:
            return json.load(f)
    return None


def save_batch_tracking(tracking_file: Path, data: Dict[str, Any]):
    """Save batch tracking data to file."""
    with open(tracking_file, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def extract_video_id(youtube_url: str) -> str:
    """Extract video ID from YouTube URL."""
    try:
        parsed = urlparse(youtube_url)
        if parsed.hostname in ['youtube.com', 'www.youtube.com', 'youtu.be']:
            if 'watch' in parsed.path or 'watch' in parsed.query:
                if 'v=' in parsed.query:
                    return parsed.query.split('v=')[1].split('&')[0]
                elif parsed.path.startswith('/watch/'):
                    return parsed.path.split('/watch/')[1].split('/')[0]
            elif parsed.hostname == 'youtu.be':
                return parsed.path.lstrip('/').split('?')[0]
    except Exception:
        pass
    
    # Fallback: try to extract from URL string
    if 'watch?v=' in youtube_url:
        return youtube_url.split('watch?v=')[1].split('&')[0]
    elif 'youtu.be/' in youtube_url:
        return youtube_url.split('youtu.be/')[1].split('?')[0]
    
    return "unknown"


def main():
    parser = argparse.ArgumentParser(
        description="Batch process test videos from test_videos.json"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Process only first N videos"
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip videos that already have results"
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
        "--parallel",
        type=int,
        default=1,
        help="Process N videos concurrently (default: 1, sequential)"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default=DEFAULT_API_URL,
        help=f"API URL (default: {DEFAULT_API_URL})"
    )
    parser.add_argument(
        "--batch-file",
        type=str,
        help="Use existing batch tracking file (for resuming)"
    )
    
    args = parser.parse_args()
    
    # Load test videos
    print("📚 Loading test videos...")
    test_data = load_test_videos()
    videos = test_data.get("test_videos", [])
    
    # Filter videos
    filtered_videos = []
    for video in videos:
        # Filter by video_id
        if args.video_id and video.get("video_id") != args.video_id:
            continue
        
        # Filter by category
        if args.category and video.get("category") != args.category:
            continue
        
        # Skip existing if requested
        if args.skip_existing:
            video_id = video.get("video_id", extract_video_id(video.get("youtube_url", "")))
            if check_existing_results(video_id):
                print(f"⏭️  Skipping {video_id} (already has results)")
                continue
        
        filtered_videos.append(video)
    
    # Apply limit
    if args.limit:
        filtered_videos = filtered_videos[:args.limit]
    
    if not filtered_videos:
        print("❌ No videos to process after filtering")
        sys.exit(1)
    
    print(f"✅ Found {len(filtered_videos)} video(s) to process")
    
    # Check API health
    print(f"🔍 Checking API health at {args.api_url}...")
    try:
        response = requests.get(f"{args.api_url}/health", timeout=5)
        response.raise_for_status()
        print("✅ API is healthy")
    except requests.exceptions.RequestException as e:
        print(f"❌ API health check failed: {e}")
        print(f"   Make sure the API is running at {args.api_url}")
        sys.exit(1)
    
    # Create or load batch tracking file
    if args.batch_file:
        tracking_file = Path(args.batch_file)
        if not tracking_file.exists():
            print(f"❌ Batch tracking file not found: {tracking_file}")
            sys.exit(1)
        batch_data = load_batch_tracking(tracking_file)
        batch_dir = tracking_file.parent
        batch_id = batch_data.get("batch_id", "unknown")
        print(f"📂 Resuming batch: {batch_id}")
    else:
        tracking_file, batch_id, batch_dir = create_batch_tracking_file()
        batch_data = {
            "batch_id": batch_id,
            "started_at": datetime.now().isoformat(),
            "total_videos": len(filtered_videos),
            "api_url": args.api_url,
            "videos": []
        }
        print(f"📂 Created new batch: {batch_id}")
    
    # Process videos
    print(f"\n🚀 Submitting {len(filtered_videos)} video(s) to API...")
    print("=" * 80)
    
    for idx, video in enumerate(filtered_videos, 1):
        video_id = video.get("video_id", extract_video_id(video.get("youtube_url", "")))
        youtube_url = video.get("youtube_url", "")
        title = video.get("title", "Unknown")[:60]
        
        print(f"\n[{idx}/{len(filtered_videos)}] Processing: {title}")
        print(f"  Video ID: {video_id}")
        print(f"  URL: {youtube_url}")
        
        # Check if already in tracking
        existing_entry = None
        for entry in batch_data.get("videos", []):
            if entry.get("video_id") == video_id:
                existing_entry = entry
                break
        
        if existing_entry:
            print(f"  ⏭️  Already tracked (status: {existing_entry.get('status')})")
            continue
        
        # Submit to API
        print(f"  📤 Submitting to API...")
        result = submit_video_to_api(args.api_url, youtube_url)
        
        if not result:
            print(f"  ❌ Failed to submit")
            entry = {
                "test_id": video.get("id"),
                "video_id": video_id,
                "youtube_url": youtube_url,
                "title": title,
                "category": video.get("category"),
                "task_id": None,
                "status": "error",
                "submitted_at": datetime.now().isoformat(),
                "error_message": "Failed to submit to API"
            }
        else:
            task_id = result.get("task_id")
            print(f"  ✅ Submitted successfully (task_id: {task_id})")
            entry = {
                "test_id": video.get("id"),
                "video_id": video_id,
                "youtube_url": youtube_url,
                "title": title,
                "category": video.get("category"),
                "task_id": task_id,
                "status": "pending",
                "submitted_at": datetime.now().isoformat(),
                "completed_at": None,
                "result_path": None,
                "error_message": None
            }
        
        batch_data["videos"].append(entry)
        save_batch_tracking(tracking_file, batch_data)
        
        # Small delay to avoid overwhelming API
        if idx < len(filtered_videos):
            time.sleep(1)
    
    # Final summary
    print("\n" + "=" * 80)
    print("✅ Batch submission complete!")
    print(f"📂 Tracking file: {tracking_file}")
    print(f"📊 Total videos: {len(batch_data['videos'])}")
    
    status_counts = {}
    for entry in batch_data["videos"]:
        status = entry.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print("\nStatus summary:")
    for status, count in status_counts.items():
        print(f"  {status}: {count}")
    
    print(f"\n💡 Next steps:")
    print(f"  1. Monitor progress: python scripts/monitor_batch_progress.py --batch-file {tracking_file}")
    print(f"  2. Import to gallery: python scripts/import_test_results_to_gallery.py --batch-file {tracking_file}")


if __name__ == "__main__":
    main()

