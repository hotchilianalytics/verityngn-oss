# YouTube Services & Search API Setup

Complete guide to enabling optional YouTube and search features.

---

## 🎯 What Each API Enables

### Without Optional APIs (Current State)

- ✅ Video analysis with Gemini
- ✅ Claim extraction from video
- ✅ Basic metadata via yt-dlp
- ⚠️ **Limited** claim verification (no web search)
- ⚠️ **No** YouTube counter-intelligence search

### With Optional APIs Enabled

- ✅ **Web search** for claim verification
- ✅ **YouTube Data API** for better metadata
- ✅ **YouTube counter-intelligence** - finds debunking videos
- ✅ **Transcript analysis** of counter-evidence
- ✅ **Higher quality** verification results

---

## 📋 Prerequisites

1. **Google Cloud Project** (you already have this)
2. **Billing enabled** (required for YouTube Data API)
   - Go to: <https://console.cloud.google.com/billing>
   - YouTube API has free quota: 10,000 units/day
   - Custom Search: 100 queries/day free

---

## 🔧 Step-by-Step Setup

### Step 1: Enable APIs in Google Cloud

```bash
# Set your project (if not already set)
gcloud config set project YOUR_PROJECT_ID

# Enable Custom Search API
gcloud services enable customsearch.googleapis.com

# Enable YouTube Data API v3
gcloud services enable youtube.googleapis.com
```

Or enable via Console:

- Custom Search: <https://console.cloud.google.com/apis/library/customsearch.googleapis.com>
- YouTube Data API: <https://console.cloud.google.com/apis/library/youtube.googleapis.com>

### Step 2: Create API Keys

**Option A: Using gcloud**

```bash
# Create a new API key
gcloud alpha services api-keys create \
  --display-name="VerityNgn APIs" \
  --api-target=service=customsearch.googleapis.com \
  --api-target=service=youtube.googleapis.com

# Get the key value
gcloud alpha services api-keys list
```

**Option B: Using Console (Recommended)**

1. Go to: <https://console.cloud.google.com/apis/credentials>
2. Click **"Create Credentials"** → **"API Key"**
3. Copy the key (e.g., `AIzaSyC-1234567890abcdefghijk`)
4. (Optional) Click "Edit API key" to restrict:
   - **API restrictions**: Select "Restrict key" → Choose:
     - Custom Search API
     - YouTube Data API v3
   - **Application restrictions**: None (or IP/Referrer if desired)

### Step 3: Create Custom Search Engine

1. Go to: <https://programmablesearchengine.google.com/>
2. Click **"Add"** or **"Create"**
3. **Settings:**
   - Name: `VerityNgn Search`
   - What to search: **"Search the entire web"**
   - (Enable) "Search the entire web"
4. Click **"Create"**
5. Copy the **Search engine ID** (e.g., `a1b2c3d4e5f678901`)

---

## 🔑 Set Environment Variables

### Quick Setup (Interactive)

```bash
cd /Users/ajjc/proj/verityngn-oss
source set_api_keys.sh
```

This will prompt you for each key.

### Manual Setup

**For current session:**

```bash
# Google Search (for claim verification)
export GOOGLE_API_KEY="AIzaSyC-YOUR-KEY-HERE"
export GOOGLE_CSE_ID="your-search-engine-id"

# YouTube Data API (can be same key or different)
export YOUTUBE_API_KEY="AIzaSyC-YOUR-KEY-HERE"
```

**To persist across sessions (add to `~/.zshrc`):**

```bash
echo 'export GOOGLE_API_KEY="AIzaSyC-YOUR-KEY-HERE"' >> ~/.zshrc
echo 'export GOOGLE_CSE_ID="your-search-engine-id"' >> ~/.zshrc
echo 'export YOUTUBE_API_KEY="AIzaSyC-YOUR-KEY-HERE"' >> ~/.zshrc

# Reload shell
source ~/.zshrc
```

---

## ✅ Verify Setup

**Run the test script:**

```bash
cd /Users/ajjc/proj/verityngn-oss
python test_credentials.py
```

**Expected output with all APIs:**

```
3️⃣  Testing optional APIs...
   ✅ GOOGLE_API_KEY set
   ✅ GOOGLE_CSE_ID set
   ✅ YOUTUBE_API_KEY set
```

**Test YouTube API directly:**

```bash
# Test if YouTube API works
curl "https://www.googleapis.com/youtube/v3/videos?part=snippet&id=dQw4w9WgXcQ&key=$YOUTUBE_API_KEY"
```

Should return JSON with video details (not an error).

---

## 🚀 What Changes in the System

### With YouTube Data API

- `extract_metadata_youtube_api()` in `analysis.py` will **succeed** instead of fallback
- Faster, more reliable metadata extraction
- No yt-dlp bot detection issues

### With Google Search API

- `google_search()` in `web_search.py` will **return results** instead of empty
- Claims get verified with real web sources
- Higher quality verification verdicts

### With Both APIs

- **YouTube counter-intelligence** feature activates:
  - Searches YouTube for debunking videos
  - Downloads transcripts of counter-evidence
  - Analyzes claims against counter-arguments
- Enhanced reports with external validation

---

## 📊 Cost & Quotas

### Free Tier Limits

- **Custom Search**: 100 queries/day free
  - $5 per 1,000 queries after
- **YouTube Data API**: 10,000 units/day free
  - 1 video metadata = ~3 units
  - 1 search = ~100 units
  - Enough for ~30 videos/day

### Typical Usage per Video

- **Custom Search**: ~20-40 queries (for claim verification)
- **YouTube API**: ~5-10 calls (metadata + counter-intel search)

**Estimated cost per video**: $0.00 (within free tier for ~3-5 videos/day)

---

## 🧪 Test the Full System

```bash
# Activate your environment
source venv/bin/activate  # or your env name

# Run Streamlit with full APIs
cd ui
streamlit run streamlit_app.py
```

Analyze the `tLJC8hkK-ao` video and check the logs for:

```
✅ YouTube API extracted: [video title]
✅ Google Search returned [N] results for claim [X]
✅ YouTube counter-intel found [N] debunking videos
✅ Transcript analysis enhanced counter-intelligence
```

---

## 🔍 Troubleshooting

### "API key not valid"

- Check the key is copied correctly (no extra spaces)
- Verify API is enabled in Google Cloud Console
- Check API key restrictions don't block the service

### "Quota exceeded"

- Check your quota: <https://console.cloud.google.com/apis/dashboard>
- YouTube API: 10,000 units/day is usually enough
- Custom Search: 100 queries/day might need increase

### "Billing not enabled"

- YouTube Data API requires billing enabled
- Go to: <https://console.cloud.google.com/billing>
- You won't be charged within free tier limits

### Environment variables not persisting

- Make sure you added to `~/.zshrc` (not `~/.bashrc` on zsh)
- Run `source ~/.zshrc` after editing
- Check with: `echo $GOOGLE_API_KEY`

---

## 📚 Related Documentation

- **Main Setup**: `CONFIG_SETUP.md`
- **Quick Start**: `QUICK_START_CREDENTIALS.md`
- **Credential Basics**: `CREDENTIALS_SETUP.md`
- **Testing**: Run `python test_credentials.py`

---

## 🎯 Next Steps

Once APIs are configured:

1. **Run full integration test:**

   ```bash
   cd /Users/ajjc/proj/verityngn-oss
   python -c "from verityngn.workflows.pipeline import run_verification; import asyncio; asyncio.run(run_verification('https://www.youtube.com/watch?v=tLJC8hkK-ao', max_claims=20))"
   ```

2. **Check the enhanced features:**
   - Counter-intelligence section in report
   - Transcript analysis of debunking videos
   - Higher quality claim verdicts
   - More diverse verification sources

3. **Compare results:**
   - Previous run: Limited verification
   - New run: Full web search + YouTube counter-intel

---

## ✨ Summary

**Set three variables to unlock full features:**

```bash
export GOOGLE_API_KEY="your-key"      # Web search for verification
export GOOGLE_CSE_ID="your-cse-id"    # Custom search engine
export YOUTUBE_API_KEY="your-key"     # YouTube metadata + counter-intel
```

**Benefits:**

- 🔍 Real claim verification with web sources
- 🎥 YouTube counter-intelligence analysis
- 📊 Higher quality truth scores
- 🚀 Better metadata extraction


