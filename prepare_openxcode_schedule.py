#!/usr/bin/env python3
"""
Build schedule_openxcode.json for this week's remaining peak LinkedIn slots.

Peak strategy (IST, B2B / software — midweek midday):
  Tue 11:00 AM | Wed 12:00 PM | Thu 11:00 AM | Fri 1:00 PM
Weekends skipped (lowest LinkedIn B2B engagement).

If Monday peak already passed, starts from next weekday.
Set OPENXCODE_INCLUDE_WEEKENDS=1 to also schedule Sat/Sun at 11:00 AM.
"""
import datetime
import glob
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))

# Peak slots by weekday (Mon=0 … Sun=6) — LinkedIn account timezone (IST)
PEAK_TIMES = {
    0: "1:00 PM",   # Monday secondary peak
    1: "11:00 AM",  # Tuesday core peak
    2: "12:00 PM",  # Wednesday midday peak
    3: "11:00 AM",  # Thursday core peak
    4: "1:00 PM",   # Friday early-afternoon peak
    5: "11:00 AM",  # weekend (only if enabled)
    6: "11:00 AM",
}

LABELS = [
    "1. NEWS → BUILD",
    "2. CASE STUDY",
    "3. MYTH BUST",
    "4. BUILD TIP",
    "5. SERVICE SPOTLIGHT",
    "6. PAIN → PRODUCT",
    "7. DIRECT OFFER",
]

INCLUDE_WEEKENDS = os.environ.get("OPENXCODE_INCLUDE_WEEKENDS", "0") == "1"


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


def next_week_days(start: datetime.date, include_weekends: bool):
    """Remaining days in this calendar week (Mon–Sun), starting from start."""
    # End of this week = upcoming Sunday
    days_until_sunday = 6 - start.weekday()
    end = start + datetime.timedelta(days=days_until_sunday)
    days = []
    d = start
    while d <= end:
        if include_weekends or d.weekday() < 5:
            days.append(d)
        d += datetime.timedelta(days=1)
    return days


# Prefer week file, else latest daily
week_files = sorted(glob.glob(os.path.join(BASE, "openxcode_posts_week_*.txt")))
daily_files = sorted(glob.glob(os.path.join(BASE, "openxcode_posts_*.txt")))
# Exclude week files from daily list
daily_files = [f for f in daily_files if "week" not in os.path.basename(f)]

if week_files:
    POSTS_FILE = week_files[-1]
elif daily_files:
    POSTS_FILE = daily_files[-1]
else:
    raise SystemExit("No openxcode_posts_*.txt — run generate_openxcode_week.py first")

with open(POSTS_FILE) as f:
    sections = split_sections(f.read())

if len(sections) < 2:
    raise SystemExit(
        f"Expected a week batch with multiple sections in {POSTS_FILE}. "
        "Run: python3 generate_openxcode_week.py"
    )

now = datetime.datetime.now()
today = now.date()

# If today's peak time already passed, start tomorrow
start = today
if today.weekday() in PEAK_TIMES:
    peak = PEAK_TIMES[today.weekday()]
    # crude parse of "11:00 AM" / "1:00 PM"
    m = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM)", peak, re.I)
    if m:
        h, mi, ap = int(m.group(1)), int(m.group(2)), m.group(3).upper()
        if ap == "PM" and h != 12:
            h += 12
        if ap == "AM" and h == 12:
            h = 0
        peak_dt = datetime.datetime.combine(today, datetime.time(h, mi))
        if now >= peak_dt:
            start = today + datetime.timedelta(days=1)

days = next_week_days(start, INCLUDE_WEEKENDS)
if not days:
    raise SystemExit("No remaining days left in this week to schedule.")

# Map remaining days → archetype by weekday index
posts = []
for i, day in enumerate(days, 1):
    label = LABELS[day.weekday()]
    body = sections.get(label, "").strip()
    if not body:
        # fallback: take sections in order
        keys = list(sections.keys())
        body = sections[keys[min(i - 1, len(keys) - 1)]].strip()
        label = keys[min(i - 1, len(keys) - 1)]
    time = PEAK_TIMES[day.weekday()]
    posts.append({
        "id": i,
        "type": "text",
        "date": day.strftime("%m/%d/%Y"),
        "time": time,
        "caption": body,
        "stream": "openxcode",
        "archetype": label,
        "peak": True,
    })

out = os.path.join(BASE, "schedule_openxcode.json")
payload = {
    "posts": posts,
    "generated": today.isoformat(),
    "stream": "openxcode-company-week",
    "sourceFile": os.path.basename(POSTS_FILE),
    "scheduleNote": (
        "Peak LinkedIn B2B slots (IST): Tue 11AM, Wed 12PM, Thu 11AM, Fri 1PM. "
        "Weekends skipped unless OPENXCODE_INCLUDE_WEEKENDS=1."
    ),
    "companyPage": "https://www.linkedin.com/company/open-xcode/",
}
with open(out, "w") as f:
    json.dump(payload, f, indent=2)

print(f"Wrote {out} — {len(posts)} peak-time posts")
for p in posts:
    print(f"  #{p['id']} {p['date']} {p['time']} — {p['archetype']}")
print(payload["scheduleNote"])
