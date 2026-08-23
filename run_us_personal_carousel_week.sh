#!/usr/bin/env bash
# Personal LinkedIn — 7-day carousel-only batch (3-4 slides each)
set -euo pipefail
cd "$(dirname "$0")"

BATCH="${US_PERSONAL_BATCH:-us_personal_carousel_week_20260823.json}"

if [[ ! -f "$BATCH" ]]; then
  echo "Batch file not found: $BATCH"
  exit 1
fi

echo "== Build carousel PDFs from $BATCH =="
US_PERSONAL_BATCH="$BATCH" python3 build_us_personal_carousel_assets.py

echo "== Build schedule JSON =="
python3 prepare_us_personal_carousel_schedule.py

echo ""
echo "Done. Schedule on PERSONAL LinkedIn feed:"
echo "  agent-browser --session linkedin_bot --profile Default open https://www.linkedin.com/feed/"
echo "  LINKEDIN_START_URL=https://www.linkedin.com/feed/ SCHEDULE_FILE=schedule_us_personal_carousel_week.json node schedule_all_posts.cjs"
