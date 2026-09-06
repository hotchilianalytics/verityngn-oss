#!/usr/bin/env bash
# Quality battery: sb1507 + tL + 5 gallery videos (full/local-full + --deep)
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${QUALITY_BATTERY_OUT:-$ROOT/outputs/quality_battery_2026-09-04}"
cd "$ROOT" || exit 1
echo "ROOT=$ROOT OUT=$OUT"
# shellcheck disable=SC1091
set -a
[ -f .env ] && . ./.env
set +a
export DEEP_RESEARCH_MODEL="${DEEP_RESEARCH_MODEL:-gemini-3.8-flash}"
export DEEP_RESEARCH_FALLBACK_MODEL="${DEEP_RESEARCH_FALLBACK_MODEL:-gemini-3.6-flash}"
export DEEP_RESEARCH_PROMPT_VERSION="${DEEP_RESEARCH_PROMPT_VERSION:-dr_prompt_v2}"
export DEEP_SOURCE_HOPS="${DEEP_SOURCE_HOPS:-2}"
export VN_MAX_CLAIMS="${VN_MAX_CLAIMS:-100}"
# Force 3.8 for extract/verify/deep (override stale .env LLM_MODEL=2.5)
export LLM_MODEL=gemini-3.8-flash
export VERTEX_MODEL_NAME=gemini-3.8-flash
export AGENT_MODEL_NAME=gemini-3.8-flash
export VERIFICATION_MODEL_NAME=gemini-3.8-flash
# Force agentic REST for this battery (overrides .env VN_AGENTIC_VIDEO=0)
export VN_AGENTIC_VIDEO=1
export VN_VIDEO_MODEL="${VN_VIDEO_MODEL:-gemini-3.8-flash}"
export USE_VERTEX_YOUTUBE_URL=false
export USE_GENAI_YOUTUBE_URL=true
echo "models: LLM=$LLM_MODEL VERTEX=$VERTEX_MODEL_NAME AGENT=$AGENT_MODEL_NAME DR=$DEEP_RESEARCH_MODEL agentic=$VN_AGENTIC_VIDEO"

mkdir -p "$OUT"
RESULTS="$OUT/results.jsonl"
if [[ "${RESUME:-0}" != "1" ]]; then : > "$RESULTS"; fi
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] battery start model=$DEEP_RESEARCH_MODEL" | tee -a "$OUT/battery.log"

run_one() {
  local id="$1" kind="$2" target="$3" title="$4" tier="$5"
  local dest="$OUT/$id"
  mkdir -p "$dest"
  local t0
  t0=$(date +%s)
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] START $id tier=$tier" | tee -a "$OUT/battery.log"
  local rc=0
  if [[ "$kind" == "local" ]]; then
    verityngn analyze --file "$target" --title "$title" --tier "$tier" --deep -o "$dest" -v \
      >"$dest/run.stdout.log" 2>"$dest/run.stderr.log" || rc=$?
  else
    verityngn analyze "$target" --tier "$tier" --deep -o "$dest" -v \
      >"$dest/run.stdout.log" 2>"$dest/run.stderr.log" || rc=$?
  fi
  local t1 elapsed
  t1=$(date +%s)
  elapsed=$((t1 - t0))
  local report deep md claims
  report=$(ls "$dest"/*_report.json 2>/dev/null | head -1 || true)
  deep=$(ls "$dest"/*_deep_private_report.md 2>/dev/null | head -1 || true)
  claims=0
  if [[ -n "$report" ]]; then
    claims=$(python3 -c "import json; d=json.load(open('$report')); print(len(d.get('claims_breakdown') or d.get('claims') or []))" 2>/dev/null || echo 0)
  fi
  python3 - <<PY
import json, time
row={
  "id": "$id",
  "rc": $rc,
  "elapsed_s": $elapsed,
  "claims": int("$claims" or 0),
  "report": "$report",
  "deep_md": "$deep",
  "status": "ok" if $rc == 0 else "failed",
  "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
open("$RESULTS","a").write(json.dumps(row)+"\n")
print(json.dumps(row))
PY
  if [[ -n "$deep" ]]; then deep_flag=yes; else deep_flag=no; fi
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] DONE $id rc=$rc elapsed=${elapsed}s claims=$claims deep=$deep_flag" | tee -a "$OUT/battery.log"
}

# 1) SB1507 local
run_one "sb1507" "local" "/Users/ajjc/Downloads/sb1507.mp4" "SB1507 Oregon QSBS" "local-full"
# 2) Lipozem tL
run_one "tLJC8hkK-ao" "youtube" "https://www.youtube.com/watch?v=tLJC8hkK-ao" "Lipozem" "full"
# 3-7) live gallery
run_one "tSdWpsj1Cyo" "youtube" "https://www.youtube.com/watch?v=tSdWpsj1Cyo" "Odd Lots Franchise Gig Economy" "full"
run_one "7MXE1kDCY-k" "youtube" "https://www.youtube.com/watch?v=7MXE1kDCY-k" "Butler Kahn Expert Deposition" "full"
run_one "cBtOIRV4uPE" "youtube" "https://www.youtube.com/watch?v=cBtOIRV4uPE" "Legal Videography Deposition Sample" "full"
run_one "nvvw0oslqpE" "youtube" "https://www.youtube.com/watch?v=nvvw0oslqpE" "Brian Panish Punitive Damages" "full"
run_one "RuinHdlpXvE" "youtube" "https://www.youtube.com/watch?v=RuinHdlpXvE" "Scott Carney Peptides Lab" "full"

python3 - <<'PY'
import json
from pathlib import Path
out = Path("/Users/ajjc/proj/verityngn-oss/outputs/quality_battery_2026-09-04")
rows = [json.loads(l) for l in (out/"results.jsonl").read_text().splitlines() if l.strip()]
summary = {
  "n": len(rows),
  "ok": sum(1 for r in rows if r.get("status")=="ok"),
  "failed": sum(1 for r in rows if r.get("status")!="ok"),
  "rows": rows,
}
(out/"summary.json").write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
PY
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] battery complete" | tee -a "$OUT/battery.log"
