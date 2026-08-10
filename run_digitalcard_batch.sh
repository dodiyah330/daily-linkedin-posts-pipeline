#!/usr/bin/env bash
# Digital Card Creator company page — N-day batch (default 10): 4 posts/day (2 image + 2 carousel)
set -euo pipefail
cd "$(dirname "$0")"

DAYS="${DIGITALCARD_DAYS:-10}"
COMPANY_ID="${DIGITALCARD_COMPANY_ID:-135187143}"
ADMIN_URL="https://www.linkedin.com/company/${COMPANY_ID}/admin/dashboard/"

echo "== Generate ${DAYS}-day Digital Card Creator batch (4 posts/day: 2 image + 2 carousel) =="
DIGITALCARD_DAYS="$DAYS" python3 generate_digitalcard_batch.py

echo "== Build images + carousel PDFs =="
python3 build_digitalcard_assets.py

echo "== Build schedule JSON =="
python3 prepare_digitalcard_schedule.py

echo "== Send summary to Slack =="
python3 - << 'PY'
import json, urllib.request
token=channel=None
for line in open('.env'):
    if line.startswith('SLACK_BOT_TOKEN='): token=line.strip().split('=',1)[1]
    elif line.startswith('SLACK_CHANNEL_ID='): channel=line.strip().split('=',1)[1]
channel=channel or 'C0BEG7HAXHQ'
sched=json.load(open('schedule_digitalcard.json'))
def send(t):
    req=urllib.request.Request('https://slack.com/api/chat.postMessage',
        data=json.dumps({'channel':channel,'text':t,'unfurl_links':False}).encode(),
        headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'}, method='POST')
    with urllib.request.urlopen(req) as r:
        print('ok' if json.loads(r.read().decode()).get('ok') else 'err', len(t))
send(
    "📇 *Digital Card Creator — multi-day schedule*\n"
    f"{sched.get('scheduleNote','')}\n"
    f"Posts: {len(sched.get('posts',[]))}\n"
    '`SCHEDULE_FILE=schedule_digitalcard.json POST_AS="Digital Card Creator" node schedule_all_posts.cjs`'
)
for p in sched.get('posts',[])[:8]:
    kind='🖼 IMAGE' if p['type']=='infographic' else '📑 CAROUSEL'
    send(f"*{kind} — {p['date']} {p['time']}*\n{p.get('label','')} · {p.get('audience','')}\n\n{p.get('caption','')[:500]}")
if len(sched.get('posts',[]))>8:
    send(f"_…plus {len(sched['posts'])-8} more posts in schedule_digitalcard.json_")
print('Slack done')
PY

echo ""
echo "Done. Schedule on Digital Card Creator company page:"
echo "  agent-browser --session linkedin_bot --profile Default open ${ADMIN_URL}"
echo '  SCHEDULE_FILE=schedule_digitalcard.json POST_AS="Digital Card Creator" node schedule_all_posts.cjs'
