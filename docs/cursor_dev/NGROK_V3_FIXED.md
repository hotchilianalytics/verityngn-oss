# ✅ ngrok v3 Configuration Fixed!

## What Was Wrong

ngrok v3 changed the config format. These fields were removed/moved:
- ❌ `region` - Now set via command line: `ngrok start --region=us`
- ❌ `web_addr` - Now set via command line: `ngrok start --web-addr=localhost:4040`
- ❌ `log_level`, `log_format` - Now set via command line flags
- ❌ `console_ui`, `console_ui_color` - Removed in v3

## ✅ Fixed Configuration

Your `.ngrok.yml` now contains only valid v3 fields:

```yaml
version: "3"
agent:
    authtoken: k2vbAz... (your token)

tunnels:
    verityngn-api:
        proto: http
        addr: 8080
        inspect: true
        metadata: "VerityNgn API - Video Verification Service"
        
    verityngn-ui:
        proto: http
        addr: 8501
        inspect: true
        metadata: "VerityNgn UI - Streamlit Interface"
```

---

## 🚀 Start Your Tunnel

### Option 1: Named Tunnel (Recommended)

```bash
cd /Users/ajjc/proj/verityngn-oss
ngrok start verityngn-api --config=.ngrok.yml
```

### Option 2: Both API + UI

```bash
ngrok start verityngn-api verityngn-ui --config=.ngrok.yml
```

### Option 3: With Additional Options

```bash
# Specify region
ngrok start verityngn-api --config=.ngrok.yml --region=us

# Change web interface port
ngrok start verityngn-api --config=.ngrok.yml --web-addr=localhost:4040

# Enable logging
ngrok start verityngn-api --config=.ngrok.yml --log=stdout --log-level=info
```

---

## 🎨 Reserve a Domain (Optional)

For a persistent URL that never changes:

1. **Reserve domain at:** https://dashboard.ngrok.com/cloud-edge/domains

2. **Update `.ngrok.yml`:**
   ```yaml
   tunnels:
       verityngn-api:
           proto: http
           addr: 8080
           domain: verityngn-api.ngrok.app  # Your reserved domain
           inspect: true
   ```

3. **Restart:**
   ```bash
   ngrok start verityngn-api --config=.ngrok.yml
   ```

Now your URL will always be: `https://verityngn-api.ngrok.app` 🎉

---

## 📋 Quick Commands

```bash
# Start API tunnel
ngrok start verityngn-api --config=.ngrok.yml

# Start with US region
ngrok start verityngn-api --config=.ngrok.yml --region=us

# Start with logging
ngrok start verityngn-api --config=.ngrok.yml --log=stdout

# Start both API and UI
ngrok start verityngn-api verityngn-ui --config=.ngrok.yml

# Check config is valid
ngrok config check --config=.ngrok.yml

# View local web interface
open http://localhost:4040
```

---

## ⚙️ Available Command-Line Options

Since v3 removed some config file options, use command-line flags:

```bash
ngrok start verityngn-api --config=.ngrok.yml \
  --region=us \              # Region: us, eu, ap, au, sa, jp, in
  --web-addr=localhost:4040 \ # Web interface address
  --log=stdout \             # Enable logging
  --log-level=info \         # Log level: debug, info, warn, error
  --log-format=json          # Log format: json, logfmt, term
```

---

## 🔍 Verify Configuration

```bash
# Check config syntax
ngrok config check --config=.ngrok.yml

# View config (sanitized)
ngrok config view --config=.ngrok.yml
```

---

## ✅ Status

- ✅ Configuration syntax: **VALID**
- ✅ Authtoken: **Configured**
- ✅ Tunnels defined: **verityngn-api**, **verityngn-ui**
- ✅ Ready to start!

---

**Try it now:**

```bash
cd /Users/ajjc/proj/verityngn-oss
ngrok start verityngn-api --config=.ngrok.yml
```

Then look for the **Forwarding** line to get your public URL! 🚀

