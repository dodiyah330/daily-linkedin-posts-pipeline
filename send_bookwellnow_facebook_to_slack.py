#!/usr/bin/env python3
"""Send BookWellNow Facebook schedule captions to Slack for review."""
import json
import os
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

slack_token = slack_channel = None
with open(".env") as f:
    for line in f:
        if line.startswith("SLACK_BOT_TOKEN="):
            slack_token = line.strip().split("=", 1)[1]
        elif line.startswith("SLACK_CHANNEL_ID="):
            slack_channel = line.strip().split("=", 1)[1]

if not slack_token:
    raise SystemExit("Error: SLACK_BOT_TOKEN not found in .env")

channel = slack_channel or "C0BEG7HAXHQ"
SCHEDULE = os.environ.get("SCHEDULE_FILE", "schedule_bookwellnow_facebook.json")


def send(text: str) -> None:
    req = urllib.request.Request(
        "https://slack.com/api/chat.postMessage",
        data=json.dumps(
            {
                "channel": channel,
                "text": text,
                "unfurl_links": False,
                "unfurl_media": False,
            }
        ).encode(),
        headers={
            "Authorization": f"Bearer {slack_token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as res:
        resp = json.loads(res.read().decode())
        print("OK" if resp.get("ok") else resp.get("error"))


if not os.path.exists(SCHEDULE):
    raise SystemExit(f"No {SCHEDULE} — run python3 prepare_bookwellnow_facebook_schedule.py")

data = json.load(open(SCHEDULE))
posts = data.get("posts") or []
send(
    f"*BookWellNow Facebook schedule* ({data.get('generated')}) — "
    f"{len(posts)} posts — `{os.path.basename(SCHEDULE)}`\n"
    f"{data.get('scheduleNote', '')}"
)
for p in posts:
    n = len(p.get("assetPaths") or [])
    send(
        f"*#{p.get('id')} {p.get('date')} {p.get('time')}* [{n} photos] {p.get('label')}\n"
        f"```\n{(p.get('caption') or '')[:3500]}\n```"
    )
print(f"Done — {len(posts)} posts to Slack channel {channel}")
