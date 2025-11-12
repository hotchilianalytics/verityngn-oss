# 🧪 Testing Your ngrok Tunnel

**Your ngrok URL:** `https://oriented-flea-large.ngrok-free.app`

---

## 🌐 Test 1: Browser Test (Easiest)

### Health Check

Open this URL in your browser:
```
https://oriented-flea-large.ngrok-free.app/health
```

**Expected:** `{"status":"healthy"}`

**Note:** Free ngrok plan may show a warning page first - just click **"Visit Site"**

---

### API Documentation

View interactive API docs:
```
https://oriented-flea-large.ngrok-free.app/docs
```

This gives you a web interface to test all endpoints!

---

## 💻 Test 2: Command Line Tests

### Health Check

```bash
curl https://oriented-flea-large.ngrok-free.app/health
```

**Expected output:**
```json
{"status":"healthy"}
```

---

### List Available Reports

```bash
curl https://oriented-flea-large.ngrok-free.app/api/v1/reports/list
```

**Expected output:**
```json
{
  "reports": [
    {
      "video_id": "tLJC8hkK-ao",
      "title": "LIPOZEM...",
      "created_at": "...",
      "formats": ["html", "json", "md"]
    }
  ]
}
```

---

### Get a Specific Report (if you have one)

```bash
# Replace VIDEO_ID with actual video ID (e.g., tLJC8hkK-ao)
curl https://oriented-flea-large.ngrok-free.app/api/v1/reports/tLJC8hkK-ao/report.json | jq .
```

---

### Submit a Verification Task

```bash
# Submit a video for verification
curl -X POST https://oriented-flea-large.ngrok-free.app/api/v1/verification/verify \
  -H "Content-Type: application/json" \
  -d '{"video_url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ"}' \
  | jq .
```

**Expected output:**
```json
{
  "task_id": "abc-123-def-456",
  "status": "processing",
  "message": "Verification task submitted"
}
```

---

### Check Task Status

```bash
# Replace TASK_ID with the actual task ID from above
curl https://oriented-flea-large.ngrok-free.app/api/v1/verification/status/TASK_ID | jq .
```

**Expected output:**
```json
{
  "task_id": "abc-123-def-456",
  "status": "processing",
  "progress": 0.3,
  "message": "Analyzing video content..."
}
```

---

## 🐍 Test 3: Python Script

Save this as `test_ngrok.py`:

```python
#!/usr/bin/env python3
import requests
import json
import time

# Your ngrok URL
API_URL = "https://oriented-flea-large.ngrok-free.app"

print("🧪 Testing VerityNgn API via ngrok")
print("="*60)

# Test 1: Health Check
print("\n1️⃣ Testing health endpoint...")
try:
    response = requests.get(f"{API_URL}/health", timeout=10)
    if response.status_code == 200:
        print(f"   ✅ API is healthy: {response.json()}")
    else:
        print(f"   ❌ Error: {response.status_code}")
except Exception as e:
    print(f"   ❌ Connection error: {e}")
    print(f"   💡 If using free ngrok, visit {API_URL} in browser first")
    exit(1)

# Test 2: List Reports
print("\n2️⃣ Listing available reports...")
try:
    response = requests.get(f"{API_URL}/api/v1/reports/list", timeout=10)
    if response.status_code == 200:
        reports = response.json().get("reports", [])
        print(f"   ✅ Found {len(reports)} report(s)")
        for report in reports[:3]:  # Show first 3
            print(f"      - {report.get('video_id')}: {report.get('title', 'N/A')[:50]}")
    else:
        print(f"   ⚠️  Status: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Submit Verification (optional - comment out if you don't want to run)
print("\n3️⃣ Testing verification submission (skipped - uncomment to test)")
# Uncomment below to actually submit a verification:
"""
try:
    video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    print(f"   Submitting: {video_url}")
    response = requests.post(
        f"{API_URL}/api/v1/verification/verify",
        json={"video_url": video_url},
        timeout=10
    )
    if response.status_code == 200:
        task_data = response.json()
        task_id = task_data.get("task_id")
        print(f"   ✅ Task submitted: {task_id}")
        
        # Check status
        print(f"   Checking status...")
        status_response = requests.get(f"{API_URL}/api/v1/verification/status/{task_id}")
        print(f"   Status: {status_response.json()}")
    else:
        print(f"   ❌ Error: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")
"""

print("\n" + "="*60)
print("✅ Testing complete!")
print(f"\n🌐 View API docs: {API_URL}/docs")
print(f"🔍 Monitor tunnel: http://localhost:4040")

