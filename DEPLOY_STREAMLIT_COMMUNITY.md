# 🚀 Run VerityNgn UI Locally & Deploy to Streamlit Community

## ✅ Current Status

Your UI is **already running** locally!

**Access it at:** <http://localhost:8501>

---

## 🖥️ Test Local UI Now

### Option 1: Using Docker (Already Running)

Your UI is running in Docker:

```bash
# View UI logs
docker compose logs -f ui

# Restart UI if needed
docker compose restart ui

# Stop UI
docker compose stop ui
```

**Access:** <http://localhost:8501>

### Option 2: Run UI Directly (Alternative)

If you want to run outside Docker:

```bash
cd /Users/ajjc/proj/verityngn-oss

# Install UI dependencies (lightweight!)
pip install -r ui/requirements.txt

# Run Streamlit
streamlit run ui/streamlit_app.py
```

---

## 🎯 Deploy to Streamlit Community Cloud

### Prerequisites

✅ **GitHub Account** - To host the code  
✅ **Streamlit Community Account** - Free at <https://share.streamlit.io>  
✅ **ngrok Tunnel Running** - Your API at `https://oriented-flea-large.ngrok-free.app`

---

## 📋 Step-by-Step Deployment

### Step 1: Prepare Your Repository

Your repo should already be on GitHub. If not:

```bash
cd /Users/ajjc/proj/verityngn-oss

# Add all files
git add .

# Commit
git commit -m "Prepare UI for Streamlit Community deployment"

# Push to GitHub
git push origin main
```

**Important:** Make sure your repo is **public** for Streamlit Community free tier!

---

### Step 2: Deploy to Streamlit Community

1. **Go to:** <https://share.streamlit.io>

2. **Sign in** with GitHub

3. **Click:** "New app" or "Create app"

4. **Fill in the form:**

   ```
   Repository: your-username/verityngn-oss
   Branch: main
   Main file path: ui/streamlit_app.py
   App URL (optional): verityngn (or your choice)
   ```

5. **Click:** "Deploy!"

---

### Step 3: Configure Secrets

After deployment starts, you need to add your ngrok URL as a secret.

#### In Streamlit Cloud Dashboard

1. **Click:** Your app name
2. **Click:** ⚙️ Settings (bottom left)
3. **Click:** "Secrets" tab
4. **Add this configuration:**

```toml
# VerityNgn API Configuration
VERITYNGN_API_URL = "https://oriented-flea-large.ngrok-free.app"

# Alternative format (also supported)
[api]
url = "https://oriented-flea-large.ngrok-free.app"
```

5. **Click:** "Save"

6. **Your app will restart automatically** and connect to your local API via ngrok!

---

### Step 4: Test Your Deployed App

1. **Wait for deployment** (usually 1-2 minutes)

2. **Access your app:**

   ```
   https://verityngn.streamlit.app
   ```

   (or whatever subdomain you chose)

3. **Test submission:**
   - Submit a YouTube URL
   - Should connect to your local API via ngrok
   - Process and display results

---

## 🎨 Customize Your App

### Update App Name & Description

Create or update `ui/.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[server]
headless = true
enableCORS = false
```

### Add App Metadata

Create `ui/README.md` or update it with:

```markdown
# VerityNgn - YouTube Video Verification

AI-powered truthfulness analysis for YouTube videos.

## Features
- 📹 Submit YouTube videos for verification
- 🔍 Detailed claim analysis
- 📊 Truth scoring
- 🎯 Evidence-based verification
```

---

## 🔄 Update Your App

### When You Make Changes

```bash
# Make your changes to code

# Commit and push
git add .
git commit -m "Update UI feature"
git push origin main

# Streamlit Community will auto-deploy!
```

The app will automatically rebuild and redeploy when you push to main.

---

## ⚡ Important Notes

### ngrok URL Management

**Free ngrok plan:** URL changes on restart

- You'll need to update Streamlit secrets when ngrok restarts
- Consider upgrading to ngrok Personal ($8/mo) for persistent URLs

**Paid ngrok plan:** Reserve a domain

- URL never changes
- Update secrets once, never again!

### Keeping ngrok Running

Your Streamlit app needs the ngrok tunnel to stay active:

```bash
# Keep ngrok running
ngrok start verityngn-api --config=.ngrok.yml

# Or use the free URL
ngrok http 8080
```

**Tip:** Run ngrok in a `tmux` or `screen` session so it stays running!

---

## 🔒 Security Considerations

### Public App + Local API

Your Streamlit app is public, but it connects to your local API via ngrok.

**To secure:**

1. **Add IP whitelisting** (ngrok paid plan)
2. **Add API authentication** to your backend
3. **Rate limiting** to prevent abuse

### Don't Expose Secrets

Never commit to git:

- ❌ `.env` files
- ❌ `secrets.toml`
- ❌ Service account JSON files
- ❌ API keys

These should only be in:

- ✅ `.gitignore`
- ✅ Streamlit Cloud secrets
- ✅ Local development only

---

## 📊 Monitor Your App

### Streamlit Cloud Dashboard

View app health:

- **Logs:** Real-time logs
- **Analytics:** Visitor stats
- **Resources:** CPU/memory usage

### ngrok Web Interface

Monitor API calls:

- **URL:** <http://localhost:4040>
- Shows all requests from Streamlit to your API

---

## 🆘 Troubleshooting

### "Cannot connect to API"

**Check:**

1. Is ngrok still running? Check terminal
2. Is API healthy? `curl http://localhost:8080/health`
3. Is ngrok URL correct in secrets?

**Fix:**

```bash
# Restart ngrok
ngrok http 8080

# Update Streamlit secrets with new URL
# Go to app settings → Secrets → Update URL
```

---

### "Module not found" error

**Check:** `ui/requirements.txt` has all dependencies

**Current UI dependencies:**

```txt
streamlit>=1.28.0
requests>=2.31.0
python-dotenv>=1.0.0
pyyaml>=6.0.1
```

These are lightweight and should install quickly!

---

### App is slow to load

**Streamlit Community limitations:**

- Free tier has resource limits
- Apps "sleep" after inactivity
- First load after sleep is slower

**Solution:** Upgrade to Streamlit Teams for better performance

---

## 🎯 Production Deployment Alternative

Instead of ngrok, deploy API to Cloud Run for production:

```bash
# Deploy API to Cloud Run
gcloud run deploy verityngn-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated

# Get the URL
gcloud run services describe verityngn-api \
  --region us-central1 \
  --format='value(status.url)'

# Update Streamlit secrets with Cloud Run URL
```

This gives you:

- ✅ Persistent URL
- ✅ No ngrok needed
- ✅ Scalable infrastructure
- ✅ Production-ready

---

## 📚 Quick Reference

### Local Testing

```bash
# UI at http://localhost:8501
docker compose up ui

# Or run directly
streamlit run ui/streamlit_app.py
```

### Streamlit Community

```
Deploy: https://share.streamlit.io
Docs: https://docs.streamlit.io/streamlit-community-cloud
```

### Your URLs

```
Local UI: http://localhost:8501
Ngrok API: https://oriented-flea-large.ngrok-free.app
Streamlit App: https://your-subdomain.streamlit.app
```

---

## ✅ Deployment Checklist

- [ ] Local UI tested at <http://localhost:8501>
- [ ] ngrok tunnel running
- [ ] Repo pushed to GitHub (public)
- [ ] Streamlit Community account created
- [ ] App deployed with correct main file path (`ui/streamlit_app.py`)
- [ ] Secrets configured with ngrok URL
- [ ] App tested with video submission
- [ ] Monitoring set up (Streamlit + ngrok dashboards)

---

**Ready to deploy?** Go to <https://share.streamlit.io> and click "New app"! 🚀
