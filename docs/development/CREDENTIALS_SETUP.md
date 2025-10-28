# 🔐 Credentials Setup Guide for VerityNgn

## Quick Setup (Required for Full Functionality)

### 1. Google Cloud Authentication

The system needs Google Cloud credentials for Vertex AI (Gemini models).

```bash
# Authenticate with Google Cloud
gcloud auth application-default login

# Verify authentication
gcloud auth application-default print-access-token
```

**What this enables:**

- Gemini 2.0 Flash for video analysis
- Gemini for claim extraction
- Multimodal video processing

### 2. Optional: Google Search API (for verification)

If you want full web search capabilities:

```bash
# Set these in your environment or .env file
export GOOGLE_API_KEY="your-google-search-api-key"
export GOOGLE_CSE_ID="your-custom-search-engine-id"
```

**How to get these:**

1. Go to <https://console.cloud.google.com/apis/credentials>
2. Create API key
3. Enable "Custom Search API"
4. Create Custom Search Engine at <https://programmablesearchengine.google.com/>

**What this enables:**

- Web search for claim verification
- Better source diversity

**Without it:** System falls back to mock/limited search results.

### 3. Optional: YouTube Data API

For enhanced YouTube metadata:

```bash
export YOUTUBE_API_KEY="your-youtube-api-key"
```

**How to get this:**

1. Go to <https://console.cloud.google.com/apis/credentials>
2. Create API key
3. Enable "YouTube Data API v3"

**What this enables:**

- Better video metadata extraction
- YouTube counter-intelligence search

**Without it:** System uses yt-dlp fallback (works but slower).

---

## Environment Variables

Create a `.env` file in the project root:

```bash
# Required for Vertex AI
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Optional: Google Search
GOOGLE_API_KEY=your-google-search-api-key
GOOGLE_CSE_ID=your-custom-search-engine-id

# Optional: YouTube
YOUTUBE_API_KEY=your-youtube-api-key
YOUTUBE_API_ENABLED=true

# Project settings
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# Model settings
AGENT_MODEL_NAME=gemini-2.0-flash-exp
AGENT_MODEL_TEMPERATURE=0.1

# Enhanced features (enabled by default)
ENHANCED_CLAIMS_ENABLED=true
YOUTUBE_TRANSCRIPT_ANALYSIS_ENABLED=true
ABSENCE_CLAIMS_ENABLED=true
```

---

## Minimal Working Configuration

**For basic functionality with just Google Cloud:**

```bash
# 1. Authenticate
gcloud auth application-default login

# 2. Set project
export GOOGLE_CLOUD_PROJECT=your-project-id

# 3. Run
cd /Users/ajjc/proj/verityngn-oss/ui
streamlit run streamlit_app.py
```

**This will work with:**

- ✅ Video analysis (Gemini multimodal)
- ✅ Claim extraction
- ✅ Enhanced claims scoring
- ⚠️ Limited verification (no web search)
- ⚠️ No YouTube counter-intelligence

---

## Troubleshooting

### Error: "Google Search API key or CSE ID not configured"

**Impact:** Web search for verification won't work, but analysis will continue.

**Fix (if you want search):**

```bash
export GOOGLE_API_KEY="your-key"
export GOOGLE_CSE_ID="your-cse-id"
```

**Or skip:** The system will work without it, just with limited verification sources.

### Error: "YouTube API key not configured"

**Impact:** Falls back to yt-dlp (slower but works).

**Fix (optional):**

```bash
export YOUTUBE_API_KEY="your-key"
```

### Error: "cannot access local variable 'json_lib'"

**Fixed:** This is a code bug I'll patch in the next update.

### Error: "No module named 'verityngn.services...'"

**Impact:** Some optional features unavailable.

**Status:** These are private repo modules. OSS version uses fallbacks.

---

## What Works Without Extra Credentials?

With just `gcloud auth application-default login`:

| Feature | Status | Notes |
|---------|--------|-------|
| Video Download | ✅ Works | Uses yt-dlp |
| Multimodal Analysis | ✅ Works | Gemini Flash via Vertex AI |
| Claim Extraction | ✅ Works | Gemini Flash |
| Enhanced Claims | ✅ Works | Local scoring (no API calls) |
| Absence Claims | ✅ Works | Local generation |
| Transcript Analysis | ✅ Works | Uses youtube-transcript-api (free) |
| Web Search Verification | ⚠️ Limited | No Google Search API = mock results |
| YouTube Counter-Intel | ⚠️ Limited | No YouTube API = yt-dlp fallback |
| Report Generation | ✅ Works | All formats |

**Bottom line:** You can run full analysis with just Google Cloud auth. Search features require additional APIs but are optional.

---

## Quick Test

After setting up credentials:

```bash
# Test authentication
gcloud auth application-default print-access-token

# Test the system
cd /Users/ajjc/proj/verityngn-oss
python test_enhanced_claims.py

# Test full workflow
cd ui
streamlit run streamlit_app.py
```

If you see the Streamlit UI and can submit a video, you're good to go!


