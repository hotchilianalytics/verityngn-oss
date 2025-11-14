# Streamlit Community Cloud Architecture

**Date**: November 12, 2025  
**Version**: v2.1.0

---

## Architecture Overview

When using Streamlit Community Cloud, the architecture is:

```
┌─────────────────────────────────┐
│  Streamlit Community Cloud UI  │  (Public, hosted on share.streamlit.io)
│  (share.streamlit.io/your-app) │
└──────────────┬──────────────────┘
               │ HTTPS
               │ (via VERITYNGN_API_URL)
               ▼
┌─────────────────────────────────┐
│   ngrok Tunnel (Public URL)     │  (e.g., https://xxx.ngrok-free.app)
│   or Cloud Run URL               │
└──────────────┬──────────────────┘
               │ HTTP
               ▼
┌─────────────────────────────────┐
│   Local API Container           │  (localhost:8080)
│   verityngn-api:latest          │
└─────────────────────────────────┘
```

---

## Should You Stop the Local Streamlit UI?

### ✅ **YES - Recommended**

**When using Streamlit Community Cloud UI:**
- **Stop the local UI**: `docker compose stop ui` or `docker compose down ui`
- **Keep the API running**: The API must stay running for Cloud UI to work
- **Why**: Saves resources, avoids confusion, cleaner setup

### ❌ **NO - Not Required**

**You can keep both running if:**
- You want to test locally while Cloud UI is active
- You're developing/debugging
- You have sufficient resources

**Note**: Both UIs can run simultaneously without conflicts since they're separate applications.

---

## Recommended Setup for Cloud UI

### Option 1: Stop UI Container Only (Recommended)

```bash
# Stop only the UI container, keep API running
docker compose stop ui

# Or remove it entirely
docker compose rm ui

# Start only API
docker compose up -d api
```

**Benefits:**
- Saves memory and CPU
- Cleaner process list
- No port conflicts
- API still accessible for Cloud UI

### Option 2: Use Separate docker-compose File

Create `docker-compose.api-only.yml`:

```yaml
services:
  api:
    # ... same as main docker-compose.yml
```

Then run:
```bash
docker compose -f docker-compose.api-only.yml up -d
```

### Option 3: Keep Both Running

If you want both:
- Local UI: `http://localhost:8501` (for local testing)
- Cloud UI: `share.streamlit.io/your-app` (for public access)

Both connect to the same API backend.

---

## Resource Usage

**With UI running:**
- API container: ~500MB RAM
- UI container: ~200MB RAM
- **Total**: ~700MB RAM

**Without UI (API only):**
- API container: ~500MB RAM
- **Total**: ~500MB RAM

**Savings**: ~200MB RAM by stopping UI

---

## Quick Commands

### Stop Local UI (Keep API)
```bash
docker compose stop ui
```

### Start Local UI Again
```bash
docker compose start ui
```

### Check What's Running
```bash
docker compose ps
```

### View Resource Usage
```bash
docker stats
```

---

## Summary

**For Streamlit Community Cloud usage:**
1. ✅ **Stop local UI**: `docker compose stop ui`
2. ✅ **Keep API running**: Required for Cloud UI
3. ✅ **Start ngrok**: If using ngrok tunnel
4. ✅ **Configure Cloud UI**: Set `VERITYNGN_API_URL` secret

**Result**: Clean, efficient setup with only necessary services running.

