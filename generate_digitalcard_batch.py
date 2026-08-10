#!/usr/bin/env python3
"""
Generate 10 days of Digital Card Creator company LinkedIn content:
  each day = 2 IMAGE posts + 2 CAROUSEL posts (4 total).
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
    START = datetime.date.today()

SITE_URL = "https://my.digitalcardcreator.com/"
PLAY_URL = "https://play.google.com/store/apps/details?id=com.digital_card_creator_app"
FOOTER = f"Create free: {SITE_URL}\nAndroid app: {PLAY_URL}"

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

# 4 posts/day: image_am, carousel_am, image_pm, carousel_pm
DAY_SLOTS = [
    ("PAPER_CARD_PAIN", "QR_SHARE_CHECKLIST", "NETWORKING_MOMENT", "SETUP_STEPS"),
    ("SALES_FOLLOWUP", "ANALYTICS_STACK", "AUDIENCE_SPOT", "BEFORE_AFTER"),
    ("WHATSAPP_CONNECT", "CLIENT_JOURNEY", "MYTH_BUST", "FEATURE_LISTICLE"),
    ("TEAM_BRANDING", "MISTAKE_FIX", "EVENT_NETWORKING", "UPDATE_ANYTIME"),
    ("COST_OF_PRINT", "WHY_DCC", "SOFT_CTA", "LAUNCH_CHECKLIST"),
    ("PAPER_CARD_PAIN", "SETUP_STEPS", "SALES_FOLLOWUP", "QR_SHARE_CHECKLIST"),
    ("AUDIENCE_SPOT", "BEFORE_AFTER", "WHATSAPP_CONNECT", "ANALYTICS_STACK"),
    ("EVENT_NETWORKING", "CLIENT_JOURNEY", "TEAM_BRANDING", "FEATURE_LISTICLE"),
    ("MYTH_BUST", "UPDATE_ANYTIME", "COST_OF_PRINT", "MISTAKE_FIX"),
    ("SOFT_CTA", "LAUNCH_CHECKLIST", "NETWORKING_MOMENT", "WHY_DCC"),
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
    "SOFT_CTA": "Soft offer: create free, under 5 minutes, app + web. Invite Comment CARD. Include Play Store link.",
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

ANALYTICS_HINTS = """
ANALYTICS LESSONS (from recent Digital Card Creator company posts):
- Highest impressions: question hooks + named audience pain (consultants/lawyers follow-up, student status changes, sales lost paper leads, freelancer meetup friction).
- Highest clicks: checklist carousels, update-anytime stories, recruiter QR checklists, clinic recipient journeys, real-estate analytics.
- Highest engagement rate: cost-of-print team angles, share-ready checklists, analytics after open house, patient walk-out journey.
- ZERO comments across the last batch — make Comment CARD impossible to miss; ask a reply-worthy question in the hook.
- Walls of single-paragraph text underperformed vs structured hooks; always use hook + short paragraphs + bullets.
- Prefer concrete moments (trade show, clinic desk, open house, campus fair, co-working chat) over generic networking talk.
- Prioritize audiences that pulled: lawyers/consultants, students, sales, freelancers, real estate, clinics, recruiters/agencies.
"""

SYSTEM = f"""You are the LinkedIn ghostwriter for Digital Card Creator, a mobile app to create digital visiting cards.
Company voice only: we / our / Digital Card Creator team. Never solo "I".
Audience: professionals who network in person and online (sales, freelancers, realtors, clinics, consultants, students, creators).
STRICT NICHE: only digital visiting cards, QR sharing, save to contacts, WhatsApp Connect, card analytics, templates, update-anytime, paper-card replacement.
Do NOT write about WordPress plugins, appointment booking, custom software development, or OpenXcode services.
Goal: free card creates and app downloads. Talk about scans, contacts saved, WhatsApp follow-ups, not vanity likes.

CAPTION FORMAT (never one wall of text):
1) Hook line (question or sharp audience pain — this drives impressions)
2) Blank line
3) 1-2 short paragraphs naming the audience + concrete networking moment
4) Blank line
5) 3-5 bullets starting with "- " (product outcomes: QR, save-to-contacts, WhatsApp, analytics, update-anytime)
6) Blank line
7) CTA that invites a reply: Comment CARD / DM us your role
8) Blank line
9) Always end with BOTH URLs:
{FOOTER}

No em-dashes. Never name a competitor app; contrast with "paper cards" or "static PDF cards".
Banned: game-changer, cutting-edge, leverage, synergy, unlock, delve, disruptive, revolutionary.
Return ONLY valid JSON."""


def call_llm(user, max_tokens=8000):
    openrouter_model = os.environ.get("OPENROUTER_MODEL", "google/gemini-2.5-flash")
    gemini_models = [
        m.strip()
        for m in os.environ.get(
            "GEMINI_MODELS",
            os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
            + ",gemini-flash-latest,gemini-3.5-flash",
        ).split(",")
        if m.strip()
    ]
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
                time.sleep(1.2)
    if openrouter_key:
        for model in [openrouter_model, "google/gemini-2.5-flash"]:
            try:
                url = "https://openrouter.ai/api/v1/chat/completions"
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
                        "HTTP-Referer": "https://my.digitalcardcreator.com",
                        "X-Title": "DigitalCardBatch",
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


def ensure_urls(caption: str) -> str:
    caption = (caption or "").strip().replace("—", "-").replace("–", "-")
    caption = re.sub(r"[ \t]+\n", "\n", caption)
    caption = re.sub(r"\n{3,}", "\n\n", caption)
    low = caption.lower()
    needs_site = "digitalcardcreator.com" not in low
    needs_play = "play.google.com/store/apps/details?id=com.digital_card_creator_app" not in low
    if needs_site or needs_play:
        caption = (caption + "\n\n" + FOOTER).strip()
    return caption


def densify_image(spec):
    bars = spec.get("bars") or []
    defaults = [
        ("QR scans after event", "Tracked", "90%", "#536EFD"),
        ("Contacts saved in 1 tap", "Instant", "78%", "#EF5197"),
        ("WhatsApp taps", "1-click", "66%", "#A855F7"),
        ("Reprint cost avoided", "₹0", "54%", "#FFE866"),
    ]
    while len(bars) < 4:
        label, value, width, color = defaults[len(bars)]
        bars.append({"label": label, "value": value, "width_pct": width, "color": color})
    for bi, bar in enumerate(bars[:4]):
        bar.setdefault("color", defaults[bi][3])
        bar.setdefault("width_pct", defaults[bi][2])
        if not str(bar.get("width_pct", "")).endswith("%"):
            bar["width_pct"] = f"{bar['width_pct']}%"
    spec["bars"] = bars[:4]
    bullets = spec.get("bullets") or []
    while len(bullets) < 4:
        bullets.append([
            "Smart QR — recipient needs no app",
            "One-tap save to phone contacts",
            "WhatsApp Connect built in",
            "Live views, scans, and click analytics",
        ][len(bullets)])
    spec["bullets"] = [str(b)[:80] for b in bullets[:4]]
    spec["caption"] = ensure_urls(spec.get("caption", ""))
    return spec


def densify_carousel(car):
    car["caption"] = ensure_urls(car.get("caption", ""))
    slides = car.get("slides") or []
    while len(slides) < 6:
        slides.append({
            "cta": True,
            "headline": "Ready for your <em>digital card</em>?",
            "body": "Comment CARD and we will send the free app link plus a 5-minute setup checklist.",
            "bullets": [
                "Free to create on web or Android",
                SITE_URL,
                PLAY_URL,
            ],
        })
    slides = slides[:6]
    slides[-1]["cta"] = True
    for s in slides:
        sb = s.get("bullets") or []
        while len(sb) < 3:
            sb.append("Concrete digital-card outcome for this audience")
        s["bullets"] = [str(b)[:90] for b in sb[:4]]
        if not s.get("body"):
            s["body"] = "A specific networking outcome for this audience with Digital Card Creator."
    car["slides"] = slides
    return car


def gen_day(day_i, date_obj, slots, audience):
    img_a, car_a, img_b, car_b = slots
    user = f"""PRODUCT PROFILE:
{profile[:4500]}

{ANALYTICS_HINTS}

Site URL (required in every caption): {SITE_URL}
Play Store URL (required in every caption): {PLAY_URL}

BANNED topics (already posted): {json.dumps(used[-40:])}

Generate ONE day of Digital Card Creator LinkedIn content for {date_obj.isoformat()} ({date_obj.strftime('%A')}).
Primary audience for this day: {audience}

Four posts required:
1) image_am archetype {img_a} -> {ARCHETYPE_BRIEFS.get(img_a, '')}
2) carousel_am archetype {car_a} -> {ARCHETYPE_BRIEFS.get(car_a, '')}
3) image_pm archetype {img_b} -> {ARCHETYPE_BRIEFS.get(img_b, '')}
4) carousel_pm archetype {car_b} -> {ARCHETYPE_BRIEFS.get(car_b, '')}

Make AM and PM distinct angles (do not repeat the same hook). Prefer question hooks for at least 2 of 4 captions.

Return JSON:
{{
  "topic": "short unique day theme about digital cards / QR / networking",
  "audience": "{audience}",
  "image_am": {{
    "caption": "structured caption with newlines + bullets + both URLs",
    "badge": "Digital Card Creator",
    "title_main": "3-5 punchy words",
    "title_span": "2-4 accent words",
    "subtitle": "specific promise with audience + feature (max 140 chars)",
    "takeaway_num": "hero stat or short label",
    "takeaway_text": "outcome max 90 chars",
    "bars": [
      {{"label": "specific outcome", "value": "v", "width_pct": "90%", "color": "#536EFD"}},
      {{"label": "b", "value": "v", "width_pct": "78%", "color": "#EF5197"}},
      {{"label": "c", "value": "v", "width_pct": "66%", "color": "#A855F7"}},
      {{"label": "d", "value": "v", "width_pct": "54%", "color": "#FFE866"}}
    ],
    "bullets": ["feature/outcome 1", "2", "3", "4"]
  }},
  "carousel_am": {{
    "caption": "structured caption + both URLs",
    "slides": [
      {{"kick": "HOOK", "headline": "hook with optional <em>accent</em>", "body": "2 concrete sentences", "bullets": ["a","b","c"]}},
      {{"kick": "01", "headline": "...", "body": "...", "bullets": ["a","b","c"]}},
      {{"kick": "02", "headline": "...", "body": "...", "bullets": ["a","b","c"]}},
      {{"kick": "03", "headline": "...", "body": "...", "bullets": ["a","b","c"]}},
      {{"kick": "04", "headline": "...", "body": "...", "bullets": ["a","b","c"]}},
      {{"cta": true, "headline": "Ready for your <em>digital card</em>?", "body": "Comment CARD for free app link + setup checklist.", "bullets": ["Free to create", "{SITE_URL}", "{PLAY_URL}"]}}
    ]
  }},
  "image_pm": {{ "...same shape as image_am..." }},
  "carousel_pm": {{ "...same shape as carousel_am..." }}
}}

Rules:
- Exactly 6 slides per carousel; last cta:true
- Captions use real newlines and "- " bullets (never a single paragraph wall)
- Every caption includes BOTH {SITE_URL} and {PLAY_URL}
- Each image has 4 bars + 4 bullets (dense, catchy, fill the 1080 square — no empty feel)
- Each carousel slide has body + 3 bullets (content-dense; avoid sparse slides)
- Bars show digital-card outcomes (QR scans, contacts saved, WhatsApp taps, reprint cost avoided, setup minutes). Never fake user counts beyond the known 5,000+ professionals
- Name the audience and a concrete networking moment in every caption
- Topics distinct from banned list
- Company voice throughout
- Stay strictly in the digital visiting card niche
"""
    raw = call_llm(user)
    data = parse_json(raw)
    for key in ("image_am", "carousel_am", "image_pm", "carousel_pm"):
        if key not in data:
            raise ValueError(f"missing {key}")
    data["image_am"] = densify_image(data["image_am"])
    data["image_pm"] = densify_image(data["image_pm"])
    data["carousel_am"] = densify_carousel(data["carousel_am"])
    data["carousel_pm"] = densify_carousel(data["carousel_pm"])
    # legacy aliases for older builders
    data["image"] = data["image_am"]
    data["carousel"] = data["carousel_am"]
    data["day"] = day_i
    data["date"] = date_obj.isoformat()
    data["audience"] = data.get("audience") or audience
    data["image_archetype"] = img_a
    data["carousel_archetype"] = car_a
    data["image_pm_archetype"] = img_b
    data["carousel_pm_archetype"] = car_b
    data["slots"] = {
        "image_am": img_a,
        "carousel_am": car_a,
        "image_pm": img_b,
        "carousel_pm": car_b,
    }
    return data


offset = 0
for aud in reversed(used_audiences[-len(AUDIENCES):]):
    if aud in AUDIENCES:
        offset = (AUDIENCES.index(aud) + 1) % len(AUDIENCES)
        break

days_out = []
date_compact = datetime.date.today().isoformat().replace("-", "")
out_path = f"digitalcard_batch_{date_compact}.json"


def save_partial():
    payload = {
        "generated": datetime.date.today().isoformat(),
        "days": DAYS,
        "postsPerDay": 4,
        "start": START.isoformat(),
        "end": (START + datetime.timedelta(days=DAYS - 1)).isoformat(),
        "posts": days_out,
        "partial": len(days_out) < DAYS,
    }
    json.dump(payload, open(out_path, "w"), indent=2)


for i in range(DAYS):
    d = START + datetime.timedelta(days=i)
    slots = DAY_SLOTS[i % len(DAY_SLOTS)]
    audience = AUDIENCES[(offset + i) % len(AUDIENCES)]
    print(f"Generating day {i+1}/{DAYS} {d.isoformat()} {slots} [{audience}]...")
    last_err = None
    for attempt in range(5):
        try:
            day = gen_day(i + 1, d, slots, audience)
            topic = day.get("topic") or f"day-{i+1}"
            used.append(topic)
            used.append(f"{topic}-pm")
            days_out.append(day)
            save_partial()
            print(f"  OK topic={topic}")
            break
        except Exception as e:
            last_err = e
            print(f"  retry {attempt+1}: {e}")
            time.sleep(3 + attempt * 2)
    else:
        traceback.print_exc()
        sys.exit(f"Failed day {i+1}: {last_err}")
    time.sleep(1.0)

payload = {
    "generated": datetime.date.today().isoformat(),
    "days": DAYS,
    "postsPerDay": 4,
    "start": START.isoformat(),
    "end": (START + datetime.timedelta(days=DAYS - 1)).isoformat(),
    "posts": days_out,
}
json.dump(payload, open(out_path, "w"), indent=2)
print(f"Wrote {out_path} ({DAYS} days, {DAYS*4} posts)")

log_path = "digitalcard-run-log.json"
try:
    log = json.load(open(log_path)) if os.path.exists(log_path) else []
except Exception:
    log = []
log.append({
    "date": datetime.date.today().isoformat(),
    "mode": f"{DAYS}-day-4posts-image-carousel",
    "file": out_path,
    "topics": [p.get("topic") for p in days_out],
    "audiences": [p.get("audience") for p in days_out],
})
json.dump(log[-60:], open(log_path, "w"), indent=2)
print("Updated digitalcard-run-log.json")
