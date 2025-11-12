# 🚀 Streamlit Community Deployment - Step by Step Guide

**Status:** ✅ Ready to Deploy  
**Repository:** verityngn-oss  
**Commit:** Checkpoint 2.4  
**ngrok URL:** `https://oriented-flea-large.ngrok-free.app`

---

## ✅ Pre-Deployment Checklist

- [x] Code committed (checkpoint 2.4)
- [x] UI tested locally (http://localhost:8501)
- [x] API running and healthy
- [x] ngrok tunnel active
- [ ] Code pushed to GitHub
- [ ] Repository is public (required for free tier)
- [ ] Streamlit Community account created

---

## Step 1: Push to GitHub

```bash
cd /Users/ajjc/proj/verityngn-oss

# Push to GitHub
git push origin main
```

**Important:** Make sure your repository is **PUBLIC** for Streamlit Community free tier!

To check/make public:
1. Go to: https://github.com/YOUR_USERNAME/verityngn-oss/settings
2. Scroll to "Danger Zone"
3. If private, click "Change visibility" → "Make public"

---

## Step 2: Deploy to Streamlit Community

### 2.1 Go to Streamlit Community

**URL:** https://share.streamlit.io

### 2.2 Sign In

Click **"Sign in"** and authenticate with your GitHub account.

### 2.3 Create New App

Click **"New app"** or **"Create app"** button.

### 2.4 Fill in Deployment Form

```yaml
Repository: YOUR_USERNAME/verityngn-oss
Branch: main
Main file path: ui/streamlit_app.py
App URL (optional): verityngn  # Or your preferred subdomain
```

**Important:** The main file path must be exactly: `ui/streamlit_app.py`

### 2.5 Click "Deploy!"

The deployment will start. This takes 2-5 minutes.

---

## Step 3: Configure Secrets (CRITICAL)

Once deployment starts, you MUST add secrets for the app to work.

### 3.1 Access Settings

1. In the Streamlit Community dashboard, click your app
2. Click **⚙️ Settings** (bottom left or hamburger menu)
3. Click **"Secrets"** tab

### 3.2 Add API Configuration

Paste this configuration into the secrets editor:

```toml
# VerityNgn API Configuration
VERITYNGN_API_URL = "https://oriented-flea-large.ngrok-free.app"

[api]
url = "https://oriented-flea-large.ngrok-free.app"
base_url = "https://oriented-flea-large.ngrok-free.app"
```

### 3.3 Save Secrets

1. Click **"Save"**
2. The app will automatically restart with the new configuration

---

## Step 4: Wait for Deployment

Monitor the deployment logs:
- You'll see a build log showing:
  - Installing dependencies
  - Starting the app
  - Health checks

**Expected build time:** 2-5 minutes

---

## Step 5: Test Your Deployed App

### 5.1 Access Your App

Your app will be available at:
```
https://verityngn.streamlit.app
```
(or whatever subdomain you chose)

### 5.2 First Visit

**Important for ngrok free plan:**
1. First, visit your ngrok URL in a browser to accept the warning
2. Go to: https://oriented-flea-large.ngrok-free.app
3. Click "Visit Site"
4. Now your Streamlit app can connect!

### 5.3 Test Video Submission

1. Open your Streamlit app
2. Paste a YouTube URL (e.g., the LIPOZEM video)
3. Click Submit
4. Monitor progress
5. View the report!

---

## Step 6: Monitor & Debug

### 6.1 Streamlit App Logs

In Streamlit Community dashboard:
- Click your app
- Click **"Logs"** tab
- Watch real-time logs

### 6.2 Monitor ngrok Traffic

Open locally:
```
http://localhost:4040
```

This shows all requests from Streamlit to your API!

### 6.3 Check API Health

Verify API is responding:
```bash
curl https://oriented-flea-large.ngrok-free.app/health
```

---

## 🆘 Troubleshooting

### "Cannot connect to API"

**Cause:** ngrok URL not configured or tunnel disconnected

**Fix:**
1. Check ngrok is running: `ps aux | grep ngrok`
2. Test API: `curl https://oriented-flea-large.ngrok-free.app/health`
3. Update secrets in Streamlit with correct ngrok URL
4. Restart app in Streamlit dashboard

---

### "Module not found" or Build Errors

**Cause:** Missing dependencies

**Fix:**
1. Check `ui/requirements.txt` has all needed packages
2. Current dependencies (should work):
   ```txt
   streamlit>=1.28.0
   requests>=2.31.0
   python-dotenv>=1.0.0
   pyyaml>=6.0.1
   ```
3. Commit and push changes
4. Redeploy in Streamlit dashboard

---

### App is Slow or "Sleeping"

**Cause:** Free tier sleeps after inactivity

**Behavior:**
- App sleeps after 7 days of no traffic
- First load after sleep is slower (~30 seconds)
- Subsequent loads are fast

**Solution:**
- This is normal for free tier
- Upgrade to Streamlit Teams for always-on apps

---

### ngrok URL Changed

**Cause:** Free ngrok plan gives new URL on restart

**Fix:**
1. Stop old ngrok (Ctrl+C)
2. Start new tunnel: `ngrok http 8080`
3. Copy new URL
4. Update Streamlit secrets
5. Wait for app to restart

**Better Solution:**
- Upgrade to ngrok Personal ($8/mo)
- Reserve a permanent domain
- Update secrets once, never again!

---

## 🎯 Post-Deployment Checklist

- [ ] App deployed successfully
- [ ] Secrets configured with ngrok URL
- [ ] App accessible at your URL
- [ ] Video submission tested
- [ ] Report display verified
- [ ] Logs reviewed for errors
- [ ] ngrok traffic monitored

---

## 🔄 Updating Your App

### When You Make Code Changes

```bash
# Make your changes
git add .
git commit -m "Update: description"
git push origin main

# Streamlit Community auto-deploys!
```

The app will automatically rebuild and redeploy within 1-2 minutes.

---

## 📊 Monitor Your Deployment

### Streamlit Community Dashboard

**URL:** https://share.streamlit.io/YOUR_USERNAME

Features:
- **Logs:** Real-time application logs
- **Analytics:** Visitor statistics and usage
- **Resources:** CPU and memory usage
- **Settings:** Configuration and secrets

### ngrok Web Interface

**URL:** http://localhost:4040

Features:
- Request inspection
- Response times
- Error tracking
- Request replay

---

## 🎨 Customize Your App (Optional)

### Update Theme

Edit `ui/.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#FF4B4B"      # Your brand color
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
```

Commit and push to apply changes.

### Add Custom Domain (Paid Tier)

Streamlit Teams allows custom domains:
1. Upgrade to Streamlit Teams
2. Configure DNS records
3. Add domain in dashboard

---

## 💡 Tips for Success

### 1. Keep ngrok Running

Your app needs the tunnel to stay active:
- Run ngrok in a persistent terminal
- Use `tmux` or `screen` for long-running sessions
- Or upgrade to reserved domain

### 2. Monitor Usage

Check your dashboards:
- Streamlit: App health and usage
- ngrok: API traffic and errors

### 3. Test Thoroughly

Before sharing publicly:
- Test multiple videos
- Verify all features work
- Check error handling
- Test from different devices

### 4. Upgrade Path

For production use:
- **ngrok Personal** ($8/mo): Persistent URL
- **Streamlit Teams** ($25/mo): Better performance
- **Cloud Run**: Deploy API to production

---

## 🚀 Quick Commands Reference

```bash
# Push to GitHub
git push origin main

# Check ngrok status
ps aux | grep ngrok

# Start ngrok
ngrok http 8080

# Test API health
curl https://oriented-flea-large.ngrok-free.app/health

# Monitor ngrok traffic
open http://localhost:4040

# Test local UI
open http://localhost:8501
```

---

## 📚 Resources

- **Streamlit Community:** https://share.streamlit.io
- **Streamlit Docs:** https://docs.streamlit.io/streamlit-community-cloud
- **ngrok Dashboard:** https://dashboard.ngrok.com
- **Your Deployment Guide:** `DEPLOY_STREAMLIT_COMMUNITY.md`

---

## ✅ Success Criteria

Your deployment is successful when:

1. ✅ App loads at `https://YOUR_APP.streamlit.app`
2. ✅ No errors in Streamlit logs
3. ✅ Can submit a YouTube video
4. ✅ Video processes successfully
5. ✅ Report displays correctly
6. ✅ ngrok traffic shows in dashboard

---

**Ready to Deploy?** Follow the steps above! 🚀

**Current Status:**
- Repository: Ready to push
- ngrok: `https://oriented-flea-large.ngrok-free.app`
- Main file: `ui/streamlit_app.py`

**Next Action:** Push to GitHub, then go to https://share.streamlit.io!

