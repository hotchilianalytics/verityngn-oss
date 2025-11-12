# 🚨 FIX: Streamlit Community Not Using ngrok API

## Problem Identified

Your Streamlit Community app **does NOT have the API URL configured** in secrets!

The `ui/.streamlit/secrets.toml` file has Google Cloud credentials but is **missing**:
```toml
VERITYNGN_API_URL = "https://oriented-flea-large.ngrok-free.app"
```

---

## ✅ IMMEDIATE FIX

### Go to Streamlit Community Dashboard

1. **Open:** https://share.streamlit.io
2. **Click:** Your app name (`verityngn-oss` or whatever you named it)
3. **Click:** ⚙️ Settings (bottom left)
4. **Click:** "Secrets" tab
5. **ADD this at the TOP of the secrets:**

```toml
# VerityNgn API Configuration - ADD THIS!
VERITYNGN_API_URL = "https://oriented-flea-large.ngrok-free.app"
```

6. **Click:** "Save"
7. **App will restart automatically**

---

## 📋 Complete Secrets Configuration

Your Streamlit Community secrets should look like this:

```toml
# ═══════════════════════════════════════════════════════════
# VERITYNGN API URL - REQUIRED!
# ═══════════════════════════════════════════════════════════
VERITYNGN_API_URL = "https://oriented-flea-large.ngrok-free.app"

# Alternative format (also supported)
[api]
url = "https://oriented-flea-large.ngrok-free.app"

# ═══════════════════════════════════════════════════════════
# API Keys (only needed if running workflows directly in UI)
# ═══════════════════════════════════════════════════════════
GOOGLE_SEARCH_API_KEY = "AIzaSyBiC_tsCAmwmPA6zcqOFJgAHGRM4Th6IJA"
CSE_ID = "800c584b1ca5f460a"
YOUTUBE_API_KEY = "AIzaSyBiC_tsCAmwmPA6zcqOFJgAHGRM4Th6IJA"
PROJECT_ID = "verityindex-0-0-1"
LOCATION = "us-central1"

# ═══════════════════════════════════════════════════════════
# Google Service Account (only needed if running workflows directly)
# ═══════════════════════════════════════════════════════════
[gcp_service_account]
type = "service_account"
project_id = "verityindex-0-0-1"
private_key_id = "6a21e94ca0a31c17af8d201a7e52f62bfe6f2e97"
private_key = """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCgPawRJL6FztbJ
vjuIOWPSVCtG+6d/DQRURLxPCKH031McCvUXgcSYg2gxpyDzNcU67NmIU0Yws/pO
hhiwaMam0N4Ekg+hAt13fqAIPVGOuiDQTV+COcwVHWP7LDJiimvJqQEvy9Annevj
OnZV9DW02qQLH0lfx+4aUmeFQ7MkqeS8UuyOyEi2aqnHjj2X+RHaXbCk/kEvsXGq
WicPMaxDZP+t9FpuF3NEEdRxttKn+ViGyXOr+PYj68w7AsxwrzIuvf5pnpDVXyqk
+IdZkYBFhZOxI0VOvEbxp6QHpH7wdIDMDq/AleflAtn7F6j+N3dcYj1+7C60iumj
ewGa3lHjAgMBAAECggEANQABBBCXtbFSqJqznRyCUESHpexBm8vF5Utwz2FHFDOz
jQBwzWweBuXb1iR1yQu9Zv6E+sq0WhKFVWiUDPEy12UZMgDPi41jjA0FSIRjj+Yv
SUZ2MyADyO4WLjMRnTc0bJhqLJFokVnx9g/VqRtjkiSJAqbAAZ6iufEMjW71d0f2
QE2vWSsUlNwnHh3IxUkr5hxbGGcHLKgGHr6ZhnwT1zd6Z2YH65KUUilpxU75qzMW
W3kBA1J7alOmlZIjX9zNp762nDJWGqP8YhIUcrHS45a5HILWNFTXgQp9NE2ZhivQ
6pOlblVvsZ+zdpP7mNvAjv7iX4FOMBQXNZNIvmgVFQKBgQDN9UDAlFqnLAkALss3
V/aOAdEgWQE5CM/Z0qH0p8huKuHT2TB+ygtFb+z8xVr/V3Cna8E0zA9e+FnfdmzP
vITW7rRZZ5M5ryBbINC5xgod20OrFXKNcHNMBWyK+N6BDV5oBZi4UeenNFGyqVxE
s8YeaANmEsmSv5FiDDKAQLNMzwKBgQDHLMeYeQbSYbF1CffMgQxeSWQPCfmNibwU
y6Kg69FnM/YFtDMfUqWgv8rf32qbIFcSQpLlPRZ0OH7Msfb6Q9aU8ow5S7Q86egp
AYr+xgsDF2utplZwmsjKSlzcHtTZzeIgL/J8RZDN18jQXt2J0y5WoASez/aVxpft
nyeZSfR2rQKBgQCJubR4U3yfh8npDmGke7ULV1mySPKRYjwkDD9zLHPSf+iN0xIj
5xZMc8FFcvAcCivyORN1K/QnbOokjbvL2uP2GqANnT6Nd3eqmLIbWLxRJNwGXwxA
Wu8u6f2gnTWllPwJkZyDvXmsjUcIs0pZQuJ8WM/VBUE4WdRtfXyT2TBNbwKBgA8n
LwBApO44lIGtAndCkihSORST07Ka+f4zB+pqRoIth9gjP4hwhz1Vmh+yJbAro7Q1
8GsUXLL24V69Y2bi5l5qnZR2V/4SZaFJBsQfWRMhIwYRE555iDEruyjcB6GSclO0
kiQ2PrAKbLK9pOkpcesRPYi/lakLdN+VLjQRVlH5AoGBAI4sf8p4Asbw8lkB7Xko
IXvEj569LKw4COUY03+GMELGkCkn+3pBq7lBd2rWrYOkLeY8zoWqxwrbMcS9YScv
bWGqbdyVh45hfpelI4iz4lYTpWqI21N6x905xWHChhk6rEl0OGledsL5YO9uEuv0
li47BFdZQahLdQ2QI3zYHkiK
-----END PRIVATE KEY-----"""
client_email = "verityindex-sa-research@verityindex-0-0-1.iam.gserviceaccount.com"
client_id = "100999611098674545291"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/verityindex-sa-research%40verityindex-0-0-1.iam.gserviceaccount.com"
universe_domain = "googleapis.com"
```

---

## 🔍 How the UI Finds the API

The code in `ui/api_client.py` line 37:

```python
self.api_url = api_url or os.getenv('VERITYNGN_API_URL', 'http://localhost:8080')
```

This means:
1. **First**: Check for `VERITYNGN_API_URL` environment variable ← **YOU NEED THIS!**
2. **Fallback**: Use `http://localhost:8080` (local only)

Without `VERITYNGN_API_URL` in Streamlit secrets, your app tries to connect to `localhost:8080`, which doesn't exist in Streamlit Cloud!

---

## 🧪 Verify ngrok is Working

Run this command locally:

```bash
curl https://oriented-flea-large.ngrok-free.app/health
```

**Expected output:**
```json
{"status":"healthy"}
```

**If it doesn't work:**
1. Check ngrok is still running: `ps aux | grep ngrok`
2. Check ngrok web interface: http://localhost:4040
3. Restart ngrok if needed: `ngrok http 8080`

---

## 📊 Step-by-Step Fix

### 1. Verify ngrok is running

```bash
# Check process
ps aux | grep ngrok | grep -v grep

# Test endpoint
curl https://oriented-flea-large.ngrok-free.app/health
```

### 2. Go to Streamlit Settings

https://share.streamlit.io → Your App → ⚙️ Settings → Secrets

### 3. Add API URL at the top

```toml
VERITYNGN_API_URL = "https://oriented-flea-large.ngrok-free.app"
```

### 4. Save and wait for restart

App will automatically restart with new secrets (~30 seconds)

### 5. Test your app

Submit a YouTube URL and verify it connects to your local API

---

## 🎯 What You'll See After Fix

### Before (Current - Broken)
```
UI tries to connect to: http://localhost:8080
❌ Connection refused (localhost doesn't exist in Streamlit Cloud)
```

### After (Fixed)
```
UI tries to connect to: https://oriented-flea-large.ngrok-free.app
✅ Connects to your local API via ngrok
✅ Processes video successfully
✅ Displays results
```

---

## 🔄 If ngrok URL Changes

Free ngrok URLs change when you restart. When that happens:

1. **Get new URL** from ngrok terminal
2. **Update Streamlit secrets** with new URL
3. **App restarts automatically**

**Permanent solution:** Reserve a domain with your paid ngrok account

---

## 📝 Quick Fix Checklist

- [ ] ngrok is running locally (`ps aux | grep ngrok`)
- [ ] ngrok endpoint works (`curl https://oriented-flea-large.ngrok-free.app/health`)
- [ ] API is healthy locally (`curl http://localhost:8080/health`)
- [ ] Streamlit secrets has `VERITYNGN_API_URL` at the top
- [ ] Streamlit app restarted after adding secret
- [ ] Test video submission in Streamlit Community app

---

## 🆘 Still Not Working?

### Check Streamlit Logs

In Streamlit Community dashboard:
1. Click your app
2. Click "Manage app"
3. Check logs for error messages

Look for:
```
🌐 API Client initialized with URL: http://localhost:8080  ← BAD! Should be ngrok URL
```

Should see:
```
🌐 API Client initialized with URL: https://oriented-flea-large.ngrok-free.app  ← GOOD!
```

---

**IMMEDIATE ACTION:** Go add `VERITYNGN_API_URL` to your Streamlit secrets now!

https://share.streamlit.io → Your App → ⚙️ Settings → Secrets











