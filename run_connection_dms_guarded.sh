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

# Human session defaults: small runs, longer gaps, up to ~15/day.
export MAX_DMS_PER_RUN="${MAX_DMS_PER_RUN:-3}"
export MAX_DMS_PER_DAY="${MAX_DMS_PER_DAY:-15}"
export MAX_DMS_PER_HOUR="${MAX_DMS_PER_HOUR:-2}"
export MAX_DMS_PER_WEEK="${MAX_DMS_PER_WEEK:-60}"
export DM_DELAY_MS="${DM_DELAY_MS:-180000}"
export DM_DELAY_JITTER_MS="${DM_DELAY_JITTER_MS:-120000}"
export DM_HUMANIZE="${DM_HUMANIZE:-1}"
export DM_VARIANT="${DM_VARIANT:-auto}"
export DM_USE_CACHE="${DM_USE_CACHE:-1}"
export DM_SCROLLS="${DM_SCROLLS:-4}"
export DM_SEARCH_BATCH="${DM_SEARCH_BATCH:-25}"
export DM_MAX_GEO_SEARCHES="${DM_MAX_GEO_SEARCHES:-3}"

echo "== Guarded connection DMs (humanized) =="
echo "    watchdog_pid=$WATCHDOG_PID variant=$DM_VARIANT humanize=$DM_HUMANIZE continuous=${DM_CONTINUOUS:-0}"
echo "    run=$MAX_DMS_PER_RUN/day=$MAX_DMS_PER_DAY/hour=$MAX_DMS_PER_HOUR/week=$MAX_DMS_PER_WEEK"
echo "    delay=${DM_DELAY_MS}ms + jitter 0..${DM_DELAY_JITTER_MS}ms"
node send_connection_dms.cjs
