# Streamlit Community Cloud Deployment Guide

## ✅ Prerequisites Checklist

- [x] Cloud Run API deployed and accessible: `https://verityngn-api-ze7rxua3dq-uc.a.run.app`
- [x] Signed URL generation working (HTTPS URLs)
- [x] Gallery API endpoints implemented
- [x] Streamlit app configured for Cloud Run mode
- [x] Secrets template created: `ui/.streamlit/secrets.toml.example`

## 📋 Pre-Deployment Steps

### 1. Commit and Push Changes

Ensure all changes are committed and pushed to GitHub:

```bash
cd /Users/ajjc/proj/verityngn-oss

# Check status
git status

# Add all changes
git add .

# Commit (if needed)
git commit -m "Prepare for Streamlit Community Cloud deployment"

# Push to GitHub
git push origin main
```

### 2. Verify Repository Structure

Key files that must exist:
- ✅ `ui/streamlit_app.py` - Main Streamlit app
- ✅ `ui/requirements.txt` - Python dependencies (minimal for UI)
- ✅ `ui/.streamlit/config.toml` - Streamlit configuration
- ✅ `ui/.streamlit/secrets.toml.example` - Secrets template
- ✅ `ui/api_client.py` - API client for Cloud Run

## 🚀 Deployment Steps

### Step 1: Create Streamlit Community Cloud Account

1. Go to https://share.streamlit.io
2. Sign in with your GitHub account
3. Authorize Streamlit to access your repositories

### Step 2: Create New App

1. Click **"New app"** button
2. Fill in the deployment form:
   - **Repository**: Select `hotchilianalytics/verityngn-oss`
   - **Branch**: `main`
   - **Main file path**: `ui/streamlit_app.py`
   - **App URL** (optional): `verityngn` or your preferred name
3. Click **"Deploy"**

### Step 3: Configure Secrets

After deployment starts (or if it fails due to missing secrets):

1. Click your app name in the dashboard
2. Click **⚙️ Settings** (gear icon, bottom left)
3. Click **"Secrets"** tab
4. Add this configuration:

```toml
# Cloud Run API URL (REQUIRED)
CLOUDRUN_API_URL = "https://verityngn-api-ze7rxua3dq-uc.a.run.app"
```

5. Click **"Save"**
6. The app will automatically restart with new secrets

### Step 4: Monitor Deployment

1. Watch the deployment logs in Streamlit Cloud dashboard
2. Look for:
   - ✅ Package installation progress
   - ✅ App startup messages
   - ❌ Any import errors or missing dependencies

**Expected deployment time**: ~3-5 minutes

### Step 5: Verify Deployment

1. **Open your app URL**: `https://verityngn.streamlit.app` (or your chosen URL)
2. **Check sidebar**:
   - ✅ Backend mode selector appears
   - ✅ "☁️ Cloud Run + Batch" option available
3. **Test API connection**:
   - Select "☁️ Cloud Run + Batch" mode
   - Navigate to "⚙️ Processing" tab
   - Verify API health check passes
4. **Test Gallery**:
   - Navigate to "🖼️ Gallery" tab
   - Verify videos load from GCS
   - Check that reports have HTTPS signed URLs

## 🧪 Testing Checklist

### Basic Functionality
- [ ] App loads without errors
- [ ] Sidebar displays correctly
- [ ] All navigation tabs visible
- [ ] Backend mode selector works

### ✅ Quick Release Checklist

For a tighter, copy/paste checklist, see:
- `docs/deployment/STREAMLIT_COMMUNITY_CLOUD_CHECKLIST.md`

### Cloud Run Mode
- [ ] API health check passes
- [ ] Gallery loads videos from GCS
- [ ] Report URLs are HTTPS signed URLs (not `gs://`)
- [ ] Can view reports in gallery

### End-to-End Flow
- [ ] Submit single video via "Verify Video" tab
- [ ] Video processing completes successfully
- [ ] Results appear in gallery automatically
- [ ] Can view report for processed video

### Batch Processing
- [ ] Submit batch job via API
- [ ] All videos process successfully
- [ ] All results appear in gallery
- [ ] Gallery pagination works

## 🔧 Troubleshooting

### App Won't Deploy

**Issue**: Build fails with import errors

**Solution**:
- Check `ui/requirements.txt` includes all dependencies
- Verify Python version compatibility (Streamlit Cloud uses Python 3.11)
- Check deployment logs for specific missing packages

### Gallery Not Loading

**Issue**: Gallery shows "No videos found" or error

**Solutions**:
1. **Check CLOUDRUN_API_URL**: Verify it's set correctly in secrets
2. **Test API directly**: `curl https://verityngn-api-ze7rxua3dq-uc.a.run.app/api/v1/batch/gallery/list`
3. **Check backend mode**: Ensure "Cloud Run + Batch" is selected
4. **Check logs**: Look for API connection errors

### Reports Not Viewable

**Issue**: Report links don't work or show `gs://` paths

**Solution**:
- ✅ Already fixed! Signed URLs now generate HTTPS URLs
- If still seeing `gs://`, check Cloud Run service account has `iam.serviceAccountTokenCreator` role
- Verify Cloud Run service is using latest revision

### API Connection Errors

**Issue**: "Cannot connect to API" or timeout errors

**Solutions**:
1. **Check API URL**: Verify `CLOUDRUN_API_URL` in secrets
2. **Test API health**: `curl https://verityngn-api-ze7rxua3dq-uc.a.run.app/health`
3. **Cold start**: First request may take 30-60 seconds
4. **CORS**: Cloud Run API has CORS enabled (already configured)

## 📊 Architecture

```
┌─────────────────────────────────────┐
│  Streamlit Community Cloud          │
│  (share.streamlit.io)                │
│  ┌───────────────────────────────┐  │
│  │  Streamlit UI                 │  │
│  │  (ui/streamlit_app.py)        │  │
│  └───────────┬───────────────────┘  │
└──────────────┼──────────────────────┘
               │ HTTPS API Calls
               ▼
┌─────────────────────────────────────┐
│  Cloud Run API                      │
│  (verityngn-api-*.run.app)         │
│  ┌───────────────────────────────┐  │
│  │  FastAPI Service             │  │
│  │  - Verification endpoints    │  │
│  │  - Batch job management     │  │
│  │  - Gallery API               │  │
│  └───────────┬───────────────────┘  │
└──────────────┼──────────────────────┘
               │ Submit Jobs
               ▼
┌─────────────────────────────────────┐
│  Google Cloud Batch                 │
│  (Video Processing)                 │
└───────────┬─────────────────────────┘
            │ Store Results
            ▼
┌─────────────────────────────────────┐
│  Google Cloud Storage                │
│  (verityindex_bucket)               │
│  └─ vngn_reports/                   │
│     └─ {video_id}/                  │
│        └─ {timestamp}_processing/   │
│           ├─ {video_id}_report.html │
│           ├─ {video_id}_report.json │
│           └─ {video_id}_report.md   │
└─────────────────────────────────────┘
```

## ✅ Success Criteria

- [x] App deploys without errors
- [x] Backend mode selector works
- [x] Gallery loads videos from GCS
- [x] Reports are viewable via HTTPS signed URLs
- [x] End-to-end flow works: submit → process → gallery
- [x] All processed videos appear in gallery automatically

## 📝 Next Steps After Deployment

1. **Monitor Usage**: Track Cloud Run costs and usage
2. **User Testing**: Get feedback on UI/UX
3. **Performance**: Monitor API response times
4. **Scaling**: Adjust Cloud Run concurrency if needed
5. **Documentation**: Update user-facing docs

## 🔗 Useful Links

- **Streamlit Community Cloud**: https://share.streamlit.io
- **Cloud Run Console**: https://console.cloud.google.com/run
- **GCS Bucket**: https://console.cloud.google.com/storage/browser/verityindex_bucket
- **API Health Check**: https://verityngn-api-ze7rxua3dq-uc.a.run.app/health
- **Gallery API**: https://verityngn-api-ze7rxua3dq-uc.a.run.app/api/v1/batch/gallery/list

