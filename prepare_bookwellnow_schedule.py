#!/usr/bin/env python3
"""
Build schedule_bookwellnow.json from bookwellnow_batch_*.json
2 carousel posts/day (3-4 slides each).
"""
import datetime
import glob
import json
import os
import re

from bookwellnow_links import ensure_tracked_footer, site_url

BASE = os.path.dirname(os.path.abspath(__file__))

COMPANY_ID = os.environ.get("BOOKWELLNOW_COMPANY_ID", "130384348")
POST_AS = os.environ.get("BOOKWELLNOW_POST_AS", "BookWellNow")
SITE_URL = site_url("linkedin")

files = sorted(glob.glob(os.path.join(BASE, "bookwellnow_batch_*.json")))
if not files:
    raise SystemExit("No bookwellnow_batch_*.json — run generate + build first")

BATCH = files[-1]
data = json.load(open(BATCH))
posts_days = data["posts"]

SLOTS_BY_WD = {
    0: ("10:30 AM", "3:30 PM"),
    1: ("10:00 AM", "3:00 PM"),
    2: ("10:30 AM", "3:30 PM"),
    3: ("10:00 AM", "3:00 PM"),
    4: ("10:30 AM", "3:30 PM"),
    5: ("10:00 AM", "3:00 PM"),
    6: ("10:00 AM", "3:00 PM"),
}


def ensure_site(text, hiring=False):
    return ensure_tracked_footer(text, "linkedin", hiring=hiring)


def find_pdf(day_i, day_date, slot):
    day = posts_days[day_i - 1]
    key = f"_carousel_pdf_{slot}"
    if day.get(key) and os.path.exists(day[key]):
        return day[key]
    pdfs_map = day.get("_carousel_pdfs") or {}
    if pdfs_map.get(slot) and os.path.exists(pdfs_map[slot]):
        return pdfs_map[slot]
    car_name = f"bookwellnow-day-{day_i:02d}-{slot}"
    d = os.path.join(BASE, "carousel-routine", "output", day_date, car_name)
    if not os.path.isdir(d):
        # legacy names
        legacy = f"bookwellnow-day-{day_i:02d}" if slot in ("a", "am") else f"bookwellnow-day-{day_i:02d}-pm"
        d = os.path.join(BASE, "carousel-routine", "output", day_date, legacy)
    if not os.path.isdir(d):
        return None
    pdfs = sorted(glob.glob(os.path.join(d, "*.pdf")))
    return pdfs[0] if pdfs else None


def parse_time(t):
    m = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM)", t, re.I)
    h, mi, ap = int(m.group(1)), int(m.group(2)), m.group(3).upper()
    if ap == "PM" and h != 12:
        h += 12
    if ap == "AM" and h == 12:
        h = 0
    return (h, mi)


def bump_past_times(date_obj, times):
    now = datetime.datetime.now()
    if date_obj != now.date():
        return times
    out = []
    cursor = now + datetime.timedelta(minutes=40)
    if cursor.minute == 0 and cursor.second == 0:
        pass
    elif cursor.minute <= 30:
        cursor = cursor.replace(minute=30, second=0, microsecond=0)
    else:
        cursor = (cursor + datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    latest = datetime.datetime.combine(date_obj, datetime.time(23, 45))
    for t in times:
        h, mi = parse_time(t)
        slot_dt = datetime.datetime.combine(date_obj, datetime.time(h, mi))
        if slot_dt <= now:
            if cursor > latest:
                out.append("10:00 AM")
            else:
                ap = "AM" if cursor.hour < 12 else "PM"
                hh = cursor.hour % 12 or 12
                out.append(f"{hh}:{cursor.minute:02d} {ap}")
                cursor += datetime.timedelta(minutes=30)
                if cursor.minute not in (0, 30):
                    cursor = cursor.replace(minute=0 if cursor.minute < 30 else 30, second=0, microsecond=0)
        else:
            out.append(t)
    return out


def day_carousels(day):
    if day.get("carousels"):
        return list(enumerate(day["carousels"][:2], 1))
    out = []
    if day.get("carousel_am") or day.get("carousel"):
        out.append((1, day.get("carousel_am") or day.get("carousel")))
    if day.get("carousel_pm"):
        out.append((2, day.get("carousel_pm")))
    return out


schedule_posts = []
pid = 1
missing = []

for day in posts_days:
    day_i = day.get("day") or (pid // 2 + 1)
    date_str = day.get("date")
    if not date_str:
        raise SystemExit("day missing date")
    d = datetime.date.fromisoformat(date_str)
    times = list(SLOTS_BY_WD[d.weekday()])
    times = bump_past_times(d, times)
    cars = day_carousels(day)
    day_posts = []
    for idx, car in cars:
        slot = chr(ord("a") + idx - 1)
        asset = find_pdf(day_i, date_str, slot)
        if not asset:
            missing.append(f"carousel day {day_i} {slot}")
        arch = (car or {}).get("archetype") or (day.get("slots") or {}).get(f"carousel_{idx}", "")
        hiring = str(arch).startswith("HIRING")
        caption = ensure_site((car or {}).get("caption", ""), hiring=hiring)
        industry = (car or {}).get("industry") or day.get("industry") or "BookWellNow"
        title = ((car or {}).get("industry") or day.get("topic") or "BookWellNow")[:58].rstrip(" -:,")
        day_posts.append({
            "id": None,
            "type": "carousel",
            "date": d.strftime("%m/%d/%Y"),
            "time": times[min(idx - 1, len(times) - 1)],
            "caption": caption,
            "assetPath": asset,
            "title": title,
            "stream": "bookwellnow",
            "label": f"DAY {day_i} CAROUSEL {slot.upper()} — {arch}",
            "topic": day.get("topic"),
            "industry": industry,
        })

    for p in sorted(day_posts, key=lambda x: parse_time(x["time"])):
        p["id"] = pid
        pid += 1
        schedule_posts.append(p)

if missing:
    raise SystemExit("Missing assets: " + ", ".join(missing) + " — run build_bookwellnow_assets.py")

out = os.path.join(BASE, "schedule_bookwellnow.json")
payload = {
    "posts": schedule_posts,
    "generated": datetime.date.today().isoformat(),
    "stream": "bookwellnow-company",
    "scheduleNote": (
        f"{len(posts_days)} days × 2 carousel posts/day (3-4 slides). "
        "Company page BookWellNow. IST peaks. Analytics-led industries + 2 hiring posts. "
        "Site URL on every product caption."
    ),
    "companyPage": f"https://www.linkedin.com/company/{COMPANY_ID}/",
    "startUrl": f"https://www.linkedin.com/company/{COMPANY_ID}/admin/dashboard/",
    "postAs": POST_AS,
    "sourceFile": os.path.basename(BATCH),
}
json.dump(payload, open(out, "w"), indent=2)
print(f"Wrote {out} — {len(schedule_posts)} posts")
print(payload["scheduleNote"])
for p in schedule_posts:
    print(f"  #{p['id']:02d} {p['date']} {p['time']:>8} [CAR] {p['label']}")
