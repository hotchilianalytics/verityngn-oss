#!/usr/bin/env python3
"""
Test script to verify credentials and setup.
"""

import os
import sys

print("=" * 70)
print("🔐 VERITYNGN CREDENTIALS TEST")
print("=" * 70)
print()

# Test 1: Python environment
print("1️⃣  Testing Python environment...")
print(f"   Python: {sys.version}")
print(f"   Path: {sys.executable}")
print("   ✅ Python OK")
print()

# Test 2: Load .env first (before checking auth)
print("2️⃣  Loading .env file...")
try:
    from dotenv import load_dotenv
    from pathlib import Path

    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"   ✅ Loaded .env from {env_file}")
    else:
        print(f"   ⚠️  .env file not found at {env_file}")
except ImportError:
    print("   ℹ️  python-dotenv not installed, using system env only")
except Exception as e:
    print(f"   ℹ️  Could not load .env: {e}")
print()

# Test 3: Check for service account JSON
print("3️⃣  Testing service account authentication...")
service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if service_account_path:
    from pathlib import Path

    if Path(service_account_path).exists():
        print(f"   ✅ Service account JSON found: {service_account_path}")
        try:
            from google.oauth2 import service_account

            creds = service_account.Credentials.from_service_account_file(
                service_account_path
            )
            print(f"   ✅ Valid service account: {creds.service_account_email}")
        except Exception as e:
            print(f"   ⚠️  Could not load service account: {e}")
    else:
        print(f"   ❌ Service account file not found: {service_account_path}")
else:
    print("   ℹ️  GOOGLE_APPLICATION_CREDENTIALS not set")
print()

# Test 4: Google Cloud gcloud authentication (fallback)
print("4️⃣  Testing gcloud authentication (fallback)...")
try:
    import subprocess

    result = subprocess.run(
        ["gcloud", "auth", "application-default", "print-access-token"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode == 0 and result.stdout.strip():
        print("   ✅ gcloud authenticated!")
        print(f"   Token: {result.stdout[:20]}...")
    else:
        print("   ℹ️  Not authenticated via gcloud")
        print("   (This is OK if using service account JSON)")
except FileNotFoundError:
    print("   ℹ️  gcloud not found")
    print("   (This is OK if using service account JSON)")
except Exception as e:
    print(f"   ℹ️  Could not verify: {e}")
print()

# Test 5: Google Cloud project
print("5️⃣  Testing Google Cloud project...")
project = os.getenv("GOOGLE_CLOUD_PROJECT")
if project:
    print(f"   ✅ Project set: {project}")
else:
    print("   ⚠️  GOOGLE_CLOUD_PROJECT not set")
    print("   Set with: export GOOGLE_CLOUD_PROJECT=your-project-id")
print()

# Test 6: Optional APIs
print("6️⃣  Testing optional APIs...")

# Check for API keys (support multiple variable names)
google_api_key = (
    os.getenv("GOOGLE_API_KEY")
    or os.getenv("GOOGLE_SEARCH_API_KEY")
    or os.getenv("GOOGLE_AI_STUDIO_KEY")
)
google_cse_id = os.getenv("GOOGLE_CSE_ID") or os.getenv("CSE_ID")
youtube_api_key = os.getenv("YOUTUBE_API_KEY")

if google_api_key:
    print(f"   ✅ Google Search API Key: {google_api_key[:10]}...")
else:
    print("   ⚠️  GOOGLE_API_KEY not set (optional - verification limited)")

if google_cse_id:
    print(f"   ✅ Google CSE ID: {google_cse_id[:10]}...")
else:
    print("   ⚠️  GOOGLE_CSE_ID not set (optional - verification limited)")

if youtube_api_key:
    print(f"   ✅ YouTube API Key: {youtube_api_key[:10]}...")
else:
    print("   ⚠️  YOUTUBE_API_KEY not set (optional - uses yt-dlp fallback)")
print()

# Test 7: Import key modules
print("7️⃣  Testing module imports...")
try:
    from verityngn.workflows.analysis import extract_video_metadata_reliable

    print("   ✅ verityngn.workflows.analysis imported")
except Exception as e:
    print(f"   ❌ Failed to import analysis: {e}")

try:
    from verityngn.workflows.counter_intel import run_counter_intel_once

    print("   ✅ verityngn.workflows.counter_intel imported")
except Exception as e:
    print(f"   ❌ Failed to import counter_intel: {e}")

try:
    from verityngn.workflows.enhanced_integration import enhance_extracted_claims

    print("   ✅ verityngn.workflows.enhanced_integration imported")
except Exception as e:
    print(f"   ❌ Failed to import enhanced_integration: {e}")

try:
    from verityngn.workflows.youtube_transcript_analysis import (
        enhance_youtube_counter_intelligence,
    )

    print("   ✅ verityngn.workflows.youtube_transcript_analysis imported")
except Exception as e:
    print(f"   ❌ Failed to import youtube_transcript_analysis: {e}")

print()

# Test 8: Verify fixes
print("8️⃣  Verifying bug fixes...")
try:
    # Test that json is imported correctly
    from verityngn.workflows import analysis
    import inspect

    source = inspect.getsource(analysis.extract_video_metadata_reliable)
    if "import json" in source:
        print("   ✅ json_lib bug fixed")
    else:
        print("   ⚠️  json import not found (check manually)")
except Exception as e:
    print(f"   ⚠️  Could not verify: {e}")

print()
print("=" * 70)
print("📋 SUMMARY")
print("=" * 70)
print()
print("✅ = Ready to use")
print("⚠️  = Optional (system works without it)")
print("❌ = Required (system won't work)")
print()

# Final verdict
print("🎯 VERDICT:")

# Check if authenticated via service account or gcloud
service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
has_service_account = False
has_gcloud_auth = False

if service_account_path:
    from pathlib import Path

    if Path(service_account_path).exists():
        try:
            from google.oauth2 import service_account

            creds = service_account.Credentials.from_service_account_file(
                service_account_path
            )
            has_service_account = True
        except:
            pass

try:
    result = subprocess.run(
        ["gcloud", "auth", "application-default", "print-access-token"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode == 0 and result.stdout.strip():
        has_gcloud_auth = True
except:
    pass

if has_service_account or has_gcloud_auth:
    print("✅ You're ready to run VerityNgn!")
    print()
    if has_service_account:
        print(f"   Using service account: {service_account_path}")
    if has_gcloud_auth:
        print("   Using gcloud authentication")
    print()
    print("Next steps:")
    print("  cd ui")
    print("  streamlit run streamlit_app.py")
else:
    print("❌ No authentication found!")
    print()
    print("Option 1: Service account JSON (recommended)")
    print("  1. Download service account JSON")
    print("  2. Add to .env:")
    print("     GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json")
    print()
    print("Option 2: gcloud authentication")
    print("  gcloud auth application-default login")
    print()
    print("See ENV_AUTH_SETUP.md for details")
print()
print("=" * 70)
