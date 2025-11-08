# VerityNgn Google Colab Demo - WITH NGROK

This notebook demonstrates how to use VerityNgn API through an ngrok tunnel to your local API.

## 🚀 Quick Start

### 1. Configure API URL

```python
# Your ngrok tunnel URL
API_URL = "https://oriented-flea-large.ngrok-free.app"

# Or use environment variable
import os
API_URL = os.getenv("VERITYNGN_API_URL", "https://oriented-flea-large.ngrok-free.app")
```

### 2. Test Connection

```python
import requests

# Test API health
response = requests.get(f"{API_URL}/health")
print(f"API Status: {response.json()}")
# Should print: API Status: {'status': 'healthy'}
```

### 3. Submit a Verification

```python
import requests
import time
import json

# Video to verify
video_url = "https://www.youtube.com/watch?v=tLJC8hkK-ao"

# Submit verification task
print(f"🚀 Submitting video for verification...")
response = requests.post(
    f"{API_URL}/api/v1/verification/verify",
    json={"video_url": video_url}
)

if response.status_code == 200:
    task_data = response.json()
    task_id = task_data["task_id"]
    print(f"✅ Task submitted successfully!")
    print(f"📋 Task ID: {task_id}")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
    task_id = None
```

### 4. Monitor Progress

```python
if task_id:
    print("\n⏳ Monitoring verification progress...")
    
    while True:
        # Check status
        status_response = requests.get(
            f"{API_URL}/api/v1/verification/status/{task_id}"
        )
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            status = status_data.get("status")
            progress = status_data.get("progress", 0)
            message = status_data.get("message", "Processing...")
            
            print(f"Status: {status} | Progress: {progress*100:.0f}% | {message}")
            
            if status == "completed":
                print("\n✅ Verification complete!")
                video_id = status_data.get("video_id")
                print(f"📊 Video ID: {video_id}")
                break
            elif status == "failed":
                print("\n❌ Verification failed!")
                print(f"Error: {status_data.get('error_message')}")
                break
        else:
            print(f"❌ Error checking status: {status_response.status_code}")
            break
        
        # Wait before checking again
        time.sleep(10)
```

### 5. Retrieve Report

```python
if video_id:
    # Get JSON report
    print("\n📄 Fetching report...")
    report_response = requests.get(
        f"{API_URL}/api/v1/reports/{video_id}/report.json"
    )
    
    if report_response.status_code == 200:
        report = report_response.json()
        
        print(f"\n{'='*60}")
        print(f"📊 VERIFICATION REPORT")
        print(f"{'='*60}")
        print(f"Video: {report.get('video_title')}")
        print(f"Channel: {report.get('channel_name')}")
        print(f"Duration: {report.get('duration_seconds')} seconds")
        print(f"\n📈 Truth Score: {report.get('truth_score', 0):.1f}/100")
        print(f"📊 Claims Analyzed: {len(report.get('claims', []))}")
        
        # Show claim breakdown
        claims = report.get('claims', [])
        if claims:
            print(f"\n🔍 Claims Summary:")
            true_count = sum(1 for c in claims if c.get('verdict') == 'TRUE')
            false_count = sum(1 for c in claims if c.get('verdict') == 'FALSE')
            uncertain_count = sum(1 for c in claims if c.get('verdict') == 'UNCERTAIN')
            
            print(f"  ✅ TRUE: {true_count}")
            print(f"  ❌ FALSE: {false_count}")
            print(f"  ❓ UNCERTAIN: {uncertain_count}")
            
            # Show first few claims
            print(f"\n📝 Sample Claims:")
            for i, claim in enumerate(claims[:3], 1):
                verdict = claim.get('verdict', 'UNKNOWN')
                claim_text = claim.get('claim_text', '')[:100]
                print(f"\n  {i}. {claim_text}...")
                print(f"     Verdict: {verdict}")
                print(f"     Confidence: {claim.get('confidence', 0):.1f}")
        
        print(f"\n{'='*60}")
    else:
        print(f"❌ Error fetching report: {report_response.status_code}")
```

### 6. View HTML Report (Optional)

```python
from IPython.display import IFrame, HTML

# Get HTML report
html_url = f"{API_URL}/api/v1/reports/{video_id}/report.html"
print(f"📄 HTML Report: {html_url}")

# Display in iframe (may not work with ngrok free plan due to headers)
display(HTML(f'<a href="{html_url}" target="_blank">Open Report in New Tab</a>'))
```

---

## 🎯 Complete Example (All in One Cell)

```python
import requests
import time
import json

# Configuration
API_URL = "https://oriented-flea-large.ngrok-free.app"
VIDEO_URL = "https://www.youtube.com/watch?v=tLJC8hkK-ao"

print("="*60)
print("VerityNgn Video Verification Demo")
print("="*60)

# 1. Test Connection
print("\n1️⃣ Testing API connection...")
health = requests.get(f"{API_URL}/health").json()
print(f"   Status: {health.get('status')} ✅")

# 2. Submit Verification
print("\n2️⃣ Submitting verification task...")
response = requests.post(
    f"{API_URL}/api/v1/verification/verify",
    json={"video_url": VIDEO_URL}
)
task_data = response.json()
task_id = task_data["task_id"]
print(f"   Task ID: {task_id} ✅")

# 3. Monitor Progress
print("\n3️⃣ Monitoring progress...")
while True:
    status_response = requests.get(f"{API_URL}/api/v1/verification/status/{task_id}")
    status_data = status_response.json()
    
    status = status_data.get("status")
    progress = status_data.get("progress", 0)
    message = status_data.get("message", "")
    
    print(f"   {status.upper()} | {progress*100:.0f}% | {message}")
    
    if status == "completed":
        video_id = status_data.get("video_id")
        print(f"\n✅ Complete! Video ID: {video_id}")
        break
    elif status == "failed":
        print(f"\n❌ Failed: {status_data.get('error_message')}")
        video_id = None
        break
    
    time.sleep(10)

# 4. Get Report
if video_id:
    print("\n4️⃣ Fetching report...")
    report = requests.get(f"{API_URL}/api/v1/reports/{video_id}/report.json").json()
    
    print(f"\n{'='*60}")
    print(f"📊 RESULTS")
    print(f"{'='*60}")
    print(f"Video: {report.get('video_title')}")
    print(f"Truth Score: {report.get('truth_score', 0):.1f}/100")
    print(f"Claims: {len(report.get('claims', []))}")
    print(f"\nHTML Report: {API_URL}/api/v1/reports/{video_id}/report.html")
    print(f"{'='*60}")
```

---

## 📋 API Endpoints Reference

```python
# Health check
GET {API_URL}/health

# Submit verification
POST {API_URL}/api/v1/verification/verify
Body: {"video_url": "https://youtube.com/watch?v=..."}

# Check status
GET {API_URL}/api/v1/verification/status/{task_id}

# List all reports
GET {API_URL}/api/v1/reports/list

# Get report (JSON)
GET {API_URL}/api/v1/reports/{video_id}/report.json

# Get report (HTML)
GET {API_URL}/api/v1/reports/{video_id}/report.html

# Get report (Markdown)
GET {API_URL}/api/v1/reports/{video_id}/report.md
```

---

## ⚠️ Important Notes

1. **ngrok URL Changes**: The URL `https://oriented-flea-large.ngrok-free.app` will change when ngrok restarts
2. **First Visit**: Free ngrok plan may show a warning page - click "Visit Site"
3. **Rate Limits**: Free plan has ~40 req/min limit
4. **Tunnel Must Be Running**: Keep the ngrok terminal window open
5. **Processing Time**: Video verification can take 10-20 minutes for long videos

---

## 🆘 Troubleshooting

### Connection Refused
- Check ngrok is still running
- Test local API: `curl http://localhost:8080/health`

### Timeout Errors
- Video processing takes time (10-20 min)
- Increase `time.sleep()` interval in monitoring loop

### Rate Limit Errors
- Wait 1-2 minutes
- Reduce polling frequency

---

## 📚 Resources

- **ngrok Active URL**: `NGROK_ACTIVE.md` in project root
- **API Documentation**: Visit `{API_URL}/docs` for interactive API docs
- **Monitor Tunnel**: http://localhost:4040 (on your local machine)

---

**Current ngrok URL:** https://oriented-flea-large.ngrok-free.app  
**Status:** 🟢 Active (remember to keep ngrok running!)

