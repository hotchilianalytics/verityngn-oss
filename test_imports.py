#!/usr/bin/env python3
"""
Quick test to verify imports are working correctly after fixes.
"""

import sys
from pathlib import Path

# Add repo root to path (same as streamlit_app.py does)
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root))

print("="*80)
print("Testing VerityNgn Imports")
print("="*80)

try:
    print("\n1. Testing extract_video_id import from utils...")
    from verityngn.utils.file_utils import extract_video_id
    print("   ✅ SUCCESS: extract_video_id imported")
    
    # Test the function
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    video_id = extract_video_id(test_url)
    print(f"   ✅ Function works: {test_url} -> {video_id}")
    
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n2. Testing video service imports...")
    from verityngn.services.video_service import get_video_info
    print("   ✅ SUCCESS: video service imported")
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n3. Testing workflow pipeline import...")
    from verityngn.workflows.pipeline import run_verification
    print("   ✅ SUCCESS: pipeline imported")
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n4. Testing config loader...")
    from verityngn.config.config_loader import get_config
    config = get_config()
    print("   ✅ SUCCESS: config loader imported and initialized")
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("Import test complete!")
print("="*80)

