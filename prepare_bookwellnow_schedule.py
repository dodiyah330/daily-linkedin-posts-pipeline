#!/usr/bin/env python3
"""
Build schedule_bookwellnow.json from bookwellnow_batch_*.json
Supports 4 posts/day: image_am, carousel_am, image_pm, carousel_pm
"""
import datetime
import glob
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))

COMPANY_ID = os.environ.get("BOOKWELLNOW_COMPANY_ID", "130384348")
POST_AS = os.environ.get("BOOKWELLNOW_POST_AS", "BookWellNow")
SITE_URL = "https://bookwellnow.com/"

files = sorted(glob.glob(os.path.join(BASE, "bookwellnow_batch_*.json")))
if not files:
    raise SystemExit("No bookwellnow_batch_*.json — run generate + build first")

BATCH = files[-1]
data = json.load(open(BATCH))
posts_days = data["posts"]
date_compact = re.search(r"bookwellnow_batch_(\d{8})", os.path.basename(BATCH))
DATE_COMPACT = date_compact.group(1) if date_compact else datetime.date.today().isoformat().replace("-", "")
img_dir = data.get("assetDir") or os.path.join(BASE, "bookwellnow-images", DATE_COMPACT)

# 4 IST peak slots / day
SLOTS_BY_WD = {
    # weekday: (img_am, car_am, img_pm, car_pm)
    0: ("10:30 AM", "1:00 PM", "3:30 PM", "6:00 PM"),
    1: ("10:00 AM", "12:30 PM", "3:00 PM", "5:30 PM"),
    2: ("10:30 AM", "1:00 PM", "3:30 PM", "6:00 PM"),
    3: ("10:00 AM", "12:30 PM", "3:00 PM", "5:30 PM"),
    4: ("10:30 AM", "1:00 PM", "3:30 PM", "6:00 PM"),
    5: ("10:00 AM", "12:00 PM", "3:00 PM", "5:00 PM"),
    6: ("10:00 AM", "12:00 PM", "3:00 PM", "5:00 PM"),
}


def ensure_site(text):
    t = (text or "").strip()
    if "bookwellnow.com" not in t.lower():
        t = (t + f"\n\nStart free: {SITE_URL}").strip()
    return t


def find_pdf(day_i, day_date, slot="am"):
    day = posts_days[day_i - 1]
    key = f"_carousel_pdf_{slot}"
    if day.get(key) and os.path.exists(day[key]):
        return day[key]
    if slot == "am" and day.get("_carousel_pdf") and os.path.exists(day["_carousel_pdf"]):
        return day["_carousel_pdf"]
    car_name = f"bookwellnow-day-{day_i:02d}" if slot == "am" else f"bookwellnow-day-{day_i:02d}-pm"
    d = os.path.join(BASE, "carousel-routine", "output", day_date, car_name)
    if not os.path.isdir(d):
        return None
    pdfs = sorted(glob.glob(os.path.join(d, "*.pdf")))
    return pdfs[0] if pdfs else None


def find_png(day_i, slot="am"):
    day = posts_days[day_i - 1]
    key = f"_image_png_{slot}"
    if day.get(key) and os.path.exists(day[key]):
        return day[key]
    p = os.path.join(img_dir, f"day-{day_i:02d}-{slot}.png")
    if os.path.exists(p):
        return p
    if slot == "am":
        p2 = os.path.join(img_dir, f"day-{day_i:02d}.png")
        if os.path.exists(p2):
            return p2
        if day.get("_image_png") and os.path.exists(day["_image_png"]):
            return day["_image_png"]
    return None


def parse_time(t):
    m = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM)", t, re.I)
    h, mi, ap = int(m.group(1)), int(m.group(2)), m.group(3).upper()
    if ap == "PM" and h != 12:
        h += 12
    if ap == "AM" and h == 12:
        h = 0
    return (h, mi)


def bump_past_times(date_obj, times):
    """If scheduling for today, push any past slots forward in 30-min steps (never past 11:45 PM)."""
    now = datetime.datetime.now()
    if date_obj != now.date():
        return times
    out = []
    cursor = now + datetime.timedelta(minutes=40)
    # round up to next :00 / :30
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
                # cannot fit tonight — keep original (scheduler may skip) but prefer next-day morning
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


schedule_posts = []
pid = 1
missing = []

for day in posts_days:
    day_i = day.get("day") or (pid // 4 + 1)
    date_str = day.get("date")
    if not date_str:
        raise SystemExit("day missing date")
    d = datetime.date.fromisoformat(date_str)
    times = list(SLOTS_BY_WD[d.weekday()])
    times = bump_past_times(d, times)

    has_pm = bool(day.get("image_pm") or day.get("carousel_pm"))
    specs = [
        ("infographic", "am", day.get("image_am") or day.get("image"), times[0], day.get("image_archetype") or day.get("slots", {}).get("image_am", "")),
        ("carousel", "am", day.get("carousel_am") or day.get("carousel"), times[1], day.get("carousel_archetype") or day.get("slots", {}).get("carousel_am", "")),
    ]
    if has_pm:
        specs.extend([
            ("infographic", "pm", day.get("image_pm"), times[2], day.get("image_pm_archetype") or day.get("slots", {}).get("image_pm", "")),
            ("carousel", "pm", day.get("carousel_pm"), times[3], day.get("carousel_pm_archetype") or day.get("slots", {}).get("carousel_pm", "")),
        ])

    day_posts = []
    for typ, slot, body, when, arch in specs:
        if not body:
            continue
        if typ == "infographic":
            asset = find_png(day_i, slot)
            if not asset:
                missing.append(f"image day {day_i} {slot}")
            caption = ensure_site((body or {}).get("caption", ""))
            day_posts.append({
                "id": None,
                "type": "infographic",
                "date": d.strftime("%m/%d/%Y"),
                "time": when,
                "caption": caption,
                "assetPath": asset,
                "stream": "bookwellnow",
                "label": f"DAY {day_i} IMAGE {slot.upper()} — {arch}",
                "topic": day.get("topic"),
                "industry": day.get("industry"),
            })
        else:
            asset = find_pdf(day_i, date_str, slot)
            if not asset:
                missing.append(f"carousel day {day_i} {slot}")
            caption = ensure_site((body or {}).get("caption", ""))
            title = (day.get("topic") or "BookWellNow")[:58].rstrip(" -:,")
            if slot == "pm":
                title = (title[:50] + " · New").rstrip()[:58]
            day_posts.append({
                "id": None,
                "type": "carousel",
                "date": d.strftime("%m/%d/%Y"),
                "time": when,
                "caption": caption,
                "assetPath": asset,
                "title": title,
                "stream": "bookwellnow",
                "label": f"DAY {day_i} CAROUSEL {slot.upper()} — {arch}",
                "topic": day.get("topic"),
                "industry": day.get("industry"),
            })

    for p in sorted(day_posts, key=lambda x: parse_time(x["time"])):
        p["id"] = pid
        pid += 1
        schedule_posts.append(p)

if missing:
    raise SystemExit("Missing assets: " + ", ".join(missing) + " — run build_bookwellnow_assets.py")

out = os.path.join(BASE, "schedule_bookwellnow.json")
ppd = 4 if any(p.get("image_pm") for p in posts_days) else 2
payload = {
    "posts": schedule_posts,
    "generated": datetime.date.today().isoformat(),
    "stream": "bookwellnow-company",
    "scheduleNote": (
        f"{len(posts_days)} days × {ppd} posts/day (2 images + 2 carousels). "
        "Company page BookWellNow. IST peaks. Site URL on every caption. "
        "New features: Google Calendar, Meet, Custom Fields, Buffer, Reschedule, Notifications."
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
    kind = "IMG" if p["type"] == "infographic" else "CAR"
    print(f"  #{p['id']:02d} {p['date']} {p['time']:>8} [{kind}] {p['label']}")
