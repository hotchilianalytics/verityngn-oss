# VerityNgn UI Testing Instructions

## ✅ Status: Ready for Testing!

Both services are running and the 404 error has been fixed!

## 🚀 Access Points

- **Streamlit UI**: http://localhost:8501
- **API Backend**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs

## 📋 Quick Test

### Step 1: Open the UI
The browser should already be open at http://localhost:8501

If not, run:
```bash
open http://localhost:8501
```

### Step 2: Submit a Video for Verification

**Test Video URL (short, recommended)**:
```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

**Or your original URL**:
```
https://www.youtube.com/watch?v=sbChYUijRKE
```

### Step 3: What Should Happen

1. **Enter URL** in the video input field
2. **Click Submit** (or equivalent button)
3. **No more 404 error!** ✅
4. **Task ID** should appear (e.g., `9a9e53b9-eeee-41e4-b40d-de21f434529f`)
5. **Status updates** should show in real-time:
   - "Submitting verification request..."
   - "Task submitted successfully!"
   - "Monitoring task status..."
   - "Status: processing (0-100%) - [messages]"
6. **Progress bar** should update
7. **Logs** should appear in the processing tab

### Step 4: Monitor Progress

Go to the "Processing Status" tab and watch:
- Real-time log updates
- Progress bar moving from 0% to 100%
- Status messages:
  - "Downloading video..."
  - "Analyzing content..."
  - "Verifying claims..."
  - "Generating report..."

### Step 5: View Report

Once complete (status: "completed"):
1. Go to "View Reports" tab
2. Click on the report for your video
3. Verify that:
   - HTML report loads
   - Links to claim sources work
   - Video embed displays
   - All sections render correctly

## 🔍 Troubleshooting

### If you still see auth errors:
The credentials should now be properly mounted. Refresh the page.

### If you see 404 errors:
The verification endpoint has been added. The services should be working.

### If the UI is slow:
The first verification takes longer because:
- Video needs to be downloaded
- Multimodal analysis is running
- Web searches are happening
- Multiple LLM calls are being made

**Expected time for a 2-minute video**: 2-5 minutes  
**Expected time for a 10-minute video**: 5-15 minutes

### Check Service Status

```bash
# View all containers
docker compose ps

# Check API logs
docker logs verityngn-api --tail 50

# Check UI logs
docker logs verityngn-streamlit --tail 50

# Check API health
curl http://localhost:8080/health

# Check UI health
curl http://localhost:8501/_stcore/health
```

## 🧪 Manual API Testing (Optional)

If you want to test the API directly:

### Submit a task:
```bash
curl -X POST http://localhost:8080/api/v1/verification/verify \
  -H "Content-Type: application/json" \
  -d '{"video_url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

### Check status (replace TASK_ID):
```bash
curl http://localhost:8080/api/v1/verification/status/TASK_ID
```

### List all tasks:
```bash
curl http://localhost:8080/api/v1/verification/tasks
```

## ✅ Success Indicators

- [ ] UI loads without authentication errors
- [ ] Can submit video URL
- [ ] Receives task ID (no 404)
- [ ] Status updates appear in real-time
- [ ] Progress bar moves
- [ ] Logs show workflow steps
- [ ] Report appears when complete
- [ ] Report links work

## 🎯 What to Look For

1. **No 404 errors** when submitting
2. **Task ID** is returned immediately
3. **Status updates** every few seconds
4. **Progress bar** increments
5. **Logs** show detailed workflow steps
6. **Complete status** when finished
7. **Report available** in reports tab

## 📞 Need Help?

If something isn't working:
1. Check the logs (see troubleshooting section)
2. Verify both containers are healthy: `docker compose ps`
3. Restart if needed: `docker compose restart`

## 🎉 You're All Set!

The MVP is ready for testing. Try submitting a video and watch the magic happen!




