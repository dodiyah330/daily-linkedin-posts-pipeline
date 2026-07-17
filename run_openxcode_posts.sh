#!/usr/bin/env bash
# OpenXcode company page — 1 LinkedIn post per day
set -euo pipefail
cd "$(dirname "$0")"

echo "== Fetch latest AI news (shared, for Mon news→build archetype) =="
python3 fetch_ai_news_rss.py

echo "== Generate today's OpenXcode company post =="
python3 generate_openxcode_posts.py

echo "== Build schedule JSON (tomorrow) =="
python3 prepare_openxcode_schedule.py

echo "== Send to Slack =="
python3 send_openxcode_to_slack.py

echo ""
echo "Done. To schedule on the OpenXcode LinkedIn company page session:"
echo "  agent-browser --session linkedin_bot open https://www.linkedin.com/feed/"
echo "  SCHEDULE_FILE=schedule_openxcode.json node schedule_all_posts.cjs"
echo ""
echo "Override post time (LinkedIn account timezone):"
echo "  OPENXCODE_POST_TIME='11:00 AM' python3 prepare_openxcode_schedule.py"
