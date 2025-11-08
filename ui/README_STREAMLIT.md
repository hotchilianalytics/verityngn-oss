# VerityNgn UI
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)

## Quick Start for Streamlit Community Cloud

### 1. Local Testing

```bash
# UI is already running at:
open http://localhost:8501
```

### 2. Deploy to Streamlit

1. **Go to:** https://share.streamlit.io
2. **New app:**
   - Repository: `your-username/verityngn-oss`
   - Branch: `main`
   - Main file: `ui/streamlit_app.py`
3. **Add secrets:**
   ```toml
   VERITYNGN_API_URL = "https://oriented-flea-large.ngrok-free.app"
   ```
4. **Deploy!**

### 3. That's it!

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
- **Local development:** ngrok tunnel
- **Production:** Cloud Run deployment

Set `VERITYNGN_API_URL` in Streamlit secrets.

---

**Full docs:** See `DEPLOY_TO_STREAMLIT.md` in project root

