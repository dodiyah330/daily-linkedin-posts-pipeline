#!/usr/bin/env python3
"""Send 14 automation lead posts (7 image + 7 text) to Slack."""
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
        print("OK" if resp.get("ok") else f"Error: {resp.get('error')}")


def upload_file(filepath, comment):
    size = os.path.getsize(filepath)
    g = urllib.request.urlopen(urllib.request.Request(
        "https://slack.com/api/files.getUploadURLExternal",
        data=f"filename={os.path.basename(filepath)}&length={size}".encode(),
        headers={"Authorization": f"Bearer {slack_token}", "Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    ))
    g_resp = json.loads(g.read().decode())
    if not g_resp.get("ok"):
        print(f"Upload URL error: {g_resp.get('error')}")
        return
    with open(filepath, "rb") as f:
        urllib.request.urlopen(urllib.request.Request(g_resp["upload_url"], data=f.read(), method="POST"))
    urllib.request.urlopen(urllib.request.Request(
        "https://slack.com/api/files.completeUploadExternal",
        data=json.dumps({
            "files": [{"id": g_resp["file_id"], "title": os.path.basename(filepath)}],
            "channel_id": channel,
            "initial_comment": comment,
        }).encode(),
        headers={"Authorization": f"Bearer {slack_token}", "Content-Type": "application/json; charset=utf-8"},
        method="POST",
    ))
    print(f"Uploaded {os.path.basename(filepath)}")


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
    exit("No automation_leads_*.txt")

posts_file = files[-1]
date_m = re.search(r"automation_leads_(\d{8})\.txt", posts_file)
date_str = (
    f"{date_m.group(1)[:4]}-{date_m.group(1)[4:6]}-{date_m.group(1)[6:8]}"
    if date_m else datetime.date.today().isoformat()
)
date_compact = date_str.replace("-", "")

with open(posts_file) as f:
    sections = split_sections(f.read())

note = "2 posts/day Mon–Sun (1 image + 1 text)"
if os.path.exists("schedule_automation_leads.json"):
    with open("schedule_automation_leads.json") as f:
        note = json.load(f).get("scheduleNote", note)

send(
    f"🎯 *Automation Lead Week — {date_str}*\n"
    f"14 posts: **2/day Mon–Sun**, one image + one text each day.\n"
    f"{note}\n"
    "`SCHEDULE_FILE=schedule_automation_leads.json node schedule_all_posts.cjs`"
)

# Prefer schedule order if available
if os.path.exists("schedule_automation_leads.json"):
    with open("schedule_automation_leads.json") as f:
        sched = json.load(f)
    for p in sched.get("posts", []):
        kind = "🖼 IMAGE" if p.get("type") == "infographic" else "📝 TEXT"
        send(f"*{kind} — {p.get('date')} {p.get('time')}*\n{p.get('label','')}\n\n{p.get('caption','')}")
else:
    for label, body in sections.items():
        send(f"*{label}*\n\n{body}")

img_dir = os.path.join(BASE, "automation-images", date_compact)
if not os.path.isdir(img_dir):
    batches = sorted(
        d for d in os.listdir(os.path.join(BASE, "automation-images"))
        if os.path.isdir(os.path.join(BASE, "automation-images", d))
    ) if os.path.isdir(os.path.join(BASE, "automation-images")) else []
    if batches:
        img_dir = os.path.join(BASE, "automation-images", batches[-1])

if os.path.isdir(img_dir):
    send("📸 *7 daily image posts* attached below")
    for i in range(1, 8):
        png = os.path.join(img_dir, f"automation-img-{i:02d}.png")
        if os.path.exists(png):
            upload_file(png, f"Automation image {i}/7 — {date_str}")

upload_file(posts_file, f"Raw automation leads batch — {date_str}")
print("Automation leads Slack delivery complete.")
