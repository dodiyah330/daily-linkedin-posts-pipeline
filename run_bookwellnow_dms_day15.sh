#!/usr/bin/env bash
# Fill remaining daily DM budget (up to 15) with BookWellNow → WP developer DMs.
# Continuous: one pass, no hourly sleep windows.
set -u
cd "$(dirname "$0")"

TARGET="${TARGET:-15}"
LOG="${LOG:-/tmp/bookwellnow_dms_day15.log}"

count_today() {
  python3 -c "
import json
from datetime import datetime, timezone
log=json.load(open('connection-dms-run-log.json'))
today=datetime.now(timezone.utc).strftime('%Y-%m-%d')
n=sum(1 for e in log if e.get('date')==today and e.get('status')=='sent' and not e.get('dry_run'))
print(n)
"
}

keep_browser_alive() {
  npx --yes agent-browser --session linkedin_bot open https://www.linkedin.com/feed/ >>"$LOG" 2>&1 || true
  url=$(npx --yes agent-browser --session linkedin_bot get url 2>/dev/null | tail -1 || true)
  if echo "$url" | grep -qiE 'login|uas/login'; then
    echo "Login wall — restarting Default profile" | tee -a "$LOG"
    npx --yes agent-browser --session linkedin_bot close >>"$LOG" 2>&1 || true
    sleep 2
    npx --yes agent-browser --session linkedin_bot --profile Default open https://www.linkedin.com/feed/ >>"$LOG" 2>&1 || true
  fi
}

n=$(count_today)
echo "== BookWellNow continuous day target $TARGET @ $(date -u +%Y-%m-%dT%H:%M:%SZ) ==" | tee -a "$LOG"
echo "Already sent today: $n / $TARGET" | tee -a "$LOG"

if [[ "$n" -ge "$TARGET" ]]; then
  echo "Daily target already hit ($n). Nothing to send until tomorrow." | tee -a "$LOG"
  exit 0
fi

keep_browser_alive || true

echo "--- Continuous session (no hourly sleeps) ---" | tee -a "$LOG"
DM_CONTINUOUS=1 MAX_DMS_PER_DAY=15 MAX_DMS_PER_HOUR=15 MAX_DMS_PER_RUN=15 \
  ./run_bookwellnow_connection_dms.sh 2>&1 | tee -a "$LOG"
code=${PIPESTATUS[0]:-0}

n=$(count_today)
echo "[$(date -u +%H:%M:%SZ)] finished: $n / $TARGET (exit=$code)" | tee -a "$LOG"
if [[ "$n" -ge "$TARGET" ]]; then
  echo "HIT TARGET $TARGET" | tee -a "$LOG"
else
  echo "Stopped at $n (check log for skips/failures/out of targets)." | tee -a "$LOG"
fi
echo "== Done $(date -u +%Y-%m-%dT%H:%M:%SZ) ==" | tee -a "$LOG"
