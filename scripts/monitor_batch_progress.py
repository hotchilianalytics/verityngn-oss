#!/usr/bin/env python3
"""
Monitor batch processing progress.

This script reads a batch tracking file and polls the API to update
the status of all verification tasks.

Usage:
    # Monitor latest batch
    python scripts/monitor_batch_progress.py

    # Monitor specific batch file
    python scripts/monitor_batch_progress.py --batch-file test_results/batch_.../batch_tracking.json

    # Watch mode (continuous monitoring)
    python scripts/monitor_batch_progress.py --watch

    # Update once and exit
    python scripts/monitor_batch_progress.py --once
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configuration
TEST_RESULTS_DIR = project_root / "test_results"
DEFAULT_API_URL = os.getenv("VERITYNGN_API_URL", "http://localhost:8080")
POLL_INTERVAL = 10  # seconds


def find_latest_batch_file() -> Optional[Path]:
    """Find the latest batch tracking file."""
    if not TEST_RESULTS_DIR.exists():
        return None
    
    batch_dirs = [d for d in TEST_RESULTS_DIR.iterdir() if d.is_dir() and d.name.startswith("batch_")]
    if not batch_dirs:
        return None
    
    # Sort by modification time
    latest_dir = max(batch_dirs, key=lambda d: d.stat().st_mtime)
    tracking_file = latest_dir / "batch_tracking.json"
    
    if tracking_file.exists():
        return tracking_file
    
    return None


def load_batch_tracking(tracking_file: Path) -> Dict[str, Any]:
    """Load batch tracking file."""
    with open(tracking_file, 'r') as f:
        return json.load(f)


def save_batch_tracking(tracking_file: Path, data: Dict[str, Any]):
    """Save batch tracking file."""
    with open(tracking_file, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_task_status(api_url: str, task_id: str) -> Optional[Dict[str, Any]]:
    """Get task status from API."""
    try:
        response = requests.get(
            f"{api_url}/api/v1/verification/status/{task_id}",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return None


def find_result_path(video_id: str) -> Optional[str]:
    """Find the result path for a completed video."""
    outputs_dir = project_root / "outputs" / video_id
    if not outputs_dir.exists():
        return None
    
    # Find most recent _complete directory
    complete_dirs = sorted(
        [d for d in outputs_dir.glob("*_complete") if d.is_dir()],
        key=lambda d: d.stat().st_mtime,
        reverse=True
    )
    
    if complete_dirs:
        return str(complete_dirs[0].relative_to(project_root))
    
    return None


def update_batch_status(tracking_file: Path, api_url: str) -> Dict[str, Any]:
    """Update status of all videos in batch."""
    batch_data = load_batch_tracking(tracking_file)
    updated = False
    
    for entry in batch_data.get("videos", []):
        task_id = entry.get("task_id")
        if not task_id:
            continue
        
        current_status = entry.get("status")
        
        # Skip if already completed or errored
        if current_status in ["completed", "error"]:
            continue
        
        # Get status from API
        status_data = get_task_status(api_url, task_id)
        if not status_data:
            continue
        
        new_status = status_data.get("status")
        progress = status_data.get("progress", 0.0)
        message = status_data.get("message", "")
        video_id = status_data.get("video_id")
        error_message = status_data.get("error_message")
        
        # Update entry
        entry["status"] = new_status
        entry["progress"] = progress
        entry["message"] = message
        entry["updated_at"] = datetime.now().isoformat()
        
        if video_id:
            entry["video_id"] = video_id
        
        if error_message:
            entry["error_message"] = error_message
        
        # If completed, find result path
        if new_status == "completed":
            entry["completed_at"] = datetime.now().isoformat()
            result_path = find_result_path(video_id or entry.get("video_id", ""))
            if result_path:
                entry["result_path"] = result_path
            
            # Calculate processing time
            submitted_at = entry.get("submitted_at")
            if submitted_at:
                try:
                    submitted = datetime.fromisoformat(submitted_at.replace('Z', '+00:00'))
                    completed = datetime.fromisoformat(entry["completed_at"].replace('Z', '+00:00'))
                    processing_time = (completed - submitted).total_seconds()
                    entry["processing_time_seconds"] = processing_time
                except Exception:
                    pass
        
        if new_status != current_status:
            updated = True
    
    if updated:
        batch_data["last_updated"] = datetime.now().isoformat()
        save_batch_tracking(tracking_file, batch_data)
    
    return batch_data


def print_status_summary(batch_data: Dict[str, Any]):
    """Print a summary of batch status."""
    videos = batch_data.get("videos", [])
    total = len(videos)
    
    status_counts = {
        "pending": 0,
        "processing": 0,
        "completed": 0,
        "error": 0
    }
    
    for entry in videos:
        status = entry.get("status", "unknown")
        if status in status_counts:
            status_counts[status] += 1
    
    print("\n" + "=" * 80)
    print(f"📊 Batch Status: {batch_data.get('batch_id', 'unknown')}")
    print("=" * 80)
    print(f"Total videos: {total}")
    print(f"  ✅ Completed: {status_counts['completed']}")
    print(f"  🔄 Processing: {status_counts['processing']}")
    print(f"  ⏳ Pending: {status_counts['pending']}")
    print(f"  ❌ Error: {status_counts['error']}")
    
    # Show currently processing videos
    processing = [v for v in videos if v.get("status") == "processing"]
    if processing:
        print(f"\n🔄 Currently processing ({len(processing)}):")
        for entry in processing[:5]:  # Show max 5
            video_id = entry.get("video_id", "unknown")
            title = entry.get("title", "Unknown")[:50]
            progress = entry.get("progress", 0.0) * 100
            message = entry.get("message", "")[:40]
            print(f"  • {video_id}: {title}")
            print(f"    Progress: {progress:.1f}% - {message}")
        if len(processing) > 5:
            print(f"  ... and {len(processing) - 5} more")
    
    # Show recent completions
    completed = [v for v in videos if v.get("status") == "completed"]
    if completed:
        recent = sorted(completed, key=lambda v: v.get("completed_at", ""), reverse=True)[:3]
        print(f"\n✅ Recent completions ({len(completed)} total):")
        for entry in recent:
            video_id = entry.get("video_id", "unknown")
            title = entry.get("title", "Unknown")[:50]
            completed_at = entry.get("completed_at", "")
            if completed_at:
                try:
                    dt = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                    completed_at = dt.strftime("%H:%M:%S")
                except Exception:
                    pass
            print(f"  • {video_id}: {title} (completed at {completed_at})")
    
    # Show errors
    errors = [v for v in videos if v.get("status") == "error"]
    if errors:
        print(f"\n❌ Errors ({len(errors)}):")
        for entry in errors[:3]:  # Show max 3
            video_id = entry.get("video_id", "unknown")
            title = entry.get("title", "Unknown")[:50]
            error_msg = entry.get("error_message", "Unknown error")[:40]
            print(f"  • {video_id}: {title}")
            print(f"    Error: {error_msg}")
    
    # Estimate time remaining
    if status_counts["processing"] > 0 or status_counts["pending"] > 0:
        avg_time = None
        completed_times = [
            v.get("processing_time_seconds")
            for v in videos
            if v.get("status") == "completed" and v.get("processing_time_seconds")
        ]
        if completed_times:
            avg_time = sum(completed_times) / len(completed_times)
        
        remaining = status_counts["processing"] + status_counts["pending"]
        if avg_time:
            est_seconds = remaining * avg_time
            est_time = timedelta(seconds=int(est_seconds))
            hours = est_time.total_seconds() / 3600
            if hours < 1:
                print(f"\n⏱️  Estimated time remaining: ~{int(est_seconds / 60)} minutes")
            else:
                print(f"\n⏱️  Estimated time remaining: ~{hours:.1f} hours")
    
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Monitor batch processing progress"
    )
    parser.add_argument(
        "--batch-file",
        type=str,
        help="Path to batch tracking file (default: latest batch)"
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Continuously monitor until all complete"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Update once and exit (default behavior)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=POLL_INTERVAL,
        help=f"Polling interval in seconds (default: {POLL_INTERVAL})"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default=DEFAULT_API_URL,
        help=f"API URL (default: {DEFAULT_API_URL})"
    )
    
    args = parser.parse_args()
    
    # Find batch file
    if args.batch_file:
        tracking_file = Path(args.batch_file)
        if not tracking_file.exists():
            print(f"❌ Batch tracking file not found: {tracking_file}")
            sys.exit(1)
    else:
        tracking_file = find_latest_batch_file()
        if not tracking_file:
            print("❌ No batch tracking file found")
            print(f"   Run batch_process_test_videos.py first")
            sys.exit(1)
    
    print(f"📂 Using batch file: {tracking_file}")
    
    # Check API health
    try:
        response = requests.get(f"{args.api_url}/health", timeout=5)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"⚠️  API health check failed: {e}")
        print(f"   Continuing anyway...")
    
    # Monitor loop
    watch_mode = args.watch and not args.once
    iteration = 0
    
    while True:
        iteration += 1
        if iteration > 1:
            print(f"\n🔄 Update #{iteration} ({datetime.now().strftime('%H:%M:%S')})")
        
        # Update status
        batch_data = update_batch_status(tracking_file, args.api_url)
        
        # Print summary
        print_status_summary(batch_data)
        
        # Check if all done
        videos = batch_data.get("videos", [])
        all_done = all(
            v.get("status") in ["completed", "error"]
            for v in videos
        )
        
        if all_done:
            print("\n🎉 All videos completed!")
            break
        
        # Exit if not watching
        if not watch_mode:
            break
        
        # Wait before next update
        print(f"\n⏳ Waiting {args.interval} seconds before next update...")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()

