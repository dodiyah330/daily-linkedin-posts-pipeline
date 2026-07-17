#!/usr/bin/env python3
"""Send today's OpenXcode company post to Slack."""
import datetime
import glob
import json
import os
import re
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
    print("Error: SLACK_BOT_TOKEN not found")
    raise SystemExit(1)

channel = slack_channel or "C0BEG7HAXHQ"


def send(text):
    print(f"Sending ({len(text)} chars)...")
    req = urllib.request.Request(
        "https://slack.com/api/chat.postMessage",
        data=json.dumps({
            "channel": channel,
            "text": text,
            "unfurl_links": False,
            "unfurl_media": False,
        }).encode(),
        headers={
            "Authorization": f"Bearer {slack_token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as res:
        resp = json.loads(res.read().decode())
        if not resp.get("ok"):
            print(f"Error: {resp.get('error')}")
        else:
            print("OK")


def split_sections(text):
    text = re.sub(r"^={50}\n", "", text.strip())
    chunks = [c.strip() for c in re.split(r"\n={50}\n", text) if c.strip()]
    sections = {}
    i = 0
    while i + 1 < len(chunks):
        if re.match(r"^\d+\.", chunks[i]):
            sections[chunks[i]] = chunks[i + 1]
            i += 2
        else:
            i += 1
    if not sections and text.strip():
        sections["1. POST"] = text.strip()
    return sections


files = sorted(glob.glob("openxcode_posts_*.txt"))
if not files:
    raise SystemExit("No openxcode_posts_*.txt — run generate_openxcode_posts.py first")

posts_file = files[-1]
date_m = re.search(r"openxcode_posts_(\d{8})\.txt", posts_file)
date_str = (
    f"{date_m.group(1)[:4]}-{date_m.group(1)[4:6]}-{date_m.group(1)[6:8]}"
    if date_m else datetime.date.today().isoformat()
)

sched_note = "tomorrow @ 10:00 AM (LinkedIn timezone)"
sched_date = ""
if os.path.exists("schedule_openxcode.json"):
    with open("schedule_openxcode.json") as f:
        sched = json.load(f)
    sched_note = sched.get("scheduleNote", sched_note)
    if sched.get("posts"):
        p0 = sched["posts"][0]
        sched_date = f"{p0.get('date', '')} {p0.get('time', '')}".strip()

with open(posts_file) as f:
    sections = split_sections(f.read())

label, body = next(iter(sections.items())) if sections else ("POST", "")

send(
    f"🏢 *OpenXcode Company Post — {date_str}*\n"
    f"1 post/day for the OpenXcode LinkedIn company page.\n"
    f"Archetype: `{label}`\n"
    f"Schedule: `{sched_date or sched_note}`\n"
    "`SCHEDULE_FILE=schedule_openxcode.json node schedule_all_posts.cjs`"
)
send(f"*OpenXcode — {label}*\n\n{body.strip()}")
print("Done.")
