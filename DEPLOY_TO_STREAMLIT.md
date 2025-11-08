# 🚀 Deploy VerityNgn UI to Streamlit Community Cloud

## Current Status

✅ **UI is running locally:** http://localhost:8501  
✅ **API is running locally:** http://localhost:8080  
✅ **ngrok tunnel active:** https://oriented-flea-large.ngrok-free.app  

---

## 📋 Quick Deployment Steps

### Step 1: Push Code to GitHub (if not already)

```bash
cd /Users/ajjc/proj/verityngn-oss

# Check current status
git status

# If you have uncommitted changes, commit them:
git add ui/.streamlit/
git add ui/README.md
git add ui/packages.txt
git commit -m "Add Streamlit Community Cloud deployment config"
git push origin main
```

### Step 2: Sign Up for Streamlit Community

1. **Go to:** https://share.streamlit.io
2. **Sign in** with your GitHub account
3. **Free forever** (no credit card needed!)

### Step 3: Deploy App

1. **Click:** "New app" button
2. **Fill in:**
   - **Repository:** `yourusername/verityngn-oss` (your repo)
   - **Branch:** `main`
   - **Main file path:** `ui/streamlit_app.py`
   - **App URL:** Choose subdomain (e.g., `verityngn`)

3. **Advanced settings** (optional):
   - Python version: 3.12
   - Click "Deploy"

### Step 4: Configure Secrets

**IMPORTANT:** Add your API URL before the app starts!

1. While app is deploying, click **"⚙️ Settings"**
2. Click **"Secrets"** tab
3. Add this configuration:

```toml
# Your ngrok URL
VERITYNGN_API_URL = "https://oriented-flea-large.ngrok-free.app"
```

4. **Click "Save"**
5. App will automatically restart with new secrets

### Step 5: Wait for Deployment

- Takes ~2-3 minutes
- Watch the logs for progress
- App will auto-open when ready

### Step 6: Test Your Deployed App

1. **Visit your app:** `https://verityngn.streamlit.app` (or your chosen URL)
2. **Test health:** Should show "API is healthy" indicator
3. **Submit a video:** Try the example videos
4. **View reports:** Check existing verification results

---

## ⚙️ Configuration Files Created

I've created these files for you:

### 1. `ui/.streamlit/config.toml`
Streamlit app configuration (theme, server settings)

### 2. `ui/.streamlit/secrets.toml.example`
Template showing what secrets to add (don't commit real secrets!)

### 3. `ui/packages.txt`
System dependencies for Streamlit Cloud

### 4. `ui/README.md`
Complete deployment documentation

---

## 🔧 Secrets Configuration

### What You Need to Add

In Streamlit Cloud Dashboard → Settings → Secrets:

```toml
# Your API URL (choose one)

# Option 1: Using ngrok (development)
VERITYNGN_API_URL = "https://oriented-flea-large.ngrok-free.app"

# Option 2: Using Cloud Run (production)
# VERITYNGN_API_URL = "https://verityngn-api-xxxxxx.run.app"
```

### What You DON'T Need

- ❌ `GOOGLE_APPLICATION_CREDENTIALS` - API handles this
- ❌ `GOOGLE_CLOUD_PROJECT` - API handles this
- ❌ Any other secrets - UI is stateless!

---

## 🎯 Using ngrok URL

### Current URL

```
https://oriented-flea-large.ngrok-free.app
```

### Important Notes

⚠️ **Free ngrok URL changes** when you restart ngrok!

**When URL changes:**
1. Get new ngrok URL
2. Go to Streamlit Cloud → Settings → Secrets
3. Update `VERITYNGN_API_URL`
4. Save (app auto-restarts)

### Better Option: Paid ngrok or Cloud Run

**Paid ngrok ($8/month):**
- Reserve domain: `https://verityngn-api.ngrok.app`
- Never changes!
- Update secrets once

**Cloud Run (production):**
- Permanent URL
- Better performance
- No dependency on local machine

---

## 🧪 Testing Checklist

Before going live:

- [ ] Local UI works: http://localhost:8501
- [ ] Local API works: http://localhost:8080/health
- [ ] ngrok tunnel works: https://oriented-flea-large.ngrok-free.app/health
- [ ] Code pushed to GitHub
- [ ] Streamlit account created
- [ ] Secrets configured
- [ ] App deployed successfully

---

## 📊 What Users Will See

### 1. Home Page
- Submit YouTube video URLs
- See processing status
- View recent reports

### 2. View Reports
- Browse all verification reports
- See truthfulness scores
- Expand claim details

### 3. Processing Status
- Real-time progress updates
- Estimated completion time
- Error messages if any

---

## 🔍 Troubleshooting

### App won't start

**Check logs** in Streamlit Cloud dashboard

Common issues:
- Missing `VERITYNGN_API_URL` secret
- Wrong file path (should be `ui/streamlit_app.py`)
- Python version mismatch

### Can't connect to API

**Verify:**
1. ngrok is still running locally
2. API is healthy: `curl https://your-url/health`
3. URL in secrets matches ngrok URL exactly

### ngrok URL changed

**Fix:**
1. Get new URL from ngrok terminal
2. Update secrets in Streamlit Cloud
3. Save (auto-restarts app)

### Deployment timeout

**Streamlit Cloud might be busy**
- Wait 5-10 minutes
- Try deploying again
- Check Streamlit status: https://status.streamlit.io

---

## 🎨 Customization

### Change App Appearance

Edit `ui/.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#FF4B4B"  # Change this
backgroundColor = "#FFFFFF"
```

### Add Features

Modify `ui/streamlit_app.py` and components in `ui/components/`

### Update Dependencies

Edit `ui/requirements.txt` (use minimal dependencies for faster deploys)

---

## 🚀 Going Live

### Share Your App

Once deployed, share the URL:
```
https://your-app-name.streamlit.app
```

### Add to GitHub README

Add a badge to your repo README:
```markdown
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-name.streamlit.app)
```

### Monitor Usage

View stats in Streamlit Cloud dashboard:
- Active users
- Resource usage
- Error rates
- Logs

---

## 📚 Next Steps

### Immediate
1. Deploy to Streamlit Community (follow steps above)
2. Test with ngrok URL
3. Share with users

### Short-term
- Get paid ngrok for persistent URL
- OR deploy API to Cloud Run

### Long-term
- Deploy API to Cloud Run (production)
- Remove ngrok dependency
- Add authentication if needed
- Scale as needed

---

## ✅ Ready to Deploy?

Run these commands:

```bash
# 1. Check local UI works
open http://localhost:8501

# 2. Verify ngrok tunnel
curl https://oriented-flea-large.ngrok-free.app/health

# 3. Push to GitHub (if needed)
git status
git add .
git commit -m "Ready for Streamlit Community deployment"
git push

# 4. Deploy!
open https://share.streamlit.io
```

Then follow the steps in **Step 3: Deploy App** above!

---

**Your ngrok URL:** https://oriented-flea-large.ngrok-free.app  
**Local UI:** http://localhost:8501  
**Streamlit Cloud:** https://share.streamlit.io  

**Let's deploy! 🚀**

