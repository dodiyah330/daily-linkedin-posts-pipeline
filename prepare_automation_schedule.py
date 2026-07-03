#!/usr/bin/env python3
"""Parse automation_leads_*.txt into schedule_automation_leads.json (5 posts, Mon–Fri)."""
import datetime
import glob
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))

files = sorted(glob.glob(os.path.join(BASE, "automation_leads_*.txt")))
if not files:
    raise SystemExit("No automation_leads_*.txt — run generate_automation_leads.py first")

POSTS_FILE = files[-1]
START = datetime.date.today() + datetime.timedelta(days=1)

# Mon–Fri slots (skip weekend)
days = []
d = START
while len(days) < 5:
    if d.weekday() < 5:
        days.append(d)
    d += datetime.timedelta(days=1)

TIMES = ["9:00 AM", "12:00 PM", "9:00 AM", "12:00 PM", "9:00 AM"]
LABELS = [
    "1. NEWS → AUTOMATION",
    "2. CASE STUDY",
    "3. QUALIFYING POLL",
    "4. STEAL THIS WORKFLOW",
    "5. DIRECT OFFER",
]
TYPES = ["regular", "regular", "poll", "regular", "regular"]


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


def extract_poll_options(body):
    opts = re.findall(r"☐ (.+)", body)
    return "|".join(o[:30] for o in opts[:4])


def extract_poll_question(body):
    lines = [ln.strip() for ln in body.split("\n") if ln.strip() and not ln.startswith("☐")]
    questions = [ln for ln in lines if "?" in ln]
    if questions:
        return min(questions, key=len)
    return "What's blocking your AI automation?"


with open(POSTS_FILE) as f:
    sections = split_sections(f.read())

posts = []
for i, (label, day, time, ptype) in enumerate(zip(LABELS, days, TIMES, TYPES), 1):
    body = sections.get(label, "").strip()
    post = {
        "id": i,
        "type": ptype,
        "date": day.strftime("%m/%d/%Y"),
        "time": time,
        "caption": body,
    }
    if ptype == "poll":
        post["title"] = extract_poll_question(body)
        post["pollOptionsStr"] = extract_poll_options(body)
    posts.append(post)

out = os.path.join(BASE, "schedule_automation_leads.json")
with open(out, "w") as f:
    json.dump({"posts": posts, "generated": datetime.date.today().isoformat(), "stream": "automation-leads"}, f, indent=2)

print(f"Wrote {out} with {len(posts)} posts")
print(f"Schedule: {days[0].strftime('%m/%d/%Y')} – {days[-1].strftime('%m/%d/%Y')}")
