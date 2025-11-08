# 🚂 Deploy VerityNgn to Railway

## Why Railway?
- ✅ **Docker-native**: Uses your existing `Dockerfile.streamlit`
- ✅ **Simple**: One-click GitHub integration
- ✅ **Affordable**: $5/month credit, ~$5-10/month for this app
- ✅ **Fast**: Deploys in 2-3 minutes
- ✅ **No limits**: Can handle conda + pip dependencies

---

## 🚀 Quick Setup (10 minutes)

### Step 1: Prepare Repository

Ensure these files exist (they do):
```
✅ Dockerfile.streamlit
✅ requirements.txt  
✅ .env (local only, DON'T commit)
```

### Step 2: Sign Up for Railway

1. Go to: https://railway.app
2. Sign up with GitHub
3. Verify email
4. Get $5 free credit

### Step 3: Create New Project

1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose: `hotchilianalytics/verityngn-oss`
4. Railway will auto-detect the Dockerfile

### Step 4: Configure Build

In Railway dashboard:
1. Go to **Settings** → **Build**
2. Set **Dockerfile Path**: `Dockerfile.streamlit`
3. Set **Root Directory**: `/`

### Step 5: Add Environment Variables

In Railway dashboard, go to **Variables** and add:

```bash
# Google Cloud API Keys
GOOGLE_SEARCH_API_KEY=AIzaSy...
CSE_ID=01234567...
YOUTUBE_API_KEY=AIzaSy...

# Google Cloud Project
PROJECT_ID=your-project-id
LOCATION=us-central1

# Service Account (as JSON string)
GOOGLE_APPLICATION_CREDENTIALS=/app/gcp-credentials.json
GCP_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"..."}

# Storage Configuration
DEPLOYMENT_MODE=production
STORAGE_BACKEND=local
DEBUG_OUTPUTS=true

# LLM Configuration
DEFAULT_MODEL=gemini-2.5-flash
MAX_CLAIMS=10
```

### Step 6: Add Service Account File

**Option A: Environment Variable (Easier)**
1. Copy your entire `gcp-service-account.json` content
2. Add as Railway variable: `GCP_SERVICE_ACCOUNT_JSON`
3. Update Dockerfile.streamlit to create file from env var

**Option B: Railway Volumes (Better)**
1. Create Railway Volume
2. Upload `gcp-service-account.json` to volume
3. Mount at `/app/gcp-credentials.json`

### Step 7: Deploy

1. Click **"Deploy"**
2. Watch logs for errors
3. Wait 2-3 minutes for first build
4. Railway will provide a public URL: `https://verityngn-production.up.railway.app`

---

## 🔧 Troubleshooting

### Build Fails: "Dependency conflict"
**Fix:** Use the full `requirements.txt` that includes all dependencies

### Service Account Not Found
**Fix:** Add this to `Dockerfile.streamlit`:

```dockerfile
# After COPY . .
RUN if [ -n "$GCP_SERVICE_ACCOUNT_JSON" ]; then \
    echo "$GCP_SERVICE_ACCOUNT_JSON" > /app/gcp-credentials.json; \
    fi
```

### Out of Memory
**Fix:** Upgrade Railway plan to 1GB+ RAM (Settings → Resources)

---

## 💰 Cost Estimate

- **Free tier**: $5/month credit (enough for testing)
- **Typical usage**: $5-10/month
  - 512MB RAM: $5/month
  - 1GB RAM: $10/month
  - Pay only when running

---

## 🎯 Advantages Over Streamlit Cloud

| Feature | Streamlit Cloud | Railway |
|---------|----------------|---------|
| Docker Support | ❌ No | ✅ Yes |
| Conda + Pip | ❌ One or other | ✅ Both |
| System Packages | ⚠️ Limited | ✅ Full control |
| Memory | 1GB max | 512MB-32GB |
| Build Time | 15min timeout | No limit |
| Cost | Free (limited) | $5-10/month |
| Custom Domain | ⚠️ Pro only | ✅ Free |

---

## 🔗 Next Steps

1. Sign up: https://railway.app
2. Deploy from GitHub
3. Add environment variables
4. Test your deployment

**Railway docs**: https://docs.railway.app








