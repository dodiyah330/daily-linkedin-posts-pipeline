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
if not os.path.exists(POSTS_FILE):
    candidates = sorted(
        f for f in os.listdir(BASE)
        if f.startswith("linkedin_posts_") and f.endswith(".txt") and f != "linkedin_posts_today.txt"
    )
    if candidates:
        POSTS_FILE = os.path.join(BASE, candidates[-1])
        print(f"Using latest posts file: {candidates[-1]}")

POSTS_DATE = re.search(r"linkedin_posts_(\d{8})\.txt", os.path.basename(POSTS_FILE))
POSTS_DATE_ISO = (
    f"{POSTS_DATE.group(1)[:4]}-{POSTS_DATE.group(1)[4:6]}-{POSTS_DATE.group(1)[6:8]}"
    if POSTS_DATE else DATE.isoformat()
)
POSTS_DATE_COMPACT = POSTS_DATE.group(1) if POSTS_DATE else DATE_COMPACT

# Schedule starts tomorrow if today's slots already passed (IST evening)
START = DATE + datetime.timedelta(days=1)
DAY1 = START.strftime("%m/%d/%Y")
DAY2 = (START + datetime.timedelta(days=1)).strftime("%m/%d/%Y")
DAY3 = (START + datetime.timedelta(days=2)).strftime("%m/%d/%Y")
DAY4 = (START + datetime.timedelta(days=3)).strftime("%m/%d/%Y")

TIMES = ["9:00 AM", "12:00 PM", "3:00 PM", "6:00 PM"]


def find_carousel_pdf(subdir, fallback_name):
    d = os.path.join(BASE, "carousel-routine", "output", POSTS_DATE_ISO, subdir)
    if not os.path.isdir(d):
        return os.path.join(d, fallback_name)
    pdfs = sorted(
        [os.path.join(d, fn) for fn in os.listdir(d) if fn.endswith(".pdf")],
        key=os.path.getmtime,
        reverse=True,
    )
    return pdfs[0] if pdfs else os.path.join(d, fallback_name)


def split_sections(text):
    text = text.strip()
    text = re.sub(r"^={50}\n", "", text)
    chunks = [c.strip() for c in re.split(r"\n={50}\n", text) if c.strip()]
    sections = {}
    i = 0
    while i + 1 < len(chunks):
        header = chunks[i]
        if re.match(r"^\d+\.", header):
            sections[header] = chunks[i + 1]
            i += 2
        else:
            i += 1
    return sections


def extract_poll_options(body):
    opts = re.findall(r"☐ (.+)", body)
    return "|".join(o[:30] for o in opts[:4])


def extract_carousel_caption(body):
    m = re.search(r"CAROUSEL CAPTION:\s*\n(.*)", body, re.DOTALL)
    return m.group(1).strip() if m else body[:500]


def extract_infographic_caption(body):
    m = re.search(r"INFOGRAPHIC CAPTION:\s*\n(.*)", body, re.DOTALL)
    cap = m.group(1).strip() if m else body[:500]
    return re.sub(r"\n\(Note:.*", "", cap, flags=re.DOTALL).strip()


def extract_perf_carousel_caption(body):
    m = re.search(r"PERFORMANCE CAROUSEL CAPTION:\s*\n(.*)", body, re.DOTALL)
    cap = m.group(1).strip() if m else body[:500]
    return re.sub(r"\n\(Note:.*", "", cap, flags=re.DOTALL).strip()


def extract_perf_infographic_caption(body):
    m = re.search(r"PERFORMANCE DATA VISUAL CAPTION:\s*\n(.*)", body, re.DOTALL)
    cap = m.group(1).strip() if m else body[:500]
    return re.sub(r"\n\(Note:.*", "", cap, flags=re.DOTALL).strip()


def extract_poll_question(body):
    lines = [ln.strip() for ln in body.split("\n") if ln.strip() and not ln.startswith("☐")]
    return lines[-2] if len(lines) >= 2 else "What would you do?"


def main():
    with open(POSTS_FILE) as f:
        text = f.read()
    s = split_sections(text)

    pdf = find_carousel_pdf("carousel-branded", "startup-strategy-carousel.pdf")
    png = os.path.join(BASE, f"linkedin-infographic-{POSTS_DATE_COMPACT}.png")

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

    perf_pdf = find_carousel_pdf("carousel-performance", "carousel-performance.pdf")
    perf_png = os.path.join(BASE, f"linkedin-performance-infographic-{POSTS_DATE_COMPACT}.png")
    perf_poll_body = s.get("13. PERF 2 (LOADED POLL)", "")

    perf_posts = [
        {
            "id": 12,
            "type": "regular",
            "date": DAY3,
            "time": TIMES[3],
            "caption": s.get("12. PERF 1 (CONTRARIAN)", "").strip(),
        },
        {
            "id": 13,
            "type": "poll",
            "date": DAY4,
            "time": TIMES[0],
            "caption": perf_poll_body.strip(),
            "title": extract_poll_question(perf_poll_body),
            "pollOptionsStr": extract_poll_options(perf_poll_body),
        },
        {
            "id": 14,
            "type": "regular",
            "date": DAY4,
            "time": TIMES[1],
            "caption": s.get("14. PERF 3 (AI NEWS + IMPLICATIONS)", "").strip(),
        },
        {
            "id": 15,
            "type": "carousel" if os.path.exists(perf_pdf) else "regular",
            "date": DAY4,
            "time": TIMES[2],
            "caption": extract_perf_carousel_caption(s.get("15. PERF 4 (STORY CAROUSEL — caption)", "")),
            **({"assetPath": perf_pdf, "title": "Performance story carousel"} if os.path.exists(perf_pdf) else {}),
        },
        {
            "id": 16,
            "type": "infographic" if os.path.exists(perf_png) else "regular",
            "date": DAY4,
            "time": TIMES[3],
            "caption": extract_perf_infographic_caption(s.get("16. PERF 5 (DATA VISUAL — caption)", "")),
            **({"assetPath": perf_png} if os.path.exists(perf_png) else {}),
        },
    ]
    posts.extend(perf_posts)

    out = os.path.join(BASE, "schedule_today.json")
    with open(out, "w") as f:
        json.dump({"posts": posts, "generated": DATE.isoformat()}, f, indent=2)
    print(f"Wrote {out} with {len(posts)} posts")
    print(f"Schedule: {DAY1} – {DAY4} (16 posts)")


if __name__ == "__main__":
    main()
