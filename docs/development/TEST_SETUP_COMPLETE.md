# ✅ Test Setup Complete

## Summary

Successfully created a test script to run the tLJC8hkK-ao (LIPOZEM) video verification workflow outside of Streamlit, using credentials from the `.env` file.

---

## Files Created

### 1. `test_tl_video.py` - Main Test Script
Standalone Python script that runs the complete verification workflow for the LIPOZEM video.

**Features:**
- Runs all 7 workflow stages
- Provides detailed console logging
- Generates JSON, Markdown, and HTML reports
- Handles errors gracefully with full tracebacks

### 2. `run_test_tl.sh` - Quick Test Runner (Recommended)
Bash script wrapper that:
- Checks for `.env` file
- Loads `GOOGLE_APPLICATION_CREDENTIALS` from `.env`
- Verifies service account file exists
- Runs the test
- Shows output paths on success

### 3. `TEST_TL_VIDEO_USAGE.md` - Comprehensive Guide
Detailed documentation covering:
- Prerequisites and setup
- Expected runtime and output
- Troubleshooting section
- Customization options

### 4. `QUICK_TEST_TL.md` - Quick Reference
One-page quick start guide with minimal instructions.

### 5. `TEST_TL_VIDEO_SUCCESS.md` - Test Results
Documents the successful test run including:
- Verification verdict
- Key findings
- Generated files
- Observations and notes

---

## Quick Start

### Option 1: Using the Shell Script (Easiest)

```bash
./run_test_tl.sh
```

This will:
1. Load credentials from `.env`
2. Verify service account exists
3. Run the test
4. Show output locations

### Option 2: Using Python Directly

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/Users/ajjc/proj/verityngn-oss/verityngn/config/verityindex-0-0-1-6a21e94ca0a3.json"
python test_tl_video.py
```

---

## What the Test Does

Runs the complete VerityNgn verification pipeline:

1. 📥 **Download** - Video, audio, metadata, transcript
2. 🎬 **Analyze** - Multimodal LLM analysis
3. 🔍 **Counter-Intel** - YouTube search for reviews/debunks
4. 📋 **Extract** - Identify verifiable claims
5. ✅ **Verify** - Web search + evidence gathering
6. 📊 **Report** - Truthfulness scoring
7. 💾 **Save** - JSON + Markdown + HTML reports

---

## Test Results (From Actual Run)

### Verdict
**"Likely to be False"** - 100% of claims appear false/misleading

### Key Findings
1. **Unsubstantiated Health Claims** - No scientific evidence
2. **Lack of Specifics** - Vague, unverifiable claims
3. **Implausible Promises** - Exaggerated weight loss claims

### Output Location
```
verityngn/outputs/tLJC8hkK-ao/2025-10-27_22-39-29_complete/
├── tLJC8hkK-ao_report.html    (23 KB)
├── tLJC8hkK-ao_report.json    (12 KB)
├── tLJC8hkK-ao_report.md      (10 KB)
└── tLJC8hkK-ao_claim_*_sources.*
```

---

## Configuration via .env

Your `.env` file should contain:

```bash
# Required for Vertex AI (multimodal analysis)
GOOGLE_APPLICATION_CREDENTIALS=/Users/ajjc/proj/verityngn-oss/verityngn/config/verityindex-0-0-1-6a21e94ca0a3.json
GOOGLE_CLOUD_PROJECT=verityindex-0-0-1
PROJECT_ID=verityindex-0-0-1
LOCATION=us-central1

# Optional for enhanced features
YOUTUBE_API_KEY=AIza...           # YouTube metadata & counter-intelligence
GOOGLE_SEARCH_API_KEY=AIza...     # Web search for claim verification
GOOGLE_CSE_ID=your-search-id      # Custom Search Engine ID
```

**Note:** The test works without YouTube/Search API keys but with limited functionality:
- ✅ Video download via yt-dlp fallback
- ✅ Multimodal analysis via Vertex AI
- ⚠️ Limited counter-intelligence search
- ⚠️ Limited web evidence gathering

---

## Fixes Applied

### 1. Made `psutil` Optional
**File:** `verityngn/workflows/analysis.py`

```python
try:
    import psutil  # Add for memory monitoring (optional)
except ImportError:
    psutil = None  # Make psutil optional
```

This allows the system to run without `psutil` installed, gracefully skipping memory monitoring.

### 2. Installed Missing Dependencies

```bash
pip install isodate psutil
```

These were in `requirements.txt` but not installed in the current environment.

### 3. Explicit Credential Loading

The test script and shell wrapper explicitly set `GOOGLE_APPLICATION_CREDENTIALS` from `.env` to avoid conflicts with OAuth2 credentials.

---

## Testing Other Videos

### Edit `test_tl_video.py`

Change these lines:

```python
video_id = "your_video_id"
video_url = f"https://www.youtube.com/watch?v=&#123;video_id&#125;"
```

### Or Create a Generic Test Script

```python
#!/usr/bin/env python
import sys
from verityngn.workflows.pipeline import run_verification

if len(sys.argv) &lt; 2:
    print("Usage: python test_video.py [youtube_url]")
    sys.exit(1)

video_url = sys.argv[1]
final_state, output_dir = run_verification(video_url)
print(f"✅ Report saved to: &#123;output_dir&#125;")
```

Usage:
```bash
python test_video.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

---

## Troubleshooting

### Test Fails with "No module named X"

**Solution:** Install missing dependencies from requirements.txt

```bash
pip install -r requirements.txt
```

### Test Fails with OAuth2 RefreshError

**Solution:** Explicitly set credentials (already done in scripts)

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

### YouTube API Errors

**Solution:** System falls back to yt-dlp automatically (no action needed)

### Limited Verification Results

**Solution:** Add YouTube and Search API keys to `.env` for full functionality

---

## Performance Notes

- **Runtime:** ~9-15 minutes for a 33-minute video
- **Rate Limits:** May hit Vertex AI rate limits on repeated runs
- **Storage:** Reports are ~50 KB per video
- **Memory:** Peak usage ~2-4 GB (without psutil monitoring)

---

## Next Steps

1. ✅ **Test script working** - Verified with successful run
2. ✅ **Credentials via .env** - Working correctly
3. ✅ **Dependencies fixed** - Optional imports for missing packages
4. 🎯 **Add API keys to .env** - For enhanced verification (optional)
5. 🎯 **Test with other videos** - Verify system works with different content types

---

## Summary

**Status:** ✅ **COMPLETE**

The VerityNgn verification system can now be tested via command line:
- Uses credentials from `.env` file
- Runs outside Streamlit UI
- Generates comprehensive reports
- Handles API fallbacks gracefully
- Works with or without optional API keys

**Command to run:**
```bash
./run_test_tl.sh
```

That's it! 🎉


