#!/usr/bin/env python3
"""Build schedule_bookwellnow_facebook.json from a BookWellNow LinkedIn batch.

Facebook cannot take LinkedIn PDF carousels. Each post becomes a 4-image
album (the existing slide PNGs) with a lightly adapted caption.

Reuses the latest bookwellnow_batch_*.json unless BOOKWELLNOW_BATCH is set.
"""
from __future__ import annotations

import datetime
import glob
import json
import os
import re
import sys

from bookwellnow_links import ensure_tracked_footer, site_url

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

SITE_URL = site_url("facebook")
PAGE_URL = os.environ.get("FACEBOOK_PAGE_URL", "https://www.facebook.com/BookWellNow")
ASSET_PREFIX = os.environ.get("BOOKWELLNOW_ASSET_PREFIX", "bookwellnow-fb")

# Facebook Page peaks (IST): midday, late afternoon, evening
SLOTS_BY_WD = {
    0: ("11:00 AM", "3:30 PM", "8:00 PM"),
    1: ("11:00 AM", "3:30 PM", "8:00 PM"),
    2: ("11:00 AM", "3:30 PM", "8:00 PM"),
    3: ("11:00 AM", "3:30 PM", "8:00 PM"),
    4: ("11:00 AM", "3:30 PM", "8:00 PM"),
    5: ("11:00 AM", "4:00 PM", "7:00 PM"),
    6: ("11:00 AM", "4:00 PM", "7:00 PM"),
}


def parse_time(t: str) -> tuple[int, int]:
    m = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM)", t, re.I)
    if not m:
        raise ValueError(f"bad time: {t}")
    h, mi, ap = int(m.group(1)), int(m.group(2)), m.group(3).upper()
    if ap == "PM" and h != 12:
        h += 12
    if ap == "AM" and h == 12:
        h = 0
    return (h, mi)


def bump_past_times(date_obj: datetime.date, times: list[str]) -> list[str]:
    now = datetime.datetime.now()
    if date_obj != now.date():
        return times
    out = []
    cursor = now + datetime.timedelta(minutes=40)
    if cursor.minute not in (0, 30):
        if cursor.minute < 30:
            cursor = cursor.replace(minute=30, second=0, microsecond=0)
        else:
            cursor = (cursor + datetime.timedelta(hours=1)).replace(
                minute=0, second=0, microsecond=0
            )
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
        else:
            out.append(t)
    return out


def ensure_site(text: str, hiring: bool = False) -> str:
    return ensure_tracked_footer(text, "facebook", hiring=hiring)


def adapt_caption(text: str, hiring: bool = False) -> str:
    t = ensure_site(text, hiring=hiring)
    t = t.replace("\u2014", "-").replace("\u2013", "-")
    t = re.sub(r"(?i)\brepost if\b", "Share this if", t)
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    if hiring:
        return t.strip()
    lines = t.splitlines()
    keep: list[str] = []
    tags: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") and " " not in stripped:
            tags.extend(stripped.split())
            continue
        inline = re.findall(r"(#\w+)", line)
        if inline and stripped.startswith("#"):
            tags.extend(inline)
            continue
        keep.append(line)
    t = "\n".join(keep).strip()
    if tags:
        t = (t + "\n\n" + " ".join(tags[:3])).strip()
    return t


def day_carousels(day: dict) -> list[tuple[int, dict]]:
    if day.get("carousels"):
        return list(enumerate(day["carousels"][:3], 1))
    out = []
    if day.get("carousel_am") or day.get("carousel"):
        out.append((1, day.get("carousel_am") or day.get("carousel")))
    if day.get("carousel_mid"):
        out.append((2, day.get("carousel_mid")))
    if day.get("carousel_pm"):
        out.append((3 if day.get("carousel_mid") else 2, day.get("carousel_pm")))
    return out


def find_pngs(day: dict, day_i: int, day_date: str, slot: str) -> list[str]:
    mapped = (day.get("_carousel_pngs") or {}).get(slot)
    if mapped:
        found = [p for p in mapped if os.path.exists(p)]
        if found:
            return found
    names = [
        f"{ASSET_PREFIX}-day-{day_i:02d}-{slot}",
        f"bookwellnow-day-{day_i:02d}-{slot}",
        f"bookwellnow-day-{day_i:02d}" if slot in ("a", "am") else None,
        f"bookwellnow-day-{day_i:02d}-pm" if slot in ("b", "c", "pm") else None,
    ]
    for car_name in names:
        if not car_name:
            continue
        d = os.path.join(BASE, "carousel-routine", "output", day_date, car_name)
        if os.path.isdir(d):
            pngs = sorted(glob.glob(os.path.join(d, "slide-*.png")))
            if pngs:
                return pngs
    return []


def compute_shift(posts_days: list[dict]) -> datetime.timedelta:
    if os.environ.get("FACEBOOK_SHIFT_PAST", "1") != "1" or not posts_days:
        return datetime.timedelta(days=0)
    first = posts_days[0].get("date")
    if not first:
        return datetime.timedelta(days=0)
    start = datetime.date.fromisoformat(first)
    today = datetime.date.today()
    if start >= today:
        return datetime.timedelta(days=0)
    target = today + datetime.timedelta(days=1)
    delta = target - start
    print(f"Shifting schedule dates by {delta.days} days so day 1 = {target.isoformat()} (assets stay on original folders)")
    return delta


def load_batch() -> tuple[str, dict]:
    if os.environ.get("BOOKWELLNOW_BATCH"):
        path = os.environ["BOOKWELLNOW_BATCH"]
        if not os.path.exists(path):
            raise SystemExit(f"BOOKWELLNOW_BATCH not found: {path}")
        return path, json.load(open(path))
    fb_files = sorted(glob.glob(os.path.join(BASE, "bookwellnow_facebook_batch_*.json")))
    li_files = sorted(glob.glob(os.path.join(BASE, "bookwellnow_batch_*.json")))
    files = fb_files or li_files
    if not files:
        raise SystemExit(
            "No bookwellnow_facebook_batch_*.json — run generate_bookwellnow_facebook_batch.py first"
        )
    path = files[-1]
    return path, json.load(open(path))


def main() -> None:
    batch_path, data = load_batch()
    posts_days = data.get("posts") or []
    if not posts_days:
        raise SystemExit(f"{os.path.basename(batch_path)} has no posts")
    delta = compute_shift(posts_days)

    am_override = os.environ.get("FACEBOOK_AM_TIME")
    mid_override = os.environ.get("FACEBOOK_MID_TIME")
    pm_override = os.environ.get("FACEBOOK_PM_TIME")

    schedule_posts = []
    pid = 1
    missing = []

    for day in posts_days:
        day_i = day.get("day") or (pid // 2 + 1)
        date_str = day.get("date")
        if not date_str:
            raise SystemExit("day missing date")
        asset_date = date_str
        sched_date = (datetime.date.fromisoformat(date_str) + delta).isoformat()
        d = datetime.date.fromisoformat(sched_date)
        times = list(SLOTS_BY_WD[d.weekday()])
        if am_override:
            times[0] = am_override
        if mid_override and len(times) > 1:
            times[1] = mid_override
        if pm_override and len(times) > 2:
            times[-1] = pm_override
        elif pm_override and len(times) > 1:
            times[1] = pm_override
        times = bump_past_times(d, times)
        cars = day_carousels(day)
        day_posts = []
        for idx, car in cars:
            slot = chr(ord("a") + idx - 1)
            pngs = find_pngs(day, day_i, asset_date, slot)
            if len(pngs) < 2:
                missing.append(f"carousel day {day_i} {slot} (need slide PNGs)")
            arch = (car or {}).get("archetype") or (day.get("slots") or {}).get(
                f"carousel_{idx}", ""
            )
            hiring = str(arch).startswith("HIRING")
            caption = adapt_caption((car or {}).get("caption", ""), hiring=hiring)
            industry = (car or {}).get("industry") or day.get("industry") or "BookWellNow"
            title = ((car or {}).get("industry") or day.get("topic") or "BookWellNow")[:58]
            day_posts.append(
                {
                    "id": None,
                    "type": "photos",
                    "date": d.strftime("%m/%d/%Y"),
                    "time": times[min(idx - 1, len(times) - 1)],
                    "caption": caption,
                    "assetPath": pngs[0] if pngs else None,
                    "assetPaths": pngs,
                    "title": title.rstrip(" -:,"),
                    "stream": "bookwellnow-facebook",
                    "label": f"DAY {day_i} PHOTOS {slot.upper()} — {arch}",
                    "topic": day.get("topic"),
                    "industry": industry,
                    "hiring": hiring,
                }
            )

        for p in sorted(day_posts, key=lambda x: parse_time(x["time"])):
            p["id"] = pid
            pid += 1
            schedule_posts.append(p)

    if missing:
        raise SystemExit(
            "Missing slide PNGs: "
            + ", ".join(missing)
            + " — run python3 build_bookwellnow_assets.py"
        )

    out = os.path.join(BASE, "schedule_bookwellnow_facebook.json")
    payload = {
        "posts": schedule_posts,
        "generated": datetime.date.today().isoformat(),
        "stream": "bookwellnow-facebook-page",
        "scheduleNote": (
            f"{len(posts_days)} days × 3 Facebook posts/day (4-slide albums). "
            "New Page feature intro. IST midday / afternoon / evening. "
            "utm_source=facebook post on every product link."
        ),
        "pageUrl": PAGE_URL,
        "timezone": os.environ.get("FACEBOOK_TIMEZONE", "Asia/Kolkata"),
        "postAs": "BookWellNow",
        "sourceFile": os.path.basename(batch_path),
    }
    json.dump(payload, open(out, "w"), indent=2)
    print(f"Wrote {out} — {len(schedule_posts)} posts")
    print(payload["scheduleNote"])
    for p in schedule_posts:
        n = len(p.get("assetPaths") or [])
        print(f"  #{p['id']:02d} {p['date']} {p['time']:>8} [{n} img] {p['label']}")


if __name__ == "__main__":
    main()
