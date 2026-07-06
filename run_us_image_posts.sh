#!/usr/bin/env bash
# US-specific daily image posts — scheduled at US Eastern peak
set -euo pipefail
cd "$(dirname "$0")"

echo "== Fetch latest AI news (shared) =="
python3 fetch_ai_news_rss.py

echo "== Generate US image post captions =="
python3 generate_us_image_posts.py

echo "== Build US infographic PNGs =="
python3 build_us_image_posts.py

echo "== Build US schedule JSON =="
python3 prepare_us_image_schedule.py

echo "== Send to Slack =="
python3 send_us_image_to_slack.py

echo ""
echo "Done. Schedule on LinkedIn (US peak = 6:00 PM IST / 8:30 AM Eastern):"
echo "  agent-browser --session linkedin_bot --profile Default open https://www.linkedin.com/feed/"
echo "  SCHEDULE_FILE=schedule_us_image_posts.json node schedule_all_posts.cjs"
echo ""
echo "If LinkedIn account timezone is US Eastern, run:"
echo "  US_IMAGE_POST_TIME='8:30 AM' python3 prepare_us_image_schedule.py"
