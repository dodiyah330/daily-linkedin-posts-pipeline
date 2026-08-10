#!/usr/bin/env bash
# BookWellNow DMs → non-India 1st-degree WordPress developers
# Continuous: fill remaining daily budget one-by-one (no hourly session sleeps).
set -euo pipefail
cd "$(dirname "$0")"

export DM_VARIANT="${DM_VARIANT:-bookwellnow}"
export DM_KEYWORDS="${DM_KEYWORDS:-WordPress developer|WooCommerce developer|WordPress freelancer}"
# Soft match — keyword search is the main filter (empty disables hard skip)
export DM_MATCH="${DM_MATCH:-wordpress,woocommerce,elementor,wp developer,wp engineer,wp freelancer,wordpress developer,wordpress engineer,wordpress freelancer,wordpress agency,divi,buddyboss}"
export DM_CACHE_FILE="${DM_CACHE_FILE:-connection-dms-bookwellnow-cache.json}"
export DM_USE_CACHE="${DM_USE_CACHE:-1}"
export DM_MAX_GEO_SEARCHES="${DM_MAX_GEO_SEARCHES:-4}"
export DM_SEARCH_BATCH="${DM_SEARCH_BATCH:-40}"
export DM_SCROLLS="${DM_SCROLLS:-5}"

# Continuous fill to day cap
export DM_CONTINUOUS="${DM_CONTINUOUS:-1}"
export MAX_DMS_PER_RUN="${MAX_DMS_PER_RUN:-15}"
export MAX_DMS_PER_DAY="${MAX_DMS_PER_DAY:-15}"
export MAX_DMS_PER_HOUR="${MAX_DMS_PER_HOUR:-15}"
export MAX_DMS_PER_WEEK="${MAX_DMS_PER_WEEK:-60}"
export DM_DELAY_MS="${DM_DELAY_MS:-8000}"
export DM_DELAY_JITTER_MS="${DM_DELAY_JITTER_MS:-7000}"
export DM_HUMANIZE="${DM_HUMANIZE:-1}"

echo "== BookWellNow → WordPress developers (non-India, continuous) =="
echo "    variant=$DM_VARIANT continuous=$DM_CONTINUOUS"
echo "    keywords=$DM_KEYWORDS"
echo "    cache=$DM_CACHE_FILE run/day/hour=$MAX_DMS_PER_RUN/$MAX_DMS_PER_DAY/$MAX_DMS_PER_HOUR"
echo "    delay=${DM_DELAY_MS}ms + jitter 0..${DM_DELAY_JITTER_MS}ms"
echo ""

exec ./run_connection_dms_guarded.sh
