#!/usr/bin/env python3
"""
Quick status check for the 11 reprocessed videos.

This script provides a concise summary of the status of the 11 videos
that were reprocessed after fixing invalid video IDs.
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Test IDs for the 11 reprocessed videos
REPROCESSED_TEST_IDS = {5, 6, 7, 8, 9, 11, 12, 14, 15, 16, 19}


def load_batch_tracking(batch_file: Path) -> Dict[str, Any]:
    """Load batch tracking file."""
    with open(batch_file, 'r') as f:
        return json.load(f)


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def estimate_completion_time(submitted_at: str, progress: float) -> str:
    """Estimate completion time based on current progress."""
    if progress <= 0:
        return "Unknown"
    
    try:
        submitted = datetime.fromisoformat(submitted_at.replace('Z', '+00:00'))
        elapsed = (datetime.now() - submitted.replace(tzinfo=None)).total_seconds()
        
        if progress > 0:
            estimated_total = elapsed / progress
            remaining = estimated_total - elapsed
            return format_duration(remaining)
    except Exception:
        pass
    
    return "Unknown"


def main():
    parser = argparse.ArgumentParser(description="Check status of reprocessed videos")
    parser.add_argument(
        "--batch-file",
        type=str,
        default="test_results/batch_2025-11-12T23-07-00/batch_tracking.json",
        help="Path to batch_tracking.json file"
    )
    
    args = parser.parse_args()
    
    batch_file = Path(args.batch_file)
    if not batch_file.exists():
        print(f"❌ Batch file not found: {batch_file}")
        sys.exit(1)
    
    batch_data = load_batch_tracking(batch_file)
    
    # Filter for reprocessed videos
    reprocessed_videos = [
        v for v in batch_data.get("videos", [])
        if v.get("test_id") in REPROCESSED_TEST_IDS
    ]
    
    if not reprocessed_videos:
        print("❌ No reprocessed videos found in batch file")
        sys.exit(1)
    
    # Sort by test_id
    reprocessed_videos.sort(key=lambda x: x.get("test_id", 0))
    
    # Count by status
    status_counts = {}
    for video in reprocessed_videos:
        status = video.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Print summary
    print("=" * 80)
    print("📊 REPROCESSED VIDEOS STATUS SUMMARY")
    print("=" * 80)
    print(f"\nTotal reprocessed videos: {len(reprocessed_videos)}")
    print(f"Status breakdown:")
    for status, count in sorted(status_counts.items()):
        emoji = "✅" if status == "completed" else "❌" if status == "failed" else "🔄"
        print(f"  {emoji} {status}: {count}")
    
    print("\n" + "=" * 80)
    print("📋 DETAILED STATUS")
    print("=" * 80)
    
    for video in reprocessed_videos:
        test_id = video.get("test_id", "?")
        video_id = video.get("video_id", "unknown")
        title = video.get("title", "Unknown")[:50]
        status = video.get("status", "unknown")
        progress = video.get("progress", 0.0) * 100
        message = video.get("message", "")
        submitted_at = video.get("submitted_at", "")
        
        # Status emoji
        if status == "completed":
            emoji = "✅"
        elif status == "failed":
            emoji = "❌"
        elif status == "processing":
            emoji = "🔄"
        else:
            emoji = "⏳"
        
        print(f"\n{emoji} Test ID {test_id}: {video_id}")
        print(f"   Title: {title}")
        print(f"   Status: {status}")
        
        if status == "processing":
            print(f"   Progress: {progress:.1f}%")
            if submitted_at:
                remaining = estimate_completion_time(submitted_at, video.get("progress", 0.0))
                print(f"   Estimated remaining: {remaining}")
        
        if message:
            print(f"   Message: {message[:80]}")
        
        if status == "completed":
            completed_at = video.get("completed_at")
            processing_time = video.get("processing_time_seconds", 0)
            if processing_time:
                print(f"   Processing time: {format_duration(processing_time)}")
        
        if status == "failed":
            error = video.get("error_message", "")
            if error:
                print(f"   Error: {error[:80]}")
    
    print("\n" + "=" * 80)
    
    # Check if all done
    all_done = all(
        v.get("status") in ["completed", "failed", "error"]
        for v in reprocessed_videos
    )
    
    if all_done:
        print("🎉 All reprocessed videos are complete!")
    else:
        processing = [v for v in reprocessed_videos if v.get("status") == "processing"]
        print(f"⏳ {len(processing)} video(s) still processing...")


if __name__ == "__main__":
    main()

