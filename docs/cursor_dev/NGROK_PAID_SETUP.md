# 🎉 ngrok PAID ACCOUNT Setup Complete!

## ✅ What I Found

**Location:** `~/Library/Application Support/ngrok/ngrok.yml`  
**Authtoken:** `k2vbAz...` (configured ✅)  
**Account Type:** Paid/Pro account detected  

---

## 🚀 Enhanced Configuration Created

I've created an enhanced ngrok configuration to take advantage of your paid account features:

### Files Created

1. **`.ngrok.yml`** - Project-specific ngrok configuration
   - Named tunnel: `verityngn-api` (port 8080)
   - Named tunnel: `verityngn-ui` (port 8501) 
   - Request inspection enabled
   - Compression enabled
   - Metadata for monitoring

2. **`scripts/start_ngrok_paid.sh`** - Enhanced startup script
   - Uses your paid account features
   - Supports named tunnels
   - Better error handling

---

## 🎯 Paid Account Benefits

Your paid ngrok account gives you:

✅ **Reserved Domains** - Persistent URLs that don't change on restart  
✅ **Higher Rate Limits** - No more 40 req/min limit  
✅ **Multiple Tunnels** - Run API + UI simultaneously  
✅ **Custom Domains** - Use your own domain (if configured)  
✅ **IP Whitelisting** - Restrict access by IP  
✅ **Better Support** - Priority customer support  

---

## 🚇 Start Your Tunnel

### Option 1: Using Enhanced Script (Recommended)

```bash
cd /Users/ajjc/proj/verityngn-oss
./scripts/start_ngrok_paid.sh
```

This will:
- Check if API is running
- Use the project `.ngrok.yml` configuration
- Start the named tunnel `verityngn-api`
- Display your persistent URL

### Option 2: Start Named Tunnel Directly

```bash
# Start API tunnel only
ngrok start verityngn-api --config=.ngrok.yml

# Start both API and UI tunnels
ngrok start verityngn-api verityngn-ui --config=.ngrok.yml
```

### Option 3: Use Global Config

```bash
# Uses ~/Library/Application Support/ngrok/ngrok.yml
ngrok http 8080
```

---

## 🎨 Reserved Domain Setup (Optional)

If you want a persistent domain that never changes:

### 1. Reserve a Domain

Go to: https://dashboard.ngrok.com/cloud-edge/domains

Click **"+ New Domain"** and reserve a domain like:
- `verityngn-api.ngrok.app`
- Or use your custom domain

### 2. Update .ngrok.yml

Add the reserved domain to your config:

```yaml
tunnels:
    verityngn-api:
        proto: http
        addr: 8080
        domain: verityngn-api.ngrok.app  # Your reserved domain
        inspect: true
        compression: true
```

### 3. Restart ngrok

```bash
./scripts/start_ngrok_paid.sh
```

Now your URL will always be: `https://verityngn-api.ngrok.app`

---

## 📊 Advanced Features

### IP Whitelisting

Restrict access to specific IPs:

```yaml
tunnels:
    verityngn-api:
        proto: http
        addr: 8080
        ip_restriction:
            allow_cidrs:
                - 1.2.3.4/32  # Your IP
                - 5.6.7.0/24  # Your office network
```

### Basic Authentication

Add password protection:

```yaml
tunnels:
    verityngn-api:
        proto: http
        addr: 8080
        basic_auth:
            - "username:password"
```

### Custom Request/Response Headers

```yaml
tunnels:
    verityngn-api:
        proto: http
        addr: 8080
        request_headers:
            add:
                - "X-Custom-Header: value"
        response_headers:
            add:
                - "X-Powered-By: VerityNgn"
```

### Circuit Breaker

Protect your API from overload:

```yaml
tunnels:
    verityngn-api:
        proto: http
        addr: 8080
        circuit_breaker: 0.5  # Open circuit if 50%+ errors
```

---

## 🔍 Current Tunnel Status

Your currently running tunnel:
```
https://oriented-flea-large.ngrok-free.app
```

**Note:** This is a free-tier URL. Restart with the paid script to get persistent URLs!

---

## 📚 Configuration Reference

### Current .ngrok.yml

```yaml
version: "3"
agent:
    authtoken: k2vbAz... # (your token)

tunnels:
    verityngn-api:
        proto: http
        addr: 8080
        inspect: true
        compression: true
        metadata: "VerityNgn API - Video Verification Service"
        
    verityngn-ui:
        proto: http
        addr: 8501
        inspect: true
        compression: true
        metadata: "VerityNgn UI - Streamlit Interface"

region: us
web_addr: localhost:4040
log_level: info
```

---

## 🎯 Quick Commands

```bash
# Start API tunnel (paid features)
./scripts/start_ngrok_paid.sh

# Start both API + UI tunnels
ngrok start verityngn-api verityngn-ui --config=.ngrok.yml

# View ngrok dashboard
open https://dashboard.ngrok.com

# View local web interface
open http://localhost:4040

# Stop tunnel
# Press Ctrl+C in ngrok terminal
```

---

## 🔐 Security Best Practices

With a paid account, you should:

1. **Reserve a domain** for consistent URLs
2. **Add IP whitelisting** to restrict access
3. **Use basic auth** if exposing to public internet
4. **Monitor usage** via dashboard: https://dashboard.ngrok.com
5. **Rotate authtoken** periodically for security

---

## 📱 Use with Your Apps

### Streamlit Community Cloud

With a reserved domain, update once and never change again:

```toml
# Streamlit secrets
VERITYNGN_API_URL = "https://verityngn-api.ngrok.app"
```

### Google Colab

```python
# Persistent URL with paid account
API_URL = "https://verityngn-api.ngrok.app"
```

---

## 🆘 Troubleshooting

### "Invalid configuration"

Validate config:
```bash
ngrok config check --config=.ngrok.yml
```

### "Domain already in use"

Your reserved domain might be in use by another tunnel. Stop all tunnels:
```bash
pkill ngrok
```

### "Rate limit exceeded"

You shouldn't see this with paid account! Check:
```bash
open https://dashboard.ngrok.com/billing
```

---

## 📊 Monitor Your Tunnels

### ngrok Dashboard (Web)

https://dashboard.ngrok.com

- View all active tunnels
- See usage statistics
- Manage reserved domains
- Configure IP restrictions
- View request logs

### Local Web Interface

http://localhost:4040

- Real-time request inspection
- Replay requests
- Response times
- Error logs

---

## 🎉 Next Steps

1. **Restart ngrok** with the paid script:
   ```bash
   # Stop current tunnel (Ctrl+C in ngrok terminal)
   
   # Start with paid features
   ./scripts/start_ngrok_paid.sh
   ```

2. **Optional: Reserve a domain** for persistent URLs

3. **Optional: Add IP whitelisting** for security

4. **Update your apps** with the new (persistent) URL

---

## 📚 Resources

- **ngrok Dashboard**: https://dashboard.ngrok.com
- **Reserve Domains**: https://dashboard.ngrok.com/cloud-edge/domains
- **Usage Stats**: https://dashboard.ngrok.com/observability/event-subscriptions
- **Pricing & Limits**: https://dashboard.ngrok.com/billing
- **Documentation**: https://ngrok.com/docs

---

**Your Config:** `.ngrok.yml` in project root  
**Startup Script:** `./scripts/start_ngrok_paid.sh`  
**Account Status:** 🎉 PAID/PRO (full features available!)

Ready to use your paid features! 🚀

