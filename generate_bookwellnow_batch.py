#!/usr/bin/env python3
"""
Generate 10 days of BookWellNow company LinkedIn content:
  each day = 1 IMAGE post + 1 CAROUSEL post (6 slides).
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

ARCHETYPES = [
    ("PAIN_NO_SHOW", "FEATURE_CHECKLIST"),
    ("INDUSTRY_SPOT", "SETUP_STEPS"),
    ("FREE_VS_PAID", "WHY_BOOKWELLNOW"),
    ("STAFF_SHIFTS", "BEFORE_AFTER"),
    ("ZOOM_ONLINE", "CLIENT_JOURNEY"),
    ("MYTH_BUST", "PAYMENTS_STACK"),
    ("SPEED_SEO", "MISTAKE_FIX"),
    ("AGENCY_ANGLE", "MIGRATION_GUIDE"),
    ("CUSTOMER_PANEL", "INDUSTRY_LISTICLE"),
    ("SOFT_CTA", "LAUNCH_CHECKLIST"),
]

INDUSTRIES = [
    "barbershops",
    "beauty and hair salons",
    "spa and wellness centers",
    "fitness studios and gyms",
    "yoga studios",
    "tutors and private coaches",
    "dental practices and clinics",
    "pet grooming studios",
    "cleaning services",
    "consultants and agencies",
    "physiotherapy and therapy practices",
    "maintenance and repair workshops",
    "events and workshop hosts",
    "boat and equipment rental",
    "class and course scheduling",
]

ARCHETYPE_BRIEFS = {
    "PAIN_NO_SHOW": "Open with a booking pain (missed calls, no-shows, double bookings) for this industry, then show the free BookWellNow features that fix it.",
    "INDUSTRY_SPOT": "Spotlight how this exact industry configures BookWellNow: services, staff, shifts, and the booking page.",
    "FREE_VS_PAID": "Contrast capped booking plugins and monthly SaaS seat fees with the unlimited free core (staff, services, bookings). Never name a competitor.",
    "STAFF_SHIFTS": "Focus on staff shift management, breaks, and holiday management for multi-staff teams.",
    "ZOOM_ONLINE": "Focus on free Zoom integration for online sessions: auto-generated links, confirmations, no manual scheduling.",
    "MYTH_BUST": "Bust a myth about WordPress booking systems (too slow, too complex, needs a developer, needs a monthly subscription).",
    "SPEED_SEO": "Focus on the lightweight footprint, fast page load, and why a heavy booking plugin hurts page speed and SEO.",
    "AGENCY_ANGLE": "Speak to WordPress agencies and freelancers who build client sites and need a booking layer clients can run themselves.",
    "CUSTOMER_PANEL": "Focus on the customer panel and self-serve cancellation: fewer support emails, fewer no-shows.",
    "SOFT_CTA": "Soft offer post: free plugin download plus free expert install and configuration.",
    "FEATURE_CHECKLIST": "Checklist of the free features a booking setup should include, mapped to what this industry needs.",
    "SETUP_STEPS": "Step by step setup: install and activate, add services, add staff and shifts, drop the [bookwell_booking] shortcode, go live.",
    "WHY_BOOKWELLNOW": "Reasons to choose BookWellNow: unlimited everything free, fast, WooCommerce and PayPal, free expert setup, 24/7 support.",
    "BEFORE_AFTER": "Before and after a booking system: manual calendar chaos versus real-time availability and automatic confirmations.",
    "CLIENT_JOURNEY": "Walk the customer booking journey: choose service, pick staff and time, enter details with no login, confirm and pay.",
    "PAYMENTS_STACK": "Payments explained: free PayPal checkout, cash on arrival, WooCommerce and Stripe for paid plans.",
    "MISTAKE_FIX": "Common booking page mistakes for this industry and the fix for each.",
    "MIGRATION_GUIDE": "How to move from phone, WhatsApp, spreadsheet, or a capped plugin to BookWellNow without losing bookings.",
    "INDUSTRY_LISTICLE": "Short list of industries that run on BookWellNow with the one setting that matters most for each.",
    "LAUNCH_CHECKLIST": "Pre-launch checklist before turning on online booking: services priced, staff hours, holidays, payment method, confirmation emails.",
}

SYSTEM = """You are the LinkedIn ghostwriter for BookWellNow, a WordPress appointment booking plugin.
Company voice only: we / our / BookWellNow team. Never solo "I".
Audience: owners of appointment based service businesses and the WordPress agencies who build their sites.
Goal: free plugin installs and setup enquiries. Talk about bookings, staff, no-shows, and revenue, not developer jargon.
Lead with free features: unlimited staff, unlimited services, unlimited bookings, Zoom integration, PayPal, staff shifts and holidays, customer panel, self-serve cancellation, lightweight and fast, mobile friendly.
No em-dashes. Never name a competitor plugin; say "most booking plugins" instead.
Banned: game-changer, cutting-edge, leverage, synergy, unlock, delve, disruptive, revolutionary.
CTA rotate: Comment BOOK / DM us your industry and staff count / download the free version at bookwellnow.com
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
                "HTTP-Referer": "https://bookwellnow.com",
                "X-Title": "BookWellNowBatch",
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


def gen_day(day_i, date_obj, img_arch, car_arch, industry):
    user = f"""PRODUCT PROFILE:
{profile[:3200]}

BANNED topics (already posted): {json.dumps(used[-30:])}

Generate ONE day of BookWellNow LinkedIn content for {date_obj.isoformat()} ({date_obj.strftime('%A')}).
Primary industry for this day: {industry}
Image archetype: {img_arch} -> {ARCHETYPE_BRIEFS.get(img_arch, '')}
Carousel archetype: {car_arch} -> {ARCHETYPE_BRIEFS.get(car_arch, '')}

Return JSON:
{{
  "topic": "short unique topic phrase",
  "industry": "{industry}",
  "image": {{
    "caption": "120-200 word company-page caption ending with CTA",
    "badge": "BookWellNow",
    "title_main": "3-5 words",
    "title_span": "2-4 words",
    "subtitle": "max 120 chars",
    "takeaway_num": "hero stat or short label",
    "takeaway_text": "max 100 chars",
    "bars": [
      {{"label": "max 36 chars", "value": "display", "width_pct": "85%", "color": "#5700B4"}},
      {{"label": "b", "value": "v", "width_pct": "70%", "color": "#7C3AED"}},
      {{"label": "c", "value": "v", "width_pct": "55%", "color": "#C084FC"}}
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
      {{"cta": true, "headline": "Ready to take <em>bookings</em>?", "body": "Comment BOOK and we will send the free plugin plus a setup checklist."}}
    ]
  }}
}}

Rules:
- Exactly 6 carousel slides; last must be cta:true
- No em-dashes in any string
- Topics must be distinct from banned list
- Name the industry naturally in both the image caption and the carousel
- Bars must show booking outcomes (bookings captured, no-shows, admin hours saved, setup time), never fake client counts
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
            "headline": "Ready to take <em>bookings</em>?",
            "body": "Comment BOOK and we will send the free plugin plus a setup checklist.",
        })
    data["carousel"]["slides"] = slides[:6]
    data["carousel"]["slides"][-1]["cta"] = True
    data["day"] = day_i
    data["date"] = date_obj.isoformat()
    data["industry"] = data.get("industry") or industry
    data["image_archetype"] = img_arch
    data["carousel_archetype"] = car_arch
    return data


# Start the industry rotation after the ones used in recent runs
offset = 0
for ind in reversed(used_industries[-len(INDUSTRIES):]):
    if ind in INDUSTRIES:
        offset = (INDUSTRIES.index(ind) + 1) % len(INDUSTRIES)
        break

days_out = []
for i in range(DAYS):
    d = START + datetime.timedelta(days=i)
    img_a, car_a = ARCHETYPES[i % len(ARCHETYPES)]
    industry = INDUSTRIES[(offset + i) % len(INDUSTRIES)]
    print(f"Generating day {i+1}/{DAYS} {d.isoformat()} ({img_a} + {car_a}) [{industry}]...")
    last_err = None
    for attempt in range(3):
        try:
            day = gen_day(i + 1, d, img_a, car_a, industry)
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
out_path = f"bookwellnow_batch_{date_compact}.json"
payload = {
    "generated": datetime.date.today().isoformat(),
    "days": DAYS,
    "start": START.isoformat(),
    "end": (START + datetime.timedelta(days=DAYS - 1)).isoformat(),
    "posts": days_out,
}
json.dump(payload, open(out_path, "w"), indent=2)
print(f"Wrote {out_path} ({DAYS} days, {DAYS*2} posts)")

log_path = "bookwellnow-run-log.json"
try:
    log = json.load(open(log_path)) if os.path.exists(log_path) else []
except Exception:
    log = []
log.append({
    "date": datetime.date.today().isoformat(),
    "mode": f"{DAYS}-day-image-carousel",
    "file": out_path,
    "topics": [p.get("topic") for p in days_out],
    "industries": [p.get("industry") for p in days_out],
})
json.dump(log[-60:], open(log_path, "w"), indent=2)
print("Updated bookwellnow-run-log.json")
