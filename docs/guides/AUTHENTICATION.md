# VerityNgn Authentication Guide

Deep dive into Google Cloud authentication options for VerityNgn.

---

## Overview

VerityNgn requires Google Cloud authentication for:

- **Vertex AI** (required): Gemini multimodal analysis
- **Google Custom Search API** (optional): Evidence gathering
- **YouTube Data API v3** (optional): Enhanced counter-intelligence
- **Cloud Storage** (optional): Production deployments

---

## Authentication Methods

### Method 1: Service Account (Production)

**Best for:**
- Production deployments
- Automated workflows
- CI/CD pipelines
- Long-running services

**Advantages:**
- ✅ No browser interaction needed
- ✅ Consistent credentials
- ✅ Fine-grained permission control
- ✅ Secure key management
- ✅ Works in containers/cloud

**Disadvantages:**
- ⚠️ Must manage JSON key files
- ⚠️ Key rotation required

#### Setup Steps

1. **Create Service Account:**

```bash
gcloud iam service-accounts create verityngn-service \
    --display-name="VerityNgn Service Account" \
    --project=YOUR-PROJECT-ID
```

2. **Grant Permissions:**

```bash
# Vertex AI (required)
gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
    --member="serviceAccount:verityngn-service@YOUR-PROJECT-ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# Storage (optional)
gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
    --member="serviceAccount:verityngn-service@YOUR-PROJECT-ID.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"
```

3. **Create JSON Key:**

```bash
gcloud iam service-accounts keys create service-account.json \
    --iam-account=verityngn-service@YOUR-PROJECT-ID.iam.gserviceaccount.com
```

4. **Configure Environment:**

```bash
# Option A: Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="./service-account.json"

# Option B: Place in project root
# File names automatically detected:
# - service-account.json
# - credentials.json
# - verityindex-key.json
```

### Method 2: Application Default Credentials (Development)

**Best for:**
- Local development
- Interactive use
- Quick prototyping
- Developer workstations

**Advantages:**
- ✅ Quick setup
- ✅ No key file management
- ✅ Uses your personal credentials
- ✅ Easy for development

**Disadvantages:**
- ⚠️ Requires browser login
- ⚠️ May expire and need re-authentication
- ⚠️ Not suitable for production
- ⚠️ Doesn't work in containers

#### Setup Steps

1. **Install Google Cloud SDK:**

```bash
# macOS
brew install google-cloud-sdk

# Linux
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Verify installation
gcloud --version
```

2. **Authenticate:**

```bash
# Login with your Google account
gcloud auth application-default login

# This opens browser for authentication
# Follow prompts to grant access
```

3. **Set Project:**

```bash
gcloud config set project YOUR-PROJECT-ID
```

4. **Verify:**

```bash
# Check authentication status
gcloud auth application-default print-access-token

# Should output a valid access token
```

### Method 3: Workload Identity (Kubernetes/GKE)

**Best for:**
- Kubernetes deployments
- Google Kubernetes Engine (GKE)
- Cloud Run
- Cloud Functions

**Advantages:**
- ✅ No key files
- ✅ Automatic credential rotation
- ✅ Enhanced security
- ✅ Integrated with GCP services

**Disadvantages:**
- ⚠️ Only works in GCP environments
- ⚠️ More complex setup

#### Setup Steps

1. **Enable Workload Identity:**

```bash
gcloud container clusters update CLUSTER_NAME \
    --workload-pool=YOUR-PROJECT-ID.svc.id.goog
```

2. **Configure Service Account:**

```bash
# Create Kubernetes service account
kubectl create serviceaccount verityngn-sa

# Bind to Google service account
gcloud iam service-accounts add-iam-policy-binding \
    verityngn-service@YOUR-PROJECT-ID.iam.gserviceaccount.com \
    --role roles/iam.workloadIdentityUser \
    --member "serviceAccount:YOUR-PROJECT-ID.svc.id.goog[NAMESPACE/verityngn-sa]"

# Annotate Kubernetes service account
kubectl annotate serviceaccount verityngn-sa \
    iam.gke.io/gcp-service-account=verityngn-service@YOUR-PROJECT-ID.iam.gserviceaccount.com
```

3. **Use in Pod:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: verityngn
spec:
  serviceAccountName: verityngn-sa
  containers:
  - name: verityngn
    image: verityngn:latest
```

---

## Required Permissions

### Minimum Required (Core Functionality)

```
roles/aiplatform.user
```

**Grants access to:**
- Vertex AI API
- Gemini models
- Multimodal analysis

### Recommended (Full Features)

```
roles/aiplatform.user       # Vertex AI
roles/storage.objectAdmin   # Cloud Storage (if using GCS)
```

### Custom Role (Least Privilege)

Create a custom role with only necessary permissions:

```bash
gcloud iam roles create verityngn_minimal \
    --project=YOUR-PROJECT-ID \
    --title="VerityNgn Minimal" \
    --description="Minimal permissions for VerityNgn" \
    --permissions=aiplatform.endpoints.predict,aiplatform.models.get
```

---

## API Keys (Optional Services)

### Google Custom Search API

**Purpose:** Web evidence gathering

**Setup:**

1. **Enable API:**

```bash
gcloud services enable customsearch.googleapis.com
```

2. **Create API Key:**

```bash
# Via console: https://console.cloud.google.com/apis/credentials
# Or via CLI:
gcloud alpha services api-keys create \
    --display-name="VerityNgn Search"
```

3. **Create Custom Search Engine:**

- Go to https://programmablesearchengine.google.com/
- Click "Add"
- Configure to search entire web
- Copy Search Engine ID

4. **Add to .env:**

```bash
GOOGLE_API_KEY=AIza...
GOOGLE_CSE_ID=your-search-engine-id
```

### YouTube Data API v3

**Purpose:** Enhanced counter-intelligence

**Setup:**

1. **Enable API:**

```bash
gcloud services enable youtube.googleapis.com
```

2. **Create API Key:**

```bash
# Via console: https://console.cloud.google.com/apis/credentials
# Click "Create Credentials" → "API Key"
```

3. **Add to .env:**

```bash
YOUTUBE_API_KEY=AIza...
```

**Alternative:** yt-dlp fallback (slower but no API key needed)

---

## Security Best Practices

### Service Account Security

1. **Principle of Least Privilege:**

```bash
# Don't grant "Owner" or "Editor" roles
# Only grant specific roles needed:
gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
    --member="serviceAccount:SA-EMAIL" \
    --role="roles/aiplatform.user"  # Specific role only
```

2. **Key Rotation:**

```bash
# Delete old keys regularly
gcloud iam service-accounts keys list \
    --iam-account=SA-EMAIL

gcloud iam service-accounts keys delete KEY-ID \
    --iam-account=SA-EMAIL

# Create new key
gcloud iam service-accounts keys create new-key.json \
    --iam-account=SA-EMAIL
```

3. **Key Storage:**

```bash
# Never commit keys to git
echo "service-account.json" >> .gitignore
echo "*.json" >> .gitignore

# Restrict file permissions
chmod 600 service-account.json

# Use environment variables or secret managers in production
```

### API Key Security

1. **Restrict API Keys:**

```bash
# In Google Cloud Console:
# APIs & Services → Credentials → Edit API Key
# Add restrictions:
# - Application restrictions (IP addresses, referrers)
# - API restrictions (only allow specific APIs)
```

2. **Use Environment Variables:**

```bash
# Don't hardcode in source
export GOOGLE_API_KEY="AIza..."

# Use .env file (not committed to git)
echo ".env" >> .gitignore
```

3. **Rotate Keys:**

```bash
# Create new key
# Update .env
# Delete old key after verifying new one works
```

### Multi-Environment Setup

**Development:**

```bash
# .env.development
GOOGLE_APPLICATION_CREDENTIALS=./dev-service-account.json
GOOGLE_CLOUD_PROJECT=verityngn-dev
```

**Production:**

```bash
# .env.production
GOOGLE_APPLICATION_CREDENTIALS=./prod-service-account.json
GOOGLE_CLOUD_PROJECT=verityngn-prod
```

**Load based on environment:**

```python
import os
from dotenv import load_dotenv

env = os.getenv("ENVIRONMENT", "development")
load_dotenv(f".env.{env}")
```

---

## Troubleshooting

### "Could not automatically determine credentials"

**Cause:** No valid credentials found

**Check:**

```bash
# 1. Is GOOGLE_APPLICATION_CREDENTIALS set?
echo $GOOGLE_APPLICATION_CREDENTIALS

# 2. Does file exist?
ls -la $GOOGLE_APPLICATION_CREDENTIALS

# 3. Is file valid JSON?
cat $GOOGLE_APPLICATION_CREDENTIALS | python -m json.tool

# 4. Try ADC:
gcloud auth application-default print-access-token
```

**Solutions:**

```bash
# Option 1: Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"

# Option 2: Use ADC
gcloud auth application-default login

# Option 3: Place in project root as service-account.json
```

### "Permission denied" for Vertex AI

**Cause:** Service account lacks required role

**Fix:**

```bash
# Check current permissions
gcloud projects get-iam-policy YOUR-PROJECT-ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:SA-EMAIL"

# Grant Vertex AI User role
gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
    --member="serviceAccount:SA-EMAIL" \
    --role="roles/aiplatform.user"
```

### "Reauthentication is needed"

**Cause:** OAuth2 credentials expired (ADC)

**Fix:**

```bash
# Re-authenticate
gcloud auth application-default login

# Or switch to service account (doesn't expire)
export GOOGLE_APPLICATION_CREDENTIALS="./service-account.json"
```

### "API key not found"

**Cause:** API keys not configured (optional)

**Impact:** Limited functionality, not critical

**Fix (optional):**

```bash
# Add to .env:
GOOGLE_API_KEY=AIza...
GOOGLE_CSE_ID=your-cse-id
YOUTUBE_API_KEY=AIza...
```

**Or accept reduced functionality:**
- Works without Search API (limited verification)
- Works without YouTube API (uses yt-dlp fallback)

---

## Verification

### Test Authentication

```bash
python test_credentials.py
```

**Expected output:**

```
✅ Google Cloud Project: your-project-id
✅ Vertex AI Authentication: SUCCESS
✅ Service Account: verityngn-service@project.iam.gserviceaccount.com
✅ Location: us-central1
✅ All required credentials configured!
```

### Test Vertex AI Access

```python
from google.cloud import aiplatform

# Initialize Vertex AI
aiplatform.init(project="YOUR-PROJECT-ID", location="us-central1")

print("✅ Vertex AI authentication successful!")
```

### Test API Keys

```python
import os

# Check if API keys are set
google_api_key = os.getenv("GOOGLE_API_KEY")
google_cse_id = os.getenv("GOOGLE_CSE_ID")
youtube_api_key = os.getenv("YOUTUBE_API_KEY")

print(f"Google Search API: {'✅ Configured' if google_api_key else '⚠️  Not configured (optional)'}")
print(f"Custom Search Engine: {'✅ Configured' if google_cse_id else '⚠️  Not configured (optional)'}")
print(f"YouTube API: {'✅ Configured' if youtube_api_key else '⚠️  Not configured (optional)'}")
```

---

## Next Steps

- **[Setup Guide](SETUP.md)** - Complete setup walkthrough
- **[Quick Start](QUICK_START.md)** - Run your first verification
- **[Testing Guide](TESTING.md)** - Test authentication

---

**Last Updated:** October 28, 2025  
**Version:** 2.0


