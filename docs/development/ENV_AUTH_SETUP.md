# 🔑 Authentication via .env File

## ✅ Easiest Method: Put Everything in .env

Your `.env` file can contain ALL credentials:

```bash
# Google Cloud Project
GOOGLE_CLOUD_PROJECT=your-project-id
PROJECT_ID=your-project-id
LOCATION=us-central1

# Service Account JSON Path
GOOGLE_APPLICATION_CREDENTIALS=/Users/ajjc/proj/verityngn-oss/service-account.json

# Google Search API (for claim verification)
GOOGLE_API_KEY=AIza...
GOOGLE_SEARCH_API_KEY=AIza...

# Custom Search Engine ID
CSE_ID=your-search-engine-id
GOOGLE_CSE_ID=your-search-engine-id

# YouTube Data API
YOUTUBE_API_KEY=AIza...
```

**That's it!** The system loads `.env` automatically.

---

## 🚀 How It Works

### When Streamlit Starts

1. **Loads `.env`** from project root
2. **Sets environment variables** from the file
3. **Checks for `GOOGLE_APPLICATION_CREDENTIALS`**
4. **Uses the JSON file** for authentication
5. **All other APIs** work from env vars

### What You Get

✅ **Single configuration file** - Everything in one place  
✅ **No manual exports** - Loads automatically  
✅ **Safe from git** - `.env` is in `.gitignore`  
✅ **Easy to manage** - Edit one file  
✅ **No shell commands** - Just edit and reload  

---

## 📋 Setup Steps

### 1. Download Service Account JSON

1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts
2. Select your project
3. Click service account → Keys → Add Key → JSON
4. Download the file
5. Save as: `/Users/ajjc/proj/verityngn-oss/service-account.json`

### 2. Add Path to .env

Open `/Users/ajjc/proj/verityngn-oss/.env` and add:

```bash
GOOGLE_APPLICATION_CREDENTIALS=/Users/ajjc/proj/verityngn-oss/service-account.json
```

### 3. Run Streamlit

```bash
cd /Users/ajjc/proj/verityngn-oss/ui
streamlit run streamlit_app.py
```

**Done!** No exports, no shell commands, just works.

---

## 🔍 Verify Your .env

Your `.env` should look like this:

```bash
# Authentication
GOOGLE_CLOUD_PROJECT=verityindex-0-0-1
PROJECT_ID=verityindex-0-0-1
LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/Users/ajjc/proj/verityngn-oss/service-account.json

# Search APIs
GOOGLE_API_KEY=AIzaSyBiC_...
GOOGLE_CSE_ID=800c584b1c...
YOUTUBE_API_KEY=AIzaSyBiC_...

# Optional
GOOGLE_SEARCH_API_KEY=AIzaSyBiC_...
CSE_ID=800c584b1c...
```

---

## ✅ Test It

### Quick Test

```bash
cd /Users/ajjc/proj/verityngn-oss
python test_credentials.py
```

Should show:

```
📄 Loaded .env from /Users/ajjc/proj/verityngn-oss/.env
✅ Google Search API Key: AIzaSyBiC_...
✅ Google CSE ID: 800c584b1c...
✅ YOUTUBE_API_KEY set
```

### Full Test

```bash
python -c "
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_file = Path('.env')
if env_file.exists():
    load_dotenv(env_file)
    print('✅ .env loaded')
else:
    print('❌ .env not found')

# Check GOOGLE_APPLICATION_CREDENTIALS
json_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
if json_path and Path(json_path).exists():
    print(f'✅ Service account JSON: &#123;json_path&#125;')
else:
    print(f'❌ GOOGLE_APPLICATION_CREDENTIALS not set or file not found')

# Check other keys
for key in ['GOOGLE_API_KEY', 'GOOGLE_CSE_ID', 'YOUTUBE_API_KEY']:
    val = os.getenv(key)
    if val:
        print(f'✅ &#123;key&#125;: &#123;val[:10]&#125;...')
    else:
        print(f'⚠️  &#123;key&#125; not set')
"
```

---

## 🔒 Security

### Protected

- ✅ `.env` is in `.gitignore` (won't be committed)
- ✅ `service-account.json` is in `.gitignore`
- ✅ All credentials stay local
- ✅ Safe to keep in project

### Best Practices

```bash
# Set secure permissions
chmod 600 .env
chmod 600 service-account.json

# Never commit to git (already ignored)
# Never share .env file
# Rotate keys periodically
```

---

## 🐛 Troubleshooting

### ".env not loading"

**Check file location:**

```bash
ls -la /Users/ajjc/proj/verityngn-oss/.env
```

**Check python-dotenv is installed:**

```bash
pip list | grep python-dotenv
pip install python-dotenv  # if needed
```

### "GOOGLE_APPLICATION_CREDENTIALS not set"

**Check .env contains:**

```bash
grep GOOGLE_APPLICATION_CREDENTIALS .env
```

**Should show:**

```
GOOGLE_APPLICATION_CREDENTIALS=/Users/ajjc/proj/verityngn-oss/service-account.json
```

### "Service account JSON not found"

**Check file exists:**

```bash
ls -la /Users/ajjc/proj/verityngn-oss/service-account.json
```

**Check path in .env matches:**

```bash
cat .env | grep GOOGLE_APPLICATION_CREDENTIALS
```

### "Still getting auth errors"

**Test manually:**

```bash
# Load .env and test
export $(cat .env | grep -v '^#' | xargs)
echo $GOOGLE_APPLICATION_CREDENTIALS
ls -la $GOOGLE_APPLICATION_CREDENTIALS
```

---

## 🎯 What This Enables

With `.env` authentication:

- ✅ **One configuration file** for everything
- ✅ **No shell exports** needed
- ✅ **Works immediately** on app start
- ✅ **Easy to update** - just edit .env
- ✅ **Version control safe** - .env is ignored
- ✅ **Team friendly** - everyone uses same format

---

## 📚 Related Docs

- **`env.example`** - Template to copy
- **`SERVICE_ACCOUNT_SETUP.md`** - Detailed guide
- **`ENV_VARIABLE_GUIDE.md`** - All variables explained
- **`test_credentials.py`** - Test all credentials

---

## ✨ Summary

**The Easy Way:**

1. Get service account JSON
2. Save as `service-account.json` in project root
3. Add to `.env`:

   ```bash
   GOOGLE_APPLICATION_CREDENTIALS=/Users/ajjc/proj/verityngn-oss/service-account.json
   ```

4. Run Streamlit - it auto-loads .env!

**No exports. No shell commands. Just works.** 🚀


