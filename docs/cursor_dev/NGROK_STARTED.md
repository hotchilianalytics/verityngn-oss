# ✅ ngrok Tunnel Started

**Date**: Current Session  
**Status**: ✅ Active

## ngrok Tunnel Information

**Public API URL:**
```
https://oriented-flea-large.ngrok-free.app
```

**Local API:** http://localhost:8080  
**ngrok Web Interface:** http://localhost:4040  
**Process ID:** Running in background

## ✅ Verification

Test the tunnel:
```bash
curl https://oriented-flea-large.ngrok-free.app/health
# Should return: &#123;"status":"healthy"&#125;
```

## 📱 Use with Streamlit Community Cloud

### Check if App is Already Deployed

1. **Go to:** https://share.streamlit.io
2. **Sign in** with GitHub account (`hotchilianalytics`)
3. **Check** if app `verityngn-oss` or similar exists
4. **If exists:** Go to Settings → Secrets and update `VERITYNGN_API_URL`
5. **If not exists:** Follow deployment steps below

### Update Streamlit Secrets

If app is already deployed:

1. **Go to:** https://share.streamlit.io
2. **Click:** Your app name
3. **Click:** ⚙️ Settings → Secrets
4. **Update/Add:**
   ```toml
   VERITYNGN_API_URL = "https://oriented-flea-large.ngrok-free.app"
   ```
5. **Click:** Save (app will restart automatically)

### Deploy New App (if not deployed)

1. **Go to:** https://share.streamlit.io
2. **Click:** "New app"
3. **Fill in:**
   ```
   Repository: hotchilianalytics/verityngn-oss
   Branch: main
   Main file path: ui/streamlit_app.py
   App URL: verityngn-oss
   ```
4. **Click:** Deploy
5. **While deploying:** Go to Settings → Secrets
6. **Add:**
   ```toml
   VERITYNGN_API_URL = "https://oriented-flea-large.ngrok-free.app"
   ```
7. **Save** and wait for deployment

## 🧪 Test Deployment

Once Streamlit app is deployed/updated:

1. Visit your Streamlit app URL
2. Check API health indicator (should show "healthy")
3. Submit a test video
4. Verify it connects to your local API via ngrok

## ⚠️ Important Notes

- **Keep ngrok running** - Your Streamlit app needs it!
- **URL may change** - Free ngrok URLs change on restart
- **Update secrets** - If ngrok restarts, update Streamlit secrets with new URL

## 🛑 Stop ngrok

When done:
```bash
# Find ngrok process
ps aux | grep ngrok

# Kill it
kill [PID]
```

Or use the PID from above: `kill 12427`

---

**ngrok URL:** https://oriented-flea-large.ngrok-free.app  
**Ready for Streamlit Community Cloud!** 🚀

