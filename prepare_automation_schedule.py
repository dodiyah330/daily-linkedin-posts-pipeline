#!/usr/bin/env python3
"""
Build schedule_automation_leads.json — 14 posts (2/day Mon–Sun).

Each day: 1 IMAGE (infographic) at peak time + 1 TEXT at secondary peak.
"""
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

# Start from next Monday for a clean Mon–Sun week (override with START_DATE=YYYY-MM-DD)
start_env = os.environ.get("START_DATE")
if start_env:
    START = datetime.date.fromisoformat(start_env)
else:
    d = datetime.date.today() + datetime.timedelta(days=1)
    while d.weekday() != 0:  # Monday
        d += datetime.timedelta(days=1)
    START = d

days = [START + datetime.timedelta(days=i) for i in range(7)]  # Mon–Sun

# Peak IST: image earlier (stronger slot), text later
IMAGE_TIMES = {
    0: "1:00 PM",   # Mon
    1: "11:00 AM",  # Tue
    2: "12:00 PM",  # Wed
    3: "11:00 AM",  # Thu
    4: "1:00 PM",   # Fri
    5: "11:00 AM",  # Sat
    6: "11:00 AM",  # Sun
}
TEXT_TIMES = {
    0: "4:00 PM",
    1: "4:00 PM",
    2: "4:00 PM",
    3: "4:00 PM",
    4: "4:00 PM",
    5: "3:00 PM",
    6: "3:00 PM",
}

IMAGE_LABELS = [
    "1. MON IMAGE — NEWS → AUTOMATION",
    "3. TUE IMAGE — CASE STUDY",
    "5. WED IMAGE — QUALIFYING POLL",
    "7. THU IMAGE — WORKFLOW CARD",
    "9. FRI IMAGE — DIRECT OFFER",
    "11. SAT IMAGE — PAIN → AUTOMATION",
    "13. SUN IMAGE — MINI WIN",
]
TEXT_LABELS = [
    "2. MON TEXT — BUILDER TIP",
    "4. TUE TEXT — MYTH BUST",
    "6. WED TEXT — STEAL THIS WORKFLOW",
    "8. THU TEXT — CLIENT LESSON",
    "10. FRI TEXT — TOOL ANGLE",
    "12. SAT TEXT — FAQ",
    "14. SUN TEXT — SOFT OFFER",
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


def find_image_path(image_idx):
    """image_idx is 1..7 for Mon..Sun image posts."""
    png = os.path.join(BASE, "automation-images", DATE_COMPACT, f"automation-img-{image_idx:02d}.png")
    if os.path.exists(png):
        return png
    batches = sorted(
        d for d in os.listdir(os.path.join(BASE, "automation-images"))
        if os.path.isdir(os.path.join(BASE, "automation-images", d))
    ) if os.path.isdir(os.path.join(BASE, "automation-images")) else []
    if batches:
        png = os.path.join(BASE, "automation-images", batches[-1], f"automation-img-{image_idx:02d}.png")
        if os.path.exists(png):
            return png
    return None


with open(POSTS_FILE) as f:
    sections = split_sections(f.read())

posts = []
missing_images = []
post_id = 1

for day_i, day in enumerate(days):
    img_label = IMAGE_LABELS[day_i]
    txt_label = TEXT_LABELS[day_i]
    img_body = sections.get(img_label, "").strip()
    txt_body = sections.get(txt_label, "").strip()
    if not img_body:
        raise SystemExit(f"Missing section: {img_label}")
    if not txt_body:
        raise SystemExit(f"Missing section: {txt_label}")

    asset = find_image_path(day_i + 1)
    if not asset:
        missing_images.append(day_i + 1)

    # Order by time within the day (image often earlier except Mon/Fri)
    img_time = IMAGE_TIMES[day.weekday()]
    txt_time = TEXT_TIMES[day.weekday()]

    day_posts = [
        {
            "id": None,
            "type": "infographic",
            "date": day.strftime("%m/%d/%Y"),
            "time": img_time,
            "caption": img_body,
            "label": img_label,
            "stream": "automation-leads",
            "assetPath": asset,
        },
        {
            "id": None,
            "type": "text",
            "date": day.strftime("%m/%d/%Y"),
            "time": txt_time,
            "caption": txt_body,
            "label": txt_label,
            "stream": "automation-leads",
        },
    ]
    # Sort by parsed time so LinkedIn order is chronological
    def sort_key(p):
        m = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM)", p["time"], re.I)
        h, mi, ap = int(m.group(1)), int(m.group(2)), m.group(3).upper()
        if ap == "PM" and h != 12:
            h += 12
        if ap == "AM" and h == 12:
            h = 0
        return (h, mi)

    for p in sorted(day_posts, key=sort_key):
        p["id"] = post_id
        post_id += 1
        if p["type"] == "infographic" and not p.get("assetPath"):
            p.pop("assetPath", None)
        posts.append(p)

if missing_images:
    raise SystemExit(
        f"Missing image PNGs for day images {missing_images}. Run: python3 build_automation_images.py"
    )

out = os.path.join(BASE, "schedule_automation_leads.json")
payload = {
    "posts": posts,
    "generated": datetime.date.today().isoformat(),
    "stream": "automation-leads",
    "scheduleNote": (
        "Personal profile: 2 posts/day Mon–Sun (1 image + 1 text). "
        "Image at peak IST; text at secondary afternoon slot."
    ),
}
with open(out, "w") as f:
    json.dump(payload, f, indent=2)

print(f"Wrote {out} with {len(posts)} posts (7 image + 7 text)")
print(f"Week: {days[0].strftime('%m/%d/%Y')} – {days[-1].strftime('%m/%d/%Y')}")
for p in posts:
    kind = "IMG " if p["type"] == "infographic" else "TEXT"
    print(f"  #{p['id']:02d} {p['date']} {p['time']:>8} [{kind}] {p['label']}")
