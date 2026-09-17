#!/usr/bin/env bash
# BookWellNow Facebook Page — 10 days × 3 native posts/day (feature intro).
set -euo pipefail
cd "$(dirname "$0")"

DAYS="${BOOKWELLNOW_DAYS:-10}"
START="${BOOKWELLNOW_START:-}"
GENERATE="${GENERATE:-1}"
SKIP_SLACK="${SKIP_SLACK:-0}"
DELETE_OLD="${DELETE_OLD:-1}"

latest_batch() {
  ls -1 bookwellnow_facebook_batch_*.json 2>/dev/null | sort | tail -n 1 || true
}

if [[ "$GENERATE" == "1" ]]; then
  echo "== Generate ${DAYS}-day Facebook batch (3 posts/day) =="
  if [[ -n "$START" ]]; then
    BOOKWELLNOW_DAYS="$DAYS" BOOKWELLNOW_START="$START" python3 generate_bookwellnow_facebook_batch.py
  else
    BOOKWELLNOW_DAYS="$DAYS" python3 generate_bookwellnow_facebook_batch.py
  fi
fi

BATCH="${BOOKWELLNOW_BATCH:-$(latest_batch)}"
if [[ -z "$BATCH" ]]; then
  echo "No bookwellnow_facebook_batch_*.json found"
  exit 1
fi
echo "== Batch: ${BATCH} =="

echo "== Build 4-slide albums =="
BOOKWELLNOW_BATCH="$BATCH" python3 build_bookwellnow_assets.py

echo "== Build Facebook schedule JSON =="
BOOKWELLNOW_BATCH="$BATCH" python3 prepare_bookwellnow_facebook_schedule.py

if [[ "$SKIP_SLACK" != "1" ]]; then
  echo "== Slack review =="
  python3 send_bookwellnow_facebook_to_slack.py || echo "(Slack send skipped / failed)"
fi

echo ""
echo "Done. Queue on the BookWellNow Facebook Page:"
if [[ "$DELETE_OLD" == "1" ]]; then
  echo "  DELETE_SCHEDULED=1 python3 schedule_all_facebook_posts.py"
else
  echo "  python3 schedule_all_facebook_posts.py"
fi
echo "  DRY_RUN=1 python3 schedule_all_facebook_posts.py"
echo "  python3 schedule_all_facebook_posts.py"
