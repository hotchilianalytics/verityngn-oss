# Streamlit Deployment Guide

## Overview

This guide covers deploying the VerityNgn Streamlit UI across different platforms, with special attention to managing secrets like API keys and Google Cloud service account credentials.

## Prerequisites

✅ **Required Secrets:**
- `GOOGLE_APPLICATION_CREDENTIALS` (path to service account JSON)
- `GOOGLE_SEARCH_API_KEY`
- `CSE_ID` (Custom Search Engine ID)
- `YOUTUBE_API_KEY`
- `PROJECT_ID` (Google Cloud project ID)
- Other API keys from your `.env` file

## Deployment Options

### Option 1: Streamlit Community Cloud (Recommended for Quick Deploy)

**Best for:** Free hosting, easy setup, public/private apps

#### Step-by-Step:

1. **Push your code to GitHub** (without secrets!)
   ```bash
   # Make sure .env and *.json are in .gitignore
   git add .
   git commit -m "Deploy to Streamlit Cloud"
   git push
   ```

2. **Go to [share.streamlit.io](https://share.streamlit.io)**
   - Sign in with GitHub
   - Click "New app"
   - Select your repository and `ui/streamlit_app.py`

3. **Configure Secrets**
   - Click "Advanced settings" → "Secrets"
   - Add your secrets in TOML format:

   ```toml
   # .streamlit/secrets.toml format
   GOOGLE_SEARCH_API_KEY = "your-search-api-key"
   CSE_ID = "your-cse-id"
   YOUTUBE_API_KEY = "your-youtube-key"
   PROJECT_ID = "verityindex-0-0-1"
   LOCATION = "us-central1"
   DEBUG_OUTPUTS = "true"
   DEPLOYMENT_MODE = "research"
   
   # For Google service account JSON, paste the ENTIRE JSON content
   [gcp_service_account]
   type = "service_account"
   project_id = "verityindex-0-0-1"
   private_key_id = "your-private-key-id"
   private_key = "[PASTE_PRIVATE_KEY_PEM_HERE]"
   client_email = "your-service-account@project.iam.gserviceaccount.com"
   client_id = "your-client-id"
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
   client_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs/..."
   universe_domain = "googleapis.com"
   ```

4. **Update your code to use Streamlit secrets** (see code changes below)

5. **Deploy!** - Streamlit Cloud will handle the rest

---

### Option 2: Self-Hosted Server (VM, VPS, etc.)

**Best for:** Full control, custom domain, private deployment

#### Step-by-Step:

1. **Set up your server** (Ubuntu/Debian example)
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Python 3.11+
   sudo apt install python3.11 python3.11-venv python3-pip -y
   
   # Install system dependencies
   sudo apt install ffmpeg -y
   ```

2. **Clone your repository**
   ```bash
   git clone https://github.com/yourusername/verityngn-oss.git
   cd verityngn-oss
   ```

3. **Create virtual environment**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Set up secrets directory**
   ```bash
   # Create secrets directory (outside git repo)
   mkdir -p ~/.verityngn/secrets
   
   # Copy your service account JSON
   # Upload via scp or paste manually
   nano ~/.verityngn/secrets/service-account.json
   # Paste your JSON content, save and exit
   
   # Set restrictive permissions
   chmod 600 ~/.verityngn/secrets/service-account.json
   ```

5. **Create environment file**
   ```bash
   # Create .env file (or use systemd environment files)
   cat > .env &lt;&lt; 'EOF'
   GOOGLE_APPLICATION_CREDENTIALS=/home/yourusername/.verityngn/secrets/service-account.json
   GOOGLE_SEARCH_API_KEY=your-search-api-key
   CSE_ID=your-cse-id
   YOUTUBE_API_KEY=your-youtube-key
   PROJECT_ID=verityindex-0-0-1
   LOCATION=us-central1
   DEBUG_OUTPUTS=true
   DEPLOYMENT_MODE=research
   EOF
   
   chmod 600 .env
   ```

6. **Run with systemd (recommended for production)**
   
   Create `/etc/systemd/system/verityngn-streamlit.service`:
   ```ini
   [Unit]
   Description=VerityNgn Streamlit UI
   After=network.target
   
   [Service]
   Type=simple
   User=yourusername
   WorkingDirectory=/home/yourusername/verityngn-oss
   Environment="PATH=/home/yourusername/verityngn-oss/venv/bin"
   EnvironmentFile=/home/yourusername/verityngn-oss/.env
   ExecStart=/home/yourusername/verityngn-oss/venv/bin/streamlit run ui/streamlit_app.py --server.port=8501 --server.address=0.0.0.0
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```
   
   Enable and start:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable verityngn-streamlit
   sudo systemctl start verityngn-streamlit
   sudo systemctl status verityngn-streamlit
   ```

7. **Set up reverse proxy** (nginx example)
   ```nginx
   server &#123;
       listen 80;
       server_name your-domain.com;
       
       location / &#123;
           proxy_pass http://localhost:8501;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       &#125;
   &#125;
   ```

---

### Option 3: Docker Container

**Best for:** Consistent environments, easy scaling, cloud deployment

1. **Create `.streamlit` directory**
   ```bash
   mkdir -p .streamlit
   ```

2. **Create `.streamlit/secrets.toml`** (for local testing)
   ```toml
   # See Option 1 for full format
   GOOGLE_SEARCH_API_KEY = "your-key"
   # ... other secrets
   ```

3. **Build and run**
   ```bash
   # Build
   docker build -t verityngn-streamlit -f Dockerfile.streamlit .
   
   # Run with secrets mounted
   docker run -d \
     -p 8501:8501 \
     -v $(pwd)/.streamlit/secrets.toml:/app/.streamlit/secrets.toml:ro \
     -v $(pwd)/verityngn/config/service-account.json:/secrets/service-account.json:ro \
     -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/service-account.json \
     --name verityngn-ui \
     verityngn-streamlit
   ```

4. **Or use docker-compose** (create `docker-compose.yml`)
   ```yaml
   version: '3.8'
   services:
     streamlit:
       build:
         context: .
         dockerfile: Dockerfile.streamlit
       ports:
         - "8501:8501"
       volumes:
         - ./.streamlit/secrets.toml:/app/.streamlit/secrets.toml:ro
         - ./verityngn/config/service-account.json:/secrets/service-account.json:ro
       environment:
         - GOOGLE_APPLICATION_CREDENTIALS=/secrets/service-account.json
       restart: unless-stopped
   ```

---

## Code Changes for Streamlit Secrets

### Modify `verityngn/config/settings.py`

Add Streamlit secrets support at the top (after imports):

```python
# Load environment variables from .env at project root if present
try:
    from dotenv import load_dotenv
    _PROJECT_ROOT = Path(__file__).resolve().parent.parent
    load_dotenv(_PROJECT_ROOT / ".env")
except Exception:
    pass

# STREAMLIT SECRETS SUPPORT
# If running in Streamlit Cloud, use st.secrets instead of .env
try:
    import streamlit as st
    if hasattr(st, 'secrets'):
        # Create temporary service account JSON file from secrets
        if 'gcp_service_account' in st.secrets:
            import json
            import tempfile
            
            # Write service account to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(dict(st.secrets['gcp_service_account']), f)
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f.name
        
        # Load other secrets from Streamlit
        for key in st.secrets:
            if key != 'gcp_service_account' and isinstance(st.secrets[key], str):
                os.environ[key] = st.secrets[key]
except ImportError:
    pass  # Streamlit not installed or not running in Streamlit
```

### Alternative: Create `ui/secrets_loader.py`

```python
"""
Unified secrets loader for Streamlit deployment.
Handles both .env files (local) and Streamlit secrets (cloud).
"""
import os
import json
import tempfile
from pathlib import Path

def load_secrets():
    """Load secrets from either .env or Streamlit secrets."""
    
    # Try Streamlit secrets first (Cloud deployment)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and len(st.secrets) > 0:
            # Load GCP service account
            if 'gcp_service_account' in st.secrets:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    json.dump(dict(st.secrets['gcp_service_account']), f)
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f.name
            
            # Load other environment variables
            for key in st.secrets:
                if key != 'gcp_service_account' and isinstance(st.secrets[key], str):
                    if key not in os.environ:  # Don't override existing env vars
                        os.environ[key] = st.secrets[key]
            
            return True
    except ImportError:
        pass
    
    # Fall back to .env file (local deployment)
    try:
        from dotenv import load_dotenv
        project_root = Path(__file__).resolve().parent.parent
        env_file = project_root / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            return True
    except Exception as e:
        print(f"Warning: Could not load .env file: &#123;e&#125;")
    
    return False

# Auto-load on import
load_secrets()
```

Then in `ui/streamlit_app.py`, add at the top:
```python
# Load secrets before anything else
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import secrets loader first
from ui import secrets_loader  # This auto-loads secrets
```

---

## Security Best Practices

### ⚠️ **NEVER Commit Secrets to Git**

Ensure your `.gitignore` includes:
```gitignore
# Secrets
.env
*.json
!package.json
*.key
*.pem

# Streamlit
.streamlit/secrets.toml
.streamlit/credentials.toml
```

### 🔒 **Restrict File Permissions**

```bash
chmod 600 .env
chmod 600 verityngn/config/*.json
chmod 600 .streamlit/secrets.toml
```

### 🔑 **Use Environment-Specific Service Accounts**

- **Development**: Limited permissions, test project
- **Production**: Minimal required permissions, production project
- **Principle of Least Privilege**: Only grant necessary API access

### 🔄 **Rotate Credentials Regularly**

```bash
# Create new service account key
gcloud iam service-accounts keys create new-key.json \
  --iam-account=your-sa@project.iam.gserviceaccount.com

# Update deployment
# Delete old key after verification
```

---

## Troubleshooting

### "Could not find credentials"

**Solution:** Check GOOGLE_APPLICATION_CREDENTIALS path
```bash
# Verify file exists
ls -la $GOOGLE_APPLICATION_CREDENTIALS

# Test authentication
gcloud auth application-default login
```

### "API key not found"

**Solution:** Verify secrets are loaded
```python
# Add debug logging in streamlit_app.py
import os
import streamlit as st

st.write("Debug: Checking environment variables")
st.write(f"GOOGLE_SEARCH_API_KEY: &#123;'✅ Set' if os.getenv('GOOGLE_SEARCH_API_KEY') else '❌ Missing'&#125;")
st.write(f"CSE_ID: &#123;'✅ Set' if os.getenv('CSE_ID') else '❌ Missing'&#125;")
```

### Streamlit Cloud "Module not found"

**Solution:** Ensure `requirements.txt` is complete
```bash
# Generate fresh requirements
pip freeze > requirements.txt
```

### "Permission denied" errors

**Solution:** Check file ownership and permissions
```bash
# Fix ownership
sudo chown -R $USER:$USER /path/to/verityngn-oss

# Fix permissions
chmod 755 verityngn-oss
chmod 644 requirements.txt
chmod 600 .env
```

---

## Quick Reference

| Deployment | Secrets Location | Service Account |
|------------|------------------|-----------------|
| **Local Dev** | `.env` file | File path in `GOOGLE_APPLICATION_CREDENTIALS` |
| **Streamlit Cloud** | App settings → Secrets | Paste JSON content in `[gcp_service_account]` |
| **Self-Hosted** | `.env` or systemd environment | File path in secure location |
| **Docker** | Volume mount | Mount JSON file, set env var to container path |

---

## Next Steps

1. ✅ Choose your deployment platform
2. ✅ Set up secrets according to the platform
3. ✅ Update code to load Streamlit secrets (if using Streamlit Cloud)
4. ✅ Test locally first with `.streamlit/secrets.toml`
5. ✅ Deploy and verify

For more help, see:
- [Streamlit Secrets Management](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
- [Google Cloud Authentication](https://cloud.google.com/docs/authentication/provide-credentials-adc)
- [Docker Secrets](https://docs.docker.com/engine/swarm/secrets/)


















