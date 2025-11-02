# 🔧 Streamlit Cloud Deployment Fix

**Issue:** `ModuleNotFoundError: yaml`  
**Cause:** Missing `pyyaml` dependency in UI-specific requirements  
**Status:** ✅ **FIXED**

---

## 🎯 Problem

When deploying to Streamlit Cloud, the app failed with:

```
ModuleNotFoundError: This app has encountered an error.
File "/mount/src/verityngn-oss/ui/streamlit_app.py", line 204
    from components.settings import render_settings_tab
File "/mount/src/verityngn-oss/ui/components/settings.py", line 9
    import yaml
```

---

## 🔍 Root Cause

Streamlit Cloud looks for `requirements.txt` in:

1. Same directory as the app (`ui/requirements.txt`) ← **Was missing!**
2. Repository root (`requirements.txt`) ← Existed but not used

Since the app is at `ui/streamlit_app.py`, Streamlit Cloud expected `ui/requirements.txt`.

---

## ✅ Solution

### 1. Created `ui/requirements.txt`

**IMPORTANT:** Must include ALL dependencies for running verifications, not just UI!

The Streamlit app needs:

- ✅ Streamlit itself
- ✅ **LangChain & LangGraph** (for workflow execution)
- ✅ **Google Cloud AI** (Vertex AI, Gemini)
- ✅ **Video processing** (yt-dlp, youtube_transcript_api)
- ✅ **Web scraping** (requests, beautifulsoup4)
- ✅ All workflow dependencies

See `ui/requirements.txt` for the complete list (~80 packages)

### 2. Created `.streamlit/config.toml`

Streamlit Cloud configuration:

```toml
[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
```

---

## 📤 To Deploy

### 1. Commit the new files

```bash
git add ui/requirements.txt
git add .streamlit/config.toml
git commit -m "fix: Add Streamlit Cloud deployment requirements"
git push origin main
```

### 2. Redeploy on Streamlit Cloud

- Go to your Streamlit Cloud dashboard
- Click "Reboot app" or wait for auto-deploy
- The app should now start successfully!

---

## 🎯 What This Fixes

### Before

```
❌ ModuleNotFoundError: yaml
❌ App fails to start
```

### After

```
✅ All dependencies installed
✅ App starts successfully
✅ UI components load correctly
```

---

## 📋 Streamlit Cloud Settings

Make sure your Streamlit Cloud app is configured with:

### Main file path

```
ui/streamlit_app.py
```

### Python version

```
3.11
```

### Secrets (in Streamlit Cloud dashboard)

Add your secrets from `.streamlit/secrets.toml.example`:

- `GOOGLE_SEARCH_API_KEY`
- `CSE_ID`
- `YOUTUBE_API_KEY`
- `PROJECT_ID`
- `LOCATION`
- `gcp_service_account` (entire JSON as TOML)

---

## 🔍 Verification

After redeploying, check:

1. ✅ App loads without errors
2. ✅ Sidebar displays correctly
3. ✅ "View Reports" tab works
4. ✅ Settings tab loads (where yaml is imported)

---

## 📚 Related Files

- `ui/requirements.txt` - UI-specific dependencies (NEW)
- `.streamlit/config.toml` - Streamlit configuration (NEW)
- `.streamlit/secrets.toml.example` - Secrets template (existing)
- `requirements.txt` - Full app dependencies (existing, for local dev)

---

**Status:** ✅ Ready to deploy to Streamlit Cloud
