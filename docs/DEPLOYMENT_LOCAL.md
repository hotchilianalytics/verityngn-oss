# Local Deployment Guide

This guide covers deploying VerityNgn locally using Docker Compose for both development and testing.

## Overview

Local deployment runs:
- **API Backend**: Handles video processing and verification
- **Streamlit UI**: User-friendly web interface
- **Shared Volumes**: For data persistence

## Prerequisites

### Required

- [Docker](https://docs.docker.com/get-docker/) (version 20.10+)
- [Docker Compose](https://docs.docker.com/compose/install/) (version 2.0+)
- 8GB+ RAM recommended
- 10GB+ free disk space

### API Keys

You'll need:
1. **Google Cloud Service Account** with Vertex AI access
2. **Google Search API Key** for evidence gathering
3. **Custom Search Engine (CSE) ID**

See [`docs/guides/AUTHENTICATION.md`](guides/AUTHENTICATION.md) for setup instructions.

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/hotchilianalytics/verityngn-oss.git
cd verityngn-oss
```

### 2. Configure Environment

Create `.env` file from the example:

```bash
cp env.example .env
```

Edit `.env` and add your credentials:

```bash
# Required
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_SEARCH_API_KEY=your_api_key
CSE_ID=your_cse_id

# Optional
VERTEX_MODEL_NAME=gemini-2.0-flash-exp
```

### 3. Add Service Account

Place your Google Cloud service account JSON file in the project root:

```bash
cp /path/to/your-service-account.json ./service-account.json
```

### 4. Start Services

```bash
docker-compose up
```

This will:
- Build the API and UI Docker images
- Start both services
- Create shared volumes for data persistence

### 5. Access Application

- **Streamlit UI**: http://localhost:8501
- **API Backend**: http://localhost:8080
- **API Health**: http://localhost:8080/health

## Usage

### Submit a Video

1. Open http://localhost:8501
2. Navigate to "🎬 Video Input" tab
3. Enter a YouTube URL
4. Click "Start Verification"
5. Monitor progress in "⚙️ Processing" tab
6. View results in "📊 Reports" tab

### View Reports

Reports are saved to:
- **Local directory**: `./outputs/{video_id}/`
- **Formats**: HTML, JSON, Markdown

You can also access reports via API:
- HTML: http://localhost:8080/api/v1/reports/{video_id}/report.html
- JSON: http://localhost:8080/api/v1/reports/{video_id}/report.json

## Common Commands

### Start Services

```bash
# Start both API and UI
docker-compose up

# Start in background (detached)
docker-compose up -d

# Start only API
docker-compose up api

# Start only UI
docker-compose up ui
```

### View Logs

```bash
# View all logs
docker-compose logs -f

# View API logs only
docker-compose logs -f api

# View UI logs only
docker-compose logs -f ui
```

### Stop Services

```bash
# Stop services (keeps volumes)
docker-compose down

# Stop and remove volumes (deletes data)
docker-compose down -v
```

### Rebuild Images

If you've made code changes:

```bash
# Rebuild and restart
docker-compose up --build

# Force rebuild without cache
docker-compose build --no-cache
docker-compose up
```

## Directory Structure

```
verityngn-oss/
├── docker-compose.yml       # Orchestration config
├── Dockerfile.api           # API backend image
├── Dockerfile.streamlit     # UI image
├── .env                     # Environment variables
├── service-account.json     # GCP credentials
├── outputs/                 # Generated reports
│   └── {video_id}/
│       ├── report.html
│       ├── report.json
│       ├── report.md
│       └── claim/           # Claim-specific files
├── downloads/               # Downloaded videos
├── logs/                    # Application logs
└── verityngn/              # Source code
```

## Configuration

### Environment Variables

Key variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON | Required |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | Required |
| `GOOGLE_SEARCH_API_KEY` | Google Search API key | Required |
| `CSE_ID` | Custom Search Engine ID | Required |
| `VERTEX_MODEL_NAME` | Vertex AI model | `gemini-2.0-flash-exp` |
| `MAX_OUTPUT_TOKENS_2_5_FLASH` | Max tokens for responses | `16384` |
| `DEPLOYMENT_MODE` | Deployment environment | `container` |

### Port Configuration

To change default ports, edit `docker-compose.yml`:

```yaml
services:
  api:
    ports:
      - "8080:8080"  # Change first number for host port
  
  ui:
    ports:
      - "8501:8501"  # Change first number for host port
```

## Troubleshooting

### API Not Accessible

**Problem**: UI shows "API is not accessible"

**Solutions**:
1. Check if API container is running:
   ```bash
   docker-compose ps
   ```

2. Check API health:
   ```bash
   curl http://localhost:8080/health
   ```

3. View API logs:
   ```bash
   docker-compose logs api
   ```

4. Verify network connectivity:
   ```bash
   docker network ls
   docker network inspect verityngn-oss_verityngn-network
   ```

### Permission Errors

**Problem**: "Permission denied" when accessing files

**Solutions**:
1. Check file permissions:
   ```bash
   ls -la outputs/ downloads/ logs/
   ```

2. Fix permissions:
   ```bash
   chmod -R 755 outputs/ downloads/ logs/
   ```

3. Check Docker volume permissions:
   ```bash
   docker-compose down -v
   docker-compose up
   ```

### Out of Memory

**Problem**: Container killed due to OOM

**Solutions**:
1. Increase Docker memory limit (Docker Desktop → Settings → Resources)
2. Reduce token limits in `.env`:
   ```bash
   MAX_OUTPUT_TOKENS_2_5_FLASH=8192
   GENAI_VIDEO_MAX_OUTPUT_TOKENS=4096
   ```

### Service Won't Start

**Problem**: Container exits immediately

**Solutions**:
1. Check logs:
   ```bash
   docker-compose logs api
   ```

2. Verify environment variables:
   ```bash
   docker-compose config
   ```

3. Test service account:
   ```bash
   docker-compose run api python -c "from google.cloud import aiplatform; print('✅ Auth OK')"
   ```

## Development Workflow

### Hot Reloading

For development with live code updates:

1. Create `docker-compose.override.yml`:
   ```yaml
   version: '3.8'
   services:
     api:
       volumes:
         - ./verityngn:/app/verityngn
     ui:
       volumes:
         - ./ui:/app/ui
   ```

2. Restart services:
   ```bash
   docker-compose down
   docker-compose up
   ```

### Running Tests

```bash
# Run tests in API container
docker-compose run api pytest

# Run specific test file
docker-compose run api pytest tests/test_api.py
```

### Accessing Container Shell

```bash
# API container
docker-compose exec api /bin/bash

# UI container
docker-compose exec ui /bin/bash
```

## Performance Tuning

### Resource Limits

Edit `docker-compose.yml`:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

### Parallel Processing

For multiple videos:

```bash
# Scale API workers
docker-compose up --scale api=3
```

(Note: Requires load balancer configuration)

## Next Steps

- **Production Deployment**: See [DEPLOYMENT_CLOUD_RUN.md](DEPLOYMENT_CLOUD_RUN.md)
- **Colab Usage**: See [DEPLOYMENT_COLAB.md](DEPLOYMENT_COLAB.md)
- **API Reference**: See [api/README.md](api/README.md)
- **Troubleshooting**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## Support

- **Issues**: https://github.com/hotchilianalytics/verityngn-oss/issues
- **Discussions**: https://github.com/hotchilianalytics/verityngn-oss/discussions
- **Documentation**: `docs/` directory

---

**Last Updated**: November 4, 2025  
**Version**: 2.3.0




