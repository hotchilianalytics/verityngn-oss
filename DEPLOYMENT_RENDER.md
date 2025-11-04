# 🎨 Deploy VerityNgn to Render

## Why Render?
- ✅ **Free tier available** (with limitations)
- ✅ **Docker support**
- ✅ **GitHub integration**
- ⚠️ **Free tier spins down** after 15min inactivity (50s cold start)

---

## 🚀 Quick Setup (15 minutes)

### Step 1: Sign Up

1. Go to: https://render.com
2. Sign up with GitHub
3. Verify email

### Step 2: Create Web Service

1. Click **"New +"** → **"Web Service"**
2. Connect GitHub repository: `hotchilianalytics/verityngn-oss`
3. Configure:
   - **Name**: `verityngn-streamlit`
   - **Region**: Oregon (US West) or closest
   - **Branch**: `main`
   - **Root Directory**: `.`
   - **Environment**: `Docker`
   - **Dockerfile Path**: `Dockerfile.streamlit`

### Step 3: Configure Instance

**Free Tier:**
- ✅ 512MB RAM
- ✅ 0.1 CPU
- ⚠️ Spins down after 15min inactivity
- ⚠️ 50s cold start

**Starter ($7/month):**
- ✅ 512MB RAM
- ✅ 0.5 CPU
- ✅ Always on
- ✅ Faster

### Step 4: Add Environment Variables

In Render dashboard, go to **Environment** and add:

```bash
# Google Cloud API Keys
GOOGLE_SEARCH_API_KEY=AIzaSy...
CSE_ID=01234567...
YOUTUBE_API_KEY=AIzaSy...

# Google Cloud Project
PROJECT_ID=your-project-id
LOCATION=us-central1

# Service Account JSON (as single-line string)
GCP_SERVICE_ACCOUNT_JSON={"type":"service_account",...}

# Storage Configuration
DEPLOYMENT_MODE=production
STORAGE_BACKEND=local
DEBUG_OUTPUTS=true

# LLM Configuration
DEFAULT_MODEL=gemini-2.5-flash
MAX_CLAIMS=10
```

### Step 5: Add Secret Files (Service Account)

**Option 1: Environment Variable**
1. Copy `gcp-service-account.json` content
2. Minify to single line (remove newlines)
3. Add as `GCP_SERVICE_ACCOUNT_JSON` env var

**Option 2: Render Disk (Paid plans)**
1. Create persistent disk
2. Upload service account JSON
3. Mount to `/app/gcp-credentials.json`

### Step 6: Update Dockerfile for Render

Update `Dockerfile.streamlit` to handle env-based service account:

```dockerfile
# After COPY . .
RUN mkdir -p /app/secrets

# Create service account file from env var if present
RUN if [ -n "$GCP_SERVICE_ACCOUNT_JSON" ]; then \
    echo "$GCP_SERVICE_ACCOUNT_JSON" > /app/gcp-credentials.json && \
    export GOOGLE_APPLICATION_CREDENTIALS=/app/gcp-credentials.json; \
    fi

# Set environment variable for runtime
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/gcp-credentials.json
```

### Step 7: Deploy

1. Click **"Create Web Service"**
2. Render will:
   - Build Docker image (5-10 min)
   - Deploy container
   - Provide public URL: `https://verityngn-streamlit.onrender.com`

---

## 🔧 Troubleshooting

### Build Timeout
**Issue:** Free tier has 15min build timeout
**Fix:** 
- Use smaller base image
- Cache Docker layers
- Or upgrade to Starter plan

### Out of Memory
**Issue:** 512MB not enough during video processing
**Fix:**
- Reduce `MAX_CLAIMS` to 5
- Process smaller videos only
- Or upgrade to 2GB instance ($15/month)

### Cold Starts
**Issue:** Free tier spins down after 15min
**Fix:**
- Upgrade to Starter ($7/month)
- Or use a health check pinger (e.g., UptimeRobot)

---

## 💰 Cost Comparison

| Plan | RAM | CPU | Cost | Best For |
|------|-----|-----|------|----------|
| Free | 512MB | 0.1 | $0 | Testing only |
| Starter | 512MB | 0.5 | $7/mo | Light use |
| Standard | 2GB | 1.0 | $15/mo | Production |
| Pro | 4GB | 2.0 | $25/mo | Heavy use |

---

## 🎯 Advantages & Disadvantages

### ✅ Advantages
- Free tier available
- Simple Docker deployment
- GitHub auto-deploy
- Custom domains (free SSL)
- Good documentation

### ❌ Disadvantages
- Free tier spins down (50s cold start)
- 512MB RAM limiting for video processing
- Slower builds than Railway
- No persistent storage on free tier

---

## 🔗 Alternative: Use Render for API, Streamlit Cloud for UI

**Better Architecture:**
1. Deploy verification API to Render (Docker, always-on)
2. Deploy lightweight Streamlit UI to Streamlit Cloud
3. UI makes API calls to Render backend

This splits the complexity:
- **Render**: Heavy lifting (video processing, LLM, storage)
- **Streamlit Cloud**: Just UI (forms, display, simple logic)

---

## 📚 Resources

- Render Docs: https://render.com/docs
- Docker on Render: https://render.com/docs/deploy-docker
- Environment Variables: https://render.com/docs/environment-variables

---

## 🎯 Recommendation

**For VerityNgn:**
- ❌ **Don't use Render Free**: Too slow (cold starts) for user-facing app
- ✅ **Use Render Starter ($7/mo)**: Good for production
- ⭐ **Or use Railway**: Better dev experience, similar cost


