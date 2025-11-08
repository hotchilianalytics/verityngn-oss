# 🧪 Complete ngrok Testing Guide

**Your Tunnel:** `https://oriented-flea-large.ngrok-free.app`

---

## ⚠️ Important: First Time Setup (Free ngrok)

If using free ngrok, you **must** visit the URL in a browser first:

1. **Open in browser:** https://oriented-flea-large.ngrok-free.app
2. **Click:** "Visit Site" on the ngrok warning page
3. **Now** API calls will work!

---

## 🌐 Quick Browser Tests

### 1. Health Check
```
https://oriented-flea-large.ngrok-free.app/health
```
Should show: `{"status":"healthy"}`

### 2. Interactive API Docs
```
https://oriented-flea-large.ngrok-free.app/docs
```
Full interactive API documentation with "Try it out" buttons!

### 3. List Reports
```
https://oriented-flea-large.ngrok-free.app/api/v1/reports/list
```

---

## 💻 Command Line Tests

### Basic Health Check
```bash
curl https://oriented-flea-large.ngrok-free.app/health
```

### Pretty JSON Output
```bash
curl -s https://oriented-flea-large.ngrok-free.app/health | jq .
```

### List All Reports
```bash
curl -s https://oriented-flea-large.ngrok-free.app/api/v1/reports/list | jq .
```

### Get Specific Report (if you have video ID)
```bash
curl -s https://oriented-flea-large.ngrok-free.app/api/v1/reports/tLJC8hkK-ao/report.json | jq . | head -50
```

### Submit New Verification
```bash
curl -X POST https://oriented-flea-large.ngrok-free.app/api/v1/verification/verify \
  -H "Content-Type: application/json" \
  -d '{"video_url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ"}' | jq .
```

### Check Verification Status
```bash
# Replace TASK_ID with actual ID from submission
curl -s https://oriented-flea-large.ngrok-free.app/api/v1/verification/status/TASK_ID | jq .
```

---

## 🐍 Python Test Script

I've created `test_ngrok.py` for you. Run it:

```bash
cd /Users/ajjc/proj/verityngn-oss
python test_ngrok.py
```

This will:
- ✅ Test health endpoint
- ✅ List available reports
- ✅ Show connection status

---

## 📱 Test from Other Devices

### From Your Phone

Open Safari/Chrome and visit:
```
https://oriented-flea-large.ngrok-free.app/docs
```

Click "Try it out" on any endpoint!

### From Another Computer

Same URL works from anywhere:
```
https://oriented-flea-large.ngrok-free.app
```

---

## 🔍 Monitor Traffic in Real-Time

### Local ngrok Web Interface

Open: **http://localhost:4040**

Shows:
- All incoming requests
- Request/response details
- Response times
- Error logs

### Example View:

```
GET /health              200 OK  12ms
POST /api/v1/verify      200 OK  150ms
GET /api/v1/status/...   200 OK  8ms
```

---

## 🧪 Full Test Workflow

### Step 1: Verify Connection
```bash
curl https://oriented-flea-large.ngrok-free.app/health
# Expected: {"status":"healthy"}
```

### Step 2: Check What Reports Exist
```bash
curl https://oriented-flea-large.ngrok-free.app/api/v1/reports/list | jq .
```

### Step 3: Submit a Test Video
```bash
curl -X POST https://oriented-flea-large.ngrok-free.app/api/v1/verification/verify \
  -H "Content-Type: application/json" \
  -d '{"video_url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ"}' | jq .
```

Save the `task_id` from the response.

### Step 4: Monitor Progress
```bash
# Replace YOUR_TASK_ID with actual ID
watch -n 10 'curl -s https://oriented-flea-large.ngrok-free.app/api/v1/verification/status/YOUR_TASK_ID | jq .'
```

### Step 5: Get Final Report
```bash
# Replace VIDEO_ID with the video ID from status response
curl -s https://oriented-flea-large.ngrok-free.app/api/v1/reports/VIDEO_ID/report.json | jq . > report.json

# View in browser
open https://oriented-flea-large.ngrok-free.app/api/v1/reports/VIDEO_ID/report.html
```

---

## 📊 Example: Complete Test Session

```bash
# 1. Check API is up
curl https://oriented-flea-large.ngrok-free.app/health

# 2. See available endpoints
open https://oriented-flea-large.ngrok-free.app/docs

# 3. List existing reports
curl https://oriented-flea-large.ngrok-free.app/api/v1/reports/list | jq .

# 4. Open monitoring dashboard (in another terminal)
open http://localhost:4040

# 5. Run Python test script
python test_ngrok.py
```

---

## 🆘 Troubleshooting

### "Connection refused" or timeout

**Solution:** Visit URL in browser first (free ngrok requires this)
```
https://oriented-flea-large.ngrok-free.app
```
Click "Visit Site" on the warning page.

---

### "curl: (77) error setting certificate verify locations"

**Solution:** Use `-k` flag (skip cert verification):
```bash
curl -k https://oriented-flea-large.ngrok-free.app/health
```

---

### "404 Not Found"

Check the API is actually running locally:
```bash
# Test local API first
curl http://localhost:8080/health

# Check Docker status
docker compose ps api
```

---

### ngrok tunnel disconnected

Check ngrok is still running:
```bash
# Look for ngrok process
ps aux | grep ngrok

# Check ngrok logs in terminal where you started it
```

---

## ✅ Expected Results

### Health Check
```json
{"status":"healthy"}
```

### List Reports (if you have reports)
```json
{
  "reports": [
    {
      "video_id": "tLJC8hkK-ao",
      "title": "[LIPOZEM] Exclusive Interview...",
      "created_at": "2025-11-07T19:04:35",
      "formats": ["html", "json", "md"],
      "path": "/app/outputs/tLJC8hkK-ao"
    }
  ],
  "total": 1
}
```

### Verification Submission
```json
{
  "task_id": "abc-123-def-456",
  "status": "processing",
  "video_url": "https://youtube.com/watch?v=...",
  "message": "Verification task submitted",
  "created_at": "2025-11-07T20:30:00"
}
```

---

## 📚 Quick Reference

```bash
# Test health
curl https://oriented-flea-large.ngrok-free.app/health

# View API docs
open https://oriented-flea-large.ngrok-free.app/docs

# Monitor traffic
open http://localhost:4040

# Run test script
python test_ngrok.py

# List reports
curl https://oriented-flea-large.ngrok-free.app/api/v1/reports/list | jq .
```

---

## 🎯 Next Steps After Testing

1. **If testing works:** Update your Streamlit/Colab with this URL
2. **To get persistent URL:** Reserve a domain in ngrok dashboard
3. **Monitor usage:** https://dashboard.ngrok.com
4. **Stop when done:** Press Ctrl+C in ngrok terminal

---

**Your Tunnel:** https://oriented-flea-large.ngrok-free.app  
**Monitor:** http://localhost:4040  
**Test Script:** `python test_ngrok.py`  
**API Docs:** https://oriented-flea-large.ngrok-free.app/docs

Start testing now! 🚀

