#!/usr/bin/env python3
"""
Generate 10 days of OpenXcode company LinkedIn content:
  each day = 1 IMAGE post + 1 CAROUSEL post (6 slides).
Writes openxcode_batch_YYYYMMDD.json
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

DAYS = int(os.environ.get("OPENXCODE_DAYS", "10"))
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

profile = open("openxcode_profile.md").read() if os.path.exists("openxcode_profile.md") else ""
ai_news = []
if os.path.exists("ai_news_data.json"):
    ai_news = json.load(open("ai_news_data.json"))[:12]
news_ctx = "\n".join(
    f"- {n.get('title','')}: {str(n.get('description',''))[:180]}" for n in ai_news
)

used = []
if os.path.exists("openxcode-run-log.json"):
    try:
        for e in json.load(open("openxcode-run-log.json"))[-40:]:
            if e.get("topic"):
                used.append(e["topic"])
            if e.get("topics"):
                used.extend(e["topics"])
    except Exception:
        pass

ARCHETYPES = [
    ("NEWS_BUILD", "CASE_LISTICLE"),
    ("CASE_STUDY", "HOW_WE_BUILD"),
    ("MYTH_BUST", "SERVICE_STEPS"),
    ("BUILD_TIP", "MVP_PLAYBOOK"),
    ("SERVICE_SPOT", "CLIENT_JOURNEY"),
    ("PAIN_PRODUCT", "CHECKLIST"),
    ("DIRECT_OFFER", "WHY_OPENXCODE"),
    ("INDUSTRY_ANGLE", "MISTAKE_FIX"),
    ("AI_FEATURE", "SCOPE_GUIDE"),
    ("SOFT_CTA", "BEFORE_AFTER"),
]

SYSTEM = """You are the LinkedIn ghostwriter for OpenXcode, a software company (web apps, mobile, UI/UX, websites, AI features).
Company voice only: we / our / OpenXcode team. Never solo "I".
Attract project inquiries. No em-dashes. No FounderWing/@handles.
Banned: game-changer, cutting-edge, leverage, synergy, unlock, delve, disruptive, revolutionary.
CTA rotate: Comment BUILD / DM us / request a proposal at openxcode.com
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
                "HTTP-Referer": "https://openxcode.com",
                "X-Title": "OpenXcodeBatch",
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
    user = f"""COMPANY PROFILE:
{profile[:2800]}

NEWS (optional for NEWS_BUILD only):
{news_ctx or '(none)'}

BANNED topics: {json.dumps(used[-30:])}

Generate ONE day of OpenXcode LinkedIn content for {date_obj.isoformat()} ({date_obj.strftime('%A')}).
Image archetype: {img_arch}
Carousel archetype: {car_arch}

Return JSON:
{{
  "topic": "short unique topic phrase",
  "image": {{
    "caption": "120-200 word company-page caption ending with CTA",
    "badge": "OpenXcode",
    "title_main": "3-5 words",
    "title_span": "2-4 words",
    "subtitle": "max 120 chars",
    "takeaway_num": "hero stat or short label",
    "takeaway_text": "max 100 chars",
    "bars": [
      {{"label": "max 36 chars", "value": "display", "width_pct": "85%", "color": "#1E40AF"}},
      {{"label": "b", "value": "v", "width_pct": "70%", "color": "#2563EB"}},
      {{"label": "c", "value": "v", "width_pct": "55%", "color": "#3B82F6"}}
    ]
  }},
  "carousel": {{
    "caption": "90-160 word caption for the document carousel ending with CTA",
    "slides": [
      {{"kick": "HOOK", "headline": "6-8 word hook with optional <em>accent</em>", "body": "1-2 short sentences"}},
      {{"kick": "01", "headline": "...", "body": "..."}},
      {{"kick": "02", "headline": "...", "body": "..."}},
      {{"kick": "03", "headline": "...", "body": "..."}},
      {{"kick": "04", "headline": "...", "body": "..."}},
      {{"cta": true, "headline": "Ready to <em>build</em>?", "body": "Comment BUILD or DM us your idea."}}
    ]
  }}
}}

Rules:
- Exactly 6 carousel slides; last must be cta:true
- No em-dashes in any string
- Topics must be distinct from banned list
- Company voice throughout
"""
    raw = call_llm(user)
    data = parse_json(raw)
    if "image" not in data or "carousel" not in data:
        raise ValueError("missing image/carousel keys")
    slides = data["carousel"].get("slides") or []
    if len(slides) < 5:
        raise ValueError(f"need >=5 slides, got {len(slides)}")
    # normalize to 6
    while len(slides) < 6:
        slides.append({"cta": True, "headline": "Ready to <em>build</em>?", "body": "Comment BUILD or DM us."})
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
out_path = f"openxcode_batch_{date_compact}.json"
payload = {
    "generated": datetime.date.today().isoformat(),
    "days": DAYS,
    "start": START.isoformat(),
    "end": (START + datetime.timedelta(days=DAYS - 1)).isoformat(),
    "posts": days_out,
}
json.dump(payload, open(out_path, "w"), indent=2)
print(f"Wrote {out_path} ({DAYS} days, {DAYS*2} posts)")

log_path = "openxcode-run-log.json"
try:
    log = json.load(open(log_path)) if os.path.exists(log_path) else []
except Exception:
    log = []
log.append({
    "date": datetime.date.today().isoformat(),
    "mode": f"{DAYS}-day-image-carousel",
    "file": out_path,
    "topics": [p.get("topic") for p in days_out],
})
json.dump(log[-60:], open(log_path, "w"), indent=2)
print("Updated openxcode-run-log.json")
