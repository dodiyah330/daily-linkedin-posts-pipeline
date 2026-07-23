#!/usr/bin/env bash
# OpenXcode company page — N-day batch (default 10): 2 posts/day (image + carousel)
set -euo pipefail
cd "$(dirname "$0")"

DAYS="${OPENXCODE_DAYS:-10}"

echo "== Fetch AI news =="
python3 fetch_ai_news_rss.py || true

echo "== Generate ${DAYS}-day OpenXcode batch (image + carousel each day) =="
OPENXCODE_DAYS="$DAYS" python3 generate_openxcode_batch.py

echo "== Build images + carousel PDFs =="
python3 build_openxcode_assets.py

echo "== Build schedule JSON =="
python3 prepare_openxcode_schedule.py

echo "== Send summary to Slack =="
python3 - << 'PY'
import json, os, urllib.request
token=channel=None
for line in open('.env'):
    if line.startswith('SLACK_BOT_TOKEN='): token=line.strip().split('=',1)[1]
    elif line.startswith('SLACK_CHANNEL_ID='): channel=line.strip().split('=',1)[1]
channel=channel or 'C0BEG7HAXHQ'
sched=json.load(open('schedule_openxcode.json'))
def send(t):
    req=urllib.request.Request('https://slack.com/api/chat.postMessage',
        data=json.dumps({'channel':channel,'text':t,'unfurl_links':False}).encode(),
        headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'}, method='POST')
    with urllib.request.urlopen(req) as r:
        print('ok' if json.loads(r.read().decode()).get('ok') else 'err', len(t))
send(
    "🏢 *OpenXCode — multi-day schedule*\n"
    f"{sched.get('scheduleNote','')}\n"
    f"Posts: {len(sched.get('posts',[]))}\n"
    "`SCHEDULE_FILE=schedule_openxcode.json POST_AS=OpenXCode node schedule_all_posts.cjs`"
)
for p in sched.get('posts',[])[:6]:
    kind='🖼 IMAGE' if p['type']=='infographic' else '📑 CAROUSEL'
    send(f"*{kind} — {p['date']} {p['time']}*\n{p.get('label','')}\n\n{p.get('caption','')[:500]}")
if len(sched.get('posts',[]))>6:
    send(f"_…plus {len(sched['posts'])-6} more posts in schedule_openxcode.json_")
print('Slack done')
PY

echo ""
echo "Done. Schedule on OpenXCode company page:"
echo "  agent-browser --session linkedin_bot --profile Default open https://www.linkedin.com/company/108839748/admin/dashboard/"
echo "  SCHEDULE_FILE=schedule_openxcode.json POST_AS=OpenXCode node schedule_all_posts.cjs"
