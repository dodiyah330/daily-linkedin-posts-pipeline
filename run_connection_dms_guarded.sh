#!/usr/bin/env bash
# Guarded LinkedIn DM runner — keeps invite/inspect bots from stealing the browser.
set -euo pipefail
cd "$(dirname "$0")"

LOCK_FILE="/tmp/linkedin_connection_dms.lock"
if ! mkdir "$LOCK_FILE" 2>/dev/null; then
  echo "Another connection DM run is active ($LOCK_FILE). Aborting."
  exit 1
fi
trap 'rmdir "$LOCK_FILE" 2>/dev/null || true; kill $WATCHDOG_PID 2>/dev/null || true' EXIT

(
  while true; do
    pkill -f 'send_connections.cjs' 2>/dev/null || true
    pkill -f 'inspect_connect' 2>/dev/null || true
    pkill -f 'inspect_modal' 2>/dev/null || true
    pkill -f 'inspect_buttons' 2>/dev/null || true
    sleep 3
  done
) &
WATCHDOG_PID=$!

# Conservative defaults after prior restriction (~145 DMs in one day).
export MAX_DMS_PER_RUN="${MAX_DMS_PER_RUN:-5}"
export MAX_DMS_PER_DAY="${MAX_DMS_PER_DAY:-8}"
export MAX_DMS_PER_HOUR="${MAX_DMS_PER_HOUR:-4}"
export DM_DELAY_MS="${DM_DELAY_MS:-45000}"
export DM_DELAY_JITTER_MS="${DM_DELAY_JITTER_MS:-25000}"
export DM_VARIANT="${DM_VARIANT:-hook}"
export DM_USE_CACHE="${DM_USE_CACHE:-1}"

echo "== Guarded connection DMs (safe mode) =="
echo "    watchdog_pid=$WATCHDOG_PID variant=$DM_VARIANT"
echo "    run=$MAX_DMS_PER_RUN/day=$MAX_DMS_PER_DAY/hour=$MAX_DMS_PER_HOUR"
echo "    delay=${DM_DELAY_MS}ms + jitter 0..${DM_DELAY_JITTER_MS}ms"
node send_connection_dms.cjs
