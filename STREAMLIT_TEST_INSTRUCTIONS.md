# Streamlit Cloud Run Mode - Local Test Instructions

## 🚀 Streamlit is Starting

The Streamlit app should be launching now. Follow these steps to test Cloud Run mode:

## Test Steps

### 1. Open Browser
- Navigate to: **http://localhost:8501**
- The Streamlit app should load

### 2. Check Backend Mode Selector
- Look at the **sidebar** (left side)
- You should see a section titled **"🔌 Backend Mode"**
- There should be a radio button with two options:
  - 🏠 Local (OSS)
  - ☁️ Cloud Run + Batch

### 3. Select Cloud Run Mode
- Click on **"☁️ Cloud Run + Batch"**
- You should see a caption showing the API URL (truncated)
- If you see a warning "⚠️ Set CLOUDRUN_API_URL env var", the environment variable wasn't set correctly

### 4. Test Single Video Submission
- Go to the **"🎬 Verify Video"** tab (should be selected by default)
- Enter a YouTube URL, for example:
  ```
  https://www.youtube.com/watch?v=jNQXAC9IVRw
  ```
- Click **"Start Verification"**
- You should see: "✅ Verification started! Switch to Processing tab to monitor progress."

### 5. Monitor Status
- Switch to the **"⚙️ Processing"** tab
- You should see:
  - "🚀 Submitting verification request to API..."
  - API health check (should show "✅ API is healthy")
  - Task submission confirmation with a task_id
  - Status updates showing progress

### 6. Verify Status Updates
- The Processing tab should poll the API and show:
  - Current status (processing/completed/failed)
  - Progress percentage
  - Current stage (e.g., "Downloading video...", "Analyzing...")

## Expected Behavior

### ✅ Success Indicators:
- Backend mode selector appears in sidebar
- Can switch between Local and Cloud Run modes
- Cloud Run mode shows API URL
- Single video submission works
- Status updates appear in Processing tab
- API health check passes

### ⚠️ Troubleshooting:

**If backend mode selector doesn't appear:**
- Check browser console for errors
- Verify Streamlit app loaded completely
- Try refreshing the page

**If Cloud Run mode shows warning:**
- The environment variable wasn't set
- Check terminal output for errors
- Restart Streamlit with: `export CLOUDRUN_API_URL="https://verityngn-api-ze7rxua3dq-uc.a.run.app"`

**If API health check fails:**
- Verify Cloud Run service is running
- Check the API URL is correct
- Test API directly: `curl https://verityngn-api-ze7rxua3dq-uc.a.run.app/health`

**If submission fails:**
- Check Processing tab for error messages
- Verify video URL is valid
- Check Cloud Run service logs

## Test Results

After testing, note:
- [ ] Backend mode selector works
- [ ] Can switch to Cloud Run mode
- [ ] Single video submission works
- [ ] Status monitoring works
- [ ] Results are accessible

## Next Steps

Once local testing passes:
1. Add `CLOUDRUN_API_URL` to Streamlit Community secrets
2. Deploy to Streamlit Cloud
3. Test in production environment

