# VerityNgn Local Testing Guide

## 🎯 Quick Test

Your Streamlit UI should now be open at: **http://localhost:8501**

## ✅ What to Test

### 1. UI Loads Correctly
- [ ] Streamlit interface appears
- [ ] No error messages on page load
- [ ] Tabs are visible (Video Input, Processing, View Reports, etc.)

### 2. API Connection Test
The UI is configured to connect to the API at: `http://api:8080` (internal Docker network)

From your browser, the API is available at: `http://localhost:8080`

### 3. Basic Workflow Test

#### Option A: Quick Test (Recommended)
Use a short YouTube video (< 2 minutes):
```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

#### Option B: Real Test
Use any YouTube video you want to verify.

### 4. Test Steps

1. **Enter Video URL**
   - Go to "Video Input" tab
   - Paste YouTube URL
   - Click "Submit" or similar button

2. **Monitor Processing**
   - Go to "Processing Status" tab
   - Watch for log messages
   - Check task ID appears
   - Monitor progress updates

3. **Expected Behavior**
   - ✅ Task submitted successfully
   - ✅ Task ID displayed
   - ✅ Status updates appear
   - ✅ Progress percentage increases
   - ✅ Logs show workflow stages

4. **View Results** (when complete)
   - Go to "View Reports" tab
   - Report should be listed
   - Click to view HTML report
   - Check that claim links work

## 🐛 Troubleshooting

### UI Won't Load
```bash
# Check UI logs
docker compose logs ui

# Restart UI
docker compose restart ui
```

### API Connection Error
```bash
# Check API is running
curl http://localhost:8080/health

# Check UI can reach API (from inside container)
docker exec verityngn-streamlit curl http://api:8080/health
```

### Processing Hangs
```bash
# Check API logs
docker compose logs -f api

# Check for errors
docker compose logs api | grep -i error
```

## 📊 Monitoring Commands

### Watch Both Services
```bash
# Terminal 1: API logs
docker compose logs -f api

# Terminal 2: UI logs
docker compose logs -f ui

# Terminal 3: Overall status
watch -n 5 'docker compose ps'
```

### Check Resource Usage
```bash
docker stats verityngn-api verityngn-streamlit
```

## ✅ Success Criteria

### Minimal Success (MVP Test Passed)
- [ ] UI loads without errors
- [ ] Can enter YouTube URL
- [ ] Task submits to API
- [ ] Status updates appear
- [ ] No crashes or hangs

### Full Success (Production Ready)
- [ ] Verification completes successfully
- [ ] Report generates correctly
- [ ] Report links work (relative paths)
- [ ] Can view claim sources
- [ ] Can view counter-intelligence reports

## 🎯 Test Results Checklist

After testing, verify:
- [ ] API responded correctly
- [ ] UI displayed results
- [ ] No errors in logs
- [ ] Report is readable
- [ ] Links are functional

## 📝 Notes

**Current Configuration:**
- API URL (internal): `http://api:8080`
- API URL (external): `http://localhost:8080`
- UI URL: `http://localhost:8501`
- API Key: Check `.env` or `docker-compose.yml`

**Test Video Recommendations:**
- Short videos (< 5 min) for quick testing
- Videos with clear claims for verification testing
- Public videos only (no private/unlisted)

## 🚀 Next Steps After Successful Test

1. ✅ Local deployment verified
2. 🔄 Test Colab notebook
3. 🌐 Deploy to Cloud Run
4. 📊 Test production deployment
5. 🎉 Ready for users!

---

**Last Updated**: November 5, 2025  
**Status**: Ready for testing




