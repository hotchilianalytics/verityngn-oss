# 📊 How to Access API Logs

## 🎯 Quick Commands

### Option 1: Watch Logs in Real-Time (Filtered)

**Workflow logs only (recommended):**
```bash
./scripts/watch_api_logs.sh
```

This filters out HTTP noise and shows only workflow processing.

---

### Option 2: Watch All Logs (Unfiltered)

**Full logs including HTTP requests:**
```bash
docker compose logs -f api
```

Press `Ctrl+C` to stop.

---

### Option 3: View Recent Logs

**Last 50 lines:**
```bash
docker compose logs api --tail 50
```

**Last 100 lines:**
```bash
docker compose logs api --tail 100
```

---

### Option 4: Search for Specific Text

**Find errors:**
```bash
docker compose logs api | grep ERROR
```

**Find a specific video:**
```bash
docker compose logs api | grep "VIDEO_ID"
```

**Find claims processed:**
```bash
docker compose logs api | grep "Claims processed"
```

---

## 🔍 What to Look For

### Successful Processing

You'll see messages like:

```
🚀 Starting verification workflow for: https://www.youtube.com/watch?v=...
📹 Video ID: dQw4w9WgXcQ
📁 Output directory: /app/outputs/dQw4w9WgXcQ
🔧 Compiling workflow graph...
▶️  Executing workflow stages...
    Stage 1: Initial Analysis (download + multimodal LLM)
    Stage 2: Counter Intelligence (YouTube search)
    Stage 3: Prepare Claims (extract + filter)
    Stage 4: Claim Verification (web search + evidence)
    Stage 5: Generate Report (truthfulness scoring)
    Stage 6: Save Report (JSON + MD + HTML)
✅ Workflow completed successfully!
📊 Claims processed: 20
📄 Reports saved to: /app/outputs/dQw4w9WgXcQ
```

---

### Errors to Watch For

**Connection issues:**
```
❌ Failed to download video
❌ Connection timeout
```

**API errors:**
```
ERROR: 429 Too Many Requests  ← Rate limiting
ERROR: 400 Bad Request        ← Invalid input
ERROR: 500 Internal Error     ← Server issue
```

---

## 🌐 Monitor ngrok Traffic

See requests coming through ngrok:

**Open ngrok web interface:**
```bash
open http://localhost:4040
```

This shows:
- All requests from Streamlit → ngrok → your API
- Response times
- Status codes
- Request/response details

---

## 📊 Multiple Terminal Windows

**Recommended setup while testing:**

### Terminal 1: API Logs
```bash
cd /Users/ajjc/proj/verityngn-oss
./scripts/watch_api_logs.sh
```

### Terminal 2: ngrok Monitor
```bash
open http://localhost:4040
# Or keep ngrok terminal visible
```

### Terminal 3: Quick Commands
```bash
# Check API health
curl http://localhost:8080/health

# Check ngrok health  
curl https://oriented-flea-large.ngrok-free.app/health

# List reports
curl http://localhost:8080/api/v1/reports/list
```

---

## 🔄 Real-Time Monitoring Commands

### Watch API Container Status
```bash
watch -n 2 'docker compose ps api'
```

### Watch Disk Usage (if processing many videos)
```bash
watch -n 5 'du -sh outputs/*'
```

### Watch Report Count
```bash
watch -n 5 'ls -1 outputs/*/report.html | wc -l'
```

---

## 📝 Save Logs to File

### Save current processing logs
```bash
docker compose logs api > api_logs_$(date +%Y%m%d_%H%M%S).log
```

### Save and watch simultaneously
```bash
docker compose logs -f api | tee api_logs_$(date +%Y%m%d_%H%M%S).log
```

---

## 🆘 Troubleshooting Specific Issues

### Video stuck processing?

**Check logs for:**
```bash
docker compose logs api | grep -E "timeout|hang|stuck|waiting"
```

### Claims not being extracted?

**Check logs for:**
```bash
docker compose logs api | grep -E "Claims|extracted|processed"
```

### API not responding?

**Check container health:**
```bash
docker compose ps api
curl http://localhost:8080/health
```

**Restart if needed:**
```bash
docker compose restart api
```

---

## 🎯 Log Patterns to Recognize

### Normal Processing Flow

```
1. 🚀 Starting verification workflow
2. 📋 Extracting video metadata
3. ✅ Video metadata extracted
4. [Analysis happening - may take 5-10 min]
5. 📊 Claims processed: X
6. ✅ Workflow completed successfully!
```

### Claim Verification (Per Claim)

```
🔍 Verifying claim: "Statement here..."
🌐 Found X evidence sources
✅ Verdict: TRUE/FALSE/UNCERTAIN
```

### Report Generation

```
📝 Generating reports...
💾 Saved: report.json
💾 Saved: report.md  
💾 Saved: report.html
✅ Report generation complete
```

---

## 🚀 Quick Reference Card

```
╔════════════════════════════════════════════════════════╗
║           VERITYNGN API LOG COMMANDS                   ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  Watch (filtered):    ./scripts/watch_api_logs.sh     ║
║  Watch (all):         docker compose logs -f api      ║
║  Recent (50):         docker compose logs api --tail 50║
║  Search errors:       docker compose logs api | grep ERROR║
║                                                        ║
║  ngrok monitor:       open http://localhost:4040      ║
║  API health:          curl localhost:8080/health      ║
║                                                        ║
║  Stop watching:       Press Ctrl+C                    ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
```

---

## 📱 Monitor from Streamlit App

The Streamlit Community app shows processing status in real-time:
- Task ID
- Processing status
- Progress percentage
- Current message

But for **detailed logs**, you need to check your local API logs using the commands above.

---

**START MONITORING NOW:**

```bash
cd /Users/ajjc/proj/verityngn-oss
./scripts/watch_api_logs.sh
```

Then submit your test video in Streamlit and watch the logs! 🎬











