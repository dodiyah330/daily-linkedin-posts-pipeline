#!/usr/bin/env bash
# Send LinkedIn DMs to 1st-degree connections outside India
set -euo pipefail
cd "$(dirname "$0")"

export MAX_DMS_PER_RUN="${MAX_DMS_PER_RUN:-10}"
export MAX_DMS_PER_DAY="${MAX_DMS_PER_DAY:-20}"
export DM_DELAY_MS="${DM_DELAY_MS:-18000}"
export DM_VARIANT="${DM_VARIANT:-hook}"

echo "== Connection DMs (non-India) =="
echo "    variant=$DM_VARIANT run=$MAX_DMS_PER_RUN/day=$MAX_DMS_PER_DAY delay=${DM_DELAY_MS}ms"
echo ""

if [[ "${DRY_RUN:-0}" == "1" ]]; then
  echo "DRY RUN — no messages will be sent"
fi

node send_connection_dms.cjs

echo ""
echo "Done. Log: connection-dms-run-log.json"
