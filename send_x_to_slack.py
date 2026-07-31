#!/usr/bin/env python3
"""Send latest x_posts_*.txt (or schedule_x.json captions) to Slack for review."""
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
    raise SystemExit("Error: SLACK_BOT_TOKEN not found in .env")

channel = slack_channel or "C0BEG7HAXHQ"


def send(text: str) -> None:
    print(f"Sending ({len(text)} chars)...")
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
        if not resp.get("ok"):
            print(f"Error: {resp.get('error')}")
        else:
            print("OK")


def split_sections(text: str) -> dict[str, str]:
    text = re.sub(r"^={50}\n", "", text.strip())
    chunks = [c.strip() for c in re.split(r"\n={50}\n", text) if c.strip()]
    sections: dict[str, str] = {}
    i = 0
    while i + 1 < len(chunks):
        if re.match(r"^\d+\.", chunks[i]):
            sections[chunks[i]] = chunks[i + 1]
            i += 2
        else:
            i += 1
    return sections


files = sorted(glob.glob("x_posts_*.txt"))
posts: list[tuple[str, str]] = []

if files:
    path = files[-1]
    date_m = re.search(r"x_posts_(\d{8})\.txt", path)
    date_label = (
        f"{date_m.group(1)[:4]}-{date_m.group(1)[4:6]}-{date_m.group(1)[6:8]}"
        if date_m
        else datetime.date.today().isoformat()
    )
    with open(path) as f:
        sections = split_sections(f.read())
    for header, body in sections.items():
        posts.append((header, body.strip()))
    source = path
else:
    if not os.path.exists("schedule_x.json"):
        raise SystemExit(
            "No x_posts_*.txt or schedule_x.json — run prepare_x_schedule.py first"
        )
    data = json.load(open("schedule_x.json"))
    date_label = data.get("generated", datetime.date.today().isoformat())
    for p in data.get("posts", []):
        media = f"\n[image: {p['assetPath']}]" if p.get("assetPath") else ""
        header = f"{p['id']}. {p.get('type', 'text').upper()} — {p['date']} {p['time']}"
        posts.append((header, p.get("caption", "") + media))
    source = "schedule_x.json"

send(f"*X posts for review* ({date_label}) — source `{source}` — {len(posts)} posts")
for header, body in posts:
    send(f"*{header}*\n```\n{body}\n```")

print(f"Done — {len(posts)} posts to Slack channel {channel}")
