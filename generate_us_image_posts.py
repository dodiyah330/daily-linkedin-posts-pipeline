#!/usr/bin/env python3
"""Generate 5 US-focused LinkedIn image post captions (Mon–Fri)."""
import datetime
import json
import os
import ssl
import sys
import traceback
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

gemini_key = None
with open(".env") as f:
    for line in f:
        if line.startswith("GEMINI_API_KEY="):
            gemini_key = line.strip().split("=", 1)[1]
            break

if not gemini_key:
    sys.exit("Error: GEMINI_API_KEY not found in .env")

ai_news = []
if os.path.exists("ai_news_data.json"):
    with open("ai_news_data.json") as f:
        ai_news = json.load(f)[:12]

news_context = ""
for i, item in enumerate(ai_news, 1):
    news_context += (
        f"Story {i} [{item.get('source', '')}]:\n"
        f"Title: {item.get('title', '')}\n"
        f"Summary: {item.get('description', '')[:300]}\n---\n"
    )

used = []
log_path = "us-image-run-log.json"
if os.path.exists(log_path):
    try:
        with open(log_path) as f:
            used = [e.get("hook") for e in json.load(f)[-14:] if e.get("hook")]
    except Exception:
        pass

profile = ""
if os.path.exists("automation_profile.md"):
    with open("automation_profile.md") as f:
        profile = f.read().strip()

SYSTEM = """You write LinkedIn captions for Hitesh Dodiya, a full-stack AI developer selling custom automations to US SaaS companies.

AUDIENCE: US founders and ops leaders (East Coast + West Coast). Assume they use HubSpot, Salesforce, Slack, Stripe, DocuSign, Intercom, Notion.

US-SPECIFIC RULES:
1. Use US framing: "US SaaS teams", "Series A startups in the US", "before your 9 AM standup", "SOC 2 audit trail", dollar outcomes.
2. No jargon (no RAG, tokens, fine-tuning). Plain English.
3. No em-dashes. Short paragraphs. Under 700 characters per caption (image carries the story).
4. End every caption with: Comment AUTO or DM AUTO variant.
5. Do NOT duplicate generic global posts — angle must feel written for a US operator.
6. Banned: game-changer, leverage, synergy, cutting-edge, unlock, delve."""

USER = f"""BUILDER PROFILE:
{profile[:4000]}

AI NEWS (optional hook for Mon post only):
{news_context}

BANNED hooks (do not reuse): {json.dumps(used)}

Write 5 captions for SEPARATE daily IMAGE posts (US peak feed). Headers must match exactly:

==================================================
1. MON — US NEWS HOOK
==================================================
[Fresh AI news → pain for a US SaaS team → one automation you'd build → Comment AUTO]

==================================================
2. TUE — US OPS WIN
==================================================
[Mini case: US B2B SaaS, manual ops pain, stack, outcome with numbers → DM AUTO]

==================================================
3. WED — US STACK TIP
==================================================
[One tip for US teams using HubSpot/Salesforce + Slack — workflow they can steal → Comment AUTO]

==================================================
4. THU — US WORKFLOW CARD
==================================================
[Trigger → 2 steps → result. Under 120 words. US tool names → DM me your stack]

==================================================
5. FRI — US OFFER
==================================================
[2 automation build slots for US companies this month + free audit → DM AUTO]

Output ONLY the 5 sections. No preamble."""

gemini_model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={gemini_key}"
payload = {
    "contents": [{"role": "user", "parts": [{"text": USER}]}],
    "systemInstruction": {"parts": [{"text": SYSTEM}]},
    "generationConfig": {"maxOutputTokens": 5000},
}

print(f"Generating US image post captions via {gemini_model}...")
try:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, context=ctx) as res:
        resp = json.loads(res.read().decode())
        text = resp["candidates"][0]["content"]["parts"][0]["text"]
except Exception:
    traceback.print_exc()
    sys.exit(1)

date_compact = datetime.date.today().isoformat().replace("-", "")
out_path = os.path.join(BASE, f"us_image_posts_{date_compact}.txt")
with open(out_path, "w") as f:
    f.write(text.strip() + "\n")
print(f"Wrote {out_path}")

entry = {
    "date": datetime.date.today().isoformat(),
    "file": os.path.basename(out_path),
    "hook": ai_news[0].get("title") if ai_news else None,
}
try:
    log = json.load(open(log_path)) if os.path.exists(log_path) else []
except Exception:
    log = []
log.append(entry)
with open(log_path, "w") as f:
    json.dump(log[-30:], f, indent=2)
