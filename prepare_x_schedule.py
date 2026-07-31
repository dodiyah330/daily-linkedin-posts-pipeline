#!/usr/bin/env python3
"""Build schedule_x.json for the X (Twitter) native scheduler.

Sources (first match wins):
  1. x_posts_YYYYMMDD.txt — dedicated X copy (==== section headers)
  2. schedule_today.json / SCHEDULE_SOURCE — adapt LinkedIn schedule
  3. linkedin_posts_YYYYMMDD.txt — truncate LinkedIn captions

Types written: text | image (PDF carousels and polls are skipped / text-only).

Env:
  X_MAX_CHARS=280          Soft truncate length (Premium can raise this)
  X_POSTS_PER_DAY=4        Slots per day when building from text file
  X_TIMES="9:00 AM,12:00 PM,3:00 PM,6:00 PM"
  START_DATE=YYYY-MM-DD    First schedule day (default: tomorrow)
  SCHEDULE_SOURCE=path     Explicit LinkedIn schedule JSON to adapt
"""
from __future__ import annotations

import datetime
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "schedule_x.json")
MAX_CHARS = int(os.environ.get("X_MAX_CHARS", "280"))
POSTS_PER_DAY = int(os.environ.get("X_POSTS_PER_DAY", "4"))
TIMES = [
    t.strip()
    for t in os.environ.get(
        "X_TIMES", "9:00 AM,12:00 PM,3:00 PM,6:00 PM"
    ).split(",")
    if t.strip()
]


def scrub_dashes(text: str) -> str:
    """Never ship em-dashes or '--' as punctuation in X captions."""
    text = text.replace("\u2014", ",")  # —
    text = text.replace("\u2013", ",")  # –
    # Spaced or bare double-hyphen used as a dash (keep URL query leftovers alone)
    text = re.sub(r"\s*--\s*", ", ", text)
    text = re.sub(r" ,", ",", text)
    text = re.sub(r",\s*,+", ",", text)
    return text


def truncate_for_x(text: str, limit: int = MAX_CHARS) -> str:
    text = (text or "").strip()
    text = re.sub(r"\n\(Note:.*", "", text, flags=re.DOTALL).strip()
    # LinkedIn CTAs that feel odd on X
    text = re.sub(r"\n*Follow me\.?\s*$", "", text, flags=re.I).strip()
    text = re.sub(r"\n*Save this\.?\s*", "\n", text, flags=re.I).strip()
    text = scrub_dashes(text)
    if len(text) <= limit:
        return text
    cut = text[: limit - 1]
    # Prefer breaking on sentence / newline
    for sep in ("\n", ". ", "? ", "! "):
        idx = cut.rfind(sep)
        if idx >= max(40, limit // 3):
            cut = cut[: idx + (0 if sep == "\n" else 1)].rstrip()
            break
    else:
        sp = cut.rfind(" ")
        if sp > limit // 2:
            cut = cut[:sp]
    return cut.rstrip(" ,;:") + "…"


def split_sections(text: str) -> dict[str, str]:
    text = re.sub(r"^={50}\n", "", text.strip())
    chunks = [c.strip() for c in re.split(r"\n={50}\n", text) if c.strip()]
    sections: dict[str, str] = {}
    i = 0
    while i + 1 < len(chunks):
        if re.match(r"^\d+\.", chunks[i]):
            sections[chunks[i]] = chunks[i + 1]
            i += 2
        else:
            i += 1
    return sections


def find_latest(prefix: str, suffix: str = ".txt") -> str | None:
    files = sorted(
        f
        for f in os.listdir(BASE)
        if f.startswith(prefix) and f.endswith(suffix)
    )
    return os.path.join(BASE, files[-1]) if files else None


def assign_slots(n: int, start: datetime.date) -> list[tuple[str, str]]:
    """Return (MM/DD/YYYY, time) for n posts."""
    slots: list[tuple[str, str]] = []
    day = start
    while len(slots) < n:
        for t in TIMES[:POSTS_PER_DAY]:
            slots.append((day.strftime("%m/%d/%Y"), t))
            if len(slots) >= n:
                break
        day += datetime.timedelta(days=1)
    return slots


def from_x_posts_file(path: str, start: datetime.date) -> list[dict]:
    with open(path) as f:
        sections = split_sections(f.read())
    items = []
    for header, body in sections.items():
        caption = body
        assets: list[str] = []
        for m_img in re.finditer(r"(?im)^(?:IMAGE|IMAGES?):\s*(.+)$", body):
            raw = m_img.group(1).strip()
            for part in re.split(r"\s*\|\s*", raw):
                part = part.strip()
                if not part:
                    continue
                if not os.path.isabs(part):
                    part = os.path.join(BASE, part)
                assets.append(part)
        caption = re.sub(r"(?im)^(?:IMAGE|IMAGES?):\s*.+$", "", body).strip()
        m_cap = re.search(
            r"(?is)^(?:X )?CAPTION:\s*\n(.*)$", caption
        )
        if m_cap:
            caption = m_cap.group(1).strip()
        # X allows up to 4 images per post (gallery / "carousel")
        assets = assets[:4]
        item = {
            "type": "image" if assets else "text",
            "caption": truncate_for_x(caption),
            "label": header,
        }
        if len(assets) == 1:
            item["assetPath"] = assets[0]
        elif len(assets) > 1:
            item["assetPaths"] = assets
            item["assetPath"] = assets[0]
        items.append(item)
    slots = assign_slots(len(items), start)
    posts = []
    for i, (item, (date, time)) in enumerate(zip(items, slots), 1):
        post = {
            "id": i,
            "type": item["type"],
            "date": date,
            "time": time,
            "caption": item["caption"],
            "label": item["label"],
        }
        if item.get("assetPaths"):
            post["assetPaths"] = item["assetPaths"]
            post["assetPath"] = item["assetPaths"][0]
        elif item.get("assetPath"):
            post["assetPath"] = item["assetPath"]
        posts.append(post)
    return posts


def find_carousel_slide_pngs(limit: int = 4) -> list[str]:
    """Best-effort: LinkedIn carousel slide PNGs (not the PDF) for an X gallery."""
    out_root = os.path.join(BASE, "carousel-routine", "output")
    if not os.path.isdir(out_root):
        return []
    dates = sorted(
        (
            os.path.join(out_root, d)
            for d in os.listdir(out_root)
            if os.path.isdir(os.path.join(out_root, d))
        ),
        reverse=True,
    )
    for day in dates:
        for sub in ("carousel-branded", "carousel", "slides"):
            d = os.path.join(day, sub)
            if not os.path.isdir(d):
                continue
            pngs = sorted(
                os.path.join(d, f)
                for f in os.listdir(d)
                if f.lower().endswith(".png")
            )
            if pngs:
                return pngs[:limit]
        # flat day folder
        pngs = sorted(
            os.path.join(day, f)
            for f in os.listdir(day)
            if f.lower().endswith(".png")
        )
        if pngs:
            return pngs[:limit]
    return []


def from_linkedin_schedule(path: str) -> list[dict]:
    data = json.load(open(path))
    posts = []
    for p in data.get("posts", []):
        ptype = p.get("type", "regular")
        if ptype == "poll":
            continue
        caption = truncate_for_x(p.get("caption", ""))
        if not caption:
            continue
        asset = p.get("assetPath")
        assets: list[str] = []
        out_type = "text"
        if ptype == "infographic" and asset and str(asset).lower().endswith(
            (".png", ".jpg", ".jpeg", ".webp", ".gif")
        ):
            out_type = "image"
            assets = [asset]
        elif ptype == "carousel":
            # LinkedIn PDF docs are not a thing on X — use up to 4 slide PNGs if present
            slides = find_carousel_slide_pngs(4)
            if slides:
                out_type = "image"
                assets = slides
            else:
                assets = []
                out_type = "text"
        elif asset and str(asset).lower().endswith(
            (".png", ".jpg", ".jpeg", ".webp", ".gif")
        ):
            out_type = "image"
            assets = [asset]
        post = {
            "id": len(posts) + 1,
            "type": out_type,
            "date": p["date"],
            "time": p["time"],
            "caption": caption,
            "sourceId": p.get("id"),
            "sourceType": ptype,
        }
        if len(assets) == 1:
            post["assetPath"] = assets[0]
        elif len(assets) > 1:
            post["assetPaths"] = assets
            post["assetPath"] = assets[0]
        posts.append(post)
    return posts


def from_linkedin_posts_txt(path: str, start: datetime.date) -> list[dict]:
    with open(path) as f:
        sections = split_sections(f.read())
    date_m = re.search(r"linkedin_posts_(\d{8})\.txt", os.path.basename(path))
    date_compact = (
        date_m.group(1) if date_m else datetime.date.today().strftime("%Y%m%d")
    )
    items = []
    for header, body in sections.items():
        h = header.upper()
        if "POLL" in h:
            continue
        caption = body
        asset = None
        if "INFOGRAPHIC" in h or "DATA VISUAL" in h:
            m = re.search(
                r"(?is)(?:INFOGRAPHIC|PERFORMANCE DATA VISUAL) CAPTION:\s*\n(.*)$",
                body,
            )
            caption = m.group(1).strip() if m else body[:500]
            png = os.path.join(BASE, f"linkedin-infographic-{date_compact}.png")
            if os.path.exists(png):
                asset = png
        elif "CAROUSEL" in h:
            m = re.search(
                r"(?is)(?:CAROUSEL|PERFORMANCE CAROUSEL) CAPTION:\s*\n(.*)$",
                body,
            )
            caption = m.group(1).strip() if m else body[:500]
            # no PDF on X
        items.append(
            {
                "type": "image" if asset else "text",
                "caption": truncate_for_x(caption),
                "assetPath": asset,
                "label": header,
            }
        )
    slots = assign_slots(len(items), start)
    posts = []
    for i, (item, (date, time)) in enumerate(zip(items, slots), 1):
        post = {
            "id": i,
            "type": item["type"],
            "date": date,
            "time": time,
            "caption": item["caption"],
            "label": item["label"],
        }
        if item["assetPath"]:
            post["assetPath"] = item["assetPath"]
        posts.append(post)
    return posts


def main() -> int:
    start_env = os.environ.get("START_DATE")
    if start_env:
        start = datetime.date.fromisoformat(start_env)
    else:
        start = datetime.date.today() + datetime.timedelta(days=1)

    source = os.environ.get("SCHEDULE_SOURCE")
    posts: list[dict] = []
    used = None

    x_posts = find_latest("x_posts_")
    if x_posts and not source:
        posts = from_x_posts_file(x_posts, start)
        used = x_posts
    elif source or os.path.exists(os.path.join(BASE, "schedule_today.json")):
        path = (
            os.path.abspath(source)
            if source
            else os.path.join(BASE, "schedule_today.json")
        )
        if os.path.exists(path):
            posts = from_linkedin_schedule(path)
            used = path
    if not posts:
        li = find_latest("linkedin_posts_")
        if li:
            posts = from_linkedin_posts_txt(li, start)
            used = li

    if not posts:
        print(
            "No source found. Create x_posts_YYYYMMDD.txt, or run prepare_schedule_today.py first.",
            file=sys.stderr,
        )
        return 1

    payload = {
        "generated": datetime.date.today().isoformat(),
        "stream": "x-personal",
        "startUrl": "https://x.com/home",
        "scheduleNote": (
            f"X native schedule; account timezone; maxChars={MAX_CHARS}. "
            "Premium required for Schedule UI. Times are wall-clock in account TZ."
        ),
        "source": os.path.basename(used) if used else None,
        "posts": posts,
    }
    with open(OUT, "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Wrote {len(posts)} posts → {os.path.basename(OUT)} (from {os.path.basename(used) if used else '?'})")
    for p in posts:
        media = " +img" if p.get("assetPath") else ""
        print(
            f"  {p['id']:2d}. {p['date']} {p['time']:>8s}  "
            f"{p['type']:5s}{media}  {len(p['caption']):3d}c  "
            f"{p['caption'][:60].replace(chr(10), ' ')}…"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
