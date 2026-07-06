#!/usr/bin/env python3
"""Parse automation_leads_*.txt into schedule_automation_leads.json (5 image posts, Mon–Fri)."""
import datetime
import glob
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))

files = sorted(glob.glob(os.path.join(BASE, "automation_leads_*.txt")))
if not files:
    raise SystemExit("No automation_leads_*.txt — run generate_automation_leads.py first")

POSTS_FILE = files[-1]
date_m = re.search(r"automation_leads_(\d{8})\.txt", POSTS_FILE)
DATE_COMPACT = date_m.group(1) if date_m else datetime.date.today().isoformat().replace("-", "")

START = datetime.date.today() + datetime.timedelta(days=1)

# Mon–Fri slots (skip weekend)
days = []
d = START
while len(days) < 5:
    if d.weekday() < 5:
        days.append(d)
    d += datetime.timedelta(days=1)

TIMES = ["9:00 AM", "12:00 PM", "9:00 AM", "12:00 PM", "9:00 AM"]
LABELS = [
    "1. NEWS → AUTOMATION",
    "2. CASE STUDY",
    "3. QUALIFYING POLL",
    "4. STEAL THIS WORKFLOW",
    "5. DIRECT OFFER",
]


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


def find_image_path(post_id):
    png = os.path.join(BASE, "automation-images", DATE_COMPACT, f"automation-img-{post_id:02d}.png")
    if os.path.exists(png):
        return png
    # fallback: latest batch folder
    batches = sorted(
        d for d in os.listdir(os.path.join(BASE, "automation-images"))
        if os.path.isdir(os.path.join(BASE, "automation-images", d))
    ) if os.path.isdir(os.path.join(BASE, "automation-images")) else []
    if batches:
        png = os.path.join(BASE, "automation-images", batches[-1], f"automation-img-{post_id:02d}.png")
        if os.path.exists(png):
            return png
    return None


with open(POSTS_FILE) as f:
    sections = split_sections(f.read())

posts = []
missing_images = []
for i, (label, day, time) in enumerate(zip(LABELS, days, TIMES), 1):
    body = sections.get(label, "").strip()
    asset = find_image_path(i)
    if not asset:
        missing_images.append(i)
    post = {
        "id": i,
        "type": "infographic",
        "date": day.strftime("%m/%d/%Y"),
        "time": time,
        "caption": body,
    }
    if asset:
        post["assetPath"] = asset
    posts.append(post)

if missing_images:
    raise SystemExit(
        f"Missing image PNGs for posts {missing_images}. Run: python3 build_automation_images.py"
    )

out = os.path.join(BASE, "schedule_automation_leads.json")
with open(out, "w") as f:
    json.dump({"posts": posts, "generated": datetime.date.today().isoformat(), "stream": "automation-leads"}, f, indent=2)

print(f"Wrote {out} with {len(posts)} image posts")
print(f"Schedule: {days[0].strftime('%m/%d/%Y')} – {days[-1].strftime('%m/%d/%Y')}")
