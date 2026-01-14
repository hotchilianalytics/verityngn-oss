---
title: "Cloud Run Deployment"
description: "Deploy the VerityNgn API to Google Cloud Run"
---

# Google Cloud Run Deployment Guide

Deploy VerityNgn API to Google Cloud Run for production use.

## Prerequisites

- Google Cloud Project with billing enabled
- `gcloud` CLI installed and configured
- Docker installed locally
- Service account with Vertex AI and Cloud Run permissions

## Quick Deploy

### 1. Set Project

```bash
gcloud config set project YOUR_PROJECT_ID
export PROJECT_ID=$(gcloud config get-value project)
export REGION="us-central1"
```

### 2. Enable APIs

```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  aiplatform.googleapis.com
```

### 3. Create Artifact Registry

```bash
gcloud artifacts repositories create verityngn \
  --repository-format=docker \
  --location=$REGION
```

### 4. Build and Push Image

```bash
# Build image
docker build -f Dockerfile.api -t verityngn-api .

# Tag for Artifact Registry
docker tag verityngn-api \
  $REGION-docker.pkg.dev/$PROJECT_ID/verityngn/api:latest

# Push
docker push $REGION-docker.pkg.dev/$PROJECT_ID/verityngn/api:latest
```

### 5. Deploy to Cloud Run

```bash
gcloud run deploy verityngn-api \
  --image=$REGION-docker.pkg.dev/$PROJECT_ID/verityngn/api:latest \
  --platform=managed \
  --region=$REGION \
  --allow-unauthenticated \
  --memory=4Gi \
  --cpu=2 \
  --timeout=3600 \
  --set-env-vars="DEPLOYMENT_MODE=production,STORAGE_BACKEND=gcs,GCS_BUCKET_NAME=your-bucket" \
  --set-secrets="GOOGLE_SEARCH_API_KEY=google_search_key:latest,CSE_ID=cse_id:latest"
```

## Configuration

### Environment Variables

Set in Cloud Run:
- `DEPLOYMENT_MODE=production`
- `STORAGE_BACKEND=gcs`
- `GCS_BUCKET_NAME=your-bucket-name`
- `VERTEX_MODEL_NAME=gemini-2.0-flash-exp`

### Secrets

Store API keys in Google Secret Manager:

```bash
# Create secrets
echo -n "your-api-key" | gcloud secrets create google_search_key --data-file=-
echo -n "your-cse-id" | gcloud secrets create cse_id --data-file=-

# Grant access to Cloud Run service account
gcloud secrets add-iam-policy-binding google_search_key \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"
```

## Streamlit UI Deployment

Deploy to Streamlit Cloud:

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repository
4. Set app path: `ui/streamlit_app.py`
5. Add secrets in `.streamlit/secrets.toml`:
   ```toml
   VERITYNGN_API_URL = "https://your-service.run.app"
   ```

## Monitoring

View logs:
```bash
gcloud run services logs read verityngn-api --region=$REGION
```

## Cost Estimation

- Cloud Run: $0.00002400/vCPU-second, $0.00000250/GiB-second
- Vertex AI: ~$0.25 per video
- Storage: ~$0.02/GB/month
- Expected: $10-50/month for light usage

See [DEPLOYMENT_LOCAL.md](DEPLOYMENT_LOCAL.md) for local testing.




