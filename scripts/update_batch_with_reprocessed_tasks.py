#!/usr/bin/env python3
"""
Update batch tracking file with new task IDs from reprocessed videos.

This script takes task IDs from reprocessed videos and updates the batch
tracking file with the new task IDs, resetting status to "processing".
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# Task IDs from reprocessing output
REPROCESSED_TASK_IDS = {
    5: "11df841f-46ef-42f8-8767-c65ebaea9d6b",   # dQw4w9WgXcQ - Essential Oils
    6: "022a8752-e3dd-4167-9ba2-f5e9d40d4b40",   # YQ_xWvX1n9g - Line Goes Up
    7: "18963aeb-85b7-45c4-963d-6da6e462334d",   # dQw4w9WgXcQ - Coffeezilla
    8: "b09cb1b1-5645-4e54-b92e-9571ff8737c0",   # dQw4w9WgXcQ - Tinder Swindler
    9: "6bf7ef59-72b0-47b3-a07c-beeccc126bf3",   # dQw4w9WgXcQ - Real Hustle
    11: "f88fa68e-5c16-4c5f-a29e-66cc1343f65b",  # dQw4w9WgXcQ - Get Rich Quick
    12: "a0d540a6-3e68-4b8d-9602-605f89cf465e",  # dQw4w9WgXcQ - MLM
    14: "173d667e-92d2-4c08-9f93-630d2607dfc3",  # dQw4w9WgXcQ - BitConnect
    15: "18ebb5eb-64eb-44e5-ad90-3f86dd8a49fa",  # dQw4w9WgXcQ - Bitcoin Prediction
    16: "55ca6d6a-1bdb-4de1-8170-8a4c248e5e39",  # dQw4w9WgXcQ - Absolute Proof
    19: "d1d45408-2413-4887-8e76-601830f438c3",  # VNqNnUJVcVs - Flat Earth
}


def load_batch_tracking(batch_file: Path) -> Dict[str, Any]:
    """Load batch tracking file."""
    with open(batch_file, 'r') as f:
        return json.load(f)


def save_batch_tracking(batch_file: Path, data: Dict[str, Any]):
    """Save batch tracking file."""
    with open(batch_file, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def update_batch_with_task_ids(batch_file: Path, task_ids: Dict[int, str], dry_run: bool = False) -> Dict[str, Any]:
    """Update batch tracking file with new task IDs."""
    batch_data = load_batch_tracking(batch_file)
    updated_count = 0
    
    now = datetime.now().isoformat()
    
    for entry in batch_data.get("videos", []):
        test_id = entry.get("test_id")
        if test_id in task_ids:
            old_task_id = entry.get("task_id")
            new_task_id = task_ids[test_id]
            
            if old_task_id != new_task_id:
                print(f"  Test ID {test_id}: Updating task_id")
                print(f"    Old: {old_task_id}")
                print(f"    New: {new_task_id}")
                
                if not dry_run:
                    entry["task_id"] = new_task_id
                    entry["status"] = "processing"
                    entry["submitted_at"] = now
                    entry["updated_at"] = now
                    entry["progress"] = 0.0
                    entry["message"] = "Task resubmitted, waiting to start..."
                    entry["completed_at"] = None
                    entry["result_path"] = None
                    entry["error_message"] = None
                
                updated_count += 1
            else:
                print(f"  Test ID {test_id}: Task ID already matches (skipping)")
    
    if not dry_run and updated_count > 0:
        batch_data["last_updated"] = now
        save_batch_tracking(batch_file, batch_data)
    
    return batch_data


def main():
    parser = argparse.ArgumentParser(description="Update batch tracking file with reprocessed task IDs")
    parser.add_argument(
        "--batch-file",
        type=str,
        required=True,
        help="Path to batch_tracking.json file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without making changes"
    )
    
    args = parser.parse_args()
    
    batch_file = Path(args.batch_file)
    if not batch_file.exists():
        print(f"❌ Batch file not found: {batch_file}")
        sys.exit(1)
    
    print(f"📂 Loading batch file: {batch_file}")
    print(f"📋 Found {len(REPROCESSED_TASK_IDS)} task IDs to update")
    
    if args.dry_run:
        print("\n🔍 DRY RUN MODE - No changes will be made\n")
    
    print("\n📝 Updating batch tracking file...")
    batch_data = update_batch_with_task_ids(batch_file, REPROCESSED_TASK_IDS, dry_run=args.dry_run)
    
    if args.dry_run:
        print("\n✅ Dry run complete - no changes made")
    else:
        print(f"\n✅ Updated batch tracking file!")
        print(f"   Updated {len([t for t in REPROCESSED_TASK_IDS.keys()])} video entries")
        print(f"   File saved: {batch_file}")


if __name__ == "__main__":
    main()

