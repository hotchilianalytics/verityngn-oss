#!/usr/bin/env python3
"""
Find and verify replacement videos for placeholder entries in test_videos.json.

This script helps identify active YouTube videos that match the profile of
placeholder videos, then verifies they're accessible.
"""

import json
import sys
import argparse
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List

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
                "thumbnail": data.get("thumbnail_url", "")
            }
        else:
            return False, None
    except Exception as e:
        return False, None


def find_placeholder_videos(test_videos_file: Path) -> List[Dict[str, Any]]:
    """Find all videos with placeholder video IDs."""
    with open(test_videos_file, 'r') as f:
        data = json.load(f)
    
    placeholders = []
    for video in data.get("test_videos", []):
        video_id = video.get("video_id", "")
        if video_id == "dQw4w9WgXcQ":  # Rick Astley placeholder
            placeholders.append(video)
    
    return placeholders


def main():
    parser = argparse.ArgumentParser(description="Find replacement videos for placeholders")
    parser.add_argument(
        "--test-videos",
        type=str,
        default="test_videos.json",
        help="Path to test_videos.json"
    )
    parser.add_argument(
        "--verify",
        type=str,
        nargs="+",
        help="Video IDs to verify (space-separated)"
    )
    
    args = parser.parse_args()
    
    test_videos_file = Path(args.test_videos)
    if not test_videos_file.exists():
        print(f"❌ Test videos file not found: {test_videos_file}")
        sys.exit(1)
    
    if args.verify:
        # Verify specific video IDs
        print("🔍 Verifying video IDs...\n")
        for video_id in args.verify:
            is_active, info = verify_video_active(video_id)
            if is_active:
                print(f"✅ {video_id}: {info['title']}")
                print(f"   Author: {info['author']}")
            else:
                print(f"❌ {video_id}: Not accessible")
            print()
    else:
        # List placeholder videos
        placeholders = find_placeholder_videos(test_videos_file)
        
        print(f"📋 Found {len(placeholders)} placeholder videos:\n")
        print("=" * 80)
        
        for video in placeholders:
            test_id = video.get("id")
            title = video.get("title", "Unknown")
            category = video.get("category", "Unknown")
            subcategory = video.get("subcategory", "")
            tags = ", ".join(video.get("tags", []))
            
            print(f"\nTest ID {test_id}: {title}")
            print(f"  Category: {category} / {subcategory}")
            print(f"  Tags: {tags}")
            print(f"  Expected Verdict: {video.get('expected_verdict', 'Unknown')}")
            print(f"  Notes: {video.get('notes', '')[:100]}")
        
        print("\n" + "=" * 80)
        print("\n💡 To verify a video ID, use:")
        print("   python scripts/find_replacement_videos.py --verify VIDEO_ID1 VIDEO_ID2 ...")


if __name__ == "__main__":
    main()

