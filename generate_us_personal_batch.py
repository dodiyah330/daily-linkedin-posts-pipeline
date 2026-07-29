#!/usr/bin/env python3
"""
Generate 10 days of PERSONAL LinkedIn content for US SaaS audience:
  each day = 1 IMAGE post + 1 CAROUSEL post (6 slides).
Writes us_personal_batch_YYYYMMDD.json

Voice: Hitesh first-person. CTA: Comment AUTO / DM AUTO.
Timing is handled in prepare_us_personal_schedule.py (US Eastern peaks via IST).
"""
import datetime
import json
import os
import re
import ssl
import sys
import time
import traceback
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

DAYS = int(os.environ.get("US_PERSONAL_DAYS", "10"))
if os.environ.get("US_PERSONAL_START"):
    START = datetime.date.fromisoformat(os.environ["US_PERSONAL_START"])
else:
    START = datetime.date.today() + datetime.timedelta(days=1)

gemini_key = openrouter_key = None
with open(".env") as f:
    for line in f:
        if line.startswith("GEMINI_API_KEY="):
            gemini_key = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
        elif line.startswith("OPENROUTER_API_KEY="):
            openrouter_key = line.strip().split("=", 1)[1].strip().strip('"').strip("'")

if not gemini_key and not openrouter_key:
    sys.exit("Need GEMINI_API_KEY or OPENROUTER_API_KEY")

profile = open("automation_profile.md").read() if os.path.exists("automation_profile.md") else ""
ai_news = []
if os.path.exists("ai_news_data.json"):
    ai_news = json.load(open("ai_news_data.json"))[:10]
news_ctx = "\n".join(
    f"- {n.get('title','')}: {str(n.get('description',''))[:160]}" for n in ai_news
)

used = []
if os.path.exists("us-personal-run-log.json"):
    try:
        for e in json.load(open("us-personal-run-log.json"))[-40:]:
            if e.get("topic"):
                used.append(e["topic"])
            if e.get("topics"):
                used.extend(e["topics"])
    except Exception:
        pass

ARCHETYPES = [
    ("US_NEWS_HOOK", "WORKFLOW_CHECKLIST"),
    ("US_CASE_STUDY", "STACK_STEPS"),
    ("US_OPS_PAIN", "BEFORE_AFTER"),
    ("US_STACK_TIP", "STEAL_THIS"),
    ("US_WORKFLOW", "MISTAKE_FIX"),
    ("US_MYTH_BUST", "AUDIT_CHECKLIST"),
    ("US_OFFER", "HOW_I_BUILD"),
    ("US_SDR_ANGLE", "CLIENT_JOURNEY"),
    ("US_SUPPORT_ANGLE", "FEATURE_LISTICLE"),
    ("US_SOFT_CTA", "LAUNCH_CHECKLIST"),
]

ARCHETYPE_BRIEFS = {
    "US_NEWS_HOOK": "Fresh AI/ops news → pain for a US SaaS team → one automation you'd build.",
    "US_CASE_STUDY": "Anonymized US B2B SaaS case: problem, stack (HubSpot/Slack/Stripe), outcome with numbers.",
    "US_OPS_PAIN": "Ops/sales/support drowning in handoffs before 9 AM ET standup.",
    "US_STACK_TIP": "One practical tip for HubSpot/Salesforce + Slack US teams.",
    "US_WORKFLOW": "Trigger → 2-3 steps → result. Name US tools.",
    "US_MYTH_BUST": "Bust a myth about Zapier/Make/AI agents for US SaaS ops.",
    "US_OFFER": "2 build slots this month for US companies + free 15-min audit.",
    "US_SDR_ANGLE": "SDR / sales prep automation for US SaaS demos.",
    "US_SUPPORT_ANGLE": "Support triage / Intercom / Notion help-desk automation for US product teams.",
    "US_SOFT_CTA": "Soft invite: DM your stack (CRM + chat + project tool).",
    "WORKFLOW_CHECKLIST": "Checklist of automations a US SaaS ops team should wire this quarter.",
    "STACK_STEPS": "Step by step: how you'd wire their stack in a week.",
    "BEFORE_AFTER": "Before manual chaos vs after automation for a US Series A team.",
    "STEAL_THIS": "Steal-this workflow carousel with concrete HubSpot/Slack/Stripe steps.",
    "MISTAKE_FIX": "Common US SaaS automation mistakes and the fix.",
    "AUDIT_CHECKLIST": "Free automation audit checklist for US founders.",
    "HOW_I_BUILD": "How you scope and ship a fixed-price automation build.",
    "CLIENT_JOURNEY": "From Calendly book → enrich → Slack brief for the rep.",
    "FEATURE_LISTICLE": "5 automations US support teams ask for most.",
    "LAUNCH_CHECKLIST": "Pre-build checklist before hiring an automation partner.",
}

SYSTEM = """You are the LinkedIn ghostwriter for Hitesh Dodiya, a full-stack AI developer selling custom automations to US SaaS companies.
Voice: first person (I / I've / my). Practical. Name real tools.
AUDIENCE: US founders and ops leaders (East Coast + West Coast). HubSpot, Salesforce, Slack, Stripe, DocuSign, Intercom, Notion, Calendly.
US FRAMING REQUIRED: "US SaaS", "Series A", "before your 9 AM ET standup", dollar outcomes, SOC 2 / audit trail when relevant.
CTA rotate: Comment AUTO / DM AUTO / DM your stack (CRM + chat + project tool).
No em-dashes. No @handles. No company-page "we/our" voice.
Banned: game-changer, cutting-edge, leverage, synergy, unlock, delve, disruptive, revolutionary.
Return ONLY valid JSON."""


def call_llm(user, max_tokens=6000):
    openrouter_model = os.environ.get("OPENROUTER_MODEL", "google/gemini-2.5-flash")
    gemini_model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
    errors = []
    if gemini_key:
        try:
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{gemini_model}:generateContent?key={gemini_key}"
            )
            payload = {
                "contents": [{"role": "user", "parts": [{"text": user}]}],
                "systemInstruction": {"parts": [{"text": SYSTEM}]},
                "generationConfig": {
                    "maxOutputTokens": max_tokens,
                    "responseMimeType": "application/json",
                },
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, context=ctx, timeout=180) as res:
                resp = json.loads(res.read().decode())
                return resp["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            errors.append(f"gemini:{e}")
            print(f"  Gemini failed ({e})")
    if openrouter_key:
        url = "https://openrouter.ai/api/v1/chat/completions"
        payload = {
            "model": openrouter_model,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": user + "\n\nReturn ONLY valid JSON."},
            ],
            "max_tokens": max_tokens,
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {openrouter_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/dodiyah330",
                "X-Title": "USPersonalBatch",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, context=ctx, timeout=180) as res:
            resp = json.loads(res.read().decode())
            return resp["choices"][0]["message"]["content"]
    raise RuntimeError(" | ".join(errors))


def parse_json(raw):
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    raw = raw.replace("→", " to ").replace("—", "-").replace("–", "-")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", raw)
        if not m:
            raise
        return json.loads(m.group(0))


def gen_day(day_i, date_obj, img_arch, car_arch):
    user = f"""BUILDER PROFILE:
{profile[:3200]}

NEWS (use only if archetype is US_NEWS_HOOK):
{news_ctx or '(none)'}

BANNED topics: {json.dumps(used[-30:])}

Generate ONE day of PERSONAL LinkedIn content for {date_obj.isoformat()} ({date_obj.strftime('%A')}).
Image archetype: {img_arch} -> {ARCHETYPE_BRIEFS.get(img_arch, '')}
Carousel archetype: {car_arch} -> {ARCHETYPE_BRIEFS.get(car_arch, '')}

Return JSON:
{{
  "topic": "short unique US-automation topic phrase",
  "image": {{
    "caption": "120-180 word first-person caption ending with CTA (Comment AUTO or DM AUTO)",
    "badge": "AI Automation",
    "title_main": "3-5 words",
    "title_span": "2-4 words",
    "subtitle": "max 120 chars",
    "takeaway_num": "hero stat or short label",
    "takeaway_text": "max 100 chars",
    "bars": [
      {{"label": "max 36 chars", "value": "display", "width_pct": "85%", "color": "#5E6AD2"}},
      {{"label": "b", "value": "v", "width_pct": "70%", "color": "#2563EB"}},
      {{"label": "c", "value": "v", "width_pct": "55%", "color": "#059669"}}
    ]
  }},
  "carousel": {{
    "caption": "90-150 word first-person caption for the document carousel ending with CTA",
    "slides": [
      {{"kick": "HOOK", "headline": "6-8 word hook with optional <em>accent</em>", "body": "1-2 short sentences"}},
      {{"kick": "01", "headline": "...", "body": "..."}},
      {{"kick": "02", "headline": "...", "body": "..."}},
      {{"kick": "03", "headline": "...", "body": "..."}},
      {{"kick": "04", "headline": "...", "body": "..."}},
      {{"cta": true, "headline": "Want this on <em>your</em> stack?", "body": "Comment AUTO or DM AUTO and I will suggest 3 automations."}}
    ]
  }}
}}

Rules:
- Exactly 6 carousel slides; last must be cta:true
- No em-dashes
- US framing in both captions (US SaaS / Eastern standup / dollar or hour outcomes)
- Bars show automation outcomes (hours saved, response time, demo-to-close lift) - not fake follower counts
- First-person voice throughout
"""
    raw = call_llm(user)
    data = parse_json(raw)
    if "image" not in data or "carousel" not in data:
        raise ValueError("missing image/carousel keys")
    slides = data["carousel"].get("slides") or []
    if len(slides) < 5:
        raise ValueError(f"need >=5 slides, got {len(slides)}")
    while len(slides) < 6:
        slides.append({
            "cta": True,
            "headline": "Want this on <em>your</em> stack?",
            "body": "Comment AUTO or DM AUTO and I will suggest 3 automations.",
        })
    data["carousel"]["slides"] = slides[:6]
    data["carousel"]["slides"][-1]["cta"] = True
    data["day"] = day_i
    data["date"] = date_obj.isoformat()
    data["image_archetype"] = img_arch
    data["carousel_archetype"] = car_arch
    return data


days_out = []
for i in range(DAYS):
    d = START + datetime.timedelta(days=i)
    img_a, car_a = ARCHETYPES[i % len(ARCHETYPES)]
    print(f"Generating day {i+1}/{DAYS} {d.isoformat()} ({img_a} + {car_a})...")
    last_err = None
    for attempt in range(3):
        try:
            day = gen_day(i + 1, d, img_a, car_a)
            topic = day.get("topic") or f"day-{i+1}"
            used.append(topic)
            days_out.append(day)
            print(f"  OK topic={topic}")
            break
        except Exception as e:
            last_err = e
            print(f"  retry {attempt+1}: {e}")
            time.sleep(2)
    else:
        traceback.print_exc()
        sys.exit(f"Failed day {i+1}: {last_err}")
    time.sleep(0.6)

date_compact = datetime.date.today().isoformat().replace("-", "")
out_path = f"us_personal_batch_{date_compact}.json"
payload = {
    "generated": datetime.date.today().isoformat(),
    "days": DAYS,
    "start": START.isoformat(),
    "end": (START + datetime.timedelta(days=DAYS - 1)).isoformat(),
    "audience": "US SaaS founders and ops leaders",
    "posts": days_out,
}
json.dump(payload, open(out_path, "w"), indent=2)
print(f"Wrote {out_path} ({DAYS} days, {DAYS*2} posts)")

log_path = "us-personal-run-log.json"
try:
    log = json.load(open(log_path)) if os.path.exists(log_path) else []
except Exception:
    log = []
log.append({
    "date": datetime.date.today().isoformat(),
    "mode": f"{DAYS}-day-image-carousel-us",
    "file": out_path,
    "topics": [p.get("topic") for p in days_out],
})
json.dump(log[-60:], open(log_path, "w"), indent=2)
print("Updated us-personal-run-log.json")
