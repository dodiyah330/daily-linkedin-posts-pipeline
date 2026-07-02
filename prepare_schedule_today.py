#!/usr/bin/env python3
"""Parse today's linkedin_posts file into schedule_today.json for the scheduler."""
import datetime
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
DATE = datetime.date.today()
DATE_COMPACT = DATE.isoformat().replace("-", "")
POSTS_FILE = os.path.join(BASE, f"linkedin_posts_{DATE_COMPACT}.txt")

# Schedule starts tomorrow if today's slots already passed (IST evening)
START = DATE + datetime.timedelta(days=1)
DAY1 = START.strftime("%m/%d/%Y")
DAY2 = (START + datetime.timedelta(days=1)).strftime("%m/%d/%Y")
DAY3 = (START + datetime.timedelta(days=2)).strftime("%m/%d/%Y")

TIMES = ["9:00 AM", "12:00 PM", "3:00 PM", "6:00 PM"]


def split_sections(text):
    parts = re.split(r"\n={50}\n", text)
    sections = {}
    for part in parts:
        part = part.strip()
        if not part:
            continue
        first = part.split("\n", 1)[0].strip()
        body = part.split("\n", 1)[1].strip() if "\n" in part else ""
        sections[first] = body
    return sections


def extract_poll_options(body):
    opts = re.findall(r"☐ (.+)", body)
    return "|".join(opts[:4])


def extract_carousel_caption(body):
    m = re.search(r"CAROUSEL CAPTION:\s*\n(.*)", body, re.DOTALL)
    return m.group(1).strip() if m else body[:500]


def extract_infographic_caption(body):
    m = re.search(r"INFOGRAPHIC CAPTION:\s*\n(.*)", body, re.DOTALL)
    cap = m.group(1).strip() if m else body[:500]
    return re.sub(r"\n\(Note:.*", "", cap, flags=re.DOTALL).strip()


def extract_poll_question(body):
    lines = [ln.strip() for ln in body.split("\n") if ln.strip() and not ln.startswith("☐")]
    return lines[-2] if len(lines) >= 2 else "What would you do?"


def main():
    with open(POSTS_FILE) as f:
        text = f.read()
    s = split_sections(text)

    pdf = os.path.join(
        BASE,
        "carousel-routine",
        "output",
        DATE.isoformat(),
        "carousel-branded",
        "startup-strategy-carousel.pdf",
    )
    png = os.path.join(BASE, f"linkedin-infographic-{DATE_COMPACT}.png")

    posts = [
        {
            "id": 1,
            "type": "carousel",
            "date": DAY1,
            "time": TIMES[0],
            "caption": extract_carousel_caption(s.get("3. CAROUSEL", "")),
            "assetPath": pdf,
            "title": "The day an AI vanished in 90 minutes",
        },
        {
            "id": 2,
            "type": "infographic",
            "date": DAY1,
            "time": TIMES[1],
            "caption": extract_infographic_caption(s.get("4. INFOGRAPHIC", "")),
            "assetPath": png,
        },
        {
            "id": 3,
            "type": "regular",
            "date": DAY1,
            "time": TIMES[2],
            "caption": s.get("1. COLLABORATIVE ARTICLE", "").strip(),
        },
        {
            "id": 4,
            "type": "poll",
            "date": DAY1,
            "time": TIMES[3],
            "caption": s.get("2. POLL", "").strip(),
            "title": extract_poll_question(s.get("2. POLL", "")),
            "pollOptionsStr": extract_poll_options(s.get("2. POLL", "")),
        },
    ]

    ai_keys = [
        ("5. POST 1", DAY2, TIMES[0]),
        ("6. POST 2", DAY2, TIMES[1]),
        ("7. POST 3", DAY2, TIMES[2]),
        ("8. POST 4", DAY2, TIMES[3]),
        ("9. POST 5", DAY3, TIMES[0]),
        ("10. POST 6", DAY3, TIMES[1]),
        ("11. POST 7", DAY3, TIMES[2]),
    ]
    for i, (key, day, time) in enumerate(ai_keys, 5):
        body = s.get(key, "").strip()
        body = re.sub(r"\n(?:Tool featured|Tools/stories|What's being shared|Source|Archetype|Why this works|Word count):.*", "", body, flags=re.DOTALL).strip()
        posts.append({"id": i, "type": "regular", "date": day, "time": time, "caption": body})

    out = os.path.join(BASE, "schedule_today.json")
    with open(out, "w") as f:
        json.dump({"posts": posts, "generated": DATE.isoformat()}, f, indent=2)
    print(f"Wrote {out} with {len(posts)} posts")
    print(f"Schedule: {DAY1} – {DAY3}")


if __name__ == "__main__":
    main()
