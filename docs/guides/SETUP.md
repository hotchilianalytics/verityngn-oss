---
title: "Setup Guide"
description: "Complete installation and configuration walkthrough"
---

# VerityNgn Setup Guide

Complete guide to setting up VerityNgn with Google Cloud authentication.

---

## Prerequisites

- Python 3.12+
- Google Cloud account
- Google Cloud project with billing enabled

---

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/hotchilianalytics/verityngn-oss.git
cd verityngn-oss
```

### 2. Install Dependencies

**Using Conda (Recommended):**

```bash
conda env create -f environment.yml
conda activate verityngn
```

**Using pip:**

```bash
pip install -r requirements.txt
```

---

## Authentication Setup

VerityNgn requires Google Cloud authentication for Vertex AI (Gemini). Choose **one** of the following methods:

### Method 1: Service Account (Recommended for Automation)

Best for: Automated workflows, production deployments, CI/CD

#### Step 1: Create Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Select your project at the top of the page
3. Click **"Create Service Account"**
   - Name: `verityngn-service`
   - Description: `Service account for VerityNgn video verification`
   - Click **"Create and Continue"**

#### Step 2: Grant Required Permissions

Add these roles:

- ✅ **Vertex AI User** (required for Gemini multimodal analysis)
- ✅ **Storage Object Admin** (optional, if using GCS)

Click **"Continue"** → **"Done"**

#### Step 3: Create & Download JSON Key

1. Click on your new service account in the list
2. Go to **"Keys"** tab
3. Click **"Add Key"** → **"Create new key"**
4. Select **JSON** format
5. Click **"Create"**
6. The JSON file will download automatically

#### Step 4: Configure Environment

**Option A: Place in project directory (easiest)**

Save the JSON file as one of:
- `service-account.json`
- `credentials.json`
- `verityindex-key.json`

The app will find it automatically!

**Option B: Set environment variable**

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account.json"
```

To persist across sessions, add to `~/.zshrc`:

```bash
echo 'export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"' >> ~/.zshrc
source ~/.zshrc
```

#### Step 5: Set Project ID

Create a `.env` file in the project root:

```bash
# Copy template
cp env.example .env

# Edit .env file
nano .env
```

Add your project ID:

```bash
GOOGLE_CLOUD_PROJECT=your-project-id
PROJECT_ID=your-project-id
LOCATION=us-central1
```

### Method 2: Application Default Credentials (Recommended for Development)

Best for: Local development, interactive use

#### Step 1: Install Google Cloud SDK

**macOS:**

```bash
brew install google-cloud-sdk
```

**Linux:**

```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

#### Step 2: Authenticate

```bash
# Login to your Google account
gcloud auth application-default login

# Set your project
gcloud config set project YOUR-PROJECT-ID

# Verify authentication
gcloud auth application-default print-access-token
```

#### Step 3: Set Project Environment Variables

Create `.env` file:

```bash
GOOGLE_CLOUD_PROJECT=your-project-id
PROJECT_ID=your-project-id
LOCATION=us-central1
```

---

## API Keys (Optional but Recommended)

### Google Custom Search API (for evidence gathering)

1. Go to [Google Cloud Console → APIs & Services → Credentials](https://console.cloud.google.com/apis/credentials)
2. Click **"Create Credentials"** → **"API Key"**
3. Copy the API key

4. Create Custom Search Engine:
   - Go to [Programmable Search Engine](https://programmablesearchengine.google.com/)
   - Click **"Add"**
   - Search the entire web
   - Copy the **Search Engine ID**

5. Add to `.env`:

```bash
GOOGLE_API_KEY=AIza...
GOOGLE_CSE_ID=your-cse-id
```

**Without this:** System works but has limited verification capabilities.

### YouTube Data API v3 (for enhanced counter-intelligence)

1. Go to [Google Cloud Console → APIs & Services → Library](https://console.cloud.google.com/apis/library)
2. Search for "YouTube Data API v3"
3. Click **"Enable"**
4. Go to **Credentials** → **"Create Credentials"** → **"API Key"**
5. Copy the API key

Add to `.env`:

```bash
YOUTUBE_API_KEY=AIza...
```

**Without this:** System uses yt-dlp fallback (slower but functional).

---

## Configuration

### Environment Variables Reference

Create/edit `.env` file in project root:

```bash
# === REQUIRED ===

# Google Cloud Project
GOOGLE_CLOUD_PROJECT=your-project-id
PROJECT_ID=your-project-id
LOCATION=us-central1

# Service Account (if using Method 1)
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json

# === OPTIONAL (Recommended) ===

# Google Custom Search (for evidence verification)
GOOGLE_API_KEY=AIza...
GOOGLE_CSE_ID=your-cse-id

# YouTube Data API (for counter-intelligence)
YOUTUBE_API_KEY=AIza...

# === OPTIONAL (Advanced) ===

# Model configuration
VERTEX_MODEL_NAME=gemini-2.5-flash

# Segmentation (leave commented for intelligent calculation)
# SEGMENT_DURATION_SECONDS=3000

# Frame rate for video analysis
SEGMENT_FPS=1.0

# Max output tokens
MAX_OUTPUT_TOKENS_2_5_FLASH=65536

# Thinking budget (set to 0 for fast mode)
THINKING_BUDGET=0
```

---

## Verification

### Test Authentication

**Quick test:**

```bash
python test_credentials.py
```

Expected output:

```
✅ Google Cloud Project: your-project-id
✅ Vertex AI Authentication: SUCCESS
✅ Service Account: service-account@your-project.iam.gserviceaccount.com
✅ Location: us-central1

✅ All required credentials configured!
```

**Full workflow test:**

```bash
./run_test_tl.sh
```

---

## Troubleshooting

### Error: "Could not automatically determine credentials"

**Solution 1:** Use service account method

1. Download service account JSON
2. Place in project root as `service-account.json`
3. Restart application

**Solution 2:** Use gcloud auth

```bash
gcloud auth application-default login
```

### Error: "Reauthentication is needed"

OAuth2 credentials expired. Switch to service account or re-run:

```bash
gcloud auth application-default login
```

### Error: "Permission denied" for Vertex AI

Grant **Vertex AI User** role to your service account:

```bash
gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
    --member="serviceAccount:SERVICE-ACCOUNT-EMAIL" \
    --role="roles/aiplatform.user"
```

### Error: "Google Search API key not configured"

This is optional. System works without it but has limited verification.

To fix: See [Google Custom Search API](#google-custom-search-api-for-evidence-gathering) section.

### Error: "ModuleNotFoundError"

Reinstall dependencies:

```bash
pip install -r requirements.txt --force-reinstall
```

---

## Next Steps

- **[Quick Start Guide](QUICK_START.md)** - Run your first verification
- **[Testing Guide](TESTING.md)** - Test the complete workflow
- **[Authentication Guide](AUTHENTICATION.md)** - Deep dive into auth options
- **[Configuration Guide](../api/CONFIGURATION.md)** - Advanced configuration

---

## Security Best Practices

1. **Never commit credentials to git:**
   ```bash
   # .gitignore already includes:
   .env
   *.json (service accounts)
   ```

2. **Restrict service account permissions:**
   - Only grant necessary roles
   - Use separate service accounts for dev/prod

3. **Rotate keys regularly:**
   - Delete old service account keys
   - Create new keys every 90 days

4. **Use environment-specific credentials:**
   - Development: application-default credentials
   - Production: service account with minimal permissions

---

**Last Updated:** October 28, 2025  
**Version:** 2.0


















