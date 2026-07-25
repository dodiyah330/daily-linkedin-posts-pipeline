#!/usr/bin/env bash
# Comment on LinkedIn posts that match hiring signals and/or your skill sets
set -euo pipefail
cd "$(dirname "$0")"

export MAX_COMMENTS_PER_RUN="${MAX_COMMENTS_PER_RUN:-15}"
export MAX_COMMENTS_PER_DAY="${MAX_COMMENTS_PER_DAY:-15}"
export COMMENT_DELAY_MS="${COMMENT_DELAY_MS:-20000}"

echo "== LinkedIn skill / hiring comments =="
echo "    run=$MAX_COMMENTS_PER_RUN/day=$MAX_COMMENTS_PER_DAY delay=${COMMENT_DELAY_MS}ms"
echo "    Config: linkedin_comments_config.json"
echo ""

if [[ "${DRY_RUN:-0}" == "1" ]]; then
  echo "DRY RUN — no comments will be posted"
fi

node comment_on_posts.cjs

echo ""
echo "Done. Log: linkedin-comments-run-log.json"
