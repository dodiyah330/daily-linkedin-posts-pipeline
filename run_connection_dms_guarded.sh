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

export MAX_DMS_PER_RUN="${MAX_DMS_PER_RUN:-10}"
export MAX_DMS_PER_DAY="${MAX_DMS_PER_DAY:-20}"
export DM_DELAY_MS="${DM_DELAY_MS:-12000}"
export DM_VARIANT="${DM_VARIANT:-hook}"
export DM_USE_CACHE="${DM_USE_CACHE:-1}"

echo "== Guarded connection DMs =="
echo "    watchdog_pid=$WATCHDOG_PID variant=$DM_VARIANT run=$MAX_DMS_PER_RUN"
node send_connection_dms.cjs
