#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${QUALITY_BATTERY_OUT:-$ROOT/outputs/quality_battery_2026-09-04}"
cd "$ROOT" || exit 1
set -a; [ -f .env ] && . ./.env; set +a
export DEEP_RESEARCH_MODEL=gemini-3.8-flash
export DEEP_RESEARCH_FALLBACK_MODEL=gemini-3.6-flash
export DEEP_RESEARCH_PROMPT_VERSION=dr_prompt_v2
export DEEP_SOURCE_HOPS=2
export VN_MAX_CLAIMS=100
export LLM_MODEL=gemini-3.8-flash
export VERTEX_MODEL_NAME=gemini-3.8-flash
export AGENT_MODEL_NAME=gemini-3.8-flash
export VERIFICATION_MODEL_NAME=gemini-3.8-flash
export VN_AGENTIC_VIDEO=1
export VN_VIDEO_MODEL=gemini-3.8-flash
export USE_VERTEX_YOUTUBE_URL=false
export USE_GENAI_YOUTUBE_URL=true
RESULTS="$OUT/results.jsonl"
mkdir -p "$OUT"
run_one() {
  local id="$1" url="$2" title="$3"
  local dest="$OUT/$id"
  mkdir -p "$dest"
  local t0 rc=0
  t0=$(date +%s)
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] START $id tier=full" | tee -a "$OUT/battery.log"
  verityngn analyze "$url" --tier full --deep -o "$dest" -v >"$dest/run.stdout.log" 2>"$dest/run.stderr.log" || rc=$?
  local t1 elapsed report deep claims=0 deep_flag=no
  t1=$(date +%s); elapsed=$((t1-t0))
  report=$(ls "$dest"/*_report.json 2>/dev/null | head -1 || true)
  deep=$(ls "$dest"/*_deep_private_report.md 2>/dev/null | head -1 || true)
  [[ -n "$deep" ]] && deep_flag=yes
  if [[ -n "$report" ]]; then
    claims=$(python3 -c "import json; d=json.load(open('$report')); print(len(d.get('claims_breakdown') or d.get('claims') or []))" 2>/dev/null || echo 0)
  fi
  python3 -c "import json,time; open('$RESULTS','a').write(json.dumps({'id':'$id','rc':$rc,'elapsed_s':$elapsed,'claims':int('$claims' or 0),'report':'$report','deep_md':'$deep','status':'ok' if $rc==0 else 'failed','finished_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})+'\n')"
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] DONE $id rc=$rc elapsed=${elapsed}s claims=$claims deep=$deep_flag" | tee -a "$OUT/battery.log"
}
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] gallery continuation start" | tee -a "$OUT/battery.log"
run_one tSdWpsj1Cyo "https://www.youtube.com/watch?v=tSdWpsj1Cyo" "Odd Lots"
run_one 7MXE1kDCY-k "https://www.youtube.com/watch?v=7MXE1kDCY-k" "Butler Kahn"
run_one cBtOIRV4uPE "https://www.youtube.com/watch?v=cBtOIRV4uPE" "Legal Videography"
run_one nvvw0oslqpE "https://www.youtube.com/watch?v=nvvw0oslqpE" "Brian Panish"
run_one RuinHdlpXvE "https://www.youtube.com/watch?v=RuinHdlpXvE" "Scott Carney"
python3 - <<'PY'
import json
from pathlib import Path
out=Path('/Users/ajjc/proj/verityngn-oss/outputs/quality_battery_2026-09-04')
rows=[json.loads(l) for l in (out/'results.jsonl').read_text().splitlines() if l.strip()]
# dedupe by id keeping last
by={}
for r in rows: by[r['id']]=r
rows=list(by.values())
summary={'n':len(rows),'ok':sum(1 for r in rows if r.get('status')=='ok'),'failed':sum(1 for r in rows if r.get('status')!='ok'),'rows':rows}
(out/'summary.json').write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
PY
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] gallery continuation complete" | tee -a "$OUT/battery.log"
