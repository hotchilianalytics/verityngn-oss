# 🎉 ngrok Tunnel is Active!

## Your Public API URL

```
https://oriented-flea-large.ngrok-free.app
```

**Status:** ✅ Active and tunneling to your local API

---

## 🧪 Test Your Tunnel

### First Time Setup (ngrok Free Plan)

If using ngrok free plan, you may need to visit the URL in a browser first to accept the warning page. After that, API calls will work.

**Visit this URL in your browser:**
```
https://oriented-flea-large.ngrok-free.app
```

Click "Visit Site" on the ngrok warning page.

### Test the Health Endpoint

```bash
curl https://oriented-flea-large.ngrok-free.app/health
# Should return: &#123;"status":"healthy"&#125;
```

### Test List Reports

```bash
curl https://oriented-flea-large.ngrok-free.app/api/v1/reports/list
```

---

## 📱 Use with Streamlit Community Cloud

### Step 1: Add to Streamlit Secrets

In your Streamlit Community Cloud dashboard:

1. Go to your app settings
2. Click **Secrets**
3. Add this configuration:

```toml
# Streamlit Secrets
VERITYNGN_API_URL = "https://oriented-flea-large.ngrok-free.app"

[api]
url = "https://oriented-flea-large.ngrok-free.app"
base_url = "https://oriented-flea-large.ngrok-free.app"
```

### Step 2: Update Environment Variables (if needed)

If your app uses environment variables instead:

```bash
VERITYNGN_API_URL=https://oriented-flea-large.ngrok-free.app
API_URL=https://oriented-flea-large.ngrok-free.app
```

### Step 3: Restart Your App

After adding secrets, restart your Streamlit app for changes to take effect.

---

## 📓 Use with Google Colab

### Update Your Notebook

At the top of `notebooks/VerityNgn_Colab_Demo.ipynb`, change the API URL:

```python
# VerityNgn API Configuration
API_URL = "https://oriented-flea-large.ngrok-free.app"

# Verify connection
import requests
response = requests.get(f"&#123;API_URL&#125;/health")
print(f"API Status: &#123;response.json()&#125;")
```

### Example: Submit a Verification

```python
import requests
import json

# Your ngrok API URL
API_URL = "https://oriented-flea-large.ngrok-free.app"

# Submit a verification task
response = requests.post(
    f"&#123;API_URL&#125;/api/v1/verification/verify",
    json=&#123;"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"&#125;
)

task_data = response.json()
task_id = task_data["task_id"]
print(f"Task submitted: &#123;task_id&#125;")

# Check status
status_response = requests.get(
    f"&#123;API_URL&#125;/api/v1/verification/status/&#123;task_id&#125;"
)
print(f"Status: &#123;status_response.json()&#125;")
```

---

## 🖥️ Test from Command Line

### Submit a Verification Task

```bash
# Submit verification
curl -X POST https://oriented-flea-large.ngrok-free.app/api/v1/verification/verify \
  -H "Content-Type: application/json" \
  -d '&#123;"video_url":"https://www.youtube.com/watch?v=tLJC8hkK-ao"&#125;'

# Example response:
# &#123;"task_id":"abc-123-def","status":"processing"&#125;
```

### Check Task Status

```bash
# Replace TASK_ID with the actual task ID from above
curl https://oriented-flea-large.ngrok-free.app/api/v1/verification/status/TASK_ID
```

### Get a Report

```bash
# Replace VIDEO_ID with actual video ID (e.g., tLJC8hkK-ao)
curl https://oriented-flea-large.ngrok-free.app/api/v1/reports/VIDEO_ID/report.json
```

---

## 🔍 Monitor Traffic

### ngrok Web Interface

Open in your browser: **http://localhost:4040**

This shows:
- All requests in real-time
- Request/response details
- Timing information
- Error logs

**Tip:** Keep this open to debug issues!

---

## 📋 Copy-Paste Configurations

### For Python Scripts

```python
import os

# Set API URL
os.environ["VERITYNGN_API_URL"] = "https://oriented-flea-large.ngrok-free.app"

# Or use directly
API_URL = "https://oriented-flea-large.ngrok-free.app"
```

### For .env Files

```bash
VERITYNGN_API_URL=https://oriented-flea-large.ngrok-free.app
API_BASE_URL=https://oriented-flea-large.ngrok-free.app
```

### For Docker Compose (if running UI separately)

```yaml
environment:
  - VERITYNGN_API_URL=https://oriented-flea-large.ngrok-free.app
```

---

## ⚙️ Configuration Examples

### Streamlit UI (ui/streamlit_app.py)

If hardcoding in the app:

```python
# At the top of streamlit_app.py
import os

# Use ngrok URL
API_BASE_URL = os.getenv(
    "VERITYNGN_API_URL",
    "https://oriented-flea-large.ngrok-free.app"  # Your ngrok URL
)
```

### JavaScript/Fetch

```javascript
const API_URL = "https://oriented-flea-large.ngrok-free.app";

fetch(`$&#123;API_URL&#125;/health`)
  .then(response => response.json())
  .then(data => console.log("API Status:", data));
```

---

## ⚠️ Important Reminders

### Tunnel Behavior

1. **URL Expires**: This URL (`https://oriented-flea-large.ngrok-free.app`) will change when you restart ngrok
2. **Keep Running**: Keep the ngrok terminal window open
3. **Free Plan**: Has request rate limits (usually sufficient for testing)
4. **First Visit**: Free plan may show a warning page on first browser visit

### Security

1. **Public Access**: Anyone with this URL can access your local API
2. **Testing Only**: Never use for production
3. **API Keys**: Consider adding authentication to your API
4. **Stop When Done**: Press Ctrl+C in the ngrok terminal when finished

### Rate Limits

Free ngrok plan limits:
- **40 connections/minute** (burst)
- **~20 req/sec** sustained
- Usually sufficient for testing

If you hit limits, wait a minute or upgrade to ngrok Pro.

---

## 🆘 Troubleshooting

### "ngrok warning page" in browser

**Normal for free plan!** Click "Visit Site" to proceed. API calls will work after first browser visit.

### Connection timeouts

1. Check ngrok is still running
2. Verify local API is healthy: `curl http://localhost:8080/health`
3. Check ngrok web interface: http://localhost:4040

### "Rate limit exceeded"

Free plan limits reached. Wait 1-2 minutes or upgrade to ngrok Pro.

### Tunnel disconnects

ngrok free tunnels may disconnect after inactivity. Just restart:
```bash
./scripts/start_ngrok_tunnel.sh
```

---

## 📊 Monitor Your Tunnel

### View ngrok Web Interface

Open: **http://localhost:4040**

Shows:
- Request history
- Response times
- Error logs
- Traffic statistics

### View API Logs

```bash
# View API logs
docker compose logs -f api

# Or use the filtered view
./scripts/view_workflow_logs.sh
```

---

## 🎯 Quick Reference

```bash
# Your ngrok URL
https://oriented-flea-large.ngrok-free.app

# Health check
curl https://oriented-flea-large.ngrok-free.app/health

# List reports
curl https://oriented-flea-large.ngrok-free.app/api/v1/reports/list

# Submit verification
curl -X POST https://oriented-flea-large.ngrok-free.app/api/v1/verification/verify \
  -H "Content-Type: application/json" \
  -d '&#123;"video_url":"https://www.youtube.com/watch?v=VIDEO_ID"&#125;'

# ngrok web interface
open http://localhost:4040

# Stop tunnel (in ngrok terminal)
# Press Ctrl+C
```

---

## 📚 Documentation

- **This Guide**: `NGROK_ACTIVE.md`
- **Quick Start**: `NGROK_QUICKSTART.md`
- **Full Docs**: `docs/NGROK_REMOTE_ACCESS.md`

---

## ✅ Next Steps

1. **Test the health endpoint** in your browser:
   - Visit: https://oriented-flea-large.ngrok-free.app/health
   - Should see: `&#123;"status":"healthy"&#125;`

2. **Add to Streamlit secrets** (if using Streamlit Community Cloud)

3. **Update Colab notebook** (if using Google Colab)

4. **Start testing!** Your local API is now accessible from anywhere 🎉

---

**Tunnel Status:** 🟢 Active  
**Public URL:** https://oriented-flea-large.ngrok-free.app  
**Local API:** http://localhost:8080  
**Monitor:** http://localhost:4040  

**Remember:** This URL will change when you restart ngrok!

