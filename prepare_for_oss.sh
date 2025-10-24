#!/bin/bash
#
# prepare_for_oss.sh - Prepare repository for open source release
#
# This script removes sensitive credentials and replaces them with placeholders
# Run this before making the repository public!
#

set -e

echo "================================================================================================"
echo "🔒 Preparing VerityNgn for Open Source Release"
echo "================================================================================================"
echo ""
echo "⚠️  WARNING: This will remove sensitive credentials from the repository!"
echo "⚠️  Make sure you have backups of:"
echo "   - Service account JSON files"
echo "   - API keys in settings.py"
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Aborted."
    exit 1
fi

echo ""
echo "📋 Step 1: Removing service account key files..."
find verityngn/config -name "*.json" -type f ! -name "config.example.json" -delete
echo "✅ Removed: verityngn/config/*.json"

echo ""
echo "📋 Step 2: Creating .env.example..."
cat > .env.example << 'EOF'
# VerityNgn Configuration
# Copy this file to .env and fill in your actual values

# ===== Google Cloud Configuration =====
PROJECT_ID=your-gcp-project-id
LOCATION=us-central1
GCS_BUCKET_NAME=your-bucket-name

# Google Cloud Service Account
# Download from: https://console.cloud.google.com/iam-admin/serviceaccounts
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your-service-account-key.json

# ===== API Keys =====

# Google Search API (https://developers.google.com/custom-search/v1/overview)
GOOGLE_SEARCH_API_KEY=your-google-search-api-key
CSE_ID=your-custom-search-engine-id

# YouTube Data API v3 (https://developers.google.com/youtube/v3/getting-started)
YOUTUBE_API_KEY=your-youtube-api-key

# OpenAI API (https://platform.openai.com/api-keys)
OPENAI_API_KEY=your-openai-api-key

# TWL API
TWL_API_KEY=your-twl-api-key

# Google AI Studio (https://aistudio.google.com/app/apikey)
GOOGLE_AI_STUDIO_KEY=your-google-ai-studio-key
EOF
echo "✅ Created: .env.example"

echo ""
echo "📋 Step 3: Updating .gitignore..."
cat >> .gitignore << 'EOF'

# ===== Sensitive Credentials =====
.env
*.json
!config.example.json
verityngn/config/*.json
EOF
echo "✅ Updated: .gitignore"

echo ""
echo "📋 Step 4: Creating credential setup guide..."
cat > CREDENTIALS_SETUP.md << 'EOF'
# Credentials Setup Guide

This guide explains how to configure VerityNgn with your own API credentials.

## Required Credentials

### 1. Google Cloud Service Account (Required)

**Purpose:** Access Vertex AI (Gemini models) for video analysis

**Setup:**
1. Go to https://console.cloud.google.com/
2. Create or select a project
3. Enable Vertex AI API
4. Create a service account:
   - IAM & Admin → Service Accounts → Create Service Account
   - Grant roles: "Vertex AI User"
5. Create and download JSON key
6. Save as `verityngn/config/your-service-account-key.json`
7. Set environment variable:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your-service-account-key.json"
   ```

### 2. Google Search API (Required for Claim Verification)

**Purpose:** Search the web for evidence to verify claims

**Setup:**
1. Go to https://developers.google.com/custom-search/v1/overview
2. Create API key
3. Create Custom Search Engine: https://programmablesearchengine.google.com/
4. Get your Search Engine ID (CSE ID)
5. Add to `.env`:
   ```
   GOOGLE_SEARCH_API_KEY=your_api_key
   CSE_ID=your_cse_id
   ```

### 3. YouTube Data API (Required for Counter-Intelligence)

**Purpose:** Search YouTube for contradictory videos/reviews

**Setup:**
1. Go to https://console.developers.google.com/
2. Enable YouTube Data API v3
3. Create credentials (API key)
4. Add to `.env`:
   ```
   YOUTUBE_API_KEY=your_youtube_api_key
   ```

**Note:** You can use the same API key as Google Search API

### 4. OpenAI API (Optional - for alternative models)

**Purpose:** Optional fallback for some analysis tasks

**Setup:**
1. Go to https://platform.openai.com/api-keys
2. Create API key
3. Add to `.env`:
   ```
   OPENAI_API_KEY=your_openai_api_key
   ```

## Setup Steps

1. **Copy example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your credentials:**
   ```bash
   nano .env  # or use your favorite editor
   ```

3. **Set service account path:**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your-service-account-key.json"
   ```

4. **Start the application:**
   ```bash
   ./run_streamlit.sh
   # or
   streamlit run ui/streamlit_app.py
   ```

## Verification

Test your credentials:
```bash
# Test Google Cloud auth
gcloud auth application-default print-access-token

# Test environment variables
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('✅ Credentials loaded')"
```

## Troubleshooting

### "Reauthentication is needed"
```bash
gcloud auth application-default login
```

### "Resource exhausted (429)"
- You've hit API rate limits
- Wait a few minutes and try again
- Check quota: https://console.cloud.google.com/iam-admin/quotas

### "No module named 'google.cloud'"
```bash
pip install google-cloud-aiplatform
```
EOF
echo "✅ Created: CREDENTIALS_SETUP.md"

echo ""
echo "📋 Step 5: Checking for hardcoded secrets in settings.py..."
echo "⚠️  Manual step required:"
echo "   Edit verityngn/config/settings.py and replace hardcoded API keys with:"
echo ""
echo "   # Replace:"
echo "   GOOGLE_SEARCH_API_KEY = os.getenv(\"GOOGLE_SEARCH_API_KEY\", \"AIza...\")"
echo "   # With:"
echo "   GOOGLE_SEARCH_API_KEY = os.getenv(\"GOOGLE_SEARCH_API_KEY\")"
echo ""

echo ""
echo "================================================================================================"
echo "✅ OSS Preparation Complete!"
echo "================================================================================================"
echo ""
echo "📋 Manual steps remaining:"
echo "   1. Edit verityngn/config/settings.py - remove hardcoded API keys (lines 101, 102, 156-158)"
echo "   2. Review all files for any remaining sensitive data"
echo "   3. Update README.md with setup instructions"
echo "   4. Test with clean .env file"
echo ""
echo "📁 Files created:"
echo "   - .env.example (credential template)"
echo "   - CREDENTIALS_SETUP.md (setup guide)"
echo ""
echo "🔒 Files removed:"
echo "   - verityngn/config/*.json (service account keys)"
echo ""
echo "================================================================================================"

