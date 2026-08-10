#!/usr/bin/env bash
# BookWellNow company page — N-day batch (default 10): 4 posts/day (2 image + 2 carousel)
set -euo pipefail
cd "$(dirname "$0")"

DAYS="${BOOKWELLNOW_DAYS:-10}"
COMPANY_ID="${BOOKWELLNOW_COMPANY_ID:-130384348}"
ADMIN_URL="https://www.linkedin.com/company/${COMPANY_ID}/admin/dashboard/"
START="${BOOKWELLNOW_START:-}"

echo "== Generate ${DAYS}-day BookWellNow batch (2 images + 2 carousels each day) =="
if [[ -n "$START" ]]; then
  BOOKWELLNOW_DAYS="$DAYS" BOOKWELLNOW_START="$START" python3 generate_bookwellnow_batch.py
else
  BOOKWELLNOW_DAYS="$DAYS" python3 generate_bookwellnow_batch.py
fi

echo "== Build images + carousel PDFs =="
python3 build_bookwellnow_assets.py

echo "== Build schedule JSON =="
python3 prepare_bookwellnow_schedule.py

echo ""
echo "Done. Schedule on BookWellNow company page:"
echo "  agent-browser --session linkedin_bot --profile Default open ${ADMIN_URL}"
echo "  SCHEDULE_FILE=schedule_bookwellnow.json POST_AS=BookWellNow FORCE_GENERAL_BATCH=1 node schedule_all_posts.cjs"
