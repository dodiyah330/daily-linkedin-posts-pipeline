#!/usr/bin/env python3
"""Generate 14 LinkedIn posts/week for personal profile: 2/day Mon–Sun (1 image + 1 text each day)."""
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

gemini_key = openrouter_key = None
with open(".env") as f:
    for line in f:
        if line.startswith("GEMINI_API_KEY="):
            gemini_key = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
        elif line.startswith("OPENROUTER_API_KEY="):
            openrouter_key = line.strip().split("=", 1)[1].strip().strip('"').strip("'")

if not gemini_key and not openrouter_key:
    print("Error: need GEMINI_API_KEY or OPENROUTER_API_KEY in .env")
    sys.exit(1)

# 14 slots: each day = IMAGE then TEXT
SLOTS = [
    ("1. MON IMAGE — NEWS → AUTOMATION", "image", "Fresh AI/news hook → SaaS pain → automation you'd build → Comment AUTO"),
    ("2. MON TEXT — BUILDER TIP", "text", "One practical tip from shipping automations. No image. Soft CTA."),
    ("3. TUE IMAGE — CASE STUDY", "image", "Anonymized mini case: problem, stack, what you built, outcome. Soft CTA."),
    ("4. TUE TEXT — MYTH BUST", "text", "Bust a myth about Zapier/custom AI/outsourcing. Soft CTA."),
    ("5. WED IMAGE — QUALIFYING POLL", "image", "Setup + poll question + 4 ☐ options that self-identify prospects."),
    ("6. WED TEXT — STEAL THIS WORKFLOW", "text", "Trigger → AI step → SaaS action → result. Under 150 words. Soft CTA."),
    ("7. THU IMAGE — WORKFLOW CARD", "image", "Visual-friendly workflow: Trigger / Step 1 / Step 2 / Result. Soft CTA."),
    ("8. THU TEXT — CLIENT LESSON", "text", "One lesson from a real (anonymized) client build. Soft CTA."),
    ("9. FRI IMAGE — DIRECT OFFER", "image", "2 build slots / free 15-min audit. List 3 things you automate. Strong CTA."),
    ("10. FRI TEXT — TOOL ANGLE", "text", "How a common tool (HubSpot/Slack/Stripe) gets 10x better with custom glue. Soft CTA."),
    ("11. SAT IMAGE — PAIN → AUTOMATION", "image", "Messy ops pain (tabs, copy-paste, WhatsApp) → automation fix. Soft CTA."),
    ("12. SAT TEXT — FAQ", "text", "Answer one common buyer question (cost, timeline, Zapier vs custom). Soft CTA."),
    ("13. SUN IMAGE — MINI WIN", "image", "Short before/after win with a number. Soft CTA."),
    ("14. SUN TEXT — SOFT OFFER", "text", "Low-pressure discovery / audit invite for the week ahead. Soft CTA."),
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
        f"Summary: {item.get('description', '')[:350]}\n---\n"
    )

used_topics = []
log_path = "automation-leads-run-log.json"
if os.path.exists(log_path):
    try:
        with open(log_path) as f:
            log = json.load(f)
        used_topics = [e.get("news_hook") for e in log[-21:] if e.get("news_hook")]
    except Exception:
        pass

profile_context = ""
if os.path.exists("automation_profile.md"):
    with open("automation_profile.md") as f:
        profile_context = f.read().strip()
    print("Loaded automation_profile.md")
else:
    profile_context = "(No automation_profile.md — using generic builder profile.)"

format_block = "\n\n".join(
    f"==================================================\n{label}\n==================================================\n[{brief}]"
    for label, _kind, brief in SLOTS
)

SYSTEM = """You are a LinkedIn ghostwriter for Hitesh, a full-stack AI web developer who:
- Builds full-stack SaaS products, websites, and SaaS modules
- Ships custom AI automations (agents, API integrations, workflow pipelines)
- Connects AI tools to real business stacks: CRMs, Slack, Notion, HubSpot, Stripe, internal dashboards

Your job: write 14 LinkedIn posts for ONE week (2 per day, Mon–Sun) that attract PAYING automation clients.

CADENCE RULES:
- Odd-numbered sections (1,3,5,7,9,11,13) are IMAGE posts — write captions that pair with an infographic (punchy, scannable).
- Even-numbered sections (2,4,6,8,10,12,14) are TEXT-ONLY posts — no image dependency.
- All 14 topics must be distinct (zero overlap).

WRITING RULES:
1. First person is allowed for credibility ("I build…", "I've wired…", "I shipped…").
2. Lead with fresh AI news only where the section says NEWS.
3. No jargon: plain English (no LLM, RAG, tokens, inference, fine-tuning).
4. No em-dashes. Use commas or periods.
5. Every post MUST end with a lead CTA — rotate:
   - "Comment AUTO and I'll suggest 3 automations for your stack."
   - "DM me your tools (CRM + chat + project tool) and I'll reply with one workflow worth building first."
   - "DM AUTO if you want a free 15-minute automation audit this week."
6. Never mention @handles, FounderWing, or third-party personal brands.
7. Banned words: game-changer, disruptive, leverage (verb), synergy, paradigm shift, revolutionary, cutting-edge, empower, unlock, delve, landscape (as buzzword).
8. Be specific: name tools, triggers, outcomes, time saved.
9. Length: IMAGE captions ~90–180 words; TEXT posts ~120–220 words. Poll section includes 4 ☐ options."""

USER = f"""BUILDER PROFILE:
{profile_context}

AI NEWS (use mainly for MON IMAGE — NEWS → AUTOMATION; do NOT reuse banned hooks: {json.dumps(used_topics)}):
{news_context or '(none)'}

Write EXACTLY 14 posts using these headers (must match exactly):

{format_block}

Output ONLY the 14 sections. No preamble. No META."""


def call_gemini(model):
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={gemini_key}"
    )
    payload = {
        "contents": [{"role": "user", "parts": [{"text": USER}]}],
        "systemInstruction": {"parts": [{"text": SYSTEM}]},
        "generationConfig": {"maxOutputTokens": 12000},
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
        "max_tokens": 12000,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {openrouter_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://openxcode.com",
            "X-Title": "automation-leads",
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
    print(f"Generating 14 automation lead posts via Gemini {gemini_model}...")
    try:
        text = call_gemini(gemini_model)
    except Exception as e:
        errors.append(f"gemini: {e}")
        print(f"Gemini failed ({e}); trying OpenRouter...")

if text is None and openrouter_key:
    print(f"Generating 14 automation lead posts via OpenRouter {openrouter_model}...")
    try:
        text = call_openrouter(openrouter_model)
    except Exception as e:
        errors.append(f"openrouter: {e}")
        traceback.print_exc()

if text is None:
    print("Generation failed: " + " | ".join(errors))
    sys.exit(1)

text = text.strip() + "\n"
missing = [label for label, _, _ in SLOTS if label not in text]
if missing:
    print(f"Warning: missing sections: {missing}")

date_compact = datetime.date.today().isoformat().replace("-", "")
out_path = f"automation_leads_{date_compact}.txt"
with open(out_path, "w") as f:
    f.write(text)
print(f"Wrote {out_path} (14 posts: 7 image + 7 text)")

entry = {
    "date": datetime.date.today().isoformat(),
    "file": out_path,
    "mode": "14-posts-2-per-day",
    "news_hook": ai_news[0].get("title") if ai_news else None,
}
try:
    log = json.load(open(log_path)) if os.path.exists(log_path) else []
except Exception:
    log = []
log.append(entry)
with open(log_path, "w") as f:
    json.dump(log[-30:], f, indent=2)
print("Updated automation-leads-run-log.json")
