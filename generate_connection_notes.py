#!/usr/bin/env python3
"""Generate personalized LinkedIn connection notes for US automation ICP prospects."""
import datetime
import json
import os
import re
import ssl
import sys
import traceback
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

PROSPECTS_FILE = os.environ.get(
    "PROSPECTS_FILE", "prospects/us_automation_target.json"
)
NOTES_FILE = os.environ.get("CONNECTION_NOTES_FILE", "connection_notes.json")

gemini_key = None
with open(".env") as f:
    for line in f:
        if line.startswith("GEMINI_API_KEY="):
            gemini_key = line.strip().split("=", 1)[1]
            break

if not gemini_key:
    print("Error: GEMINI_API_KEY not found in .env")
    sys.exit(1)

if not os.path.exists(PROSPECTS_FILE):
    alt = "prospects/us_automation_target.example.json"
    if os.path.exists(alt):
        print(f"Warning: {PROSPECTS_FILE} not found, using {alt}")
        PROSPECTS_FILE = alt
    else:
        print(f"Error: prospects file not found: {PROSPECTS_FILE}")
        sys.exit(1)

with open(PROSPECTS_FILE) as f:
    data = json.load(f)

prospects = data.get("prospects") or []
if not prospects:
    print(f"No prospects in {PROSPECTS_FILE}. Add US ICP profiles and re-run.")
    sys.exit(1)

profile = ""
if os.path.exists("automation_profile.md"):
    with open("automation_profile.md") as f:
        profile = f.read().strip()[:3500]

existing = {}
if os.path.exists(NOTES_FILE):
    try:
        with open(NOTES_FILE) as f:
            for item in json.load(f):
                if item.get("id"):
                    existing[item["id"]] = item
    except Exception:
        pass

SYSTEM = """You write short LinkedIn connection request notes for Hitesh Dodiya, a full-stack AI developer who builds custom automations for US SaaS teams.

RULES:
1. Max 280 characters per note (LinkedIn limit is 300 — stay under 280).
2. US tone: reference their stack or ops pain if provided. No generic "I'd like to add you to my network."
3. One clear hook: automation audit, workflow idea, or relevant case study angle.
4. No jargon (no RAG, tokens, LLM). Plain English.
5. No em-dashes. No @handles. No links.
6. Sign off is optional — prefer ending with a soft question or offer.
7. Output ONLY valid JSON array — no markdown fences."""

USER = f"""BUILDER PROFILE:
{profile}

US AUDIENCE CRITERIA:
{json.dumps(data.get('criteria', {}), indent=2)}

PROSPECTS (write one note each):
{json.dumps(prospects, indent=2)}

Return JSON array:
[
  {{"id": "prospect-id", "note": "personalized note under 280 chars"}}
]"""

gemini_model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={gemini_key}"

payload = {
    "contents": [{"role": "user", "parts": [{"text": USER}]}],
    "systemInstruction": {"parts": [{"text": SYSTEM}]},
    "generationConfig": {"maxOutputTokens": 4000, "temperature": 0.7},
}

print(f"Generating connection notes for {len(prospects)} prospects via {gemini_model}...")
try:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, context=ctx) as res:
        resp = json.loads(res.read().decode("utf-8"))
        raw = resp["candidates"][0]["content"]["parts"][0]["text"].strip()
except Exception as e:
    traceback.print_exc()
    print(f"Generation failed: {e}")
    sys.exit(1)

raw = re.sub(r"^```(?:json)?\s*", "", raw)
raw = re.sub(r"\s*```$", "", raw)
notes = json.loads(raw)

by_id = {n["id"]: n for n in notes if n.get("id") and n.get("note")}
merged = []
for p in prospects:
    pid = p.get("id") or p.get("linkedin_url", "")
    entry = {
        "id": pid,
        "name": p.get("name"),
        "company": p.get("company"),
        "linkedin_url": p.get("linkedin_url"),
        "note": (by_id.get(pid) or existing.get(pid) or {}).get("note", ""),
        "generated_at": datetime.date.today().isoformat(),
    }
    if not entry["note"]:
        print(f"Warning: no note generated for {pid}")
        continue
    if len(entry["note"]) > 300:
        entry["note"] = entry["note"][:297] + "..."
    merged.append(entry)

with open(NOTES_FILE, "w") as f:
    json.dump(merged, f, indent=2)

print(f"Wrote {len(merged)} notes to {NOTES_FILE}")
