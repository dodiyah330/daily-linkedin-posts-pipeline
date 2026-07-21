#!/usr/bin/env bash
# Weekly automation lead-gen pipeline — 14 posts (2/day Mon–Sun, 1 image + 1 text)
set -euo pipefail
cd "$(dirname "$0")"

echo "== Fetch latest AI news =="
python3 fetch_ai_news_rss.py

echo "== Generate 14 automation lead posts (7 image + 7 text) =="
python3 generate_automation_leads.py

echo "== Build 7 daily infographic images =="
python3 build_automation_images.py

echo "== Build schedule JSON (next Mon–Sun, 2/day) =="
python3 prepare_automation_schedule.py

echo "== Send to Slack =="
python3 send_automation_leads_to_slack.py

echo ""
echo "Done. To schedule on your PERSONAL LinkedIn profile:"
echo "  agent-browser --session linkedin_bot --profile Default open https://www.linkedin.com/feed/"
echo "  LINKEDIN_START_URL='https://www.linkedin.com/feed/' SCHEDULE_FILE=schedule_automation_leads.json node schedule_all_posts.cjs"
