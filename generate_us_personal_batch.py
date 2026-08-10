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
    # Default: start today (same calendar day as generation)
    START = datetime.date.today()

PORTFOLIO_URL = "https://hitesh-dodiya.netlify.app/"
LINKEDIN_URL = "https://www.linkedin.com/in/hiteshdodiyaa"
FOOTER_LINKS = (
    f"Portfolio: {PORTFOLIO_URL}\n"
    f"LinkedIn: {LINKEDIN_URL}"
)

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

# Forced unique angle per day so the batch does not collapse into one sales-prep story
DAY_ANGLES = [
    "News hook: browser/legacy portal automation OR new AI agent news → one custom ops build",
    "Case study: HubSpot + Calendly sales-prep brief with hours saved and close-rate lift",
    "Ops pain: morning handoff chaos before 9 AM ET standup (Slack + CRM + tickets)",
    "Stack tip: one HubSpot/Salesforce + Slack tip that takes under a day to ship",
    "Workflow: Stripe failed-payment → AI draft → AE Slack alert",
    "Myth bust: why Zapier/Make hit a wall for Series A US SaaS (API limits, audit trail)",
    "Offer: 2 fixed-price build slots + free 15-min audit this month",
    "SDR angle: Calendly book → Apollo enrich → Slack dossier 10 min before demo",
    "Support angle: Intercom + Notion triage agent cutting first-response time",
    "Soft CTA: founders DM their CRM + chat + project tool for 3 automation ideas",
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

SYSTEM = f"""You are the LinkedIn ghostwriter for Hitesh Dodiya, a full-stack AI developer selling custom automations to US SaaS companies.
Voice: first person (I / I've / my). Practical. Name real tools.
AUDIENCE: US founders and ops leaders (East Coast + West Coast). HubSpot, Salesforce, Slack, Stripe, DocuSign, Intercom, Notion, Calendly.
US FRAMING REQUIRED: "US SaaS", "Series A", "before your 9 AM ET standup", dollar outcomes, SOC 2 / audit trail when relevant.

CAPTION FORMAT (critical for impressions — never one wall of text):
1) Hook line (1 short sentence, scroll-stopping, specific number or pain)
2) Blank line
3) 1-2 short paragraphs (2-3 sentences max each) with concrete story/stack
4) Blank line
5) 3-5 bullet lines starting with "- " (outcomes, steps, or stack specifics)
6) Blank line
7) CTA line (Comment AUTO / DM AUTO / DM your stack)
8) Blank line
9) Always end with both links exactly:
{FOOTER_LINKS}

IMPRESSION RULES: lead with a specific US pain or number; name tools; promise a stealable takeaway; avoid vague advice.
No em-dashes. No @handles. No company-page "we/our" voice.
Banned: game-changer, cutting-edge, leverage, synergy, unlock, delve, disruptive, revolutionary.
Return ONLY valid JSON."""


def call_llm(user, max_tokens=6000):
    openrouter_model = os.environ.get("OPENROUTER_MODEL", "google/gemini-2.5-flash")
    gemini_models = [
        m.strip()
        for m in os.environ.get(
            "GEMINI_MODELS",
            os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
            + ",gemini-flash-latest,gemini-3.5-flash,gemini-2.0-flash",
        ).split(",")
        if m.strip()
    ]
    # de-dupe preserve order
    seen = set()
    gemini_models = [m for m in gemini_models if not (m in seen or seen.add(m))]
    errors = []
    if gemini_key:
        for gemini_model in gemini_models:
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
                    text = resp["candidates"][0]["content"]["parts"][0]["text"]
                    print(f"  LLM ok via gemini/{gemini_model}")
                    return text
            except Exception as e:
                errors.append(f"gemini/{gemini_model}:{e}")
                print(f"  Gemini {gemini_model} failed ({e})")
                time.sleep(1.5)
    if openrouter_key:
        url = "https://openrouter.ai/api/v1/chat/completions"
        for model in [openrouter_model, "google/gemini-2.5-flash", "openai/gpt-4o-mini"]:
            try:
                payload = {
                    "model": model,
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
                    print(f"  LLM ok via openrouter/{model}")
                    return resp["choices"][0]["message"]["content"]
            except Exception as e:
                errors.append(f"openrouter/{model}:{e}")
                print(f"  OpenRouter {model} failed ({e})")
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


def ensure_links(caption: str) -> str:
    caption = (caption or "").strip().replace("—", "-").replace("–", "-")
    # Normalize whitespace but keep intentional blank lines
    caption = re.sub(r"[ \t]+\n", "\n", caption)
    caption = re.sub(r"\n{3,}", "\n\n", caption)
    has_portfolio = "hitesh-dodiya.netlify.app" in caption.lower()
    has_linkedin = "linkedin.com/in/hiteshdodiyaa" in caption.lower()
    if has_portfolio and has_linkedin:
        return caption
    parts = [caption] if caption else []
    if not has_portfolio or not has_linkedin:
        parts.append(FOOTER_LINKS)
    return "\n\n".join(parts).strip()


def densify_caption(caption: str) -> str:
    """If model returned a single paragraph, lightly split into readable blocks."""
    caption = ensure_links(caption)
    if "\n-" in caption or "\n- " in caption or caption.count("\n\n") >= 2:
        return caption
    # Keep as-is if already multi-block; ensure_links already applied
    return caption


def gen_day(day_i, date_obj, img_arch, car_arch):
    angle = DAY_ANGLES[(day_i - 1) % len(DAY_ANGLES)]
    user = f"""BUILDER PROFILE:
{profile[:3200]}

NEWS (use only if archetype is US_NEWS_HOOK):
{news_ctx or '(none)'}

BANNED topics (do NOT reuse or lightly rephrase these): {json.dumps(used[-40:])}

REQUIRED DAY ANGLE (must follow — topic + captions + visuals must match this, not sales-prep unless the angle is sales):
{angle}

Generate ONE day of PERSONAL LinkedIn content for {date_obj.isoformat()} ({date_obj.strftime('%A')}).
Image archetype: {img_arch} -> {ARCHETYPE_BRIEFS.get(img_arch, '')}
Carousel archetype: {car_arch} -> {ARCHETYPE_BRIEFS.get(car_arch, '')}

CRITICAL UNIQUENESS: topic must be clearly different from banned topics. Do not default to SDR research / Calendly prep unless the day angle is explicitly SDR or case-study sales prep.

Return JSON:
{{
  "topic": "short unique US-automation topic phrase (specific, not generic)",
  "image": {{
    "caption": "STRUCTURED caption using newlines: hook\\n\\npara\\n\\n- bullet\\n- bullet\\n- bullet\\n\\nCTA\\n\\nPortfolio: https://hitesh-dodiya.netlify.app/\\nLinkedIn: https://www.linkedin.com/in/hiteshdodiyaa",
    "badge": "AI Automation",
    "title_main": "3-5 punchy words",
    "title_span": "2-4 accent words",
    "subtitle": "specific 1-line promise with tool names (max 140 chars)",
    "takeaway_num": "hero stat e.g. 12 hrs or +14%",
    "takeaway_text": "concrete outcome (max 90 chars)",
    "bars": [
      {{"label": "specific metric label max 40 chars", "value": "display", "width_pct": "92%", "color": "#5E6AD2"}},
      {{"label": "b", "value": "v", "width_pct": "78%", "color": "#2563EB"}},
      {{"label": "c", "value": "v", "width_pct": "65%", "color": "#059669"}},
      {{"label": "d", "value": "v", "width_pct": "52%", "color": "#D9785B"}}
    ],
    "bullets": [
      "concrete stack/step line 1 (max 70 chars)",
      "concrete stack/step line 2",
      "concrete stack/step line 3",
      "concrete stack/step line 4"
    ]
  }},
  "carousel": {{
    "caption": "STRUCTURED caption same format as image (hook, paras, bullets, CTA, both URLs)",
    "slides": [
      {{"kick": "HOOK", "headline": "6-10 word scroll-stop with optional <em>accent</em>", "body": "2 short sentences naming US SaaS pain + promise", "bullets": ["takeaway 1", "takeaway 2", "takeaway 3"]}},
      {{"kick": "01", "headline": "...", "body": "2-3 sentences of specific how-to with tools", "bullets": ["step detail", "tool/API", "result"]}},
      {{"kick": "02", "headline": "...", "body": "...", "bullets": ["a", "b", "c"]}},
      {{"kick": "03", "headline": "...", "body": "...", "bullets": ["a", "b", "c"]}},
      {{"kick": "04", "headline": "...", "body": "...", "bullets": ["a", "b", "c"]}},
      {{"cta": true, "headline": "Want this on <em>your</em> stack?", "body": "Comment AUTO or DM AUTO. I will suggest 3 automations for your CRM + chat + project tools.", "bullets": ["Free 15-min audit", "Fixed-price builds", "Portfolio: hitesh-dodiya.netlify.app"]}}
    ]
  }}
}}

Rules:
- Exactly 6 carousel slides; last must be cta:true
- Captions MUST use real newline characters (\\\\n) for paragraphs and "- " bullets — never a single dense paragraph
- Every caption MUST include both portfolio and LinkedIn URLs at the end
- Image MUST have exactly 4 bars with specific US SaaS automation outcomes (hours, $, %, minutes) — fill the visual, no vague labels
- Image MUST have 4 bullets that are stack/step specific (not fluff)
- Every carousel slide (except ok to keep CTA dense) MUST include body 2-3 sentences AND 3 bullets so slides are content-rich (no empty whitespace feel)
- Headlines must be specific and catchy (numbers, tools, or sharp contrast)
- No em-dashes
- US framing in both captions
- First-person voice throughout
- Make posts targeted for impressions: specificity > generality
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
            "bullets": [
                "Free 15-min audit",
                "Fixed-price builds",
                f"Portfolio: {PORTFOLIO_URL}",
            ],
        })
    data["carousel"]["slides"] = slides[:6]
    data["carousel"]["slides"][-1]["cta"] = True

    img = data["image"]
    img["caption"] = densify_caption(img.get("caption", ""))
    bars = img.get("bars") or []
    while len(bars) < 4:
        bars.append({
            "label": f"Ops outcome {len(bars)+1}",
            "value": "n/a",
            "width_pct": f"{80 - len(bars)*12}%",
            "color": ["#5E6AD2", "#2563EB", "#059669", "#D9785B"][len(bars) % 4],
        })
    img["bars"] = bars[:4]
    bullets = img.get("bullets") or []
    while len(bullets) < 4:
        bullets.append("Wire CRM + Slack + enrichment into one flow")
    img["bullets"] = [str(b)[:80] for b in bullets[:4]]

    car = data["carousel"]
    car["caption"] = densify_caption(car.get("caption", ""))
    for s in car["slides"]:
        sb = s.get("bullets") or []
        if len(sb) < 3 and not s.get("cta"):
            # pad from body phrases if model under-delivered
            while len(sb) < 3:
                sb.append("Name the trigger, tools, and owner")
        s["bullets"] = [str(b)[:90] for b in sb[:4]]

    data["day"] = day_i
    data["date"] = date_obj.isoformat()
    data["image_archetype"] = img_arch
    data["carousel_archetype"] = car_arch
    return data


days_out = []
date_compact = datetime.date.today().isoformat().replace("-", "")
out_path = f"us_personal_batch_{date_compact}.json"

def save_partial():
    payload = {
        "generated": datetime.date.today().isoformat(),
        "days": DAYS,
        "start": START.isoformat(),
        "end": (START + datetime.timedelta(days=DAYS - 1)).isoformat(),
        "audience": "US SaaS founders and ops leaders",
        "posts": days_out,
        "partial": len(days_out) < DAYS,
    }
    json.dump(payload, open(out_path, "w"), indent=2)

for i in range(DAYS):
    d = START + datetime.timedelta(days=i)
    img_a, car_a = ARCHETYPES[i % len(ARCHETYPES)]
    print(f"Generating day {i+1}/{DAYS} {d.isoformat()} ({img_a} + {car_a})...")
    last_err = None
    for attempt in range(5):
        try:
            day = gen_day(i + 1, d, img_a, car_a)
            topic = day.get("topic") or f"day-{i+1}"
            used.append(topic)
            days_out.append(day)
            save_partial()
            print(f"  OK topic={topic} (saved {out_path})")
            break
        except Exception as e:
            last_err = e
            print(f"  retry {attempt+1}: {e}")
            time.sleep(3 + attempt * 2)
    else:
        traceback.print_exc()
        sys.exit(f"Failed day {i+1}: {last_err}")
    time.sleep(1.2)

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
