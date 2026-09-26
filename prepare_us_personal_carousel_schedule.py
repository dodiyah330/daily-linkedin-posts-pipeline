#!/usr/bin/env python3
"""
Build schedule_us_personal_carousel_week.json from us_personal_carousel_week_*.json
One carousel per day, timed for US Eastern peaks via IST account timezone.
"""
import datetime
import glob
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))

files = sorted(glob.glob(os.path.join(BASE, "us_personal_carousel_week_*.json")))
if not files:
    raise SystemExit("No us_personal_carousel_week_*.json — run build_us_personal_carousel_assets.py")

BATCH = files[-1]
data = json.load(open(BATCH))
posts_days = data["posts"]

CAROUSEL_TIME = os.environ.get("US_PERSONAL_CAROUSEL_TIME")
CAROUSEL_BY_WD = {
    0: "9:30 PM",   # Mon  -> 12:00 PM ET
    1: "9:30 PM",   # Tue  -> 12:00 PM ET
    2: "9:30 PM",   # Wed  -> 12:00 PM ET
    3: "9:30 PM",   # Thu  -> 12:00 PM ET
    4: "9:00 PM",   # Fri  -> 11:30 AM ET
    5: "10:00 PM",  # Sat  -> 12:30 PM ET
    6: "10:00 PM",  # Sun  -> 12:30 PM ET
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


schedule_posts = []
missing = []

for day in posts_days:
    day_i = day.get("day") or len(schedule_posts) + 1
    date_str = day.get("date")
    if not date_str:
        raise SystemExit("day missing date")
    d = datetime.date.fromisoformat(date_str)
    pdf = find_pdf(day_i, date_str)
    if not pdf:
        missing.append(f"carousel day {day_i}")

    car_caption = ensure_caption_links((day.get("carousel") or {}).get("caption", "").strip())
    car_time = CAROUSEL_TIME or CAROUSEL_BY_WD[d.weekday()]

    schedule_posts.append({
        "id": day_i,
        "type": "carousel",
        "date": d.strftime("%m/%d/%Y"),
        "time": car_time,
        "caption": car_caption,
        "assetPath": pdf,
        "title": (day.get("topic") or "AI Automation")[:58].rstrip(" -:,"),
        "stream": "us-personal-carousel",
        "label": f"DAY {day_i} CAROUSEL — {day.get('carousel_archetype','')}",
        "topic": day.get("topic"),
        "slideCount": len((day.get("carousel") or {}).get("slides") or []),
    })

if missing:
    raise SystemExit("Missing assets: " + ", ".join(missing) + " — run build_us_personal_carousel_assets.py")

out = os.path.join(BASE, "schedule_us_personal_carousel_week.json")
payload = {
    "posts": schedule_posts,
    "generated": datetime.date.today().isoformat(),
    "stream": "us-personal-carousel",
    "scheduleNote": (
        f"{len(posts_days)} days × 1 carousel/day on PERSONAL feed. "
        "Each carousel has 3-4 slides. Times are IST mapped to US Eastern midday peaks."
    ),
    "startUrl": "https://www.linkedin.com/feed/",
    "audience": "US SaaS founders and ops leaders",
    "timezoneNote": "LinkedIn account TZ = IST. Carousel ≈ 12:00 PM ET.",
    "sourceFile": os.path.basename(BATCH),
}
json.dump(payload, open(out, "w"), indent=2)
print(f"Wrote {out} — {len(schedule_posts)} carousel posts")
print(payload["scheduleNote"])
for p in schedule_posts:
    print(f"  #{p['id']:02d} {p['date']} {p['time']:>8} [{p['slideCount']} slides] {p['label']}")
