#!/usr/bin/env bash
# Search LinkedIn for US automation ICP and send until weekly limit
set -euo pipefail
cd "$(dirname "$0")"

export RUN_UNTIL_WEEKLY_LIMIT=1

echo "== US connection outreach (until weekly limit) =="
echo "    Searches LinkedIn for SaaS founders/ops leaders in the US"
echo "    Sends without notes until LinkedIn blocks further invites"
echo ""
node send_connections.cjs

echo ""
echo "== Report to Slack =="
python3 send_connections_to_slack.py

echo ""
echo "Done."
