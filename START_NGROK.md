# 🚇 Start ngrok Tunnel - Quick Instructions

## Current Status

✅ **API is healthy**: Running on http://localhost:8080  
✅ **ngrok is installed**: /opt/homebrew/bin/ngrok  
✅ **ngrok is configured**: authtoken is set  

---

## Start the ngrok Tunnel

### Option 1: Using the Convenience Script (Recommended)

Open a **NEW terminal window** and run:

```bash
cd /Users/ajjc/proj/verityngn-oss
./scripts/start_ngrok_tunnel.sh
```

### Option 2: Run ngrok Directly

```bash
ngrok http 8080
```

---

## What You'll See

Once started, ngrok will display something like:

```
ngrok                                                                   

Session Status                online
Account                       your-account@email.com
Version                       3.x.x
Region                        United States (us)
Latency                       -
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123-xyz.ngrok-free.app -> http://localhost:8080

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

---

## 📋 Copy Your Public URL

Look for the **Forwarding** line and copy the HTTPS URL:

```
Forwarding    https://abc123-xyz.ngrok-free.app -> http://localhost:8080
              ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑
              THIS IS YOUR PUBLIC API URL
```

---

## 🧪 Test Your Tunnel

In another terminal, test the tunnel:

```bash
# Replace with your actual ngrok URL
curl https://YOUR-URL.ngrok-free.app/health

# Should return: {"status":"healthy"}
```

---

## 📱 Use with Streamlit Community Cloud

### Option A: Environment Variable

In your Streamlit Cloud settings → Secrets, add:

```toml
VERITYNGN_API_URL = "https://YOUR-URL.ngrok-free.app"
```

### Option B: Direct Configuration

In your `ui/.streamlit/secrets.toml`:

```toml
[api]
url = "https://YOUR-URL.ngrok-free.app"
```

Then restart your Streamlit app.

---

## 📓 Use with Google Colab

Update the API URL in your Colab notebook:

```python
# At the top of notebooks/VerityNgn_Colab_Demo.ipynb
API_URL = "https://YOUR-URL.ngrok-free.app"
```

Run the cells - they'll connect to your local API!

---

## 🔍 Monitor Traffic (Optional)

ngrok provides a web interface to inspect all requests:

**Open in browser**: http://localhost:4040

Features:
- Real-time request inspection
- Request/response replay
- Traffic statistics
- Response times

---

## ⚙️ Advanced Usage

### Run with Custom Options

```bash
# With basic authentication
ngrok http 8080 --basic-auth="username:password"

# Specific region (eu, us, ap, au, sa, jp, in)
ngrok http 8080 --region=eu

# With logging
ngrok http 8080 --log=stdout
```

### Stop the Tunnel

Press **Ctrl+C** in the ngrok terminal window

---

## ⚠️ Important Notes

1. **URL Changes**: Free ngrok URLs change every time you restart ngrok
2. **Rate Limits**: Free plan has request limits (usually sufficient for testing)
3. **Security**: Your local API is now publicly accessible - use only for testing
4. **Keep Running**: Keep the ngrok terminal window open while you need the tunnel

---

## 🆘 Troubleshooting

### "Connection refused"
- Ensure API is running: `docker compose ps api`
- Check health: `curl http://localhost:8080/health`

### "Failed to start tunnel"
- Check ngrok authtoken: `ngrok config check`
- Try logging in: `ngrok authtoken YOUR_TOKEN`

### "Rate limit exceeded"
- Wait a few minutes
- Consider upgrading to ngrok Pro
- Use `./scripts/view_workflow_logs.sh` to check if you're making too many requests

---

## 📚 Documentation

- **Quick Start**: `NGROK_QUICKSTART.md`
- **Full Guide**: `docs/NGROK_REMOTE_ACCESS.md`
- **ngrok Docs**: https://ngrok.com/docs

---

## 🎯 Quick Command Reference

```bash
# Check API health
curl http://localhost:8080/health

# Start ngrok (script)
./scripts/start_ngrok_tunnel.sh

# Start ngrok (direct)
ngrok http 8080

# View ngrok web interface
open http://localhost:4040

# Test tunnel (replace URL)
curl https://YOUR-URL.ngrok-free.app/health

# Stop tunnel
# Press Ctrl+C in ngrok terminal
```

---

**Ready?** Open a new terminal and run:

```bash
./scripts/start_ngrok_tunnel.sh
```

Then copy the `https://` URL and use it in your Streamlit or Colab config! 🚀

