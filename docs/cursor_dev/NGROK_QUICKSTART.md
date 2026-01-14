# ngrok Quick Start Guide 🚇

Expose your local VerityNgn API to the internet for remote access.

## Prerequisites ✅

- ✅ **ngrok installed** (version 3.22.1 detected)
- ✅ **API running locally** on port 8080
- 🟡 **ngrok authtoken** (optional but recommended)

## Quick Start (30 seconds)

### 1. Start the API (if not already running)

```bash
docker compose up api
```

Or check if it's already running:
```bash
curl http://localhost:8080/health
# Should return: &#123;"status": "healthy"&#125;
```

### 2. Start ngrok Tunnel

**Option A: Use the convenience script**
```bash
./scripts/start_ngrok_tunnel.sh
```

**Option B: Run ngrok directly**
```bash
ngrok http 8080
```

### 3. Get Your Public URL

Look for the **Forwarding** line in the ngrok output:

```
Forwarding    https://abc123-ngrok-free.app -> http://localhost:8080
                      ↑
                Your Public API URL
```

### 4. Test the Tunnel

```bash
# Replace with your actual ngrok URL
curl https://YOUR-URL.ngrok-free.app/health

# Should return: &#123;"status": "healthy"&#125;
```

## Usage Examples

### 📱 Use with Streamlit Community Cloud

1. Deploy your UI to Streamlit Community Cloud
2. Add ngrok URL to Streamlit secrets:
   ```toml
   VERITYNGN_API_URL = "https://YOUR-URL.ngrok-free.app"
   ```
3. Restart app - it will connect to your local API!

### 📓 Use with Google Colab

1. Update the API URL in the Colab notebook:
   ```python
   API_URL = "https://YOUR-URL.ngrok-free.app"
   ```
2. Run the cells - they'll call your local API through the tunnel

### 🧪 Test from Anywhere

```bash
# Submit a verification task
curl -X POST https://YOUR-URL.ngrok-free.app/api/v1/verification/verify \
  -H "Content-Type: application/json" \
  -d '&#123;"video_url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ"&#125;'
```

## ngrok Web Interface

Monitor requests in real-time:
- **URL**: http://localhost:4040
- **Features**: Request inspection, replay, statistics

## Setup ngrok Authtoken (One-Time)

**Why?** Free plan limits, persistent URLs require authentication.

1. **Sign up**: https://ngrok.com (free)
2. **Get token**: https://dashboard.ngrok.com/get-started/your-authtoken
3. **Configure**:
   ```bash
   ngrok authtoken YOUR_TOKEN_HERE
   ```

## Security Warnings ⚠️

1. **Public Exposure**: Your local API is now accessible from the internet
2. **Free Plan**: URLs change on restart, limited requests/minute
3. **Testing Only**: Never use for production
4. **Stop When Done**: Press `Ctrl+C` to stop the tunnel

## Troubleshooting

### "ngrok: command not found"
```bash
# Install ngrok
brew install ngrok  # macOS
```

### "Connection refused"
Check if API is running:
```bash
curl http://localhost:8080/health
docker compose ps api
```

### "Rate limit exceeded"
Free plan has limits. Solutions:
- Wait a few minutes
- Upgrade to ngrok Pro
- Use Cloud Run deployment instead

## Advanced Options

### Custom Subdomain (ngrok Pro)
```bash
ngrok http 8080 --subdomain=my-verityngn
# URL: https://my-verityngn.ngrok.io
```

### Basic Authentication
```bash
ngrok http 8080 --basic-auth="username:password"
```

### Specific Region
```bash
ngrok http 8080 --region=eu
```

## Alternative: Deploy to Cloud

Instead of ngrok, deploy API to Cloud Run:
```bash
# See: docs/DEPLOYMENT_CLOUD_RUN.md
gcloud run deploy verityngn-api \
  --source . \
  --region us-central1
```

## Help & Documentation

- **Full Documentation**: `docs/NGROK_REMOTE_ACCESS.md`
- **ngrok Docs**: https://ngrok.com/docs
- **VerityNgn Issues**: https://github.com/yourusername/verityngn-oss/issues

---

**Ready?** Run `./scripts/start_ngrok_tunnel.sh` to get started! 🚀



