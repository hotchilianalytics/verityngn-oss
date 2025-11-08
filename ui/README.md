# 🚀 VerityNgn UI - Streamlit Community Cloud Deployment

## Overview

This is the VerityNgn UI - a web interface for verifying YouTube video truthfulness using AI. The UI connects to a VerityNgn API server (running locally via ngrok or deployed to Cloud Run).

## Features

- 📹 Submit YouTube videos for verification
- 📊 View truthfulness reports with claim analysis
- 🔍 Browse verification history
- 🎨 Modern, responsive interface

## Live Demo

Deploy your own instance to Streamlit Community Cloud in minutes!

---

## 🎯 Quick Deploy to Streamlit Community Cloud

### Prerequisites

1. **GitHub Account** (to host the code)
2. **Streamlit Community Account** (free at <https://share.streamlit.io>)
3. **VerityNgn API** running either:
   - Locally with ngrok tunnel
   - Deployed to Google Cloud Run

### Step 1: Fork/Push to GitHub

This repo should already be on GitHub. If not:

```bash
cd /Users/ajjc/proj/verityngn-oss
git add .
git commit -m "Prepare for Streamlit Community deployment"
git push origin main
```

### Step 2: Deploy to Streamlit Community

1. **Go to:** <https://share.streamlit.io>
2. **Click:** "New app"
3. **Repository:** Select your `verityngn-oss` repo
4. **Branch:** `main`
5. **Main file path:** `ui/streamlit_app.py`
6. **App URL:** Choose your subdomain (e.g., `verityngn`)

### Step 3: Configure Secrets

1. In Streamlit Cloud dashboard, click **"⚙️ Settings"**
2. Go to **"Secrets"** tab
3. Add your configuration:

```toml
# Your ngrok URL or Cloud Run URL
VERITYNGN_API_URL = "https://your-url-here.ngrok-free.app"

# Alternative format (also works)
[api]
url = "https://your-url-here.ngrok-free.app"
```

4. **Click "Save"**

### Step 4: Deploy

Click **"Deploy"** and wait ~2-3 minutes for the app to start.

Your app will be live at: `https://verityngn.streamlit.app` (or your chosen URL)

---

## 🔧 Configuration

### API URL

The UI needs to know where your VerityNgn API is running. Set this via Streamlit secrets:

**Option 1: Using ngrok (development)**

```toml
VERITYNGN_API_URL = "https://oriented-flea-large.ngrok-free.app"
```

**Option 2: Using Cloud Run (production)**

```toml
VERITYNGN_API_URL = "https://verityngn-api-xxxxxx.run.app"
```

### Required Secrets

- ✅ `VERITYNGN_API_URL` - The API base URL (required)
- ❌ `GOOGLE_APPLICATION_CREDENTIALS` - NOT needed (API handles this)
- ❌ `GOOGLE_CLOUD_PROJECT` - NOT needed (API handles this)

---

## 📋 File Structure

```
ui/
├── streamlit_app.py          # Main app entry point
├── requirements.txt           # Minimal dependencies for UI
├── packages.txt              # System dependencies
├── .streamlit/
│   ├── config.toml           # Streamlit configuration
│   └── secrets.toml.example  # Secrets template
├── components/               # UI components
│   ├── video_input.py       # Video URL input
│   ├── processing_api.py    # API client
│   └── report_viewer.py     # Report display
└── README.md                 # This file
```

---

## 🧪 Test Locally First

Before deploying, test the UI locally:

### Option 1: Using Docker (recommended)

```bash
docker compose up ui
open http://localhost:8501
```

### Option 2: Using Python directly

```bash
cd ui
pip install -r requirements.txt
streamlit run streamlit_app.py
```

---

## 🔍 Troubleshooting

### "Connection refused" or API errors

**Problem:** UI can't reach the API

**Solutions:**

1. Check your ngrok tunnel is running
2. Verify API URL in secrets is correct
3. Test API directly: `curl https://your-url/health`

### "Secrets not found"

**Problem:** Streamlit Cloud can't find secrets

**Solution:**

1. Go to app settings → Secrets
2. Add `VERITYNGN_API_URL`
3. Restart app

### App won't start

**Problem:** Dependency or configuration issue

**Solution:**

1. Check app logs in Streamlit Cloud dashboard
2. Verify `requirements.txt` is correct
3. Check Python version compatibility (3.12 required)

### ngrok URL changed

**Problem:** Free ngrok URLs change on restart

**Solutions:**

- **Quick fix:** Update secrets in Streamlit Cloud with new URL
- **Better fix:** Get paid ngrok account for persistent URLs
- **Best fix:** Deploy API to Cloud Run for permanent URL

---

## 🎨 Customization

### Change Theme

Edit `ui/.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#YOUR_COLOR"
backgroundColor = "#YOUR_COLOR"
```

### Modify Pages

UI components are in `ui/components/`:

- `video_input.py` - Video submission form
- `processing_api.py` - API integration
- `report_viewer.py` - Report display

---

## 🚀 Production Deployment

### Recommended Setup

1. **API:** Deploy to Google Cloud Run (permanent URL)

   ```bash
   gcloud run deploy verityngn-api \
     --source . \
     --region us-central1
   ```

2. **UI:** Deploy to Streamlit Community (free)
   - Point to Cloud Run URL
   - No more ngrok dependency!

### Why This Setup?

- ✅ **Free:** Streamlit Community is free
- ✅ **Reliable:** Cloud Run has SLA guarantees
- ✅ **Fast:** Both are globally distributed
- ✅ **Secure:** Cloud Run handles authentication
- ✅ **Scalable:** Handles traffic spikes

---

## 📊 Monitoring

### Streamlit Cloud Dashboard

View at: <https://share.streamlit.io>

Shows:

- App status
- Resource usage
- Logs
- Error traces

### Check API Health

From Streamlit app, the UI automatically checks API health on startup.

Or test manually:

```bash
curl https://your-api-url/health
```

---

## 🔐 Security

### What the UI Does

- ✅ Calls API endpoints only
- ✅ Displays results
- ❌ Does NOT process videos directly
- ❌ Does NOT need Google Cloud credentials
- ❌ Does NOT store sensitive data

### Best Practices

1. **Use HTTPS** for API (ngrok/Cloud Run provide this)
2. **Don't commit secrets** to Git
3. **Use Streamlit secrets** for configuration
4. **Keep dependencies updated**

---

## 📚 Links

- **Streamlit Community:** <https://share.streamlit.io>
- **Streamlit Docs:** <https://docs.streamlit.io>
- **VerityNgn API Docs:** `https://your-api-url/docs`
- **GitHub Issues:** Report bugs in the main repo

---

## ✅ Deployment Checklist

Before deploying:

- [ ] API is running (ngrok or Cloud Run)
- [ ] API health check works: `curl https://your-api-url/health`
- [ ] Code is pushed to GitHub
- [ ] Created Streamlit Community account
- [ ] Configured `VERITYNGN_API_URL` secret
- [ ] Tested locally first
- [ ] Ready to deploy!

---

**Need help?** Check the main repo README or open an issue on GitHub.

**Ready to deploy?** Click the button below! 👇

[![Deploy to Streamlit Cloud](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)
