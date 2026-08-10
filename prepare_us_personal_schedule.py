#!/usr/bin/env python3
"""
Build schedule_us_personal.json from us_personal_batch_*.json

Personal feed. 2 posts/day: IMAGE + CAROUSEL timed for US Eastern virality.
LinkedIn uses the account timezone (IST). Defaults map to US East Coast peaks:
  Image    ~6:00 PM IST  =  8:30 AM Eastern  (primary B2B peak)
  Carousel ~9:30 PM IST  = 12:00 PM Eastern  (midday secondary peak)
"""
import datetime
import glob
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))

files = sorted(glob.glob(os.path.join(BASE, "us_personal_batch_*.json")))
if not files:
    raise SystemExit("No us_personal_batch_*.json — run generate_us_personal_batch.py + build_us_personal_assets.py")

BATCH = files[-1]
data = json.load(open(BATCH))
posts_days = data["posts"]
date_compact = re.search(r"us_personal_batch_(\d{8})", os.path.basename(BATCH))
DATE_COMPACT = date_compact.group(1) if date_compact else datetime.date.today().isoformat().replace("-", "")
img_dir = data.get("assetDir") or os.path.join(BASE, "us-personal-images", DATE_COMPACT)

# Override both slots with a single env if needed
IMAGE_TIME = os.environ.get("US_PERSONAL_IMAGE_TIME")
CAROUSEL_TIME = os.environ.get("US_PERSONAL_CAROUSEL_TIME")

# Weekday tweaks — Tue/Thu slightly earlier (strongest US LinkedIn days)
IMAGE_BY_WD = {
    0: "6:00 PM",   # Mon  → 8:30 AM ET
    1: "5:30 PM",   # Tue  → 8:00 AM ET
    2: "6:00 PM",   # Wed  → 8:30 AM ET
    3: "5:30 PM",   # Thu  → 8:00 AM ET
    4: "6:30 PM",   # Fri  → 9:00 AM ET
    5: "7:00 PM",   # Sat  → 9:30 AM ET
    6: "7:00 PM",   # Sun  → 9:30 AM ET
}
CAROUSEL_BY_WD = {
    0: "9:30 PM",   # Mon  → 12:00 PM ET
    1: "9:30 PM",   # Tue  → 12:00 PM ET
    2: "9:30 PM",   # Wed  → 12:00 PM ET
    3: "9:30 PM",   # Thu  → 12:00 PM ET
    4: "9:00 PM",   # Fri  → 11:30 AM ET
    5: "10:00 PM",  # Sat  → 12:30 PM ET
    6: "10:00 PM",  # Sun  → 12:30 PM ET
}


def find_pdf(day_i, day_date):
    if posts_days[day_i - 1].get("_carousel_pdf") and os.path.exists(posts_days[day_i - 1]["_carousel_pdf"]):
        return posts_days[day_i - 1]["_carousel_pdf"]
    car_name = f"us-personal-day-{day_i:02d}"
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

    def ensure_caption_links(text):
        t = (text or "").strip()
        lines = []
        if "hitesh-dodiya.netlify.app" not in t.lower():
            lines.append("Portfolio: https://hitesh-dodiya.netlify.app/")
        if "linkedin.com/in/hiteshdodiyaa" not in t.lower():
            lines.append("LinkedIn: https://www.linkedin.com/in/hiteshdodiyaa")
        if lines:
            t = (t + "\n\n" + "\n".join(lines)).strip()
        return t

    img_caption = ensure_caption_links(img_caption)
    car_caption = ensure_caption_links(car_caption)
    img_time = IMAGE_TIME or IMAGE_BY_WD[d.weekday()]
    car_time = CAROUSEL_TIME or CAROUSEL_BY_WD[d.weekday()]

    day_posts = [
        {
            "id": None,
            "type": "infographic",
            "date": d.strftime("%m/%d/%Y"),
            "time": img_time,
            "caption": img_caption,
            "assetPath": png,
            "stream": "us-personal",
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
            # LinkedIn document titles hard-fail Done above 58 chars
            "title": (day.get("topic") or "AI Automation")[:58].rstrip(" -:,"),
            "stream": "us-personal",
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
    raise SystemExit("Missing assets: " + ", ".join(missing) + " — run build_us_personal_assets.py")

out = os.path.join(BASE, "schedule_us_personal.json")
payload = {
    "posts": schedule_posts,
    "generated": datetime.date.today().isoformat(),
    "stream": "us-personal",
    "scheduleNote": (
        f"{len(posts_days)} days × 2 posts (1 image + 1 carousel) on PERSONAL feed. "
        "US SaaS audience. Times are IST account TZ mapped to Eastern peaks "
        "(~8:00–9:30 AM ET image, ~12:00 PM ET carousel)."
    ),
    "startUrl": "https://www.linkedin.com/feed/",
    "audience": "US SaaS founders and ops leaders",
    "timezoneNote": "LinkedIn account TZ = IST. Image ≈ 8:30 AM ET, Carousel ≈ 12:00 PM ET.",
    "sourceFile": os.path.basename(BATCH),
}
json.dump(payload, open(out, "w"), indent=2)
print(f"Wrote {out} — {len(schedule_posts)} posts")
print(payload["scheduleNote"])
for p in schedule_posts:
    kind = "IMG" if p["type"] == "infographic" else "CAR"
    print(f"  #{p['id']:02d} {p['date']} {p['time']:>8} [{kind}] {p['label']}")
