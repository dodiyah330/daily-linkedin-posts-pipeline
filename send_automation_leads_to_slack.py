#!/usr/bin/env python3
"""Send automation lead-gen posts to Slack."""
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
    exit(1)

channel = slack_channel or "C0BEG7HAXHQ"


def send(text):
    print(f"Sending ({len(text)} chars)...")
    req = urllib.request.Request(
        "https://slack.com/api/chat.postMessage",
        data=json.dumps({"channel": channel, "text": text, "unfurl_links": False, "unfurl_media": False}).encode(),
        headers={"Authorization": f"Bearer {slack_token}", "Content-Type": "application/json; charset=utf-8"},
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
    return sections


files = sorted(glob.glob("automation_leads_*.txt"))
if not files:
    print("No automation_leads_*.txt found — run generate_automation_leads.py first")
    exit(1)

posts_file = files[-1]
date_m = re.search(r"automation_leads_(\d{8})\.txt", posts_file)
date_str = (
    f"{date_m.group(1)[:4]}-{date_m.group(1)[4:6]}-{date_m.group(1)[6:8]}"
    if date_m else datetime.date.today().isoformat()
)

with open(posts_file) as f:
    sections = split_sections(f.read())

labels = [
    "1. NEWS → AUTOMATION",
    "2. CASE STUDY",
    "3. QUALIFYING POLL",
    "4. STEAL THIS WORKFLOW",
    "5. DIRECT OFFER",
]

send(
    f"🎯 *Automation Lead Posts — {date_str}*\n"
    "5 posts to attract AI automation clients. Schedule with:\n"
    "`SCHEDULE_FILE=schedule_automation_leads.json node schedule_all_posts.cjs`"
)

for label in labels:
    body = sections.get(label, "").strip()
    if body:
        send(body)

# Upload source file
size = os.path.getsize(posts_file)
g = urllib.request.urlopen(urllib.request.Request(
    "https://slack.com/api/files.getUploadURLExternal",
    data=f"filename={os.path.basename(posts_file)}&length={size}".encode(),
    headers={"Authorization": f"Bearer {slack_token}", "Content-Type": "application/x-www-form-urlencoded"},
    method="POST",
))
g_resp = json.loads(g.read().decode())
if g_resp.get("ok"):
    with open(posts_file, "rb") as f:
        urllib.request.urlopen(urllib.request.Request(g_resp["upload_url"], data=f.read(), method="POST"))
    urllib.request.urlopen(urllib.request.Request(
        "https://slack.com/api/files.completeUploadExternal",
        data=json.dumps({
            "files": [{"id": g_resp["file_id"], "title": os.path.basename(posts_file)}],
            "channel_id": channel,
            "initial_comment": f"Raw automation leads batch — {date_str}",
        }).encode(),
        headers={"Authorization": f"Bearer {slack_token}", "Content-Type": "application/json; charset=utf-8"},
        method="POST",
    ))
    print(f"Uploaded {posts_file}")

print("Automation leads Slack delivery complete.")
