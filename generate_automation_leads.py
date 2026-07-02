#!/usr/bin/env python3
"""Generate 5 weekly LinkedIn posts aimed at AI automation client leads."""
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
    print("Error: GEMINI_API_KEY not found in .env")
    sys.exit(1)

ai_news = []
if os.path.exists("ai_news_data.json"):
    with open("ai_news_data.json") as f:
        ai_news = json.load(f)[:15]

if not ai_news:
    print("Warning: ai_news_data.json empty — run fetch_ai_news_rss.py first")

news_context = ""
for i, item in enumerate(ai_news, 1):
    news_context += (
        f"Story {i} [{item.get('source', '')}]:\n"
        f"Title: {item.get('title', '')}\n"
        f"Summary: {item.get('description', '')[:350]}\n"
        f"URL: {item.get('url', '')}\n---\n"
    )

used_topics = []
log_path = "automation-leads-run-log.json"
if os.path.exists(log_path):
    try:
        with open(log_path) as f:
            log = json.load(f)
        used_topics = [e.get("news_hook") for e in log[-14:] if e.get("news_hook")]
    except Exception:
        pass

SYSTEM = """You are a LinkedIn ghostwriter for Hitesh, a full-stack AI web developer who:
- Builds full-stack SaaS products, websites, and SaaS modules
- Ships custom AI automations (agents, API integrations, workflow pipelines)
- Connects AI tools to real business stacks: CRMs, Slack, Notion, HubSpot, Stripe, internal dashboards

Your job: write 5 LinkedIn posts per week that attract PAYING automation clients — not followers for news.

WRITING RULES:
1. First person is allowed for credibility ("I build…", "I've wired…", "I shipped…").
2. Lead with fresh AI news where specified, then pivot to a concrete automation opportunity.
3. No jargon: explain in plain English (no LLM, RAG, tokens, inference, fine-tuning).
4. No em-dashes. Use commas or periods.
5. Every post MUST end with a lead CTA — rotate these:
   - "Comment AUTO and I'll suggest 3 automations for your stack."
   - "DM me your tools (CRM + chat + project tool) and I'll reply with one workflow worth building first."
   - "DM AUTO if you want a free 15-minute automation audit this week."
6. Never mention @handles, FounderWing, or third-party personal brands.
7. Banned words: game-changer, disruptive, leverage (verb), synergy, paradigm shift, revolutionary, cutting-edge, empower, unlock, delve, landscape (as buzzword).
8. Be specific: name tools, triggers, outcomes, time saved. Vague "AI will transform business" posts fail.

POST TYPES — output exactly these 5 sections with headers shown below."""

USER = f"""TODAY'S AI NEWS (pick fresh stories — do NOT reuse these banned hooks: {json.dumps(used_topics)}):

{news_context}

Write 5 posts using EXACTLY this format (headers must match):

==================================================
1. NEWS → AUTOMATION
==================================================
[Hook: 1-2 lines on the freshest relevant news from above]
[So what: what this means for a SaaS team or ops-heavy business]
[Automation angle: describe a specific workflow you'd build — trigger, AI step, SaaS integrations]
[Proof: one line — "I've built similar automations for SaaS teams…"]
[CTA: Comment AUTO or DM variant]

==================================================
2. CASE STUDY
==================================================
[A anonymized mini case study: client type (SaaS/agency/ops team), problem, stack, what you built, outcome with numbers if plausible]
[CTA: DM AUTO if you want something similar wired into your product]

==================================================
3. QUALIFYING POLL
==================================================
[2-3 sentence setup framing an automation dilemma]

[Poll question — one line]

☐ [Option A — e.g. don't know what to automate]
☐ [Option B — tried Zapier, hit limits]
☐ [Option C — need custom SaaS/API integration]
☐ [Option D — no dev on team]

[One line: "Comment your choice — I'll reply with the fastest path for that situation."]

==================================================
4. STEAL THIS WORKFLOW
==================================================
[Under 150 words. Format:]
Trigger: [event]
Step 1: [AI action]
Step 2: [SaaS action]
Result: [business outcome]
[CTA: DM me if you want this built custom for your stack]

==================================================
5. DIRECT OFFER
==================================================
[Short post: you have bandwidth for 2 automation projects this month OR offering free 15-min audits]
[List 3 things you automate: support triage, lead enrichment, doc generation, onboarding flows, reporting, etc.]
[Strong CTA: DM AUTO with your stack]

Output ONLY the 5 sections above. No preamble."""

gemini_model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={gemini_key}"

payload = {
    "contents": [{"role": "user", "parts": [{"text": USER}]}],
    "systemInstruction": {"parts": [{"text": SYSTEM}]},
    "generationConfig": {"maxOutputTokens": 6000},
}

req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)

print(f"Generating automation lead posts via {gemini_model}...")
try:
    with urllib.request.urlopen(req, context=ctx) as res:
        resp = json.loads(res.read().decode("utf-8"))
        text = resp["candidates"][0]["content"]["parts"][0]["text"]
except Exception as e:
    traceback.print_exc()
    print(f"Generation failed: {e}")
    sys.exit(1)

date_compact = datetime.date.today().isoformat().replace("-", "")
out_path = f"automation_leads_{date_compact}.txt"
with open(out_path, "w") as f:
    f.write(text.strip() + "\n")
print(f"Wrote {out_path}")

# Append to run log
entry = {
    "date": datetime.date.today().isoformat(),
    "file": out_path,
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
