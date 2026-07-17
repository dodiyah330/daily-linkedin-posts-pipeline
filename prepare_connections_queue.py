#!/usr/bin/env python3
"""Build today's connection request queue from US automation prospects."""
import datetime
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

PROSPECTS_FILE = os.environ.get(
    "PROSPECTS_FILE", "prospects/us_automation_target.json"
)
NOTES_FILE = os.environ.get("CONNECTION_NOTES_FILE", "connection_notes.json")
QUEUE_FILE = os.environ.get("CONNECTIONS_FILE", "connections_queue.json")
LOG_FILE = "connections-run-log.json"

MAX_PER_RUN = int(os.environ.get("MAX_CONNECTIONS_PER_RUN", "10"))
MAX_PER_DAY = int(os.environ.get("MAX_CONNECTIONS_PER_DAY", "15"))
REQUIRE_US = os.environ.get("REQUIRE_US_LOCATION", "1") != "0"


def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default


if not os.path.exists(PROSPECTS_FILE):
    alt = "prospects/us_automation_target.example.json"
    if os.path.exists(alt):
        print(f"Warning: using {alt} — copy to {PROSPECTS_FILE} with real profiles")
        PROSPECTS_FILE = alt
    else:
        print(f"Error: {PROSPECTS_FILE} not found")
        sys.exit(1)

prospects_data = load_json(PROSPECTS_FILE, {})
prospects = prospects_data.get("prospects") or []
notes = {n["id"]: n for n in load_json(NOTES_FILE, []) if n.get("id")}
log = load_json(LOG_FILE, [])

today = datetime.date.today().isoformat()
sent_today = sum(
    1 for e in log if e.get("date") == today and e.get("status") == "sent"
)
sent_ids = {e.get("prospect_id") for e in log if e.get("status") in ("sent", "pending")}
failed_skip = {
    e.get("prospect_id")
    for e in log
    if e.get("status") in ("limit_reached", "email_required")
}

remaining_today = max(0, MAX_PER_DAY - sent_today)
batch_size = min(MAX_PER_RUN, remaining_today)

if batch_size <= 0:
    print(f"Daily limit reached ({sent_today}/{MAX_PER_DAY} sent today).")
    sys.exit(0)

queue = []
for p in prospects:
    if len(queue) >= batch_size:
        break

    pid = p.get("id") or p.get("linkedin_url", "")
    url = (p.get("linkedin_url") or "").strip()
    if not url or "linkedin.com/in/" not in url:
        print(f"Skipping {pid}: invalid linkedin_url")
        continue
    if pid in sent_ids:
        continue
    if pid in failed_skip:
        continue

    loc = (p.get("location") or "").lower()
    if REQUIRE_US and "united states" not in loc and ", us" not in loc and not loc.endswith(" us"):
        print(f"Skipping {pid}: not US location ({p.get('location')})")
        continue

    note_entry = notes.get(pid, {})
    note = note_entry.get("note") or p.get("note", "")
    if not note:
        print(f"Skipping {pid}: no connection note — run generate_connection_notes.py")
        continue

    queue.append({
        "id": pid,
        "name": p.get("name"),
        "title": p.get("title"),
        "company": p.get("company"),
        "location": p.get("location"),
        "linkedin_url": url,
        "note": note[:300],
    })

out = {
    "date": today,
    "audience": prospects_data.get("audience", "US SaaS automation ICP"),
    "criteria": prospects_data.get("criteria", {}),
    "limits": {
        "max_per_run": MAX_PER_RUN,
        "max_per_day": MAX_PER_DAY,
        "sent_today": sent_today,
        "remaining_today": remaining_today,
    },
    "connections": queue,
}

with open(QUEUE_FILE, "w") as f:
    json.dump(out, f, indent=2)

print(f"Queued {len(queue)} connection requests → {QUEUE_FILE}")
if not queue:
    print("Nothing to send. Add prospects, generate notes, or check run log.")
    sys.exit(1)
