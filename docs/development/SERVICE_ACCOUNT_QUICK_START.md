# 🚀 Service Account Quick Start

## TL;DR

**Download your service account JSON and place it here:**

```
/Users/ajjc/proj/verityngn-oss/service-account.json
```

That's it! The app will auto-detect it.

---

## 📥 Get Your JSON File

1. **Go here:** https://console.cloud.google.com/iam-admin/serviceaccounts
2. **Select your project**
3. **Click on service account** → Keys tab
4. **Add Key** → Create new key → **JSON**
5. **Download** → rename to `service-account.json`
6. **Move to:** `/Users/ajjc/proj/verityngn-oss/`

---

## ✅ Test It

```bash
cd /Users/ajjc/proj/verityngn-oss

# Check file exists
ls -la service-account.json

# Run Streamlit
cd ui
streamlit run streamlit_app.py
```

Should load without errors! 🎉

---

## 🔑 Required Permissions

Your service account needs these roles:

- ✅ **Vertex AI User** (for Gemini)
- ✅ **Storage Object Admin** (optional, for GCS)

Add roles at: https://console.cloud.google.com/iam-admin/iam

---

## 🎯 What This Gives You

- ✅ No browser login required
- ✅ Works in automated workflows
- ✅ Credentials don't expire
- ✅ Perfect for production use

---

## 📚 Need More Help?

See `SERVICE_ACCOUNT_SETUP.md` for detailed guide.


