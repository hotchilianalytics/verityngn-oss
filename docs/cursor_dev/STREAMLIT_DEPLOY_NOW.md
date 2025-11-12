# 🚀 Streamlit Community Deployment - Step by Step

## ✅ Prerequisites Complete

- ✅ Code committed to Git (Checkpoint 2.4)
- ✅ Pushed to GitHub: `hotchilianalytics/verityngn-oss`
- ✅ UI tested locally at http://localhost:8501
- ✅ API running with ngrok: `https://oriented-flea-large.ngrok-free.app`
- ✅ Requirements minimal and ready: `ui/requirements.txt`

---

## 📋 Deployment Steps

### Step 1: Open Streamlit Community Cloud

**Go to:** https://share.streamlit.io

**Sign in** with your GitHub account (hotchilianalytics)

---

### Step 2: Create New App

1. **Click:** "New app" or "Create app" button

2. **Fill in the deployment form:**

```
Repository: hotchilianalytics/verityngn-oss
Branch: main
Main file path: ui/streamlit_app.py
App URL (optional): verityngn-oss or verityngn
```

**Important:** Make sure the path is exactly `ui/streamlit_app.py`

3. **Click:** "Deploy!"

---

### Step 3: Configure Secrets (CRITICAL!)

While the app is deploying (or after first deploy fails):

1. **Click:** Your app name in the dashboard
2. **Click:** ⚙️ **Settings** (gear icon, bottom left)
3. **Click:** "Secrets" tab
4. **Paste this configuration:**

```toml
# VerityNgn API Configuration
VERITYNGN_API_URL = "https://oriented-flea-large.ngrok-free.app"

# Alternative format (both are supported)
[api]
url = "https://oriented-flea-large.ngrok-free.app"
base_url = "https://oriented-flea-large.ngrok-free.app"
```

5. **Click:** "Save"

6. **The app will automatically restart** with the new secrets

---

### Step 4: Wait for Deployment

- **Build time:** ~2-3 minutes (UI has minimal dependencies)
- **Watch logs** in the deployment interface
- Look for: `You can now view your Streamlit app in your browser.`

---

### Step 5: Test Your Deployed App

Once deployed, you'll get a URL like:

```
https://verityngn-oss.streamlit.app
```

**Test it:**

1. **Open the URL** in your browser
2. **Submit a test video:**
   - Example: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
3. **Watch it connect** to your local API via ngrok
4. **Verify results** display correctly

---

## 🎯 What to Expect

### During Deployment

You'll see logs like:

```
[...]
Collecting streamlit>=1.28.0
Collecting requests>=2.31.0
Collecting python-dotenv>=1.0.0
Collecting pyyaml>=6.0.1
[...]
Installing collected packages: ...
Successfully installed ...
You can now view your Streamlit app in your browser.
```

### After Deployment

Your app will be live at:
```
https://[your-chosen-name].streamlit.app
```

---

## 🔍 Troubleshooting

### "Cannot connect to API"

**Cause:** Secrets not configured or ngrok URL wrong

**Fix:**
1. Go to app Settings → Secrets
2. Verify URL is correct: `https://oriented-flea-large.ngrok-free.app`
3. Make sure ngrok is still running locally
4. Test ngrok: `curl https://oriented-flea-large.ngrok-free.app/health`

---

### "Module not found" error

**Cause:** Missing dependency in requirements

**Fix:**
1. Check `ui/requirements.txt` has all needed packages
2. Add missing package
3. Commit and push
4. Streamlit will auto-redeploy

---

### App shows "Sleeping" message

**Normal behavior!** Free Streamlit apps sleep after inactivity.

**Fix:** Just visit the URL, it will wake up in 10-30 seconds.

---

### ngrok URL changes

**Cause:** Free ngrok restarts change the URL

**Fix:**
1. Get new ngrok URL from terminal
2. Update Streamlit secrets
3. App will restart automatically

**Permanent Solution:** Reserve a domain with your paid ngrok account:
- Go to: https://dashboard.ngrok.com/cloud-edge/domains
- Reserve: `verityngn-api.ngrok.app`
- Update `.ngrok.yml` with reserved domain
- Never change URL again!

---

## 🎨 Customization After Deployment

### Change App Name/URL

1. Go to app Settings
2. Change the app URL
3. Save (may require redeployment)

### Update Code

```bash
# Make changes
git add .
git commit -m "Update UI feature"
git push origin main

# Streamlit auto-deploys!
```

### Monitor Your App

Dashboard shows:
- **Logs:** Real-time application logs
- **Analytics:** Visitor count, page views
- **Resources:** CPU/memory usage
- **Health:** App status

---

## 📊 Post-Deployment Checklist

- [ ] App deployed successfully
- [ ] Secrets configured with ngrok URL
- [ ] Test video submission works
- [ ] Results display correctly
- [ ] Share URL with testers
- [ ] Monitor logs for errors
- [ ] Consider reserving ngrok domain for persistence

---

## 🚀 Next Steps After Deployment

### Immediate

1. **Test thoroughly** with different YouTube videos
2. **Share the URL** with beta testers
3. **Monitor logs** for errors or issues
4. **Keep ngrok running** (your app needs it!)

### Short Term

1. **Reserve ngrok domain** for persistent URL
   - Visit: https://dashboard.ngrok.com/cloud-edge/domains
   - Reserve: `verityngn-api.ngrok.app`
   - Update secrets once, never again

2. **Gather feedback** from users
   - What works well?
   - What's confusing?
   - Any errors?

### Medium Term

1. **Deploy API to Cloud Run** (replace ngrok)
   ```bash
   gcloud run deploy verityngn-api --source . --region us-central1
   ```

2. **Upgrade Streamlit** to Teams ($20/mo) if needed
   - No sleeping
   - Better performance
   - More resources

---

## 📚 Useful Links

### Streamlit Community
- **Deploy:** https://share.streamlit.io
- **Docs:** https://docs.streamlit.io/streamlit-community-cloud
- **Community:** https://discuss.streamlit.io

### Your Resources
- **GitHub Repo:** https://github.com/hotchilianalytics/verityngn-oss
- **ngrok Dashboard:** https://dashboard.ngrok.com
- **Current ngrok URL:** https://oriented-flea-large.ngrok-free.app

---

## 🎉 Success Criteria

Your deployment is successful when:

- ✅ App loads at `https://[name].streamlit.app`
- ✅ Can submit a YouTube URL
- ✅ App connects to local API via ngrok
- ✅ Results display correctly
- ✅ No errors in logs

---

## 🔐 Security Note

**Your app is public** but connects to your local API via ngrok.

**Current setup:**
- ✅ Public UI (anyone can access)
- ✅ Local API (via ngrok tunnel)
- ⚠️ ngrok URL is public (anyone with URL can call API)

**To secure:**
1. Add API authentication/keys
2. Use IP whitelisting (paid ngrok)
3. Deploy API to Cloud Run with authentication

---

**Ready to deploy?** 

1. Go to: **https://share.streamlit.io**
2. Click: **"New app"**
3. Repository: **`hotchilianalytics/verityngn-oss`**
4. Main file: **`ui/streamlit_app.py`**
5. Add secrets: **ngrok URL**
6. **Deploy!** 🚀

---

**Your Deployment Configuration:**

```
Repository: hotchilianalytics/verityngn-oss
Branch: main
Main file: ui/streamlit_app.py
Secrets: VERITYNGN_API_URL = "https://oriented-flea-large.ngrok-free.app"
```

**Go deploy now!** 🎉











