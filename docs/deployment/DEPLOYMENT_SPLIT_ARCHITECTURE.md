# 🏗️ Split Architecture Deployment (RECOMMENDED)

## 🎯 Best Solution for VerityNgn

Split the app into two services:

1. **Backend API** (Railway/Render) - Complex dependencies
2. **Frontend UI** (Streamlit Cloud) - Simple, lightweight

---

## 🔍 Why This Works

### Problem: Monolithic Deployment
```
❌ Single Streamlit App with Everything:
- 3GB+ dependencies (conda + pip)
- Heavy video processing
- LLM inference
- Web scraping
- Fails on Streamlit Cloud
```

### Solution: Microservices
```
✅ Split into Two Services:

Frontend (Streamlit Cloud - FREE):
- 50MB dependencies
- Forms and UI only
- Display reports
- Make API calls

Backend (Railway - $5-10/mo):
- 3GB+ dependencies OK
- Video processing
- LLM inference
- Return JSON results
```

---

## 🏛️ Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                         INTERNET                              │
└─────────────────────┬────────────────────────────────────────┘
                      │
          ┌───────────▼───────────┐
          │   User Browser        │
          └───────────┬───────────┘
                      │
          ┌───────────▼────────────────────────────────────┐
          │   Streamlit Cloud (FREE)                       │
          │   https://verityngn.streamlit.app              │
          │                                                 │
          │   - Input form (YouTube URL)                   │
          │   - Display status                             │
          │   - Show reports                               │
          │   - 50MB Python dependencies                   │
          └───────────┬────────────────────────────────────┘
                      │ POST /api/v1/verification/verify
                      │ GET  /api/v1/verification/status/&#123;id&#125;
                      │ GET  /api/v1/reports/&#123;video_id&#125;/report.html
                      │
          ┌───────────▼────────────────────────────────────┐
          │   Railway/Render ($5-10/mo)                    │
          │   https://verityngn-api.up.railway.app         │
          │                                                 │
          │   FastAPI Backend:                             │
          │   - Video download (yt-dlp)                    │
          │   - LLM analysis (Vertex AI)                   │
          │   - Claim verification                         │
          │   - Report generation                          │
          │   - Storage (GCS or local)                     │
          │   - 3GB+ dependencies OK                       │
          └────────────────────────────────────────────────┘
```

---

## 🚀 Implementation Steps

### Phase 1: Deploy Backend API (You Already Have This!)

Your existing API is ready in `verityngn/api/`:

```python
# verityngn/api/__init__.py - ALREADY EXISTS
app = FastAPI(title="VerityNgn API")

# Routes:
POST   /api/v1/verification/verify          # Start verification
GET    /api/v1/verification/status/&#123;task_id&#125; # Check status
GET    /api/v1/reports/&#123;video_id&#125;/report.html # Get report
GET    /api/v1/reports/&#123;video_id&#125;/report.json # Get JSON
```

**Deploy to Railway:**
1. Update `Dockerfile.streamlit` → rename to `Dockerfile`
2. Change CMD to run API instead:
   ```dockerfile
   CMD ["uvicorn", "verityngn.api:app", "--host", "0.0.0.0", "--port", "8000"]
   ```
3. Deploy to Railway (see DEPLOYMENT_RAILWAY.md)
4. Get URL: `https://verityngn-api.up.railway.app`

### Phase 2: Create Lightweight Streamlit UI

Create a NEW minimal UI that only calls the API:

```python
# ui/streamlit_app_lightweight.py
import streamlit as st
import requests
import time

API_URL = "https://verityngn-api.up.railway.app"

st.title("🔍 VerityNgn - Video Verification")

# Input form
youtube_url = st.text_input("Enter YouTube URL:")

if st.button("Verify Video"):
    # Call backend API
    response = requests.post(
        f"&#123;API_URL&#125;/api/v1/verification/verify",
        json=&#123;"youtube_url": youtube_url&#125;
    )
    
    if response.status_code == 200:
        task_id = response.json()["task_id"]
        
        # Poll for status
        with st.spinner("Processing..."):
            while True:
                status = requests.get(
                    f"&#123;API_URL&#125;/api/v1/verification/status/&#123;task_id&#125;"
                ).json()
                
                if status["status"] == "completed":
                    break
                elif status["status"] == "failed":
                    st.error("Verification failed")
                    break
                
                time.sleep(5)
        
        # Display report
        video_id = status["video_id"]
        report_url = f"&#123;API_URL&#125;/api/v1/reports/&#123;video_id&#125;/report.html"
        
        st.success("Verification complete!")
        st.markdown(f"[View Full Report](&#123;report_url&#125;)")
        
        # Optionally embed report
        report_html = requests.get(report_url).text
        st.components.v1.html(report_html, height=1000, scrolling=True)
```

**New `requirements.txt` for lightweight UI:**
```txt
streamlit>=1.28.0
requests>=2.31.0
python-dotenv>=1.0.0
```

**Only 3 dependencies!** (vs 87 before)

### Phase 3: Deploy Lightweight UI to Streamlit Cloud

1. Push lightweight UI to GitHub (separate branch or `/ui_minimal/`)
2. Deploy to Streamlit Cloud
3. Set environment variable: `API_URL=https://verityngn-api.up.railway.app`
4. Done! Free Streamlit Cloud deployment works perfectly

---

## 📁 Directory Structure

```
verityngn-oss/
├── verityngn/              # Backend code (unchanged)
│   ├── api/                # FastAPI routes
│   ├── workflows/          # Verification pipeline
│   └── services/           # Video, LLM, search
│
├── ui/                     # Original full UI (for local dev)
│   └── streamlit_app.py    # Full app (87 dependencies)
│
├── ui_minimal/             # NEW: Lightweight UI for cloud
│   ├── streamlit_app.py    # Minimal UI (3 dependencies)
│   └── requirements.txt    # requests, streamlit, python-dotenv
│
├── Dockerfile              # Backend API (Railway/Render)
└── requirements.txt        # Backend dependencies (full)
```

---

## 💰 Cost Breakdown

| Service | Plan | Cost | What It Does |
|---------|------|------|--------------|
| **Streamlit Cloud** | Free | $0 | UI only (lightweight) |
| **Railway** | Starter | $5-10/mo | Backend API (heavy lifting) |
| **Google Cloud** | Pay-as-you-go | ~$5/mo | Vertex AI, Storage |
| **Total** | | **~$10-15/mo** | Full production system |

---

## 🎯 Advantages of Split Architecture

### ✅ Pros
1. **Streamlit Cloud works** - Only needs 3 simple Python packages
2. **Scalable** - Backend can handle multiple concurrent users
3. **Independent deploys** - Update UI without rebuilding backend
4. **Better caching** - Backend can cache results across sessions
5. **Cost-effective** - Only backend needs paid hosting
6. **Monitoring** - Separate logs and metrics for UI vs API
7. **Security** - API keys only in backend, not UI

### ⚠️ Cons
1. **More complex** - Two services instead of one
2. **Network latency** - API calls add ~100-200ms
3. **CORS setup** - Need to configure Cross-Origin requests

### 💡 Tradeoffs
- **Monolithic**: Simple but heavy, can't use Streamlit Cloud
- **Split**: Slightly complex but scales, FREE frontend

---

## 🔧 Implementation Checklist

- [ ] Deploy backend API to Railway
  - [ ] Update Dockerfile to run API (not Streamlit)
  - [ ] Add environment variables
  - [ ] Test API endpoints
- [ ] Create `ui_minimal/streamlit_app.py`
  - [ ] Implement form and API calls
  - [ ] Add report display
  - [ ] Test locally
- [ ] Deploy lightweight UI to Streamlit Cloud
  - [ ] Push to GitHub
  - [ ] Configure Streamlit Cloud app
  - [ ] Set `API_URL` environment variable
- [ ] Test end-to-end
  - [ ] Submit YouTube URL
  - [ ] Verify backend processes video
  - [ ] Confirm report displays

---

## 🎓 Learning Resources

- **FastAPI async endpoints**: https://fastapi.tiangolo.com/async/
- **Streamlit API calls**: https://docs.streamlit.io/library/api-reference
- **Railway deployment**: https://docs.railway.app
- **CORS setup**: https://fastapi.tiangolo.com/tutorial/cors/

---

## 🚦 Next Steps

1. **Quick test**: Deploy backend API to Railway first
2. **Verify**: Test API endpoints work
3. **Build UI**: Create minimal Streamlit UI
4. **Deploy UI**: Push to Streamlit Cloud
5. **Enjoy**: Free, scalable, production-ready system!

---

## ⭐ Recommendation

**This is the BEST solution for VerityNgn** because:
- ✅ Solves Streamlit Cloud dependency issues
- ✅ Professional architecture
- ✅ Scales to 100s of users
- ✅ Minimal cost (~$10/mo)
- ✅ Easy to maintain and update


















