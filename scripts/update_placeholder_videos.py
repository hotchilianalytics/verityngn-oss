#!/usr/bin/env python3
"""
Update placeholder videos in test_videos.json with verified active video IDs.

This script takes a mapping of test_id -> new_video_id and updates test_videos.json,
verifying each video is active before updating.
"""

import json
import sys
import argparse
import requests
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def verify_video_active(video_id: str) -> tuple[bool, Optional[Dict[str, Any]]]:
    """Verify a YouTube video is active and accessible."""
    try:
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return True, {
                "title": data.get("title", "Unknown"),
                "author": data.get("author_name", "Unknown"),
            }
        else:
            return False, None
    except Exception as e:
        return False, None


def update_test_videos(test_videos_file: Path, replacements: Dict[int, str], dry_run: bool = False) -> Dict[str, Any]:
    """Update test_videos.json with new video IDs."""
    with open(test_videos_file, 'r') as f:
        data = json.load(f)
    
    updated_count = 0
    failed_verifications = []
    
    for video in data.get("test_videos", []):
        test_id = video.get("id")
        if test_id in replacements:
            new_video_id = replacements[test_id]
            old_video_id = video.get("video_id", "")
            
            # Verify new video is active
            is_active, info = verify_video_active(new_video_id)
            
            if not is_active:
                print(f"⚠️  Test ID {test_id}: Video {new_video_id} is not accessible - skipping")
                failed_verifications.append({"test_id": test_id, "video_id": new_video_id})
                continue
            
            print(f"✅ Test ID {test_id}: Verified {new_video_id}")
            print(f"   Title: {info['title']}")
            print(f"   Author: {info['author']}")
            
            if not dry_run:
                video["video_id"] = new_video_id
                video["youtube_url"] = f"https://www.youtube.com/watch?v={new_video_id}"
                # Update notes to indicate it's been replaced
                old_notes = video.get("notes", "")
                if "placeholder" in old_notes.lower() or "replace" in old_notes.lower():
                    video["notes"] = f"Replaced placeholder with verified active video. Original notes: {old_notes}"
                updated_count += 1
            else:
                print(f"   [DRY RUN] Would update from {old_video_id} to {new_video_id}")
                updated_count += 1
    
    if not dry_run and updated_count > 0:
        with open(test_videos_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    return {
        "updated": updated_count,
        "failed": failed_verifications
    }


def main():
    parser = argparse.ArgumentParser(description="Update placeholder videos with verified active ones")
    parser.add_argument(
        "--test-videos",
        type=str,
        default="test_videos.json",
        help="Path to test_videos.json"
    )
    parser.add_argument(
        "--replacements",
        type=str,
        required=True,
        help="JSON string mapping test_id to video_id, e.g. '{\"5\":\"VIDEO_ID\",\"7\":\"VIDEO_ID2\"}'"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without making changes"
    )
    
    args = parser.parse_args()
    
    test_videos_file = Path(args.test_videos)
    if not test_videos_file.exists():
        print(f"❌ Test videos file not found: {test_videos_file}")
        sys.exit(1)
    
    # Parse replacements
    try:
        replacements = json.loads(args.replacements)
        # Convert string keys to int
        replacements = {int(k): v for k, v in replacements.items()}
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in --replacements: {e}")
        sys.exit(1)
    
    print(f"📂 Loading test videos: {test_videos_file}")
    print(f"📋 Found {len(replacements)} replacements to process\n")
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made\n")
    
    result = update_test_videos(test_videos_file, replacements, dry_run=args.dry_run)
    
    print(f"\n✅ Update complete!")
    print(f"   Updated: {result['updated']}")
    if result['failed']:
        print(f"   Failed verifications: {len(result['failed'])}")
        for item in result['failed']:
            print(f"     - Test ID {item['test_id']}: {item['video_id']}")
    
    if not args.dry_run and result['updated'] > 0:
        print(f"\n💾 File saved: {test_videos_file}")


if __name__ == "__main__":
    main()

