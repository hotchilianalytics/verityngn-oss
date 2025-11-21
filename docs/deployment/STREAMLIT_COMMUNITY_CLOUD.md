# Streamlit Community Cloud Deployment Guide

## Overview

This guide covers deploying the VerityNgn Streamlit UI to Streamlit Community Cloud with Cloud Run + Batch backend integration.

## Prerequisites

- GitHub account with `verityngn-oss` repository pushed
- Streamlit Community Cloud account (free at https://share.streamlit.io)
- Cloud Run API deployed and accessible
- GCS bucket with processed videos

## Step 1: Prepare Repository

Ensure all changes are committed and pushed:

```bash
cd /Users/ajjc/proj/verityngn-oss
git add .
git commit -m "Add GCS gallery integration and Streamlit Cloud config"
git push origin main
```

## Step 2: Deploy to Streamlit Community Cloud

1. **Go to Streamlit Community Cloud**:
   - Visit https://share.streamlit.io
   - Sign in with your GitHub account

2. **Create New App**:
   - Click "New app" button
   - Fill in the form:
     - **Repository**: `hotchilianalytics/verityngn-oss`
     - **Branch**: `main`
     - **Main file path**: `ui/streamlit_app.py`
     - **App URL** (optional): `verityngn` or your choice

3. **Click "Deploy"**

## Step 3: Configure Secrets

After deployment starts (or if it fails):

1. **Click your app name** in the dashboard
2. **Click ⚙️ Settings** (gear icon, bottom left)
3. **Click "Secrets" tab**
4. **Add this configuration**:

```toml
# Cloud Run API URL (REQUIRED)
CLOUDRUN_API_URL = "https://verityngn-api-ze7rxua3dq-uc.a.run.app"
```

5. **Click "Save"**
6. **App will automatically restart** with new secrets

## Step 4: Verify Deployment

1. **Wait for deployment** (~2-3 minutes)
2. **Open your app URL**: `https://verityngn.streamlit.app` (or your chosen URL)
3. **Check for errors** in the app logs
4. **Verify backend mode selector** appears in sidebar
5. **Test Cloud Run mode**:
   - Select "☁️ Cloud Run + Batch" mode
   - Verify API health check passes
   - Test gallery loads from GCS

## Step 5: Test Gallery Functionality

1. **Navigate to Gallery tab**
2. **Verify videos load from GCS**:
   - Should see videos from `vngn_reports/` directory
   - Each video should show title, score, claims count
3. **Test report viewing**:
   - Click "View Report" on a video
   - Verify HTML report displays (may need signed URL fix)
4. **Test filtering and search**:
   - Try category filter
   - Try search query
   - Verify sorting works

## Step 6: Test End-to-End Flow

1. **Submit a video**:
   - Go to "Verify Video" tab
   - Enter YouTube URL
   - Click "Start Verification"
   - Wait for batch job to complete

2. **Verify in Gallery**:
   - Go to Gallery tab
   - Verify new video appears automatically
   - Test report viewing

3. **Test Batch Processing**:
   - Submit multiple videos via batch
   - Verify all appear in gallery after completion

## Troubleshooting

### App Won't Deploy

- **Check requirements.txt**: Ensure all dependencies are listed
- **Check Python version**: Streamlit Cloud uses Python 3.11 by default
- **Check logs**: Look for import errors or missing dependencies

### Gallery Not Loading

- **Check CLOUDRUN_API_URL**: Verify it's set correctly in secrets
- **Check API health**: Test `https://verityngn-api-*.run.app/health`
- **Check backend mode**: Ensure "Cloud Run + Batch" is selected

### Reports Not Viewable

- **Signed URL Issue**: Currently returning `gs://` paths instead of HTTPS URLs
- **Fix**: Grant `roles/iam.serviceAccountTokenCreator` to Cloud Run service account
- **Workaround**: Reports can be accessed via GCS console or gsutil

### API Connection Errors

- **CORS Issues**: Cloud Run API should have CORS enabled (already configured)
- **Timeout Issues**: Increase timeout in `api_client.py` if needed
- **Cold Start**: First request may take 30-60 seconds

## Known Issues

### Signed URLs Returning gs:// Paths

**Problem**: Gallery API returns `gs://` paths instead of HTTPS signed URLs

**Root Cause**: Cloud Run service account missing `iam.serviceAccountTokenCreator` role

**Fix**:
```bash
gcloud projects add-iam-policy-binding verityindex-0-0-1 \
  --member="serviceAccount:verity-cloudrun-sa@verityindex-0-0-1.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountTokenCreator"
```

Then redeploy Cloud Run service.

## Architecture

```
Streamlit Community Cloud (share.streamlit.io)
  ↓ HTTPS
Cloud Run API (verityngn-api-*.run.app)
  ↓ API Calls
Google Cloud Batch (video processing)
  ↓ Results
GCS Bucket (verityindex_bucket/vngn_reports/)
  ↓ Gallery Display
Streamlit Gallery Tab (fetches from GCS via API)
```

## Success Criteria

- ✅ App deploys without errors
- ✅ Backend mode selector works
- ✅ Gallery loads videos from GCS
- ✅ Reports are viewable (after signed URL fix)
- ✅ End-to-end flow works: submit → process → gallery
- ✅ All processed videos appear in gallery automatically

## Next Steps

1. Fix signed URL generation (grant IAM role)
2. Test with real user submissions
3. Monitor Cloud Run costs
4. Set up monitoring and alerts
5. Document user-facing features

