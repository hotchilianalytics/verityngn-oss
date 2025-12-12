# VerityNgn UI
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)

## Quick Start for Streamlit Community Cloud

### 1. Deploy to Streamlit

1. Go to: `https://share.streamlit.io`
2. New app:
   - Repository: `hotchilianalytics/verityngn-oss` (or your fork)
   - Branch: `main`
   - Main file: `ui/streamlit_app.py`
3. Add Streamlit Secrets (required):

```toml
# Cloud Run API URL (REQUIRED for public Streamlit)
CLOUDRUN_API_URL = "https://your-cloudrun-service.run.app"
```

4. Deploy

### 2. That's it!

Your app will be live at: `https://your-app.streamlit.app`

---

## Files for Deployment

- ✅ `streamlit_app.py` - Main app
- ✅ `requirements.txt` - Minimal dependencies (API-only mode)
- ✅ `packages.txt` - System dependencies
- ✅ `.streamlit/config.toml` - App configuration
- ✅ `.streamlit/secrets.toml.example` - Secrets template

---

## API Connection

The UI connects to VerityNgn API via:
- **Production:** Cloud Run deployment

Set `CLOUDRUN_API_URL` in Streamlit secrets.

---

**Full docs:** See `STREAMLIT_CLOUD_DEPLOYMENT.md` in project root

