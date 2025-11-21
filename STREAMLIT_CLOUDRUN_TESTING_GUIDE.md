# Streamlit Cloud Run Mode Testing Guide

## Current Status: ✅ Ready for Testing

The Streamlit UI has been updated with Cloud Run mode support. Here's what's implemented:

### ✅ Implemented Features

1. **Backend Mode Selector** - Radio button in sidebar to switch between Local and Cloud Run modes
2. **API Client** - Supports Cloud Run URLs via `CLOUDRUN_API_URL` environment variable
3. **Processing Tab Routing** - Automatically routes to correct component based on backend mode
4. **Single Video Submission** - Works in both modes
5. **Status Monitoring** - Polls API for task status updates

### ⚠️ Missing Features (for batch)

- **Batch Submission UI** - No UI component yet for submitting multiple videos at once
- Currently, batch submission must be done via API directly

## Testing Options

### Option 1: Test Locally First (Recommended)

**Pros:**
- Faster iteration
- Easier debugging
- No deployment overhead
- Can test both modes side-by-side

**Cons:**
- Need to set up local environment
- Need to configure CLOUDRUN_API_URL

**Steps:**

1. **Set up environment variable:**
   ```bash
   export CLOUDRUN_API_URL="https://verityngn-api-ze7rxua3dq-uc.a.run.app"
   ```

2. **Or add to `.env` file:**
   ```bash
   echo "CLOUDRUN_API_URL=https://verityngn-api-ze7rxua3dq-uc.a.run.app" >> .env
   ```

3. **Run Streamlit locally:**
   ```bash
   cd /Users/ajjc/proj/verityngn-oss/ui
   streamlit run streamlit_app.py
   ```

4. **Test Cloud Run mode:**
   - Open sidebar
   - Select "☁️ Cloud Run + Batch" mode
   - Enter a YouTube URL
   - Click "Start Verification"
   - Switch to Processing tab to monitor

### Option 2: Test via Streamlit Community App

**Pros:**
- Real production environment
- Public access testing
- No local setup needed

**Cons:**
- Slower iteration
- Harder to debug
- Requires deployment

**Steps:**

1. **Configure Streamlit Secrets:**
   - Go to Streamlit Cloud dashboard
   - Add secret: `CLOUDRUN_API_URL = "https://verityngn-api-ze7rxua3dq-uc.a.run.app"`

2. **Deploy/Update app:**
   - Push to GitHub
   - Streamlit Cloud will auto-deploy

3. **Test in browser:**
   - Open Streamlit Community app
   - Select Cloud Run mode
   - Submit videos

## Recommended Testing Flow

### Phase 1: Local Testing (Do This First)

1. **Test Single Video in Cloud Run Mode:**
   ```bash
   # Set environment variable
   export CLOUDRUN_API_URL="https://verityngn-api-ze7rxua3dq-uc.a.run.app"
   
   # Run Streamlit
   cd ui && streamlit run streamlit_app.py
   ```

2. **Verify:**
   - Backend mode selector appears in sidebar
   - Can switch to Cloud Run mode
   - Single video submission works
   - Status updates appear in Processing tab
   - Results are accessible

3. **Test Mode Switching:**
   - Switch between Local and Cloud Run modes
   - Verify each mode works independently
   - Check that API client reinitializes correctly

### Phase 2: Streamlit Community Deployment

Once local testing passes:

1. **Add Cloud Run URL to Streamlit Secrets:**
   ```
   CLOUDRUN_API_URL = "https://verityngn-api-ze7rxua3dq-uc.a.run.app"
   ```

2. **Deploy to Streamlit Cloud:**
   - Push changes to GitHub
   - Streamlit Cloud auto-deploys

3. **Test in Production:**
   - Open public Streamlit app
   - Test Cloud Run mode
   - Verify public users can submit videos

## Current Limitations

### Batch Submission UI Not Yet Implemented

The UI currently supports:
- ✅ Single video submission (both modes)
- ❌ Batch submission UI (must use API directly)

**To submit batch jobs, use the API directly:**
```bash
curl -X POST "https://verityngn-api-ze7rxua3dq-uc.a.run.app/api/v1/batch/submit" \
  -H "Content-Type: application/json" \
  -d '{"video_urls": ["url1", "url2"], "parallelism": 1}'
```

**Future Enhancement:** Add batch submission UI component

## Quick Test Checklist

### Local Testing
- [ ] Set `CLOUDRUN_API_URL` environment variable
- [ ] Run Streamlit locally
- [ ] Verify backend mode selector appears
- [ ] Switch to Cloud Run mode
- [ ] Submit single video
- [ ] Monitor status in Processing tab
- [ ] Verify results are accessible

### Streamlit Community Testing
- [ ] Add `CLOUDRUN_API_URL` to Streamlit secrets
- [ ] Deploy to Streamlit Cloud
- [ ] Open public app
- [ ] Test Cloud Run mode
- [ ] Verify public access works

## Troubleshooting

### "Cloud Run mode selected but CLOUDRUN_API_URL not set!"
- **Solution:** Set environment variable or add to Streamlit secrets

### "API is not accessible"
- **Solution:** Check Cloud Run service is running and URL is correct

### "Backend mode not available"
- **Solution:** Ensure `processing_api.py` component is available

## Next Steps

1. **Test locally first** - Verify everything works before deploying
2. **Add batch UI** - Create UI component for batch submission
3. **Deploy to Streamlit Cloud** - Once local testing passes
4. **Monitor production** - Check logs and user feedback

