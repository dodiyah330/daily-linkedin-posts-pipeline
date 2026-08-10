#!/usr/bin/env bash
# Send LinkedIn DMs to 1st-degree connections outside India (humanized + anti-restriction)
set -euo pipefail
cd "$(dirname "$0")"

# Human session defaults: small runs, longer gaps, up to ~15/day.
# Absolute ceilings in send_connection_dms.cjs cannot be raised via env.
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

echo "== Connection DMs (non-India, humanized) =="
echo "    variant=$DM_VARIANT run=$MAX_DMS_PER_RUN/day=$MAX_DMS_PER_DAY/hour=$MAX_DMS_PER_HOUR/week=$MAX_DMS_PER_WEEK"
echo "    delay=${DM_DELAY_MS}ms + jitter 0..${DM_DELAY_JITTER_MS}ms humanize=$DM_HUMANIZE cache=$DM_USE_CACHE"
echo "    Absolute max in code: 5/run, 15/day, 3/hour, 70/week (cannot bypass)"
echo "    Tip: 4–6 short runs/day >> one big burst"
echo ""

if [[ "${DRY_RUN:-0}" == "1" ]]; then
  echo "DRY RUN — no messages will be sent"
fi

node send_connection_dms.cjs

echo ""
echo "Done. Log: connection-dms-run-log.json"
echo "Tip: wait ~1h between runs (hourly cap). Prefer tomorrow once daily cap is hit."
