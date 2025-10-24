# Made signed URL generation optional with fallback

try:
    signed_url = blob.generate_signed_url(...)
except Exception:
    signed_url = f"gs://{self.bucket_name}/{gcs_path}"Integration Goals

### Primary Objectives

1. **Batch Job Submission via Cloud Run API**
   - Submit batch jobs through REST API
   - Queue management for multiple submissions
   - Status tracking and notifications

2. **Replit Frontend Integration**
   - User-friendly video submission interface
   - Real-time progress tracking
   - Report viewing and download

3. **End-to-End Workflow**
   - User submits video(s) → Batch processes → Reports available
   - Seamless experience from submission to results

---

## 🏗️ Architecture Overview

gcloud auth activate-service-account --key-file="$SERVICE_ACCOUNT_KEY"ch Processing**

- Multi-video parallel processing
- GCS output persistence
- Monitoring scripts
- Service account authentication

✅ **Cloud Run API**

- `/api/v1/verification/verify` endpoint
- `/api/v1/verification/status/{task_id}` endpoint
- `/api/v1/reports/{video_id}/report.{format}` endpoints
- Task queue system (in-memory)

⚠️ **Gaps to Address**

- No batch job submission endpoint
- In-memory queue (not persistent)
- No webhook/callback system
- No frontend integration

---

## 🔌 Integration Components

### 1. Cloud Run API Enhancements

#### New Endpoints Needed

**A. Batch Job Submission**

# 1. Create video list

cat > batch/my_videos.txt << EOF
<https://www.youtube.com/watch?v=VIDEO_ID_1>
<https://www.youtube.com/watch?v=VIDEO_ID_2>
<https://www.youtube.com/watch?v=VIDEO_ID_3>
EOF

# 2. Upload to GCS

gsutil cp batch/my_videos.txt gs://verityindex_bucket/batch/

# 3. Build and submit (auto-authenticates)

./scripts/batch-build-and-deploy.sh

# 4. Monitor progress

./scripts/batch-monitor.sh <job-name>

# 5. Check outputs

./scripts/batch-check-gcs.sh VIDEO_ID_1
