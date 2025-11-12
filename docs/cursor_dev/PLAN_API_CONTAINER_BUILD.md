# Plan: Containerize verityngn-api and Connect to Streamlit Community UI

**Date**: Current Session  
**Status**: In Progress

## Build Configuration

### Critical Requirements
- ✅ **MUST USE**: `Dockerfile.api` (conda-based, adapted from `Dockerfile.conda`)
- ✅ **MUST USE**: `environment-minimal.yml` for dependency resolution
- ✅ This is the "magic build" that avoids dependency conflicts
- ✅ Entry point: `python -m verityngn.api` via `verityngn/api/__main__.py`

### Build Command
```bash
docker compose build --no-cache api
```

**Full rebuild script** (rebuilds both API and UI):
```bash
./scripts/rebuild_all_containers.sh
```

## Implementation Steps

### Phase 1: Build API Container ✅

**Task 1.1: Build API Container**
- Command: `docker compose build --no-cache api`
- Uses: `Dockerfile.api` + `environment-minimal.yml`
- Expected: Multi-stage conda/mamba build (builder + runtime)
- Time: Several minutes (conda environment creation)

**Task 1.2: Verify Build Success**
- Check build output for errors
- Verify image created: `verityngn-api:latest`
- Check logs for any dependency issues

### Phase 2: Test API Container Runtime

**Task 2.1: Start API Container**
- Command: `docker compose up -d api`
- Verify container starts successfully
- Check health endpoint: `http://localhost:8080/health`

**Task 2.2: Test API Endpoints**
- Health check: `curl http://localhost:8080/health`
- API docs: `http://localhost:8080/docs`
- Test verification endpoint (if needed)

### Phase 3: Streamlit Integration

**Task 3.1: Verify docker-compose.yml Configuration**
- ✅ API service uses `Dockerfile.api` (correct)
- ✅ Network: `verityngn-network` for inter-container communication
- ✅ UI connects to API via `http://api:8080` (internal network)

**Task 3.2: Test Streamlit UI Connection**
- Start UI: `docker compose up -d ui`
- Verify UI can reach API at `http://api:8080`
- Test health check from UI

**Task 3.3: Test End-to-End Workflow**
- Submit verification request from UI
- Verify API processes request and returns status
- Check that reports are accessible

### Phase 4: Streamlit Community Cloud Setup

**Task 4.1: Verify Streamlit Configuration**
- Check `ui/.streamlit/config.toml`
- Verify `ui/.streamlit/secrets.toml.example` structure
- Ensure `requirements-ui.txt` has minimal dependencies

**Task 4.2: Document Deployment Steps**
- Document how to set `VERITYNGN_API_URL` in Streamlit secrets
- Provide instructions for connecting to ngrok or Cloud Run API
- Update deployment documentation

## Key Files

1. **Dockerfile.api** - ✅ Conda-based build with environment-minimal.yml
2. **docker-compose.yml** - ✅ Uses Dockerfile.api (correct)
3. **environment-minimal.yml** - Conda environment definition
4. **verityngn/api/__main__.py** - Entry point
5. **ui/api_client.py** - API connection logic
6. **scripts/rebuild_all_containers.sh** - Full rebuild script

## Success Criteria

- ✅ API container builds using `docker compose build --no-cache api`
- ✅ API container runs and responds to health checks
- ✅ API verification endpoint accepts requests
- ✅ Streamlit UI can connect to API (local docker-compose network)
- ✅ End-to-end workflow works: submit → process → report
- ✅ Streamlit Community Cloud deployment documented

## Build History Reference

From `scripts/rebuild_all_containers.sh` and `REBUILD_COMPLETE.md`:
- Standard build command: `docker compose build --no-cache api`
- Full rebuild script: `./scripts/rebuild_all_containers.sh`
- Previous successful builds documented in `REBUILD_COMPLETE.md`

## Next Actions

1. ✅ Update plan (this document)
2. ⏳ Build API container: `docker compose build --no-cache api`
3. ⏳ Verify build success
4. ⏳ Test API runtime
5. ⏳ Test Streamlit integration
6. ⏳ Document Streamlit Community Cloud setup

