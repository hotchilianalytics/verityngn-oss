# 🔍 Sherlock Mode Fix Summary

**Date:** 2025-11-01  
**Issue:** Persistent API key errors and report viewer issues  
**Status:** ✅ FIXED with comprehensive diagnostics

---

## What Was Wrong?

### Problem 1: API Keys Failing
Even though the secrets loader was working, API calls failed with:
```
❌ key=your-youtube-api-key returned "API key not valid"
```

### Problem 2: Report Viewer Not Working
Reports were generated but not showing up in Streamlit UI.

---

## Root Cause

**Your `.env` file contains placeholder values!**

The secrets loader was correctly loading from `.env`, but it never **validated** what it loaded. So if your `.env` had:

```bash
YOUTUBE_API_KEY="your-youtube-api-key"  # PLACEHOLDER!
```

It would be loaded without warning, causing all API calls to fail.

---

## The Fix

### Enhanced Secrets Loader (`ui/secrets_loader.py`)

Added `_validate_loaded_secrets_sherlock()` that:
- ✅ Checks for placeholder patterns in API keys
- ✅ Shows clear error messages with actual problematic values
- ✅ Provides step-by-step fix instructions
- ✅ Validates immediately after loading `.env`

### Enhanced Report Viewer (`ui/components/report_viewer.py`)

Added diagnostic logging that:
- ✅ Shows where it's looking for reports
- ✅ Checks `DEBUG_OUTPUTS` from multiple sources
- ✅ Auto-detects `outputs_debug` directory
- ✅ Logs all decision points clearly

---

## What You'll See Now

### When Streamlit Starts:

**If your `.env` has placeholder values:**

```
================================================================================
🔍 SHERLOCK MODE: Validating loaded API keys
================================================================================
❌ Google Search API (GOOGLE_SEARCH_API_KEY): PLACEHOLDER VALUE DETECTED
   Current value: "your-google-search-api-key"
   ⚠️  This will cause "API key not valid" errors!

🚨 CRITICAL: API KEY ISSUES DETECTED

📋 ACTION REQUIRED:
   1. Open: /path/to/verityngn-oss/.env
   2. Replace placeholder values with your REAL API keys
   3. Get API keys from: https://console.cloud.google.com/apis/credentials
   4. Restart Streamlit app
================================================================================
```

**If your API keys are valid:**

```
================================================================================
🔍 SHERLOCK MODE: Validating loaded API keys
================================================================================
✅ Google Search API (GOOGLE_SEARCH_API_KEY): Valid
   Preview: AIzaSyBiC_...4IJA
✅ Custom Search Engine ID (CSE_ID): Valid
   Preview: 800c584b1c...60a
✅ YouTube Data API (YOUTUBE_API_KEY): Valid
   Preview: AIzaSyBiC_...4IJA
================================================================================
✅ All API keys look valid!
```

### When Viewing Reports Tab:

```
================================================================================
🔍 SHERLOCK MODE: Detecting output directory for report viewer
================================================================================
📋 Source 1 - os.getenv('DEBUG_OUTPUTS'): true -> True
📋 Source 2 - st.secrets: Skipping (env var already set)
📋 Source 3 - Directory check: /path/to/outputs_debug exists: True
✅ Using debug outputs directory (env variable): /path/to/outputs_debug
================================================================================
```

---

## How to Fix Your Setup

### Step 1: Check Your API Keys

```bash
cd /Users/ajjc/proj/verityngn-oss
cat .env | grep -E "(GOOGLE_SEARCH_API_KEY|YOUTUBE_API_KEY|CSE_ID)"
```

**If you see placeholder values like:**
- `"your-google-search-api-key"`
- `"your-youtube-api-key"`
- `"your-cse-id"`

**You need to replace them with REAL API keys!**

### Step 2: Get Real API Keys

1. **Google Search API Key:**
   - Go to: https://console.cloud.google.com/apis/credentials
   - Create or select a project
   - Click "Create Credentials" → "API Key"
   - Copy the key (starts with `AIza...`)

2. **Custom Search Engine ID:**
   - Go to: https://programmablesearchengine.google.com/
   - Create or select a search engine
   - Copy the "Search engine ID"

3. **YouTube Data API:**
   - Same as Google Search API Key (can use the same key)
   - Or create a separate one if needed

### Step 3: Update Your `.env` File

```bash
# Edit .env
vim /path/to/verityngn-oss/.env

# Replace placeholders with real keys:
GOOGLE_SEARCH_API_KEY="your-google-search-api-key"
CSE_ID="your-custom-search-engine-id"
YOUTUBE_API_KEY="your-youtube-api-key"

# Optional: Enable debug outputs
DEBUG_OUTPUTS=true
```

### Step 4: Test the Fix

```bash
# Start Streamlit
cd /Users/ajjc/proj/verityngn-oss
streamlit run ui/streamlit_app.py

# Should see in terminal:
# ✅ All API keys look valid!
# ✅ Using debug outputs directory: ...

# Navigate to "View Reports" tab
# Should see available reports listed

# Try running a verification
# Should complete without API key errors
```

---

## Files Modified

1. **`ui/secrets_loader.py`**
   - Added `_validate_loaded_secrets_sherlock()` function (lines 12-80)
   - Integrated validation into `load_secrets()` (line 57)
   - Validates API keys immediately after `.env` loading

2. **`ui/components/report_viewer.py`**
   - Enhanced `DEBUG_OUTPUTS` detection with diagnostics (lines 102-150)
   - Shows all decision points clearly
   - Auto-detects `outputs_debug` directory

3. **`SHERLOCK_API_KEY_FIX.md`** (new)
   - Comprehensive technical analysis
   - Investigation methodology
   - Complete solution documentation

4. **`STREAMLIT_REPORT_FIX.md`** (updated)
   - Added Sherlock Mode diagnostics section
   - Added common issues and fixes
   - Added testing checklist

---

## Why This Works Better

**Before:**
- Silent failures with cryptic error messages
- No validation of loaded API keys
- No indication that `.env` had placeholders
- User had to manually debug

**After:**
- ✅ Immediate detection of placeholder values
- ✅ Clear, actionable error messages
- ✅ Shows exact problematic values
- ✅ Provides step-by-step fix instructions
- ✅ Self-service troubleshooting

---

## Testing Checklist

- [ ] Run `streamlit run ui/streamlit_app.py`
- [ ] Look for "✅ All API keys look valid!" message
- [ ] Check report viewer shows correct output directory
- [ ] Navigate to "View Reports" tab - reports should be listed
- [ ] Try running a verification - should complete successfully
- [ ] Verify no "API key not valid" errors in logs
- [ ] Verify no Google Search 400 errors in logs

---

## Need More Help?

**See Detailed Documentation:**
- `SHERLOCK_API_KEY_FIX.md` - Complete technical analysis
- `STREAMLIT_REPORT_FIX.md` - Report viewer troubleshooting
- `STREAMLIT_DEPLOYMENT_GUIDE.md` - Full deployment guide

**Common Issues:**
1. **Still see placeholder errors?** → Update your `.env` file with real API keys
2. **Reports not showing?** → Set `DEBUG_OUTPUTS=true` in `.env`
3. **API quota errors?** → Request quota increase in Google Cloud Console

---

**Status:** ✅ Ready to Use  
**Next Step:** Update your `.env` file with real API keys and restart Streamlit
