#!/usr/bin/env python3
"""
Generate 10 days of Digital Card Creator company LinkedIn content:
  each day = 1 IMAGE post + 1 CAROUSEL post (6 slides).
Writes digitalcard_batch_YYYYMMDD.json

Niche-locked: digital visiting cards, QR share, WhatsApp Connect, analytics.
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

DAYS = int(os.environ.get("DIGITALCARD_DAYS", "10"))
if os.environ.get("DIGITALCARD_START"):
    START = datetime.date.fromisoformat(os.environ["DIGITALCARD_START"])
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

profile = open("digitalcard_profile.md").read() if os.path.exists("digitalcard_profile.md") else ""

used = []
used_audiences = []
if os.path.exists("digitalcard-run-log.json"):
    try:
        for e in json.load(open("digitalcard-run-log.json"))[-40:]:
            if e.get("topic"):
                used.append(e["topic"])
            if e.get("topics"):
                used.extend(e["topics"])
            if e.get("audiences"):
                used_audiences.extend(e["audiences"])
    except Exception:
        pass

ARCHETYPES = [
    ("PAPER_CARD_PAIN", "QR_SHARE_CHECKLIST"),
    ("NETWORKING_MOMENT", "SETUP_STEPS"),
    ("SALES_FOLLOWUP", "ANALYTICS_STACK"),
    ("AUDIENCE_SPOT", "BEFORE_AFTER"),
    ("WHATSAPP_CONNECT", "CLIENT_JOURNEY"),
    ("MYTH_BUST", "FEATURE_LISTICLE"),
    ("TEAM_BRANDING", "MISTAKE_FIX"),
    ("EVENT_NETWORKING", "UPDATE_ANYTIME"),
    ("COST_OF_PRINT", "WHY_DCC"),
    ("SOFT_CTA", "LAUNCH_CHECKLIST"),
]

AUDIENCES = [
    "sales professionals",
    "freelancers",
    "real estate agents",
    "business owners",
    "doctors and clinics",
    "lawyers and consultants",
    "event planners",
    "students",
    "influencers and creators",
    "agency and team leads",
]

ARCHETYPE_BRIEFS = {
    "PAPER_CARD_PAIN": "Open with a paper visiting card pain for this audience (lost cards, outdated phone, typing numbers). Show how a digital card with QR and save-to-contacts fixes it.",
    "NETWORKING_MOMENT": "Describe a real networking moment for this audience (meetup, showing, clinic desk, conference). Show the QR share in that moment.",
    "SALES_FOLLOWUP": "Focus on converting a scan into a WhatsApp follow-up and tracked lead for this audience.",
    "AUDIENCE_SPOT": "Spotlight how this exact audience should set up their Digital Card Creator card: template, logo, WhatsApp, social links.",
    "WHATSAPP_CONNECT": "Focus on WhatsApp Connect: one tap from the card to chat. No typing numbers.",
    "MYTH_BUST": "Bust a myth about digital cards (need design skills, recipient needs the app, only for tech people, less professional than paper).",
    "TEAM_BRANDING": "Speak to consistent branded cards across a team or agency so every intro looks professional.",
    "EVENT_NETWORKING": "Focus on events, expos, or campus networking where QR beats stacking paper cards.",
    "COST_OF_PRINT": "Contrast reprint costs and waste of paper cards with one digital card that updates forever.",
    "SOFT_CTA": "Soft offer: create free, under 5 minutes, app + web. Invite Comment CARD.",
    "QR_SHARE_CHECKLIST": "Checklist for a share-ready digital card: photo, role, WhatsApp, QR, social links, save-to-contacts.",
    "SETUP_STEPS": "4 steps: download app, create profile, build card with template, share QR and track.",
    "ANALYTICS_STACK": "Explain card views, QR scans, WhatsApp clicks, phone clicks and why they matter after networking.",
    "BEFORE_AFTER": "Before paper chaos vs after digital card: one QR, contacts saved, WhatsApp open, card always current.",
    "CLIENT_JOURNEY": "Recipient journey: scan QR, see card, save contact, tap WhatsApp. No app required for them.",
    "FEATURE_LISTICLE": "Short list of must-have digital card features mapped to this audience.",
    "MISTAKE_FIX": "Common digital networking mistakes for this audience and the fix with DCC.",
    "UPDATE_ANYTIME": "Changed phone or designation: update once, every shared link and QR stays current. No reprint.",
    "WHY_DCC": "Why Digital Card Creator: free start, premium templates, QR, WhatsApp, analytics, 5,000+ pros, 4.8 rating.",
    "LAUNCH_CHECKLIST": "Pre-share checklist before the next meetup: template, WhatsApp button, socials, test QR scan, analytics on.",
}

SYSTEM = """You are the LinkedIn ghostwriter for Digital Card Creator, a mobile app to create digital visiting cards.
Company voice only: we / our / Digital Card Creator team. Never solo "I".
Audience: professionals who network in person and online (sales, freelancers, realtors, clinics, consultants, students, creators).
STRICT NICHE: only digital visiting cards, QR sharing, save to contacts, WhatsApp Connect, card analytics, templates, update-anytime, paper-card replacement.
Do NOT write about WordPress plugins, appointment booking, custom software development, or OpenXcode services.
Goal: free card creates and app downloads. Talk about scans, contacts saved, WhatsApp follow-ups, not vanity likes.
No em-dashes. Never name a competitor app; contrast with "paper cards" or "static PDF cards".
Banned: game-changer, cutting-edge, leverage, synergy, unlock, delve, disruptive, revolutionary.
CTA rotate: Comment CARD / DM us your role / create free at my.digitalcardcreator.com
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
                "HTTP-Referer": "https://my.digitalcardcreator.com",
                "X-Title": "DigitalCardBatch",
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


def gen_day(day_i, date_obj, img_arch, car_arch, audience):
    user = f"""PRODUCT PROFILE:
{profile[:3200]}

BANNED topics (already posted): {json.dumps(used[-30:])}

Generate ONE day of Digital Card Creator LinkedIn content for {date_obj.isoformat()} ({date_obj.strftime('%A')}).
Primary audience for this day: {audience}
Image archetype: {img_arch} -> {ARCHETYPE_BRIEFS.get(img_arch, '')}
Carousel archetype: {car_arch} -> {ARCHETYPE_BRIEFS.get(car_arch, '')}

Return JSON:
{{
  "topic": "short unique topic phrase about digital cards / QR / networking",
  "audience": "{audience}",
  "image": {{
    "caption": "120-200 word company-page caption ending with CTA",
    "badge": "Digital Card Creator",
    "title_main": "3-5 words",
    "title_span": "2-4 words",
    "subtitle": "max 120 chars",
    "takeaway_num": "hero stat or short label",
    "takeaway_text": "max 100 chars",
    "bars": [
      {{"label": "max 36 chars", "value": "display", "width_pct": "85%", "color": "#536EFD"}},
      {{"label": "b", "value": "v", "width_pct": "70%", "color": "#EF5197"}},
      {{"label": "c", "value": "v", "width_pct": "55%", "color": "#A855F7"}}
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
      {{"cta": true, "headline": "Ready for your <em>digital card</em>?", "body": "Comment CARD and we will send the free app link plus a setup checklist."}}
    ]
  }}
}}

Rules:
- Exactly 6 carousel slides; last must be cta:true
- No em-dashes in any string
- Topics must be distinct from banned list
- Name the audience and a concrete networking moment in both captions
- Bars must show digital-card outcomes (QR scans, contacts saved, WhatsApp taps, reprint cost avoided, setup minutes). Never fake user counts beyond the known 5,000+ professionals
- Stay strictly in the digital visiting card niche
- Company voice throughout
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
            "headline": "Ready for your <em>digital card</em>?",
            "body": "Comment CARD and we will send the free app link plus a setup checklist.",
        })
    data["carousel"]["slides"] = slides[:6]
    data["carousel"]["slides"][-1]["cta"] = True
    data["day"] = day_i
    data["date"] = date_obj.isoformat()
    data["audience"] = data.get("audience") or audience
    data["image_archetype"] = img_arch
    data["carousel_archetype"] = car_arch
    return data


offset = 0
for aud in reversed(used_audiences[-len(AUDIENCES):]):
    if aud in AUDIENCES:
        offset = (AUDIENCES.index(aud) + 1) % len(AUDIENCES)
        break

days_out = []
for i in range(DAYS):
    d = START + datetime.timedelta(days=i)
    img_a, car_a = ARCHETYPES[i % len(ARCHETYPES)]
    audience = AUDIENCES[(offset + i) % len(AUDIENCES)]
    print(f"Generating day {i+1}/{DAYS} {d.isoformat()} ({img_a} + {car_a}) [{audience}]...")
    last_err = None
    for attempt in range(3):
        try:
            day = gen_day(i + 1, d, img_a, car_a, audience)
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
out_path = f"digitalcard_batch_{date_compact}.json"
payload = {
    "generated": datetime.date.today().isoformat(),
    "days": DAYS,
    "start": START.isoformat(),
    "end": (START + datetime.timedelta(days=DAYS - 1)).isoformat(),
    "posts": days_out,
}
json.dump(payload, open(out_path, "w"), indent=2)
print(f"Wrote {out_path} ({DAYS} days, {DAYS*2} posts)")

log_path = "digitalcard-run-log.json"
try:
    log = json.load(open(log_path)) if os.path.exists(log_path) else []
except Exception:
    log = []
log.append({
    "date": datetime.date.today().isoformat(),
    "mode": f"{DAYS}-day-image-carousel",
    "file": out_path,
    "topics": [p.get("topic") for p in days_out],
    "audiences": [p.get("audience") for p in days_out],
})
json.dump(log[-60:], open(log_path, "w"), indent=2)
print("Updated digitalcard-run-log.json")
