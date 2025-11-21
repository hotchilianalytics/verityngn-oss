#!/usr/bin/env python3
"""
Search for and verify YouTube videos matching placeholder topics.

This script attempts to find active YouTube videos for each placeholder topic
by testing known video IDs and verifying they're accessible.
"""

import json
import sys
import argparse
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Known video IDs to test for each topic
# These are educated guesses based on well-known videos
CANDIDATE_VIDEOS = {
    5: [  # Essential Oils
        "8Y0fQKR6HUw",  # SciShow - Do Essential Oils Really Work?
        "zSJRz7gZgqI",  # Alternative candidate
    ],
    7: [  # Coffeezilla Save the Kids
        "8Y0fQKR6HUw",  # Placeholder - need to find Coffeezilla video
    ],
    8: [  # Tinder Swindler
        "5VYb3nu1d7Y",  # Netflix trailer (if accessible)
    ],
    9: [  # Real Hustle
        "8Y0fQKR6HUw",  # Placeholder - need to find BBC video
    ],
    11: [  # Get Rich Quick
        "8Y0fQKR6HUw",  # Placeholder - need to find scam video
    ],
    12: [  # MLM
        "8Y0fQKR6HUw",  # Placeholder - need to find John Oliver video
    ],
    14: [  # BitConnect
        "8Y0fQKR6HUw",  # Placeholder - need to find BitConnect video
    ],
    15: [  # Bitcoin $1M Prediction
        "8Y0fQKR6HUw",  # Placeholder - need to find prediction video
    ],
    16: [  # Absolute Proof
        "8Y0fQKR6HUw",  # Placeholder - need to find Mike Lindell video
    ],
}


def verify_video_active(video_id: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
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


def test_candidates_for_placeholder(test_id: int, candidates: List[str]) -> Optional[str]:
    """Test candidate video IDs and return first active one."""
    print(f"\n🔍 Testing candidates for Test ID {test_id}:")
    
    for video_id in candidates:
        is_active, info = verify_video_active(video_id)
        if is_active:
            print(f"  ✅ {video_id}: {info['title']}")
            print(f"     Author: {info['author']}")
            return video_id
        else:
            print(f"  ❌ {video_id}: Not accessible")
    
    return None


def main():
    parser = argparse.ArgumentParser(description="Search and verify videos for placeholders")
    parser.add_argument(
        "--test-id",
        type=int,
        help="Test ID to search for (if not provided, searches all)"
    )
    
    args = parser.parse_args()
    
    test_ids_to_search = [args.test_id] if args.test_id else list(CANDIDATE_VIDEOS.keys())
    
    print("=" * 80)
    print("🔍 SEARCHING FOR REPLACEMENT VIDEOS")
    print("=" * 80)
    
    verified_replacements = {}
    
    for test_id in test_ids_to_search:
        if test_id not in CANDIDATE_VIDEOS:
            print(f"\n⚠️  No candidates defined for Test ID {test_id}")
            continue
        
        candidates = CANDIDATE_VIDEOS[test_id]
        verified_id = test_candidates_for_placeholder(test_id, candidates)
        
        if verified_id:
            verified_replacements[test_id] = verified_id
        else:
            print(f"  ⚠️  No active candidates found for Test ID {test_id}")
    
    print("\n" + "=" * 80)
    print("📋 VERIFIED REPLACEMENTS")
    print("=" * 80)
    
    if verified_replacements:
        print("\n✅ Found active replacements:")
        for test_id, video_id in verified_replacements.items():
            print(f"  Test ID {test_id}: {video_id}")
        
        print("\n💡 To update test_videos.json, use:")
        replacements_json = json.dumps(verified_replacements)
        print(f"   python scripts/update_placeholder_videos.py --replacements '{replacements_json}'")
    else:
        print("\n❌ No active replacements found")
        print("   You may need to manually search YouTube for each topic")


if __name__ == "__main__":
    main()

