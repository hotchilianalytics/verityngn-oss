# VerityNgn Credentials Setup Guide

Complete guide to setting up API credentials and authentication for VerityNgn.

---

## Overview

VerityNgn requires the following credentials:

| Service | Purpose | Required? | Cost |
|---------|---------|-----------|------|
| **Google Cloud (Vertex AI)** | Multimodal LLM (Gemini 2.5 Flash) | ✅ Yes | ~$0.30-0.80/video |
| **YouTube Data API v3** | Enhanced counter-intelligence | Recommended | ~$0.05-0.10/video |
| **Google Custom Search** | Web evidence gathering | ✅ Yes | ~$0.10-0.20/video |

**Total estimated cost:** ~$0.50-2.00 per video

---

## Step 1: Google Cloud Setup

### 1.1 Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Create Project"
3. Enter project name (e.g., `verityngn-research`)
4. Note your **Project ID** (e.g., `verityngn-research-123456`)

### 1.2 Enable Required APIs

```bash
# Set your project ID
export PROJECT_ID=your-project-id

# Enable APIs
gcloud services enable aiplatform.googleapis.com        # Vertex AI
gcloud services enable youtube.googleapis.com           # YouTube Data API
gcloud services enable customsearch.googleapis.com      # Custom Search
gcloud services enable storage.googleapis.com           # Cloud Storage (optional)
```

Or via Console:
1. Go to [APIs & Services](https://console.cloud.google.com/apis/dashboard)
2. Click "Enable APIs and Services"
3. Search and enable:
   - Vertex AI API
   - YouTube Data API v3
   - Custom Search API
   - Cloud Storage API (optional)

### 1.3 Create Service Account

```bash
# Create service account
gcloud iam service-accounts create verityngn-sa \
  --display-name="VerityNgn Service Account" \
  --project=$PROJECT_ID

# Grant necessary roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:verityngn-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:verityngn-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
```

Or via Console:
1. Go to [IAM & Admin > Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Click "Create Service Account"
3. Name: `verityngn-sa`
4. Grant roles:
   - `Vertex AI User`
   - `Storage Object Admin` (if using GCS)
5. Click "Done"

### 1.4 Create and Download Service Account Key

**⚠️ SECURITY WARNING:** Service account keys are sensitive. Store securely and never commit to git.

```bash
# Create key
gcloud iam service-accounts keys create ~/verityngn-key.json \
  --iam-account=verityngn-sa@$PROJECT_ID.iam.gserviceaccount.com

# Move to secure location
mkdir -p ~/.config/gcp
mv ~/verityngn-key.json ~/.config/gcp/verityngn-key.json
chmod 600 ~/.config/gcp/verityngn-key.json
```

Or via Console:
1. Go to [IAM & Admin > Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Click on `verityngn-sa@...`
3. Go to "Keys" tab
4. Click "Add Key" > "Create new key"
5. Select "JSON"
6. Click "Create" (downloads automatically)
7. **Move to secure location and set permissions:**
   ```bash
   mkdir -p ~/.config/gcp
   mv ~/Downloads/verityngn-*.json ~/.config/gcp/verityngn-key.json
   chmod 600 ~/.config/gcp/verityngn-key.json
   ```

---

## Step 2: YouTube Data API v3 Key

### 2.1 Create API Key

1. Go to [APIs & Services > Credentials](https://console.cloud.google.com/apis/credentials)
2. Click "Create Credentials" > "API key"
3. Copy the API key (starts with `AIza...`)
4. Click "Restrict Key" (recommended)

### 2.2 Restrict API Key (Recommended)

1. Under "API restrictions":
   - Select "Restrict key"
   - Choose "YouTube Data API v3"
2. Under "Application restrictions" (optional):
   - Select "IP addresses" or "HTTP referrers"
   - Add your IP or domain
3. Click "Save"

### 2.3 Note Your API Key

```
YOUTUBE_API_KEY=AIzaSyD...your-key-here...xyz
```

**⚠️ Security:** Treat API keys like passwords. Never commit to git.

---

## Step 3: Google Custom Search Setup

### 3.1 Create Custom Search Engine

1. Go to [Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Click "Add" or "Get Started"
3. Configure:
   - **Sites to search:** Leave empty or add `*` for "Search the entire web"
   - **Name:** `VerityNgn Web Search`
   - **Language:** English
4. Click "Create"
5. Note your **Search Engine ID** (format: `a1b2c3d4e5f6g7h8i9`)

### 3.2 Enable "Search the entire web"

1. Go to your search engine settings
2. Click "Edit search engine"
3. Under "Basics" > "Sites to search":
   - Remove any specific sites
   - Turn ON "Search the entire web"
4. Click "Update"

### 3.3 Get API Key

**Option A: Use Same Project**

Use the same API key from Step 2 (it works for both YouTube and Custom Search).

**Option B: Create Separate Key**

1. Go to [APIs & Services > Credentials](https://console.cloud.google.com/apis/credentials)
2. Click "Create Credentials" > "API key"
3. Restrict to "Custom Search API"
4. Copy the key

---

## Step 4: Configure VerityNgn

### 4.1 Create `.env` File

```bash
cd /path/to/verityngn-oss
cp .env.example .env
```

### 4.2 Edit `.env` with Your Credentials

Open `.env` in your editor and fill in:

```bash
# Google Cloud Authentication
GOOGLE_APPLICATION_CREDENTIALS=/Users/your-username/.config/gcp/verityngn-key.json
PROJECT_ID=your-project-id

# API Keys
YOUTUBE_API_KEY=AIzaSyD...your-youtube-key...xyz
GOOGLE_SEARCH_API_KEY=AIzaSyD...your-search-key...xyz  # Can be same as YouTube key
GOOGLE_SEARCH_ENGINE_ID=a1b2c3d4e5f6g7h8i9

# Deployment Configuration
DEPLOYMENT_MODE=research
STORAGE_BACKEND=local

# LLM Configuration
LLM_MODEL=gemini-2.5-flash
LLM_TEMPERATURE=0.1
MAX_OUTPUT_TOKENS=65536
LLM_LOGGING_ENABLED=true

# Processing Configuration
MAX_CLAIMS=40
MIN_CLAIMS=15
SEGMENT_FPS=1.0
YOUTUBE_CI_ENABLED=true
YOUTUBE_API_ENABLED=true

# API Server
HOST=0.0.0.0
PORT=8000
DEBUG=false
```

### 4.3 Secure Your `.env` File

```bash
# Restrict permissions (important!)
chmod 600 .env

# Verify .gitignore excludes .env
cat .gitignore | grep .env
# Should see: .env, .env.local, .env.*.local
```

---

## Step 5: Verify Setup

### 5.1 Test Google Cloud Authentication

```python
from google.cloud import aiplatform

aiplatform.init(project="your-project-id", location="us-central1")
print("✅ Vertex AI authentication successful!")
```

Or using the provided script:

```bash
python -c "from verityngn.config.auth import auto_detect_auth; auth = auto_detect_auth(); print('✅ Auth OK' if auth.validate() else '❌ Auth Failed')"
```

### 5.2 Test YouTube API

```bash
curl "https://www.googleapis.com/youtube/v3/videos?part=snippet&id=dQw4w9WgXcQ&key=YOUR_YOUTUBE_API_KEY"
```

Should return JSON with video details.

### 5.3 Test Custom Search API

```bash
curl "https://www.googleapis.com/customsearch/v1?key=YOUR_SEARCH_KEY&cx=YOUR_SEARCH_ENGINE_ID&q=test"
```

Should return search results JSON.

### 5.4 Run VerityNgn Test

```bash
# Test with a short video
python run_workflow.py https://www.youtube.com/watch?v=dQw4w9WgXcQ

# Or use Streamlit UI
./run_streamlit.sh
```

Expected output:
```
🚀 Starting verification for https://www.youtube.com/watch?v=dQw4w9WgXcQ
📹 Video ID: dQw4w9WgXcQ
📁 Output directory: outputs/dQw4w9WgXcQ/
✅ Verification complete!
📄 Reports saved to: outputs/dQw4w9WgXcQ/
```

---

## Step 6: Troubleshooting

### Error: "Could not load service account credentials"

**Cause:** `GOOGLE_APPLICATION_CREDENTIALS` path is wrong or file doesn't exist

**Fix:**
```bash
# Check if file exists
ls -la $GOOGLE_APPLICATION_CREDENTIALS

# Verify path in .env is absolute
cat .env | grep GOOGLE_APPLICATION_CREDENTIALS

# Use absolute path (not relative)
# Good: /Users/you/.config/gcp/key.json
# Bad: ./config/key.json
```

### Error: "API [aiplatform.googleapis.com] not enabled"

**Cause:** Vertex AI API not enabled for your project

**Fix:**
```bash
gcloud services enable aiplatform.googleapis.com --project=your-project-id
```

### Error: "YouTube API quota exceeded"

**Cause:** Daily quota limit reached (default: 10,000 units/day)

**Fix:**
1. Go to [APIs & Services > Quotas](https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas)
2. Request quota increase (or wait 24 hours)
3. Or disable YouTube CI temporarily:
   ```bash
   # In .env
   YOUTUBE_API_ENABLED=false
   ```

### Error: "Permission denied" on service account key

**Cause:** File permissions too open

**Fix:**
```bash
chmod 600 ~/.config/gcp/verityngn-key.json
```

### Error: "Custom Search API quota exceeded"

**Cause:** Daily limit reached (default: 100 queries/day)

**Fix:**
1. Go to [APIs & Services > Quotas](https://console.cloud.google.com/apis/api/customsearch.googleapis.com/quotas)
2. Request quota increase
3. Or use cached results / reduce evidence gathering

---

## Cost Management

### Monitor Costs

```bash
# Check Vertex AI usage
gcloud ai operations list --region=us-central1

# Check billing
gcloud billing accounts list
gcloud billing projects describe $PROJECT_ID
```

Or via Console:
- [Billing Reports](https://console.cloud.google.com/billing)
- Filter by service: Vertex AI, YouTube, Custom Search

### Set Budget Alerts

1. Go to [Billing > Budgets & Alerts](https://console.cloud.google.com/billing/budgets)
2. Click "Create Budget"
3. Set amount (e.g., $50/month)
4. Set alerts at 50%, 90%, 100%

### Estimated Costs

**Per Video:**
- Gemini 2.5 Flash (multimodal): ~$0.30-0.80
- YouTube API (if enabled): ~$0.05-0.10
- Custom Search API: ~$0.10-0.20
- **Total: ~$0.50-2.00**

**Monthly (100 videos):**
- ~$50-200/month

**Free Tier:**
- Vertex AI: $300 credit for new users
- Custom Search: 100 queries/day free
- YouTube API: 10,000 units/day free

---

## Security Best Practices

### 1. Credential Storage

```bash
# ✅ GOOD: Secure location with restricted permissions
~/.config/gcp/verityngn-key.json (chmod 600)

# ❌ BAD: In project directory or public location
/path/to/verityngn-oss/config/key.json
~/Downloads/key.json
```

### 2. Git Safety

```bash
# Before committing, always check:
git status
git diff

# Verify no credentials in diff:
git diff | grep -iE "(private_key|api_key|password)"

# If found: DO NOT COMMIT!
git reset HEAD .env
```

### 3. Key Rotation

```bash
# Rotate keys every 90 days:
gcloud iam service-accounts keys create ~/new-key.json \
  --iam-account=verityngn-sa@$PROJECT_ID.iam.gserviceaccount.com

# Update .env with new key path
# Test new key works
# Delete old key:
gcloud iam service-accounts keys delete OLD_KEY_ID \
  --iam-account=verityngn-sa@$PROJECT_ID.iam.gserviceaccount.com
```

### 4. Principle of Least Privilege

Only grant minimum required roles:
- `roles/aiplatform.user` (NOT admin)
- `roles/storage.objectAdmin` (only if using GCS)

Avoid `roles/owner` or `roles/editor`.

---

## Alternative: Application Default Credentials (ADC)

For local development, you can use gcloud ADC instead of service account keys:

```bash
# Authenticate with your user account
gcloud auth application-default login

# In .env, comment out GOOGLE_APPLICATION_CREDENTIALS
# The system will automatically use ADC
```

**Pros:**
- No key files to manage
- Your personal quotas/billing

**Cons:**
- Doesn't work in containers/production
- Requires gcloud installed

---

## Production Deployment

For Cloud Run or Kubernetes, use:
- **Workload Identity** (Kubernetes)
- **Service Account attached to Cloud Run** (no keys needed)
- **Secret Manager** for API keys

See `DEPLOYMENT_GUIDE_PRODUCTION.md` for details.

---

## Need Help?

- **Documentation:** Check [README.md](README.md) and [CLAUDE.md](CLAUDE.md)
- **Issues:** Open a [GitHub Issue](https://github.com/hotchilianalytics/verityngn-oss/issues)
- **Discussions:** Ask in [GitHub Discussions](https://github.com/hotchilianalytics/verityngn-oss/discussions)

---

**Last Updated:** October 23, 2025

