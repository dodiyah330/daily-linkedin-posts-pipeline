#!/usr/bin/env python3
"""Generate a full week of OpenXcode company LinkedIn posts (all 7 archetypes)."""
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

gemini_key = openrouter_key = None
with open(".env") as f:
    for line in f:
        if line.startswith("GEMINI_API_KEY="):
            gemini_key = line.strip().split("=", 1)[1]
        elif line.startswith("OPENROUTER_API_KEY="):
            openrouter_key = line.strip().split("=", 1)[1]

if not gemini_key and not openrouter_key:
    print("Error: need GEMINI_API_KEY or OPENROUTER_API_KEY in .env")
    sys.exit(1)

ARCHETYPES = [
    {
        "key": "NEWS_TO_BUILD",
        "label": "1. NEWS → BUILD",
        "brief": (
            "Hook with a fresh tech/product news angle relevant to founders or SMBs. "
            "Pivot to what that means for someone building a web/mobile product. "
            "Explain one concrete way OpenXcode would ship the fix. Soft CTA."
        ),
    },
    {
        "key": "CASE_STUDY",
        "label": "2. CASE STUDY",
        "brief": (
            "Anonymized or lightly named mini case: client type, problem, what we built "
            "(web/mobile/UI/AI), outcome. Company voice. Soft CTA."
        ),
    },
    {
        "key": "MYTH_BUST",
        "label": "3. MYTH BUST",
        "brief": (
            "Bust a common myth about custom software, apps, AI features, or outsourcing "
            "(e.g. 'AI replaces the need for a product', 'cheap freelancers are fine for v1'). "
            "Practical takeaway. Soft CTA."
        ),
    },
    {
        "key": "BUILD_TIP",
        "label": "4. BUILD TIP",
        "brief": (
            "One practical tip from shipping client projects: UX, performance, WordPress/Elementor "
            "speed, mobile UX, scoping an MVP, handoff. Teach first. Soft CTA."
        ),
    },
    {
        "key": "SERVICE_SPOTLIGHT",
        "label": "5. SERVICE SPOTLIGHT",
        "brief": (
            "Spotlight one OpenXcode service (web app, mobile, UI/UX, website, or AI). "
            "Who it is for, what a typical engagement looks like, when to choose it. Soft CTA."
        ),
    },
    {
        "key": "PAIN_TO_PRODUCT",
        "label": "6. PAIN → PRODUCT",
        "brief": (
            "Start from a messy ops pain (WhatsApp threads, spreadsheets, no customer app) "
            "and show how a focused web/mobile product fixes it. Soft CTA."
        ),
    },
    {
        "key": "DIRECT_OFFER",
        "label": "7. DIRECT OFFER",
        "brief": (
            "Short offer post: discovery call / proposal within one business day. "
            "List 3 things we build. Strong but non-spammy CTA (Comment BUILD or DM)."
        ),
    },
]

ai_news = []
if os.path.exists("ai_news_data.json"):
    with open("ai_news_data.json") as f:
        ai_news = json.load(f)[:15]

news_context = ""
for i, item in enumerate(ai_news, 1):
    news_context += (
        f"Story {i} [{item.get('source', '')}]:\n"
        f"Title: {item.get('title', '')}\n"
        f"Summary: {item.get('description', '')[:300]}\n---\n"
    )

used_topics = []
log_path = "openxcode-run-log.json"
if os.path.exists(log_path):
    try:
        with open(log_path) as f:
            log = json.load(f)
        used_topics = [e.get("topic") for e in log[-30:] if e.get("topic")]
    except Exception:
        pass

profile_context = ""
if os.path.exists("openxcode_profile.md"):
    with open("openxcode_profile.md") as f:
        profile_context = f.read().strip()
    print("Loaded openxcode_profile.md")

archetype_block = "\n".join(
    f"- {a['label']} ({a['key']}): {a['brief']}" for a in ARCHETYPES
)

SYSTEM = """You are the LinkedIn ghostwriter for OpenXcode, a software company that builds
custom web apps, mobile apps, UI/UX, websites, and AI features for startups, SMBs, enterprises, and agencies.

Your job: write SEVEN company-page LinkedIn posts (one per weekday archetype) that attract PROJECT INQUIRIES.

WRITING RULES:
1. Company voice only: "we", "our", "the OpenXcode team". Never write as a solo freelancer "I".
2. Audience: founders and business owners who need a reliable build partner.
3. Specific > vague. Name platforms, timelines, outcomes when plausible.
4. No em-dashes. Use commas or periods.
5. No jargon walls (no LLM/RAG/tokens). Plain English for AI topics.
6. Every post MUST end with a lead CTA — rotate variants of:
   - "Comment BUILD and we'll reply with a rough approach and timeline."
   - "DM us your idea (or current stack + deadline) and we'll reply within one business day."
   - "Request a proposal at openxcode.com — we get back within one business day."
7. Never mention FounderWing, personal @handles, or third-party personal brands.
8. Banned words: game-changer, disruptive, leverage (verb), synergy, paradigm shift,
   revolutionary, cutting-edge, empower, unlock, delve, landscape (as buzzword).
9. Length: roughly 120–220 words each. Short paragraphs. Scannable on mobile.
10. Do not invent fake client logos or impossible metrics.
11. All 7 posts must cover DIFFERENT topics (zero overlap)."""

USER = f"""COMPANY PROFILE:
{profile_context}

ARCHETYPES TO WRITE (exactly these 7, in order):
{archetype_block}

RECENT AI / TECH NEWS (use mainly for NEWS → BUILD):
{news_context or '(none)'}

BANNED TOPICS (do not reuse): {json.dumps(used_topics)}

Write EXACTLY 7 posts using this format (headers must match exactly):

==================================================
1. NEWS → BUILD
==================================================
[post body]

==================================================
2. CASE STUDY
==================================================
[post body]

==================================================
3. MYTH BUST
==================================================
[post body]

==================================================
4. BUILD TIP
==================================================
[post body]

==================================================
5. SERVICE SPOTLIGHT
==================================================
[post body]

==================================================
6. PAIN → PRODUCT
==================================================
[post body]

==================================================
7. DIRECT OFFER
==================================================
[post body]

Then one META line listing topics:
META: {{"topics":["t1","t2","t3","t4","t5","t6","t7"]}}

Output ONLY the 7 sections and the META line. No preamble."""


def call_gemini(model):
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={gemini_key}"
    )
    payload = {
        "contents": [{"role": "user", "parts": [{"text": USER}]}],
        "systemInstruction": {"parts": [{"text": SYSTEM}]},
        "generationConfig": {"maxOutputTokens": 8000},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, context=ctx) as res:
        resp = json.loads(res.read().decode("utf-8"))
        return resp["candidates"][0]["content"]["parts"][0]["text"]


def call_openrouter(model):
    url = "https://openrouter.ai/api/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": USER},
        ],
        "max_tokens": 8000,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {openrouter_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, context=ctx) as res:
        resp = json.loads(res.read().decode("utf-8"))
        return resp["choices"][0]["message"]["content"]


gemini_model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
openrouter_model = os.environ.get("OPENROUTER_MODEL", "google/gemini-2.5-flash")

text = None
errors = []
if gemini_key:
    print(f"Generating OpenXcode week via Gemini {gemini_model}...")
    try:
        text = call_gemini(gemini_model)
    except Exception as e:
        errors.append(f"gemini: {e}")
        print(f"Gemini failed ({e}); trying OpenRouter...")

if text is None and openrouter_key:
    print(f"Generating OpenXcode week via OpenRouter {openrouter_model}...")
    try:
        text = call_openrouter(openrouter_model)
    except Exception as e:
        errors.append(f"openrouter: {e}")
        traceback.print_exc()

if text is None:
    print("Generation failed: " + " | ".join(errors))
    sys.exit(1)

text = text.strip()
topics = []
for line in text.splitlines():
    if line.startswith("META:"):
        try:
            topics = json.loads(line[len("META:"):].strip()).get("topics") or []
        except Exception:
            topics = []
        break

post_body = "\n".join(
    line for line in text.splitlines() if not line.startswith("META:")
).strip() + "\n"

# Validate all 7 headers exist
missing = [a["label"] for a in ARCHETYPES if a["label"] not in post_body]
if missing:
    print(f"Warning: missing sections: {missing}")

today = datetime.date.today()
date_compact = today.isoformat().replace("-", "")
out_path = f"openxcode_posts_week_{date_compact}.txt"
with open(out_path, "w") as f:
    f.write(post_body)
print(f"Wrote {out_path}")

# Also write a convenience copy used by prepare script
daily_path = f"openxcode_posts_{date_compact}.txt"
with open(daily_path, "w") as f:
    f.write(post_body)
print(f"Also wrote {daily_path} (week batch)")

entry = {
    "date": today.isoformat(),
    "file": out_path,
    "mode": "week",
    "archetypes": [a["key"] for a in ARCHETYPES],
    "topics": topics,
}
try:
    log = json.load(open(log_path)) if os.path.exists(log_path) else []
except Exception:
    log = []
log.append(entry)
with open(log_path, "w") as f:
    json.dump(log[-60:], f, indent=2)
print(f"Updated {log_path}: {topics or '(no topics parsed)'}")
