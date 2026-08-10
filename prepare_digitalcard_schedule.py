#!/usr/bin/env python3
"""
Build schedule_digitalcard.json from digitalcard_batch_*.json
Supports 4 posts/day: image_am, carousel_am, image_pm, carousel_pm
"""
import datetime
import glob
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))

COMPANY_ID = os.environ.get("DIGITALCARD_COMPANY_ID", "135187143")
POST_AS = os.environ.get("DIGITALCARD_POST_AS", "Digital Card Creator")
SITE_URL = "https://my.digitalcardcreator.com/"
PLAY_URL = "https://play.google.com/store/apps/details?id=com.digital_card_creator_app"
FOOTER = f"Create free: {SITE_URL}\nAndroid app: {PLAY_URL}"

def pick_batch():
    if os.environ.get("DIGITALCARD_BATCH"):
        path = os.environ["DIGITALCARD_BATCH"]
        if not os.path.exists(path):
            raise SystemExit(f"DIGITALCARD_BATCH not found: {path}")
        return path
    dated = sorted(glob.glob(os.path.join(BASE, "digitalcard_batch_[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9].json")))
    if dated:
        return dated[-1]
    files = sorted(glob.glob(os.path.join(BASE, "digitalcard_batch_*.json")))
    if not files:
        raise SystemExit("No digitalcard_batch_*.json — run generate + build first")
    return files[-1]


BATCH = pick_batch()
print(f"Using batch: {os.path.basename(BATCH)}")
data = json.load(open(BATCH))
posts_days = data["posts"]
date_compact = re.search(r"digitalcard_batch_(\d{8})", os.path.basename(BATCH))
DATE_COMPACT = date_compact.group(1) if date_compact else datetime.date.today().isoformat().replace("-", "")
img_dir = data.get("assetDir") or os.path.join(BASE, "digitalcard-images", DATE_COMPACT)

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


def ensure_urls(text):
    t = (text or "").strip()
    low = t.lower()
    needs_site = "digitalcardcreator.com" not in low
    needs_play = "play.google.com/store/apps/details?id=com.digital_card_creator_app" not in low
    if needs_site or needs_play:
        t = (t + "\n\n" + FOOTER).strip()
    return t


def find_pdf(day_i, day_date, slot="am"):
    day = posts_days[day_i - 1]
    key = f"_carousel_pdf_{slot}"
    if day.get(key) and os.path.exists(day[key]):
        return day[key]
    if slot == "am" and day.get("_carousel_pdf") and os.path.exists(day["_carousel_pdf"]):
        return day["_carousel_pdf"]
    car_name = f"digitalcard-day-{day_i:02d}" if slot == "am" else f"digitalcard-day-{day_i:02d}-pm"
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
    """Push past slots forward. If the day is fully in the past or too late tonight,
    return (next usable date, peak slots for that weekday)."""
    now = datetime.datetime.now()
    today = now.date()

    # Entire content day already passed — move to today (or tomorrow if too late)
    if date_obj < today:
        date_obj = today

    if date_obj > today:
        return date_obj, times

    latest = datetime.datetime.combine(date_obj, datetime.time(23, 45))
    cursor = now + datetime.timedelta(minutes=40)
    if cursor.minute == 0 and cursor.second == 0:
        pass
    elif cursor.minute <= 30:
        cursor = cursor.replace(minute=30, second=0, microsecond=0)
    else:
        cursor = (cursor + datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)

    # Too late tonight — move the whole day to tomorrow's peak slots
    if cursor > latest or (latest - cursor).total_seconds() < 90 * 60:
        nxt = date_obj + datetime.timedelta(days=1)
        return nxt, list(SLOTS_BY_WD[nxt.weekday()])

    out = []
    for t in times:
        h, mi = parse_time(t)
        slot_dt = datetime.datetime.combine(date_obj, datetime.time(h, mi))
        if slot_dt <= now:
            if cursor > latest:
                nxt = date_obj + datetime.timedelta(days=1)
                return nxt, list(SLOTS_BY_WD[nxt.weekday()])
            ap = "AM" if cursor.hour < 12 else "PM"
            hh = cursor.hour % 12 or 12
            out.append(f"{hh}:{cursor.minute:02d} {ap}")
            cursor += datetime.timedelta(minutes=45)
            if cursor.minute not in (0, 15, 30, 45):
                snap = ((cursor.minute // 15) + 1) * 15
                if snap >= 60:
                    cursor = (cursor + datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
                else:
                    cursor = cursor.replace(minute=snap, second=0, microsecond=0)
        else:
            out.append(t)
    return date_obj, out


schedule_posts = []
pid = 1
missing = []
date_shift = datetime.timedelta(days=0)

for day in posts_days:
    day_i = day.get("day") or (pid // 4 + 1)
    date_str = day.get("date")
    if not date_str:
        raise SystemExit("day missing date")
    d = datetime.date.fromisoformat(date_str) + date_shift
    times = list(SLOTS_BY_WD[d.weekday()])
    new_d, times = bump_past_times(d, times)
    # If day 1 slipped to tomorrow, shift the whole batch so days stay consecutive
    if day_i == 1 and new_d != d:
        date_shift = new_d - datetime.date.fromisoformat(date_str)
        d = new_d
        times = list(SLOTS_BY_WD[d.weekday()])
    else:
        d = new_d

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
            caption = ensure_urls((body or {}).get("caption", ""))
            day_posts.append({
                "id": None,
                "type": "infographic",
                "date": d.strftime("%m/%d/%Y"),
                "time": when,
                "caption": caption,
                "assetPath": asset,
                "stream": "digitalcard",
                "label": f"DAY {day_i} IMAGE {slot.upper()} — {arch}",
                "topic": day.get("topic"),
                "audience": day.get("audience"),
            })
        else:
            asset = find_pdf(day_i, date_str, slot)
            if not asset:
                missing.append(f"carousel day {day_i} {slot}")
            caption = ensure_urls((body or {}).get("caption", ""))
            title = (day.get("topic") or "Digital Card Creator")[:58].rstrip(" -:,")
            if slot == "pm":
                title = (title[:50] + " · PM").rstrip()[:58]
            day_posts.append({
                "id": None,
                "type": "carousel",
                "date": d.strftime("%m/%d/%Y"),
                "time": when,
                "caption": caption,
                "assetPath": asset,
                "title": title,
                "stream": "digitalcard",
                "label": f"DAY {day_i} CAROUSEL {slot.upper()} — {arch}",
                "topic": day.get("topic"),
                "audience": day.get("audience"),
            })

    for p in sorted(day_posts, key=lambda x: parse_time(x["time"])):
        p["id"] = pid
        pid += 1
        schedule_posts.append(p)

if missing:
    raise SystemExit("Missing assets: " + ", ".join(missing) + " — run build_digitalcard_assets.py")

out = os.path.join(BASE, "schedule_digitalcard.json")
ppd = 4 if any(p.get("image_pm") for p in posts_days) else 2
payload = {
    "posts": schedule_posts,
    "generated": datetime.date.today().isoformat(),
    "stream": "digitalcard-company",
    "scheduleNote": (
        f"{len(posts_days)} days × {ppd} posts/day (2 images + 2 carousels). "
        "Niche: digital visiting cards / QR / WhatsApp. "
        "Play Store + web URL on every caption. IST peaks."
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
