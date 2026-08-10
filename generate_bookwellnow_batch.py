#!/usr/bin/env python3
"""
Generate 10 days of BookWellNow company LinkedIn content:
  each day = 2 IMAGE posts + 2 CAROUSEL posts (4 total).
Writes bookwellnow_batch_YYYYMMDD.json
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

DAYS = int(os.environ.get("BOOKWELLNOW_DAYS", "10"))
if os.environ.get("BOOKWELLNOW_START"):
    START = datetime.date.fromisoformat(os.environ["BOOKWELLNOW_START"])
else:
    START = datetime.date.today()

SITE_URL = "https://bookwellnow.com/"
DOCS_URL = "https://bookwellnow.com/docs/getting-started/installing/"
FOOTER = f"Start free: {SITE_URL}"

gemini_key = openrouter_key = None
with open(".env") as f:
    for line in f:
        if line.startswith("GEMINI_API_KEY="):
            gemini_key = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
        elif line.startswith("OPENROUTER_API_KEY="):
            openrouter_key = line.strip().split("=", 1)[1].strip().strip('"').strip("'")

if not gemini_key and not openrouter_key:
    sys.exit("Need GEMINI_API_KEY or OPENROUTER_API_KEY")

profile = open("bookwellnow_profile.md").read() if os.path.exists("bookwellnow_profile.md") else ""

used = []
used_industries = []
if os.path.exists("bookwellnow-run-log.json"):
    try:
        for e in json.load(open("bookwellnow-run-log.json"))[-40:]:
            if e.get("topic"):
                used.append(e["topic"])
            if e.get("topics"):
                used.extend(e["topics"])
            if e.get("industries"):
                used_industries.extend(e["industries"])
    except Exception:
        pass

# 4 posts/day: image_am, carousel_am, image_pm, carousel_pm
DAY_SLOTS = [
    ("PAIN_NO_SHOW", "FEATURE_CHECKLIST", "NEW_FEATURE_SPOT", "SETUP_STEPS"),
    ("INDUSTRY_SPOT", "CLIENT_JOURNEY", "GOOGLE_CALENDAR", "BEFORE_AFTER"),
    ("FREE_VS_PAID", "WHY_BOOKWELLNOW", "CUSTOM_FIELDS", "MISTAKE_FIX"),
    ("STAFF_SHIFTS", "BUFFER_RESCHEDULE", "SPEED_SEO", "LAUNCH_CHECKLIST"),
    ("ZOOM_MEET", "ONLINE_STACK", "NOTIFICATIONS", "PAYMENTS_STACK"),
    ("MYTH_BUST", "MIGRATION_GUIDE", "WIZARD_SETUP", "INDUSTRY_LISTICLE"),
    ("AGENCY_ANGLE", "SHORTCODE_CTA", "GOOGLE_MEET", "FEATURE_CHECKLIST"),
    ("CUSTOMER_PANEL", "RESCHEDULE_FLOW", "BUFFER_TIME", "SETUP_STEPS"),
    ("NEW_FEATURE_SPOT", "WHY_BOOKWELLNOW", "SOFT_CTA", "CLIENT_JOURNEY"),
    ("PAIN_NO_SHOW", "LAUNCH_CHECKLIST", "GOOGLE_CALENDAR", "SOFT_CTA"),
]

INDUSTRIES = [
    "beauty and hair salons",
    "dental practices and clinics",
    "fitness studios and gyms",
    "spa and wellness centers",
    "veterinary and pet clinics",
    "barbershops",
    "tutors and private coaches",
    "yoga studios",
    "WordPress agencies building client booking sites",
    "physiotherapy and therapy practices",
    "pet grooming studios",
    "cleaning services",
    "consultants and agencies",
    "events and workshop hosts",
    "class and course scheduling",
]

ARCHETYPE_BRIEFS = {
    "PAIN_NO_SHOW": "Open with missed calls, WhatsApp chaos, or no-shows for this industry, then the BookWellNow fix.",
    "INDUSTRY_SPOT": "How this industry configures services, staff, shifts, and the booking page.",
    "FREE_VS_PAID": "Unlimited free core vs plugins that cap staff/services/bookings. Never name a competitor.",
    "STAFF_SHIFTS": "Staff shifts, breaks, holidays for multi-staff teams.",
    "ZOOM_MEET": "Free Zoom + NEW Google Meet auto links for online sessions.",
    "MYTH_BUST": "Bust a myth: WordPress booking is slow, needs a developer, or needs a monthly SaaS.",
    "SPEED_SEO": "Under 15KB footprint, page speed, SEO for booking pages.",
    "AGENCY_ANGLE": "WordPress agencies/freelancers who need a booking layer clients can run.",
    "CUSTOMER_PANEL": "Customer panel + self-serve cancel/reschedule.",
    "SOFT_CTA": "Free download + free expert install. Include bookwellnow.com.",
    "NEW_FEATURE_SPOT": "Spotlight ONE new feature (Google Calendar, Meet, Custom Fields, Buffer, Reschedule, Notifications) with industry outcome.",
    "GOOGLE_CALENDAR": "NEW Google Calendar sync stops double-bookings.",
    "GOOGLE_MEET": "NEW Google Meet auto links for online services.",
    "CUSTOM_FIELDS": "NEW custom intake fields from the admin dashboard.",
    "BUFFER_TIME": "NEW buffer time between appointments for prep.",
    "BUFFER_RESCHEDULE": "NEW buffer time + client reschedule together.",
    "RESCHEDULE_FLOW": "NEW client reschedule without phone/DM.",
    "NOTIFICATIONS": "NEW automated reminders/notifications.",
    "WIZARD_SETUP": "Booking Setup Wizard: Basic Info → Service → Staff → Finish (docs install path).",
    "SHORTCODE_CTA": "Shortcode [bookwell_booking] + universal booking button with service_id/staff_id.",
    "ONLINE_STACK": "Online stack: Zoom, Google Meet, confirmations, reminders.",
    "FEATURE_CHECKLIST": "Checklist of must-have booking features including NEW ones.",
    "SETUP_STEPS": "Install ZIP → Activate → Wizard → shortcode → go live (link docs).",
    "WHY_BOOKWELLNOW": "Unlimited free core + new calendar/meet/fields/buffer/reschedule/reminders.",
    "BEFORE_AFTER": "Before manual chaos vs after real-time booking + reminders.",
    "CLIENT_JOURNEY": "Choose service → staff/time → details (no login) → confirm/pay.",
    "PAYMENTS_STACK": "PayPal free, cash on arrival, WooCommerce/Stripe on paid.",
    "MISTAKE_FIX": "Common booking-page mistakes for this industry + fix.",
    "MIGRATION_GUIDE": "Move from phone/WhatsApp/spreadsheet/capped plugin without losing bookings.",
    "INDUSTRY_LISTICLE": "Industries that run on BookWellNow + one key setting each.",
    "LAUNCH_CHECKLIST": "Pre-launch: services, staff hours, holidays, buffer, payments, reminders, calendar sync.",
}

ANALYTICS_HINTS = """
ANALYTICS LESSONS (impressions):
- Top organic product posts were beauty/salon agency angles, veterinary, dental pain, fitness, spa — be specific.
- Question hooks and concrete owner pain beat generic 'new feature is here' posts.
- Pair every NEW feature with a named industry outcome.
- Avoid vague consulting copy; name the setting (WhatsApp threads, empty chairs, slow clinic site).
"""

SYSTEM = f"""You are the LinkedIn ghostwriter for BookWellNow, a WordPress appointment booking plugin.
Company voice only: we / our / BookWellNow team. Never solo "I".
Audience: owners of appointment-based service businesses and WordPress agencies.
Goal: free plugin installs and setup enquiries.

CAPTION FORMAT (never one wall of text):
1) Hook line (question or sharp pain)
2) Blank line
3) 1-2 short paragraphs
4) Blank line
5) 3-5 bullets starting with "- "
6) Blank line
7) CTA (Comment BOOK / DM industry + staff count / free expert install)
8) Blank line
9) Always end with: {FOOTER}

Highlight NEW features when the archetype asks: Google Calendar, Google Meet, Custom Fields, Buffer Time, Client Reschedule, Notifications, Setup Wizard.
No em-dashes. Never name a competitor plugin; say "most booking plugins".
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
                        "HTTP-Referer": "https://bookwellnow.com",
                        "X-Title": "BookWellNowBatch",
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


def ensure_site(caption: str) -> str:
    caption = (caption or "").strip().replace("—", "-").replace("–", "-")
    caption = re.sub(r"[ \t]+\n", "\n", caption)
    caption = re.sub(r"\n{3,}", "\n\n", caption)
    if "bookwellnow.com" not in caption.lower():
        caption = (caption + "\n\n" + FOOTER).strip()
    return caption


def densify_image(spec):
    bars = spec.get("bars") or []
    while len(bars) < 4:
        bars.append({
            "label": f"Booking outcome {len(bars)+1}",
            "value": "n/a",
            "width_pct": f"{88 - len(bars)*12}%",
            "color": ["#5700B4", "#7C3AED", "#C084FC", "#4C1D95"][len(bars) % 4],
        })
    spec["bars"] = bars[:4]
    bullets = spec.get("bullets") or []
    while len(bullets) < 4:
        bullets.append("Unlimited staff, services, and bookings in free core")
    spec["bullets"] = [str(b)[:80] for b in bullets[:4]]
    spec["caption"] = ensure_site(spec.get("caption", ""))
    return spec


def densify_carousel(car):
    car["caption"] = ensure_site(car.get("caption", ""))
    slides = car.get("slides") or []
    while len(slides) < 6:
        slides.append({
            "cta": True,
            "headline": "Ready to take <em>bookings</em>?",
            "body": "Comment BOOK and we will send the free plugin plus a setup checklist.",
            "bullets": ["Free core on WordPress.org", "Setup wizard in minutes", SITE_URL],
        })
    slides = slides[:6]
    slides[-1]["cta"] = True
    for s in slides:
        sb = s.get("bullets") or []
        while len(sb) < 3:
            sb.append("Concrete setup step for this industry")
        s["bullets"] = [str(b)[:90] for b in sb[:4]]
    car["slides"] = slides
    return car


def gen_day(day_i, date_obj, slots, industry):
    img_a, car_a, img_b, car_b = slots
    user = f"""PRODUCT PROFILE:
{profile[:4500]}

{ANALYTICS_HINTS}

Install docs to reference: {DOCS_URL}
Site URL (required in every caption): {SITE_URL}

BANNED topics: {json.dumps(used[-40:])}

Generate ONE day of BookWellNow LinkedIn content for {date_obj.isoformat()} ({date_obj.strftime('%A')}).
Primary industry: {industry}

Four posts required:
1) image_am archetype {img_a} -> {ARCHETYPE_BRIEFS.get(img_a, '')}
2) carousel_am archetype {car_a} -> {ARCHETYPE_BRIEFS.get(car_a, '')}
3) image_pm archetype {img_b} -> {ARCHETYPE_BRIEFS.get(img_b, '')}
4) carousel_pm archetype {car_b} -> {ARCHETYPE_BRIEFS.get(car_b, '')}

At least TWO of the four posts must highlight NEW features (Google Calendar, Google Meet, Custom Fields, Buffer Time, Reschedule, Notifications, or Setup Wizard).

Return JSON:
{{
  "topic": "short unique day theme",
  "industry": "{industry}",
  "image_am": {{
    "caption": "structured caption with newlines + bullets + {FOOTER}",
    "badge": "BookWellNow",
    "title_main": "3-5 punchy words",
    "title_span": "2-4 accent words",
    "subtitle": "specific promise with industry + feature (max 140 chars)",
    "takeaway_num": "hero stat",
    "takeaway_text": "outcome max 90 chars",
    "bars": [
      {{"label": "specific", "value": "v", "width_pct": "90%", "color": "#5700B4"}},
      {{"label": "b", "value": "v", "width_pct": "78%", "color": "#7C3AED"}},
      {{"label": "c", "value": "v", "width_pct": "65%", "color": "#C084FC"}},
      {{"label": "d", "value": "v", "width_pct": "52%", "color": "#4C1D95"}}
    ],
    "bullets": ["stack/step 1", "2", "3", "4"]
  }},
  "carousel_am": {{
    "caption": "structured caption + {FOOTER}",
    "slides": [
      {{"kick": "HOOK", "headline": "hook with optional <em>accent</em>", "body": "2 sentences", "bullets": ["a","b","c"]}},
      {{"kick": "01", "headline": "...", "body": "...", "bullets": ["a","b","c"]}},
      {{"kick": "02", "headline": "...", "body": "...", "bullets": ["a","b","c"]}},
      {{"kick": "03", "headline": "...", "body": "...", "bullets": ["a","b","c"]}},
      {{"kick": "04", "headline": "...", "body": "...", "bullets": ["a","b","c"]}},
      {{"cta": true, "headline": "Ready to take <em>bookings</em>?", "body": "Comment BOOK for free plugin + setup checklist.", "bullets": ["Free core", "Expert install", "{SITE_URL}"]}}
    ]
  }},
  "image_pm": {{ "...same shape as image_am..." }},
  "carousel_pm": {{ "...same shape as carousel_am..." }}
}}

Rules:
- Exactly 6 slides per carousel; last cta:true
- Captions use real newlines and "- " bullets
- Every caption includes {SITE_URL}
- Each image has 4 bars + 4 bullets (dense, catchy, no empty feel)
- Each carousel slide has body + 3 bullets
- Topics distinct; industry named naturally
- Company voice throughout
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
    data["industry"] = data.get("industry") or industry
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
for ind in reversed(used_industries[-len(INDUSTRIES):]):
    if ind in INDUSTRIES:
        offset = (INDUSTRIES.index(ind) + 1) % len(INDUSTRIES)
        break

days_out = []
date_compact = datetime.date.today().isoformat().replace("-", "")
out_path = f"bookwellnow_batch_{date_compact}.json"


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
    industry = INDUSTRIES[(offset + i) % len(INDUSTRIES)]
    print(f"Generating day {i+1}/{DAYS} {d.isoformat()} {slots} [{industry}]...")
    last_err = None
    for attempt in range(5):
        try:
            day = gen_day(i + 1, d, slots, industry)
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

log_path = "bookwellnow-run-log.json"
try:
    log = json.load(open(log_path)) if os.path.exists(log_path) else []
except Exception:
    log = []
log.append({
    "date": datetime.date.today().isoformat(),
    "mode": f"{DAYS}-day-4posts-image-carousel",
    "file": out_path,
    "topics": [p.get("topic") for p in days_out],
    "industries": [p.get("industry") for p in days_out],
})
json.dump(log[-60:], open(log_path, "w"), indent=2)
print("Updated bookwellnow-run-log.json")
