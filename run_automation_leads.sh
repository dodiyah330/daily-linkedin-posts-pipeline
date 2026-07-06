#!/usr/bin/env bash
# Weekly automation lead-gen pipeline (5 posts, Mon–Fri)
set -euo pipefail
cd "$(dirname "$0")"

echo "== Fetch latest AI news =="
python3 fetch_ai_news_rss.py

echo "== Generate 5 automation lead posts =="
python3 generate_automation_leads.py

echo "== Build 5 daily infographic images =="
python3 build_automation_images.py

echo "== Build schedule JSON =="
python3 prepare_automation_schedule.py

echo "== Send to Slack =="
python3 send_automation_leads_to_slack.py

echo ""
echo "Done. To schedule on LinkedIn:"
echo "  agent-browser --session linkedin_bot open https://www.linkedin.com/feed/"
echo "  SCHEDULE_FILE=schedule_automation_leads.json node schedule_all_posts.cjs"
