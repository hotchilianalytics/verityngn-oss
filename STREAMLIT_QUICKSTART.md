# Streamlit Deployment - Quick Start

## 🚀 Local Development (Fastest)

### 1. Set Up Secrets

```bash
# Create .streamlit directory
mkdir -p .streamlit

# Copy example secrets file
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

# Edit with your credentials
nano .streamlit/secrets.toml  # or use your favorite editor
```

**What to fill in:**
- Copy your service account JSON contents into `[gcp_service_account]` section
- Add your API keys: `GOOGLE_SEARCH_API_KEY`, `CSE_ID`, `YOUTUBE_API_KEY`
- Update `PROJECT_ID` to match your GCP project

### 2. Run Streamlit

```bash
# From verityngn-oss root directory
streamlit run ui/streamlit_app.py
```

**That's it!** 🎉 The app will open at `http://localhost:8501`

---

## ☁️ Streamlit Cloud Deployment

### 1. Prepare Repository

```bash
# Make sure secrets are ignored
git add .gitignore
git commit -m "Ensure secrets are ignored"
git push
```

### 2. Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Select your repository: `verityngn-oss`
4. Main file: `ui/streamlit_app.py`
5. Click "Advanced settings"

### 3. Add Secrets

Click "Secrets" and paste this format (replace with your values):

```toml
GOOGLE_SEARCH_API_KEY = "AIza..."
CSE_ID = "your-cse-id"
YOUTUBE_API_KEY = "AIza..."
PROJECT_ID = "verityindex-0-0-1"
LOCATION = "us-central1"
DEBUG_OUTPUTS = "true"
DEPLOYMENT_MODE = "research"

[gcp_service_account]
type = "service_account"
project_id = "verityindex-0-0-1"
private_key_id = "abc123..."
private_key = "-----BEGIN PRIVATE KEY-----\nYour-Key-Here\n-----END PRIVATE KEY-----\n"
client_email = "your-sa@project.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs/your-sa%40project.iam.gserviceaccount.com"
universe_domain = "googleapis.com"
```

**Where to get service account JSON:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Select your project
3. Click service account → Keys → Add Key → JSON
4. Download and open the JSON file
5. Copy ALL contents and paste into the `[gcp_service_account]` section above

### 4. Deploy!

Click "Deploy" and wait ~2 minutes. Your app will be live! 🚀

---

## 🐳 Docker Deployment

### Quick Docker Run

```bash
# 1. Set up secrets
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit .streamlit/secrets.toml with your credentials

# 2. Build
docker build -t verityngn-streamlit -f Dockerfile.streamlit .

# 3. Run
docker run -d \
  -p 8501:8501 \
  -v $(pwd)/.streamlit/secrets.toml:/app/.streamlit/secrets.toml:ro \
  --name verityngn-ui \
  verityngn-streamlit

# 4. Access at http://localhost:8501
```

### Docker Compose (Recommended)

```bash
# 1. Set up secrets
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit .streamlit/secrets.toml

# 2. Start
docker-compose -f docker-compose.streamlit.yml up -d

# 3. View logs
docker-compose -f docker-compose.streamlit.yml logs -f

# 4. Stop
docker-compose -f docker-compose.streamlit.yml down
```

---

## 🔐 Where Do Secrets Go?

| Deployment Method | Secrets Location | Service Account JSON |
|------------------|------------------|----------------------|
| **Local Dev** | `.streamlit/secrets.toml` | Paste into `[gcp_service_account]` section |
| **Streamlit Cloud** | App dashboard → Secrets | Paste into secrets (TOML format) |
| **Docker** | Mount `.streamlit/secrets.toml` | Included in mounted secrets.toml |
| **Self-Hosted** | `.env` file or systemd | File path in `GOOGLE_APPLICATION_CREDENTIALS` |

---

## ✅ Verify Setup

After deploying, check credentials status:

1. Start the app
2. Look for the banner at the top
3. Should show: "✅ Google Cloud Authentication: Active"

If you see errors:
- Check that all secrets are filled in (no "your-key-here" placeholders)
- Verify service account JSON is complete (starts with `{` or `type = "service_account"`)
- Ensure API keys are valid

---

## 🆘 Troubleshooting

**"Could not find credentials"**
- Check `[gcp_service_account]` section has ALL fields from your JSON
- Verify no syntax errors in TOML (commas, quotes, etc.)

**"API key not found"**
- Ensure `GOOGLE_SEARCH_API_KEY`, `CSE_ID`, `YOUTUBE_API_KEY` are set
- Check for typos in key names

**"Module not found" errors**
- Verify `requirements.txt` is complete
- For Streamlit Cloud: Check Python version (should be 3.11+)

**Gallery/Reports not showing**
- Check `DEBUG_OUTPUTS = "true"` is set
- Verify reports exist in `verityngn/outputs_debug/`
- Restart Streamlit to reload

---

## 📚 Full Documentation

For detailed deployment guides, see:
- **`STREAMLIT_DEPLOYMENT_GUIDE.md`** - Complete deployment guide for all platforms
- **`.streamlit/secrets.toml.example`** - Full secrets template with comments
- **`GALLERY_CURATION_GUIDE.md`** - How to add reports to gallery

---

## 🎯 Quick Commands Reference

```bash
# Local development
streamlit run ui/streamlit_app.py

# Add report to gallery
python scripts/add_to_gallery.py --video-id VIDEO_ID --status approved

# List available reports
python scripts/add_to_gallery.py --list

# Docker
docker-compose -f docker-compose.streamlit.yml up -d

# Check logs
docker-compose -f docker-compose.streamlit.yml logs -f streamlit
```

---

**Need more help?** See `STREAMLIT_DEPLOYMENT_GUIDE.md` for comprehensive instructions.


