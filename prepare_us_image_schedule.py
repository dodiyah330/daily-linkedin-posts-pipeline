#!/usr/bin/env python3
"""Build schedule_us_image_posts.json — Mon–Fri at US Eastern peak (default 6:00 PM IST = 8:30 AM ET)."""
import datetime
import glob
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))

# LinkedIn scheduler uses YOUR account timezone.
# Default: 6:00 PM IST ≈ 8:30 AM US Eastern (EDT) — B2B peak on East Coast feeds.
# If your LinkedIn timezone is US Eastern, set: US_IMAGE_POST_TIME="8:30 AM"
US_IMAGE_POST_TIME = os.environ.get("US_IMAGE_POST_TIME", "6:00 PM")
US_PEAK_ET_LABEL = os.environ.get("US_PEAK_ET_LABEL", "8:30 AM Eastern")

files = sorted(glob.glob(os.path.join(BASE, "us_image_posts_*.txt")))
if not files:
    raise SystemExit("No us_image_posts_*.txt — run generate_us_image_posts.py first")

POSTS_FILE = files[-1]
date_m = re.search(r"us_image_posts_(\d{8})\.txt", POSTS_FILE)
DATE_COMPACT = date_m.group(1) if date_m else datetime.date.today().isoformat().replace("-", "")

START = datetime.date.today() + datetime.timedelta(days=1)
days = []
d = START
while len(days) < 5:
    if d.weekday() < 5:
        days.append(d)
    d += datetime.timedelta(days=1)

LABELS = [
    "1. MON — US NEWS HOOK",
    "2. TUE — US OPS WIN",
    "3. WED — US STACK TIP",
    "4. THU — US WORKFLOW CARD",
    "5. FRI — US OFFER",
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


def png_path(post_id):
    p = os.path.join(BASE, "us-images", DATE_COMPACT, f"us-img-{post_id:02d}.png")
    if os.path.exists(p):
        return p
    batches = sorted(
        x for x in os.listdir(os.path.join(BASE, "us-images"))
        if os.path.isdir(os.path.join(BASE, "us-images", x))
    ) if os.path.isdir(os.path.join(BASE, "us-images")) else []
    if batches:
        p = os.path.join(BASE, "us-images", batches[-1], f"us-img-{post_id:02d}.png")
        if os.path.exists(p):
            return p
    return None


with open(POSTS_FILE) as f:
    sections = split_sections(f.read())

posts = []
missing = []
for i, (label, day) in enumerate(zip(LABELS, days), 1):
    asset = png_path(i)
    if not asset:
        missing.append(i)
    posts.append({
        "id": i,
        "type": "infographic",
        "date": day.strftime("%m/%d/%Y"),
        "time": US_IMAGE_POST_TIME,
        "caption": sections.get(label, "").strip(),
        "assetPath": asset,
        "stream": "us-image",
        "usPeakET": US_PEAK_ET_LABEL,
    })

if missing:
    raise SystemExit(f"Missing US PNGs for posts {missing}. Run: python3 build_us_image_posts.py")

out = os.path.join(BASE, "schedule_us_image_posts.json")
payload = {
    "posts": posts,
    "generated": datetime.date.today().isoformat(),
    "stream": "us-image-posts",
    "scheduleNote": f"US peak target: {US_PEAK_ET_LABEL}. Scheduler time: {US_IMAGE_POST_TIME} (LinkedIn account timezone).",
}
with open(out, "w") as f:
    json.dump(payload, f, indent=2)

print(f"Wrote {out} — {len(posts)} US image posts at {US_IMAGE_POST_TIME} ({US_PEAK_ET_LABEL})")
print(f"Dates: {days[0].strftime('%m/%d/%Y')} – {days[-1].strftime('%m/%d/%Y')}")
