#!/usr/bin/env bash
# Send LinkedIn DMs to 1st-degree connections outside India (safe rate limits)
set -euo pipefail
cd "$(dirname "$0")"

# Conservative defaults after prior restriction (~145 DMs in one day).
export MAX_DMS_PER_RUN="${MAX_DMS_PER_RUN:-5}"
export MAX_DMS_PER_DAY="${MAX_DMS_PER_DAY:-8}"
export MAX_DMS_PER_HOUR="${MAX_DMS_PER_HOUR:-4}"
export DM_DELAY_MS="${DM_DELAY_MS:-45000}"
export DM_DELAY_JITTER_MS="${DM_DELAY_JITTER_MS:-25000}"
export DM_VARIANT="${DM_VARIANT:-hook}"
export DM_USE_CACHE="${DM_USE_CACHE:-1}"

echo "== Connection DMs (non-India, safe mode) =="
echo "    variant=$DM_VARIANT run=$MAX_DMS_PER_RUN/day=$MAX_DMS_PER_DAY/hour=$MAX_DMS_PER_HOUR"
echo "    delay=${DM_DELAY_MS}ms + jitter 0..${DM_DELAY_JITTER_MS}ms cache=$DM_USE_CACHE"
echo ""

if [[ "${DRY_RUN:-0}" == "1" ]]; then
  echo "DRY RUN — no messages will be sent"
fi

node send_connection_dms.cjs

echo ""
echo "Done. Log: connection-dms-run-log.json"
echo "Tip: re-run later today only if under daily/hourly caps; otherwise resume tomorrow."
