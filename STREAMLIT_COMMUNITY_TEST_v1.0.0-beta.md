# Streamlit Community Deployment Test - v1.0.0-beta

**Release:** v1.0.0-beta  
**Date:** 2025-11-13  
**Status:** Ready for Testing

## ✅ Pre-Deployment Checklist

- [x] Code pushed to GitHub (`hotchilianalytics/verityngn-oss`)
- [x] Tag `v1.0.0-beta` created and pushed
- [x] Cloud Run API verified running: `https://verityngn-api-ze7rxua3dq-uc.a.run.app`
- [x] Health check passed
- [x] New channel selector feature included

## 🚀 Deployment Steps

### Step 1: Deploy to Streamlit Community Cloud

1. **Go to:** https://share.streamlit.io
2. **Sign in** with GitHub account (`hotchilianalytics`)
3. **Click:** "New app" or select existing app
4. **Configure:**
   - **Repository:** `hotchilianalytics/verityngn-oss`
   - **Branch:** `main` (or `v1.0.0-beta` tag)
   - **Main file path:** `ui/streamlit_app.py`
   - **App URL:** `verityngn` (or your choice)

### Step 2: Configure Secrets

After deployment starts, configure secrets:

1. Click your app name
2. Click ⚙️ **Settings** (gear icon)
3. Click **"Secrets"** tab
4. Add this configuration:

```toml
# Cloud Run API URL (REQUIRED)
CLOUDRUN_API_URL = "https://verityngn-api-ze7rxua3dq-uc.a.run.app"
```

5. Click **"Save"**
6. App will automatically restart

## 🧪 Testing Checklist

### Test 1: Basic App Load
- [ ] App loads without errors
- [ ] No import errors in logs
- [ ] UI renders correctly

### Test 2: Backend Mode Selector
- [ ] Sidebar shows "🔌 Backend Mode" section
- [ ] Can select "☁️ Cloud Run + Batch" mode
- [ ] API health check shows "✅ API is healthy"
- [ ] API URL displays correctly

### Test 3: Channel Selector Feature (NEW!)
- [ ] "📺 Select from Channel" section appears
- [ ] Channel URL input field works
- [ ] Enter channel: `https://www.youtube.com/@NextMedHealth`
- [ ] Videos load (shows spinner, then success)
- [ ] Dropdown shows videos with titles, dates, views
- [ ] Can select a video from dropdown
- [ ] Selected video populates "YouTube Video URL" field
- [ ] Video URL validates correctly

### Test 4: Direct Video URL (Regression Test)
- [ ] "🎬 Or Enter Video URL Directly" section works
- [ ] Can enter direct video URL
- [ ] URL validation works
- [ ] No regression from previous functionality

### Test 5: Example Buttons Removed
- [ ] "Load Example 1" button is removed
- [ ] "Load Example 2" button is removed
- [ ] Tips section appears instead

### Test 6: Video Verification Flow
- [ ] Select video (from channel or direct URL)
- [ ] Click "🚀 Start Verification"
- [ ] Switches to Processing tab
- [ ] Task submitted successfully
- [ ] Status updates appear
- [ ] Can monitor progress

### Test 7: Gallery Tab
- [ ] Gallery tab loads
- [ ] Videos load from GCS
- [ ] Can view reports
- [ ] Links work correctly

## 🐛 Known Issues to Watch For

### Channel Selector
- **API Quota:** If YouTube API quota exceeded, should fallback to yt-dlp
- **Slow Loading:** First channel load may take 5-10 seconds
- **Invalid Channels:** Should show clear error messages

### General
- **Cold Start:** First request after inactivity may be slow
- **API Timeout:** Cloud Run may timeout on long operations

## 📊 Expected Behavior

### Channel Selector
1. User enters channel URL
2. Spinner appears: "Fetching channel videos..."
3. Success message: "✅ Found X videos"
4. Dropdown appears with video list
5. User selects video
6. Video URL field populates
7. Can proceed with verification

### Error Handling
- Invalid URL: Shows "❌ Invalid channel URL format"
- Channel not found: Shows "Channel not found" or "No videos found"
- API failure: Falls back to yt-dlp automatically

## 🔍 Debugging

### Check Logs
1. In Streamlit Cloud dashboard
2. Click your app
3. View "Logs" tab
4. Look for errors or warnings

### Common Issues

**"Module not found"**
- Check `ui/requirements.txt` includes all dependencies
- Verify Python version compatibility

**"Cannot connect to API"**
- Verify `CLOUDRUN_API_URL` in secrets
- Test API directly: `curl https://verityngn-api-ze7rxua3dq-uc.a.run.app/health`
- Check Cloud Run service is running

**"Channel videos not loading"**
- Check YouTube API key (if configured)
- Verify channel URL format
- Check logs for API errors
- Should fallback to yt-dlp if API fails

## ✅ Success Criteria

- [ ] App deploys successfully
- [ ] All UI components render
- [ ] Channel selector feature works
- [ ] Video verification flow works
- [ ] No regressions in existing features
- [ ] Error handling works correctly

## 📝 Test Results

**Tester:** _______________  
**Date:** _______________  
**App URL:** _______________  

### Results
- [ ] All tests passed
- [ ] Some issues found (see notes below)
- [ ] Critical issues found

### Notes:
_________________________________________________
_________________________________________________
_________________________________________________

## 🎯 Next Steps

After successful testing:
1. Document any issues found
2. Create GitHub issues for bugs
3. Update release notes if needed
4. Announce beta release
5. Gather user feedback

---

**Ready to test!** Deploy at https://share.streamlit.io 🚀

