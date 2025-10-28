# 🚀 Quick Start - Getting Credentials Right

## The Errors You're Seeing (and how to fix them)

### ✅ **Critical Fix:** Google Cloud Authentication

```bash
# Run this FIRST (most important)
gcloud auth application-default login

# Set your project
export GOOGLE_CLOUD_PROJECT=your-project-id

# Verify it worked
gcloud auth application-default print-access-token
```

**This fixes:**

- ✅ Gemini multimodal video analysis
- ✅ Claim extraction with LLM
- ✅ All core features

---

### ⚠️ **Optional:** Google Search (for verification)

The error `"Google Search API key or CSE ID not configured"` won't break the system, but limits verification capabilities.

**To fix (optional):**

```bash
export GOOGLE_API_KEY="AIza..."
export GOOGLE_CSE_ID="your-cse-id"
```

**Get these at:**

- API Key: <https://console.cloud.google.com/apis/credentials>
- CSE ID: <https://programmablesearchengine.google.com/>

**Without it:** System works but uses limited verification sources.

---

### ⚠️ **Optional:** YouTube Data API

The error `"YouTube API key not configured"` is handled automatically with yt-dlp fallback.

**To fix (optional):**

```bash
export YOUTUBE_API_KEY="AIza..."
```

**Without it:** System works, just uses yt-dlp (slower but functional).

---

### 🐛 **Fixed:** Missing Private Modules

The errors like `"No module named 'verityngn.services.video.metadata'"` are now handled gracefully.

**Status:** ✅ Fixed with fallback code.

---

### 🐛 **Fixed:** json_lib Error

The error `"cannot access local variable 'json_lib'"` is now patched.

**Status:** ✅ Fixed.

---

## Minimal Setup (Works Immediately)

**Just do this:**

```bash
# 1. Authenticate
gcloud auth application-default login

# 2. Set project (replace with your project ID)
export GOOGLE_CLOUD_PROJECT=your-project-id

# 3. Run Streamlit
cd /Users/ajjc/proj/verityngn-oss/ui
streamlit run streamlit_app.py
```

**That's it!** You can now:

- ✅ Analyze videos
- ✅ Extract claims with quality scoring
- ✅ Generate absence claims
- ✅ Analyze transcripts
- ✅ Generate beautiful reports

**What won't work without extra APIs:**

- ⚠️ Web search verification (will use fallback)
- ⚠️ YouTube counter-intelligence search (will skip)

---

## Full Setup (All Features)

**If you want everything:**

```bash
# 1. Google Cloud (required)
gcloud auth application-default login
export GOOGLE_CLOUD_PROJECT=your-project-id

# 2. Create .env file
cp .env.example .env

# 3. Edit .env and add (if you have them):
# GOOGLE_API_KEY=your-key
# GOOGLE_CSE_ID=your-cse-id
# YOUTUBE_API_KEY=your-key

# 4. Run
cd ui
streamlit run streamlit_app.py
```

---

## Testing the Fix

**Test that authentication works:**

```bash
# Should print a long token
gcloud auth application-default print-access-token

# Test the enhanced claims system
cd /Users/ajjc/proj/verityngn-oss
python test_enhanced_claims.py

# Test full workflow
cd ui
streamlit run streamlit_app.py
```

**Expected result:** UI loads, you can enter a YouTube URL, and analysis starts without credential errors.

---

## What Each Credential Enables

| Credential | What It Does | Required? |
|------------|--------------|-----------|
| `gcloud auth` | Vertex AI (Gemini models) | ✅ YES |
| `GOOGLE_API_KEY` | Web search verification | ⚠️ Optional |
| `GOOGLE_CSE_ID` | Custom search engine | ⚠️ Optional |
| `YOUTUBE_API_KEY` | YouTube metadata | ⚠️ Optional |

**Bottom Line:** You only NEED Google Cloud auth. Everything else is optional and has fallbacks.

---

## Still Having Issues?

**Check these:**

1. **Google Cloud project set?**

   ```bash
   echo $GOOGLE_CLOUD_PROJECT
   ```

2. **Authenticated?**

   ```bash
   gcloud auth application-default print-access-token
   ```

3. **Python environment active?**

   ```bash
   which python  # Should show your venv
   ```

4. **Dependencies installed?**

   ```bash
   pip install -r requirements.txt
   ```

---

## What Was Fixed

✅ **json_lib error** - Fixed import scoping issue  
✅ **Missing private modules** - Added ImportError handling  
✅ **Graceful fallbacks** - System continues without optional features  
✅ **Clear error messages** - You know what's optional vs required  

**All files updated:**

- `verityngn/workflows/analysis.py` - Fixed json import
- `verityngn/workflows/counter_intel.py` - Added fallbacks
- `CREDENTIALS_SETUP.md` - Full setup guide
- `QUICK_START_CREDENTIALS.md` - This file!

---

**Try it now:**

```bash
gcloud auth application-default login
cd /Users/ajjc/proj/verityngn-oss/ui
streamlit run streamlit_app.py
```

🎉 **You're ready to analyze videos!**


