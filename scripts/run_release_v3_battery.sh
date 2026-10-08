#!/usr/bin/env bash
# Primary-10 OSS release battery (post-hackathon).
# Requires: VERTEX_LOCATION=global, verityngn CLI, sb1507.mp4 for row 2.
# Stop on 0 claims. Do not run during hummingbot freeze without operator green light.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
DATE="${BATTERY_DATE:-$(date -u +%Y-%m-%d)}"
OUT="${BATTERY_OUT:-$ROOT/outputs/release_v3_battery_$DATE}"
mkdir -p "$OUT"
export VERTEX_LOCATION="${VERTEX_LOCATION:-global}"
export PYTHONUNBUFFERED=1
LOG="$OUT/battery.log"
RESULTS="$OUT/results.jsonl"
: >"$RESULTS"
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] START out=$OUT VERTEX_LOCATION=$VERTEX_LOCATION" | tee -a "$LOG"

run_yt() {
  local id="$1" title="$2" tier="${3:-full}"
  local dest="$OUT/$id"
  mkdir -p "$dest"
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] RUN $id tier=$tier" | tee -a "$LOG"
  local rc=0
  if ! verityngn analyze --tier "$tier" --deep \
    -u "https://www.youtube.com/watch?v=${id}" \
    --title "$title" \
    -o "$dest" >>"$LOG" 2>&1; then
    rc=$?
  fi
  local claims=0
  local rj
  rj="$(ls "$dest"/*_report.json 2>/dev/null | head -1 || true)"
  if [[ -n "$rj" ]]; then
    claims="$(python3 -c "import json;d=json.load(open('$rj'));print(len(d.get('claims_breakdown') or d.get('claims') or []))" 2>/dev/null || echo 0)"
  fi
  python3 -c "import json;print(json.dumps({'id':'$id','title':'''$title''','tier':'$tier','rc':$rc,'claims':int('$claims'),'out':'$dest'}))" >>"$RESULTS"
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] DONE $id rc=$rc claims=$claims" | tee -a "$LOG"
  if [[ "$claims" == "0" ]]; then
    echo "STOP: 0 claims on $id — fix Vertex/location before continuing" | tee -a "$LOG"
    exit 2
  fi
}

run_local() {
  local id="$1" file="$2" title="$3"
  local dest="$OUT/$id"
  mkdir -p "$dest"
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] RUN local $id" | tee -a "$LOG"
  local rc=0
  if ! verityngn analyze --tier local-full --deep \
    -f "$file" --title "$title" -o "$dest" >>"$LOG" 2>&1; then
    rc=$?
  fi
  local claims=0
  local rj
  rj="$(ls "$dest"/*_report.json 2>/dev/null | head -1 || true)"
  if [[ -n "$rj" ]]; then
    claims="$(python3 -c "import json;d=json.load(open('$rj'));print(len(d.get('claims_breakdown') or d.get('claims') or []))" 2>/dev/null || echo 0)"
  fi
  python3 -c "import json;print(json.dumps({'id':'$id','title':'''$title''','tier':'local-full','rc':$rc,'claims':int('$claims'),'out':'$dest'}))" >>"$RESULTS"
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] DONE $id rc=$rc claims=$claims" | tee -a "$LOG"
  if [[ "$claims" == "0" ]]; then
    echo "STOP: 0 claims on $id" | tee -a "$LOG"
    exit 2
  fi
}

# Skip rows already proven if SKIP_PRIOR=1
if [[ "${SKIP_PRIOR:-1}" != "1" ]]; then
  run_yt "tLJC8hkK-ao" "Lipozem" "full"
  SB1507="${SB1507_MP4:-/Users/ajjc/Downloads/sb1507.mp4}"
  run_local "sb1507" "$SB1507" "SB1507 Oregon QSBS"
else
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] SKIP prior Lipozem + SB1507 (SKIP_PRIOR=1)" | tee -a "$LOG"
fi

run_yt "V7mYWOzdhpc" "Alex Karp CNBC tech dominance"
run_yt "ijRuuaaM6XM" "Karp Huang Power Lunch"
run_yt "fuq0Ncdsknk" "Jensen Huang CES 2025 keynote"
run_yt "dRgPbNJ5RJc" "Alex Karp WEF 2026"
run_yt "lb_ZJylekWo" "Satya Nadella Stargate Squawk"
run_yt "tSdWpsj1Cyo" "Odd Lots Franchise Gig Economy"
run_yt "7MXE1kDCY-k" "Butler Kahn Expert Deposition"
run_yt "RuinHdlpXvE" "Scott Carney Peptides Lab"

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] battery complete" | tee -a "$LOG"
