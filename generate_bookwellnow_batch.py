#!/usr/bin/env python3
"""
Generate 10 days of BookWellNow company LinkedIn content:
  each day = 2 CAROUSEL posts (3-4 slides each).
Writes bookwellnow_batch_YYYYMMDD.json

Copy is reverse-engineered from BookWellNow page analytics
(bookwellnow_content_1788289373637.xls, Aug 1 to Aug 30 2026).
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

from bookwellnow_links import docs_url, ensure_tracked_footer, site_url

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

DAYS = int(os.environ.get("BOOKWELLNOW_DAYS", "10"))
if os.environ.get("BOOKWELLNOW_START"):
    START = datetime.date.fromisoformat(os.environ["BOOKWELLNOW_START"])
else:
    START = datetime.date.today() + datetime.timedelta(days=1)

SITE_URL = site_url("linkedin")
DOCS_URL = docs_url("linkedin")
FOOTER = f"Start free: {SITE_URL}"
APPLY = "hr@bookwellnow.com"

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
if os.path.exists("bookwellnow-run-log.json"):
    try:
        for e in json.load(open("bookwellnow-run-log.json"))[-40:]:
            if e.get("topic"):
                used.append(e["topic"])
            if e.get("topics"):
                used.extend(e["topics"])
    except Exception:
        pass

# 2 carousels/day. The Aug 19-28 4-post days averaged 12 product impressions;
# Jul 25 operational copy and hiring still carry comments. Two hiring posts
# because they produced ~40% of impressions and 7 of 12 comments in Aug.
DAY_PLAN = [
    [
        ("WordPress product team", "HIRING_WP"),
        ("dental practices and clinics", "MISTAKE_FIX"),
    ],
    [
        ("pet grooming studios", "AGENCY_BUILD"),
        ("WordPress agencies building client booking sites", "LAUNCH_CHECKLIST"),
    ],
    [
        ("physiotherapy and therapy practices", "RESCHEDULE_FLOW"),
        ("dental practices and clinics", "SPEED_SEO"),
    ],
    [
        ("veterinary and pet clinics", "INDUSTRY_SPOT"),
        ("beauty and hair salons", "AGENCY_BUILD"),
    ],
    [
        ("growth marketing team", "HIRING_SEO"),
        ("cleaning services and home care teams", "STAFF_SHIFTS"),
    ],
    [
        ("barbershops", "SETUP_STEPS"),
        ("WordPress agencies building client booking sites", "SHORTCODE_CTA"),
    ],
    [
        ("physiotherapy and therapy practices", "PAIN_NO_SHOW"),
        ("pet grooming studios", "STAFF_SHIFTS"),
    ],
    [
        ("dental practices and clinics", "RESCHEDULE_FLOW"),
        ("veterinary and pet clinics", "NOTIFICATIONS"),
    ],
    [
        ("WordPress agencies building client booking sites", "AGENCY_ANGLE"),
        ("spa and wellness centers", "TIRED_OF"),
    ],
    [
        ("fitness studios and gyms", "UNLIMITED_STAFF"),
        ("beauty and hair salons", "CLIENT_JOURNEY"),
    ],
]

ARCHETYPE_BRIEFS = {
    "AGENCY_BUILD": "Open like the top organic product post: 'If you are building a website for [industry], you do not need expensive monthly booking software.' Speak to the WordPress agency/freelancer, then the owner. 10-minute setup, shifts, 24/7 booking.",
    "MISTAKE_FIX": "The only product posts that earned comments. Name 3 concrete booking-page mistakes for this industry (slow form, forced account, hidden caps) and the fix. Question hook that names lost revenue.",
    "UNLIMITED_STAFF": "Anger at per-seat pricing. Unlimited staff/services/bookings in the free core. Name trainer/stylist/barber roles.",
    "INDUSTRY_SPOT": "How this industry configures services, staff, shifts, and the booking page. Operational, not generic.",
    "TIRED_OF": "High-CTR opener: tired of clunky plugins that slow the site and charge per staff member. Then the BookWellNow contrast.",
    "PAYMENTS": "Highest product CTR. Rigid payments lose bookings. Free PayPal + cash on arrival. Woo/Stripe on paid.",
    "LAUNCH_CHECKLIST": "Five-step go-live checklist. Agencies loved this. Comment BOOK for the checklist.",
    "HIRING_WP": "Company hiring carousel for a Remote Full-Time WordPress Developer, 2-5 years. Apply hr@bookwellnow.com. Ask people to tag a developer or repost. Hashtags like the Jul 27 post that got 13,604 impressions.",
    "HIRING_SEO": "Company hiring carousel for a Remote Full-Time SEO Executive, 2-5 years. Apply hr@bookwellnow.com. Ask people to tag or repost. Hashtags.",
    "STAFF_SHIFTS": "Shifts, breaks, holidays per staff member. Empty chairs vs real availability.",
    "SPEED_SEO": "Second comment-winning product post. 3-second bounce. Under 15KB footprint vs heavy plugins.",
    "PAIN_NO_SHOW": "Missed calls, WhatsApp chaos, no-shows. Name the empty chair / missed patient. Then reminders + self-serve cancel.",
    "BEFORE_AFTER": "Left: phone/DM/spreadsheet. Right: live WordPress booking + reminders. Concrete.",
    "FREE_VS_PAID": "Unlimited free core vs plugins that cap staff/services/bookings. Never name a competitor.",
    "CUSTOM_FIELDS": "NEW custom intake fields. Color formula, pet breed, injury notes, etc.",
    "RESCHEDULE_FLOW": "NEW client reschedule without phone/DM. High click when paired with dental.",
    "WHATSAPP_CHAOS": "Still booking via WhatsApp threads and sticky notes. Invite a reshare for owners still doing this.",
    "NOTIFICATIONS": "NEW automated reminders. Cut no-shows. Name the industry.",
    "CLIENT_JOURNEY": "Service → staff/time → details (no login) → confirm/pay. No-login was a yoga winner; reuse for beauty.",
    "ZOOM_MEET": "Free Zoom + NEW Google Meet auto links for online sessions.",
    "BUFFER_TIME": "NEW buffer between appointments for prep and cleaning.",
    "SHORTCODE_CTA": "[bookwell_booking] + universal booking button with service_id/staff_id.",
    "SETUP_STEPS": "Install ZIP → Activate → Wizard → shortcode → go live. Link docs.",
    "GOOGLE_CALENDAR": "NEW Google Calendar sync stops double-bookings.",
    "CUSTOMER_PANEL": "Self-serve view/cancel/reschedule. Fewer front-desk interruptions.",
    "MYTH_BUST": "Bust: WordPress booking is slow, needs a developer, or needs monthly SaaS.",
    "AGENCY_ANGLE": "Agencies need a booking layer clients can run without calling the developer.",
    "SOFT_CTA": "Free download + free expert install. bookwellnow.com. Invite comment BOOK and a reshare.",
}

ANALYTICS_HINTS = """
REAL PAGE ANALYTICS (bookwellnow_content_1788289373637.xls, Aug 1-30 2026 views; posts Jul 25-Aug 19):
- Hiring still wins: 4 hiring posts = 1,373 impressions, 7 comments, 329 clicks (avg 343 imp). Best: Aug 18 WP Developer 954 imp / 6 comments / 214 clicks. Repeat that WP hiring shape. SEO hiring is weaker (38-56 imp) so write it like the WP post: rocket, role, tag a person, hashtags, apply hr@bookwellnow.com.
- Product: 122 posts = 2,103 imp, 5 comments, 0 reposts, avg 17 imp. The Aug 19 4-carousel days averaged 12 product imp. Two stronger posts beat four thin ones.
- Product comments only on dental MISTAKE_FIX and dental SPEED_SEO (Jul 25). Repeat that shape: named clinic failure + we identified the mistakes.
- Best product industries by avg impressions: pet grooming (32), physio (25), vet/pet (21-28), dental (19), WordPress agencies (18). Weak: tutors (7), spa question-hooks (8), fitness question-hooks (9), thin beauty questions (12).
- Highest product CTR: dental reschedule (76%), physio missed appointments (52%), beauty 'If you are building a website for…' (50%), agency shortcode/checklist (31-38%), vet operations (33%).
- Agency launch-checklist earned the only product comment in August. Keep a 5-step go-live checklist.
- Question-hook captions averaged 13 imp. Operational statements averaged 30. Open with a named industry + a concrete loss (empty chair, 3-second bounce, per-seat fee), not 'are you ready for growth'.
- Dual CTA: Comment BOOK + a one-line debate they can answer + 'Repost if you know a [industry] still on WhatsApp.' Zero reposts in this export. Ask for the reshare anyway.
- Skip yoga filler, generic tutoring setup, events/workshops, and two posts about the same industry on one day.
"""

SYSTEM = f"""You are the LinkedIn ghostwriter for BookWellNow, a WordPress appointment booking plugin.
Company voice only: we / our / BookWellNow team. Never solo "I".
Audience: owners of appointment-based service businesses and WordPress agencies.
Goal: free plugin installs, setup enquiries, comments, likes, and reshares.

CAPTION FORMAT (never one wall of text):
1) Hook line: named industry in the first 8 words. Question or sharp operational pain. Not 'are you ready for growth'.
2) Blank line
3) 2 short paragraphs with concrete settings (WhatsApp, empty chairs, 3-second bounce, per-seat fees)
4) Blank line
5) 3-5 bullets starting with "- "
6) Blank line
7) Dual CTA:
   - Comment BOOK (or Comment DEV / SEO on hiring posts)
   - One comment-bait question they can answer in one line
   - One reshare line: Repost if you know a [industry] still booking via WhatsApp/phone
8) Blank line
9) Always end product posts with: {FOOTER}
Hiring posts end with Apply: {APPLY} plus 8-12 hashtags matching the Jul 27/29 winning posts.

Highlight NEW features when the archetype asks: Google Calendar, Google Meet, Custom Fields, Buffer Time, Client Reschedule, Notifications, Setup Wizard.
No em-dashes. Never name a competitor plugin; say "most booking plugins".
Banned: game-changer, cutting-edge, leverage, synergy, unlock, delve, disruptive, revolutionary.
Carousel slides: 4. Slide 1 hook with a giant stat or industry kicker, slides 2-3 teach with numbered facts (not fluff), slide 4 CTA.
Each slide headline uses one <em>accent</em> word.
Slide 2/3 must be informative: named features, numbers (15KB, 10 minutes, 0 per-seat fees, 24/7), before/after, or a 4-step setup.
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


def ensure_site(caption: str, hiring=False) -> str:
    caption = ensure_tracked_footer(caption, "linkedin", hiring=hiring)
    caption = caption.replace("—", "-").replace("–", "-")
    caption = re.sub(r"[ \t]+\n", "\n", caption)
    caption = re.sub(r"\n{3,}", "\n\n", caption)
    if hiring and APPLY.lower() not in caption.lower():
        caption = (caption + f"\n\nApply: {APPLY}").strip()
    return caption


LAYOUT_ROTATION = [
    ["hook_stat", "list", "cards", "cta"],
    ["hook_stat", "split", "list", "cta"],
]


def densify_carousel(car, slot_i=0, hiring=False):
    car["caption"] = ensure_site(car.get("caption", ""), hiring=hiring)
    layouts = LAYOUT_ROTATION[slot_i % 4]
    slides = car.get("slides") or []
    while len(slides) < 4:
        slides.append({
            "headline": "Ready to take <em>bookings</em>?",
            "body": "Comment BOOK and we will send the free plugin plus a setup checklist.",
            "bullets": ["Free core on WordPress.org", "Setup wizard in minutes", SITE_URL],
        })
    slides = slides[:4]
    for i, s in enumerate(slides):
        s["layout"] = layouts[i]
        if i == 3:
            s["cta"] = True
            s["layout"] = "cta"
        sb = [str(b)[:90] for b in (s.get("bullets") or []) if str(b).strip() and "Concrete setup" not in str(b)]
        if len(sb) < 3:
            extras = [
                "Unlimited staff in the free core",
                "24/7 booking on WordPress",
                "Comment BOOK for the setup checklist",
            ]
            for e in extras:
                if e not in sb:
                    sb.append(e)
                if len(sb) >= 3:
                    break
        s["bullets"] = sb[:4]
        if s["layout"] == "split":
            s.setdefault("left_title", "BEFORE")
            s.setdefault("right_title", "AFTER")
            s.setdefault("left_items", sb[:3] if sb else ["Phone tag", "No-shows", "Double books"])
            s.setdefault("right_items", ["24/7 online booking", "Automatic reminders", "Self-serve reschedule"])
            s["left_items"] = [str(x)[:48] for x in (s.get("left_items") or [])[:3]]
            s["right_items"] = [str(x)[:48] for x in (s.get("right_items") or [])[:3]]
        if s["layout"] == "cards":
            cards = s.get("cards") or []
            while len(cards) < 4:
                idx = len(cards)
                cards.append({
                    "title": (sb[idx] if idx < len(sb) else f"Step {idx+1}")[:40],
                    "body": "Set it once. Bookings run themselves.",
                })
            s["cards"] = [
                {"title": str(c.get("title", ""))[:42], "body": str(c.get("body") or "Set it once. Bookings run themselves.")[:80]}
                for c in cards[:4]
            ]
        if s["layout"] == "hook_stat":
            s.setdefault("stat", s.get("stat") or "")
            s.setdefault("stat_label", s.get("stat_label") or "")
        if "<em>" not in str(s.get("headline", "")):
            words = str(s.get("headline", "Take bookings")).split()
            if words:
                words[-1] = f"<em>{words[-1]}</em>"
                s["headline"] = " ".join(words)
    car["slides"] = slides
    car["slide_count"] = 4
    return car


def gen_day(day_i, date_obj, plan):
    slots_txt = []
    for i, (industry, arch) in enumerate(plan, 1):
        slots_txt.append(
            f"{i}) carousel_{i} industry={industry} archetype={arch} -> {ARCHETYPE_BRIEFS.get(arch, '')}"
        )
    user = f"""PRODUCT PROFILE:
{profile[:4200]}

{ANALYTICS_HINTS}

Install docs: {DOCS_URL}
Site URL (required on every PRODUCT caption): {SITE_URL}
Hiring apply email: {APPLY}

BANNED topics: {json.dumps(used[-50:])}

Generate ONE day of BookWellNow LinkedIn content for {date_obj.isoformat()} ({date_obj.strftime('%A')}).
Two DISTINCT carousel posts. Different industries. Do not recycle the same hook.

{chr(10).join(slots_txt)}

Return JSON:
{{
  "topic": "short unique day theme covering both posts",
  "carousels": [
    {{
      "industry": "from plan",
      "archetype": "from plan",
      "caption": "structured caption with newlines + bullets + CTA + reshare line",
      "stat": "short hero number if any e.g. 15KB or 0 or 3s or 10m",
      "stat_label": "what the number means",
      "slides": [
        {{
          "kick": "short kicker e.g. DENTAL or HIRING",
          "headline": "hook with one <em>accent</em>",
          "stat": "optional short stat",
          "stat_label": "optional",
          "body": "1-2 sentences, specific",
          "bullets": ["a","b","c"]
        }},
        {{
          "kick": "01",
          "headline": "...",
          "body": "...",
          "bullets": ["concrete fact 1","concrete fact 2","concrete fact 3","concrete fact 4"],
          "left_title": "BEFORE",
          "left_items": ["pain 1","pain 2","pain 3"],
          "right_title": "AFTER",
          "right_items": ["win 1","win 2","win 3"],
          "cards": [
            {{"title": "short","body": "one outcome"}},
            {{"title": "short","body": "one outcome"}},
            {{"title": "short","body": "one outcome"}},
            {{"title": "short","body": "one outcome"}}
          ]
        }},
        {{"kick": "02", "headline": "...", "body": "...", "bullets": ["a","b","c"], "cards": [...], "left_items": [...], "right_items": [...]}},
        {{"cta": true, "headline": "Ready to take <em>bookings</em>?", "body": "Comment BOOK for the free plugin + setup checklist.", "bullets": ["Free core","Expert install","{SITE_URL}"]}}
      ]
    }}
  ]
}}

Rules:
- carousels array length EXACTLY 2, order matching the plan
- Exactly 4 slides per carousel; last is CTA
- Hiring carousels: slide 1 role hook, slide 2 what you will do, slide 3 why join, slide 4 apply to {APPLY}. Caption uses 🚀, tags, hashtags, no product footer required.
- Product CTAs: Comment BOOK, a one-line debate question, and Repost if…
- Captions use real newlines and "- " bullets
- Topics distinct from banned list
- Company voice throughout
- Name the industry on slide 1 kicker
- Teaching slides must name a real BookWellNow feature, not generic advice
"""
    raw = call_llm(user)
    data = parse_json(raw)
    cars = data.get("carousels") or []
    if len(cars) < 2:
        alt = [data.get(f"carousel_{i}") for i in range(1, 3)]
        if all(alt):
            cars = alt
    if len(cars) < 2:
        raise ValueError(f"expected 2 carousels, got {len(cars)}")
    out_cars = []
    for i, (industry, arch) in enumerate(plan):
        car = cars[i]
        hiring = arch.startswith("HIRING")
        car = densify_carousel(car, slot_i=i, hiring=hiring)
        car["industry"] = car.get("industry") or industry
        car["archetype"] = arch
        out_cars.append(car)
    data["carousels"] = out_cars
    data["day"] = day_i
    data["date"] = date_obj.isoformat()
    data["industry"] = out_cars[0]["industry"]
    data["industries"] = [c["industry"] for c in out_cars]
    data["slots"] = {f"carousel_{i+1}": plan[i][1] for i in range(2)}
    data["carousel"] = out_cars[0]
    data["carousel_am"] = out_cars[0]
    data["carousel_pm"] = out_cars[1]
    return data


days_out = []
date_compact = datetime.date.today().isoformat().replace("-", "")
out_path = f"bookwellnow_batch_{date_compact}.json"


def save_partial():
    payload = {
        "generated": datetime.date.today().isoformat(),
        "days": DAYS,
        "postsPerDay": 2,
        "format": "carousel-only-4slides",
        "start": START.isoformat(),
        "end": (START + datetime.timedelta(days=DAYS - 1)).isoformat(),
        "posts": days_out,
        "partial": len(days_out) < DAYS,
    }
    json.dump(payload, open(out_path, "w"), indent=2)


for i in range(DAYS):
    d = START + datetime.timedelta(days=i)
    plan = DAY_PLAN[i % len(DAY_PLAN)]
    print(f"Generating day {i+1}/{DAYS} {d.isoformat()} {[p[1] for p in plan]}...")
    last_err = None
    for attempt in range(5):
        try:
            day = gen_day(i + 1, d, plan)
            topic = day.get("topic") or f"day-{i+1}"
            used.append(topic)
            used.extend(day.get("industries") or [])
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
    "postsPerDay": 2,
    "format": "carousel-only-4slides",
    "start": START.isoformat(),
    "end": (START + datetime.timedelta(days=DAYS - 1)).isoformat(),
    "posts": days_out,
}
json.dump(payload, open(out_path, "w"), indent=2)
print(f"Wrote {out_path} ({DAYS} days, {DAYS*2} carousel posts)")

log_path = "bookwellnow-run-log.json"
try:
    log = json.load(open(log_path)) if os.path.exists(log_path) else []
except Exception:
    log = []
log.append({
    "date": datetime.date.today().isoformat(),
    "mode": f"{DAYS}-day-2posts-carousel-only",
    "file": out_path,
    "topics": [p.get("topic") for p in days_out],
    "industries": [ind for p in days_out for ind in (p.get("industries") or [p.get("industry")])],
})
json.dump(log[-60:], open(log_path, "w"), indent=2)
print("Updated bookwellnow-run-log.json")
