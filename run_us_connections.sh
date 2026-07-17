#!/usr/bin/env bash
# Search LinkedIn for US automation ICP and send connection requests (no notes)
set -euo pipefail
cd "$(dirname "$0")"

echo "== Search US audience + send connection requests =="
echo "    Searches LinkedIn for SaaS founders/ops leaders in the US"
echo "    Sends without notes. Use DRY_RUN=1 to preview."
echo ""
node send_connections.cjs

echo ""
echo "== Report to Slack =="
python3 send_connections_to_slack.py

echo ""
echo "Done."
echo "  DRY_RUN=1 ./run_us_connections.sh           — preview search + flow"
echo "  MAX_CONNECTIONS_PER_RUN=5 ./run_us_connections.sh  — smaller batch"
echo "  agent-browser --session linkedin_bot open https://www.linkedin.com/feed/"
