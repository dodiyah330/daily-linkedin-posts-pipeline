#!/usr/bin/env python3
"""
Build schedule_openxcode.json from openxcode_batch_*.json
Next N days, 2 posts/day: IMAGE (peak AM) + CAROUSEL (peak PM).
"""
import datetime
import glob
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))

files = sorted(glob.glob(os.path.join(BASE, "openxcode_batch_*.json")))
if not files:
    raise SystemExit("No openxcode_batch_*.json — run generate_openxcode_batch.py + build_openxcode_assets.py")

BATCH = files[-1]
data = json.load(open(BATCH))
posts_days = data["posts"]
date_compact = re.search(r"openxcode_batch_(\d{8})", os.path.basename(BATCH))
DATE_COMPACT = date_compact.group(1) if date_compact else datetime.date.today().isoformat().replace("-", "")
img_dir = data.get("assetDir") or os.path.join(BASE, "openxcode-images", DATE_COMPACT)

# Peak IST slots
IMAGE_TIME = os.environ.get("OPENXCODE_IMAGE_TIME", "11:00 AM")
CAROUSEL_TIME = os.environ.get("OPENXCODE_CAROUSEL_TIME", "4:00 PM")
# Slight weekday tweaks for stronger midweek peaks
IMAGE_BY_WD = {
    0: "1:00 PM",
    1: "11:00 AM",
    2: "12:00 PM",
    3: "11:00 AM",
    4: "1:00 PM",
    5: "11:00 AM",
    6: "11:00 AM",
}
CAROUSEL_BY_WD = {
    0: "4:00 PM",
    1: "4:00 PM",
    2: "4:00 PM",
    3: "4:00 PM",
    4: "4:00 PM",
    5: "3:00 PM",
    6: "3:00 PM",
}


def find_pdf(day_i, day_date):
    if posts_days[day_i - 1].get("_carousel_pdf") and os.path.exists(posts_days[day_i - 1]["_carousel_pdf"]):
        return posts_days[day_i - 1]["_carousel_pdf"]
    car_name = f"openxcode-day-{day_i:02d}"
    d = os.path.join(BASE, "carousel-routine", "output", day_date, car_name)
    if not os.path.isdir(d):
        return None
    pdfs = sorted(glob.glob(os.path.join(d, "*.pdf")))
    return pdfs[0] if pdfs else None


def find_png(day_i):
    p = os.path.join(img_dir, f"day-{day_i:02d}.png")
    if os.path.exists(p):
        return p
    if posts_days[day_i - 1].get("_image_png") and os.path.exists(posts_days[day_i - 1]["_image_png"]):
        return posts_days[day_i - 1]["_image_png"]
    return None


schedule_posts = []
pid = 1
missing = []

for day in posts_days:
    day_i = day.get("day") or (pid // 2 + 1)
    date_str = day.get("date")
    if not date_str:
        raise SystemExit("day missing date")
    d = datetime.date.fromisoformat(date_str)
    png = find_png(day_i)
    pdf = find_pdf(day_i, date_str)
    if not png:
        missing.append(f"image day {day_i}")
    if not pdf:
        missing.append(f"carousel day {day_i}")

    img_caption = (day.get("image") or {}).get("caption", "").strip()
    car_caption = (day.get("carousel") or {}).get("caption", "").strip()
    img_time = IMAGE_BY_WD[d.weekday()] if not os.environ.get("OPENXCODE_IMAGE_TIME") else IMAGE_TIME
    car_time = CAROUSEL_BY_WD[d.weekday()] if not os.environ.get("OPENXCODE_CAROUSEL_TIME") else CAROUSEL_TIME

    day_posts = [
        {
            "id": None,
            "type": "infographic",
            "date": d.strftime("%m/%d/%Y"),
            "time": img_time,
            "caption": img_caption,
            "assetPath": png,
            "stream": "openxcode",
            "label": f"DAY {day_i} IMAGE — {day.get('image_archetype','')}",
            "topic": day.get("topic"),
        },
        {
            "id": None,
            "type": "carousel",
            "date": d.strftime("%m/%d/%Y"),
            "time": car_time,
            "caption": car_caption,
            "assetPath": pdf,
            "title": (day.get("topic") or "OpenXcode")[:80],
            "stream": "openxcode",
            "label": f"DAY {day_i} CAROUSEL — {day.get('carousel_archetype','')}",
            "topic": day.get("topic"),
        },
    ]

    def sort_key(p):
        m = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM)", p["time"], re.I)
        h, mi, ap = int(m.group(1)), int(m.group(2)), m.group(3).upper()
        if ap == "PM" and h != 12:
            h += 12
        if ap == "AM" and h == 12:
            h = 0
        return (h, mi)

    for p in sorted(day_posts, key=sort_key):
        p["id"] = pid
        pid += 1
        schedule_posts.append(p)

if missing:
    raise SystemExit("Missing assets: " + ", ".join(missing) + " — run build_openxcode_assets.py")

out = os.path.join(BASE, "schedule_openxcode.json")
payload = {
    "posts": schedule_posts,
    "generated": datetime.date.today().isoformat(),
    "stream": "openxcode-company",
    "scheduleNote": (
        f"{len(posts_days)} days × 2 posts (1 image + 1 carousel). "
        "Image at mid-morning/midday peak; carousel afternoon peak (IST)."
    ),
    "companyPage": "https://www.linkedin.com/company/108839748/",
    "startUrl": "https://www.linkedin.com/company/108839748/admin/dashboard/",
    "postAs": "OpenXCode",
    "sourceFile": os.path.basename(BATCH),
}
json.dump(payload, open(out, "w"), indent=2)
print(f"Wrote {out} — {len(schedule_posts)} posts")
print(payload["scheduleNote"])
for p in schedule_posts:
    kind = "IMG" if p["type"] == "infographic" else "CAR"
    print(f"  #{p['id']:02d} {p['date']} {p['time']:>8} [{kind}] {p['label']}")
