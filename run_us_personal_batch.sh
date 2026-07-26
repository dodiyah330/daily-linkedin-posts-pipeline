#!/usr/bin/env bash
# Personal LinkedIn — N-day US batch (default 10): 2 posts/day (image + carousel)
# Timed for US Eastern virality via IST account timezone.
set -euo pipefail
cd "$(dirname "$0")"

DAYS="${US_PERSONAL_DAYS:-10}"

echo "== Fetch AI news (optional US_NEWS_HOOK) =="
python3 fetch_ai_news_rss.py || true

echo "== Generate ${DAYS}-day US personal batch (image + carousel each day) =="
US_PERSONAL_DAYS="$DAYS" python3 generate_us_personal_batch.py

echo "== Build images + carousel PDFs =="
python3 build_us_personal_assets.py

echo "== Build schedule JSON (US Eastern peaks via IST) =="
python3 prepare_us_personal_schedule.py

echo "== Send summary to Slack =="
python3 - << 'PY'
import json, urllib.request
token=channel=None
for line in open('.env'):
    if line.startswith('SLACK_BOT_TOKEN='): token=line.strip().split('=',1)[1]
    elif line.startswith('SLACK_CHANNEL_ID='): channel=line.strip().split('=',1)[1]
channel=channel or 'C0BEG7HAXHQ'
sched=json.load(open('schedule_us_personal.json'))
def send(t):
    req=urllib.request.Request('https://slack.com/api/chat.postMessage',
        data=json.dumps({'channel':channel,'text':t,'unfurl_links':False}).encode(),
        headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'}, method='POST')
    with urllib.request.urlopen(req) as r:
        print('ok' if json.loads(r.read().decode()).get('ok') else 'err', len(t))
send(
    "🇺🇸 *Personal US LinkedIn — multi-day schedule*\n"
    f"{sched.get('scheduleNote','')}\n"
    f"Posts: {len(sched.get('posts',[]))}\n"
    "`LINKEDIN_START_URL=https://www.linkedin.com/feed/ SCHEDULE_FILE=schedule_us_personal.json node schedule_all_posts.cjs`"
)
for p in sched.get('posts',[])[:6]:
    kind='🖼 IMAGE' if p['type']=='infographic' else '📑 CAROUSEL'
    send(f"*{kind} — {p['date']} {p['time']} IST*\n{p.get('label','')}\n\n{p.get('caption','')[:500]}")
if len(sched.get('posts',[]))>6:
    send(f"_…plus {len(sched['posts'])-6} more posts in schedule_us_personal.json_")
print('Slack done')
PY

echo ""
echo "Done. Schedule on PERSONAL LinkedIn feed:"
echo "  agent-browser --session linkedin_bot --profile Default open https://www.linkedin.com/feed/"
echo "  LINKEDIN_START_URL=https://www.linkedin.com/feed/ SCHEDULE_FILE=schedule_us_personal.json node schedule_all_posts.cjs"
