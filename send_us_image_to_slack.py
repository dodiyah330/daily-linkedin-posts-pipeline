#!/usr/bin/env python3
"""Send US image posts + PNGs to Slack."""
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
    exit("Error: SLACK_BOT_TOKEN not found")

channel = slack_channel or "C0BEG7HAXHQ"


def send(text):
    req = urllib.request.Request(
        "https://slack.com/api/chat.postMessage",
        data=json.dumps({"channel": channel, "text": text, "unfurl_links": False}).encode(),
        headers={"Authorization": f"Bearer {slack_token}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as res:
        resp = json.loads(res.read().decode())
        print("OK" if resp.get("ok") else resp.get("error"))


def upload_file(filepath, comment):
    size = os.path.getsize(filepath)
    g = json.loads(urllib.request.urlopen(urllib.request.Request(
        "https://slack.com/api/files.getUploadURLExternal",
        data=f"filename={os.path.basename(filepath)}&length={size}".encode(),
        headers={"Authorization": f"Bearer {slack_token}", "Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )).read().decode())
    if not g.get("ok"):
        return
    with open(filepath, "rb") as f:
        urllib.request.urlopen(urllib.request.Request(g["upload_url"], data=f.read(), method="POST"))
    urllib.request.urlopen(urllib.request.Request(
        "https://slack.com/api/files.completeUploadExternal",
        data=json.dumps({
            "files": [{"id": g["file_id"], "title": os.path.basename(filepath)}],
            "channel_id": channel,
            "initial_comment": comment,
        }).encode(),
        headers={"Authorization": f"Bearer {slack_token}", "Content-Type": "application/json"},
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


files = sorted(glob.glob("us_image_posts_*.txt"))
if not files:
    exit("No us_image_posts_*.txt")

posts_file = files[-1]
date_m = re.search(r"us_image_posts_(\d{8})\.txt", posts_file)
date_str = f"{date_m.group(1)[:4]}-{date_m.group(1)[4:6]}-{date_m.group(1)[6:8]}" if date_m else datetime.date.today().isoformat()
date_compact = date_str.replace("-", "")

sched_note = "6:00 PM IST ≈ 8:30 AM Eastern"
if os.path.exists("schedule_us_image_posts.json"):
    with open("schedule_us_image_posts.json") as f:
        sched_note = json.load(f).get("scheduleNote", sched_note)

with open(posts_file) as f:
    sections = split_sections(f.read())

send(
    f"🇺🇸 *US Image Posts — {date_str}*\n"
    f"Separate daily image posts for US SaaS audience.\n"
    f"Schedule: `{sched_note}`\n"
    "`SCHEDULE_FILE=schedule_us_image_posts.json node schedule_all_posts.cjs`"
)

for label in [
    "1. MON — US NEWS HOOK",
    "2. TUE — US OPS WIN",
    "3. WED — US STACK TIP",
    "4. THU — US WORKFLOW CARD",
    "5. FRI — US OFFER",
]:
    body = sections.get(label, "").strip()
    if body:
        send(body)

img_dir = os.path.join(BASE, "us-images", date_compact)
if os.path.isdir(img_dir):
    for i in range(1, 6):
        png = os.path.join(img_dir, f"us-img-{i:02d}.png")
        if os.path.exists(png):
            upload_file(png, f"US image post {i}/5 — {date_str}")

print("US image Slack delivery complete.")
