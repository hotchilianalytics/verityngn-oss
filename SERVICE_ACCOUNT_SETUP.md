# 🔑 Service Account Authentication Setup

## Quick Start

**Best for:** Automated workflows, no browser interaction needed

---

## 📋 Step-by-Step Guide

### 1. Create Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. **Select your project** (top of page)
3. Click **"Create Service Account"**
   - Name: `verityngn-service`
   - Description: `Service account for VerityNgn video verification`
   - Click **"Create and Continue"**

### 2. Grant Required Permissions

Add these roles:

- ✅ **Vertex AI User** (for Gemini multimodal analysis)
- ✅ **Storage Object Admin** (if using GCS)
- ✅ **Service Account User** (optional)

Click **"Continue"** → **"Done"**

### 3. Create & Download JSON Key

1. Click on your new service account in the list
2. Go to **"Keys"** tab
3. Click **"Add Key"** → **"Create new key"**
4. Select **JSON** format
5. Click **"Create"**
6. The JSON file will download automatically

### 4. Place the JSON File

**Option A: Project Directory (Recommended)**

Save the file as:

```
/Users/ajjc/proj/verityngn-oss/service-account.json
```

Or:

```
/Users/ajjc/proj/verityngn-oss/credentials.json
```

The app will find it automatically!

**Option B: Set Environment Variable**

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account.json"
```

Add to `~/.zshrc` to persist:

```bash
echo 'export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"' >> ~/.zshrc
source ~/.zshrc
```

---

## ✅ Verify It Works

### Test Authentication

```bash
cd /Users/ajjc/proj/verityngn-oss
python -c "
import os
from pathlib import Path
from google.oauth2 import service_account

# Check if file exists
json_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS') or 'service-account.json'
if Path(json_path).exists():
    creds = service_account.Credentials.from_service_account_file(json_path)
    print(f'✅ Service account loaded: {creds.service_account_email}')
else:
    print(f'❌ File not found: {json_path}')
"
```

### Run Streamlit

```bash
cd ui
streamlit run streamlit_app.py
```

Should load without authentication errors!

---

## 🔍 How It Works

The system checks for credentials in this order:

1. **Environment variable** `GOOGLE_APPLICATION_CREDENTIALS`
2. **Project root**: `service-account.json` or `credentials.json`
3. **Home directory**: `~/.config/gcloud/service-account.json`
4. **gcloud default**: Falls back to `gcloud auth application-default`

If found, it automatically sets the environment variable for that session.

---

## 🔒 Security Best Practices

### DO

- ✅ Keep JSON file in project root (already in `.gitignore`)
- ✅ Set file permissions: `chmod 600 service-account.json`
- ✅ Use service accounts for automation
- ✅ Rotate keys periodically

### DON'T

- ❌ Commit JSON file to git
- ❌ Share JSON file publicly
- ❌ Use personal credentials for service accounts
- ❌ Grant more permissions than needed

---

## 🎯 What This Enables

With service account authentication:

- ✅ **No browser interaction** - Works in headless environments
- ✅ **Automated workflows** - Perfect for CI/CD
- ✅ **Vertex AI access** - Gemini multimodal analysis
- ✅ **GCS storage** - Upload/download reports
- ✅ **Stable credentials** - Don't expire like user tokens

---

## 🐛 Troubleshooting

### "Permission denied" errors

**Problem:** Service account lacks required roles

**Solution:**

1. Go to [IAM & Admin](https://console.cloud.google.com/iam-admin/iam)
2. Find your service account
3. Click "Edit principal" (pencil icon)
4. Add role: **Vertex AI User**
5. Save

### "File not found" errors

**Problem:** JSON file not in expected location

**Solution:**

```bash
# Check current location
ls -la /Users/ajjc/proj/verityngn-oss/service-account.json

# Or set explicit path
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/file.json"

# Test
python test_credentials.py
```

### "Invalid credentials" errors

**Problem:** JSON file is corrupted or wrong format

**Solution:**

1. Re-download the JSON key from Google Cloud Console
2. Make sure it's the **JSON** format (not P12)
3. Don't edit the file - use as-is

### "Project not set" errors

**Problem:** Service account from different project

**Solution:**

```bash
# Check which project the service account is from
cat service-account.json | grep project_id

# Make sure it matches your current project
echo $GOOGLE_CLOUD_PROJECT
```

---

## 📚 Additional Resources

- **Google Cloud IAM**: <https://cloud.google.com/iam/docs/service-accounts>
- **Vertex AI Authentication**: <https://cloud.google.com/vertex-ai/docs/authentication>
- **Service Account Keys**: <https://cloud.google.com/iam/docs/keys-create-delete>

---

## 🔄 Alternative: User Authentication

If you prefer user-based auth instead:

```bash
gcloud auth application-default login
```

See `CREDENTIALS_SETUP.md` for full details.

---

## ✨ Summary

**To use service account JSON:**

1. Create service account in Google Cloud Console
2. Grant "Vertex AI User" role
3. Download JSON key
4. Save as `/Users/ajjc/proj/verityngn-oss/service-account.json`
5. Run Streamlit - it will auto-detect!

**That's it!** No browser login, no token refresh, just works. 🚀



















