#!/usr/bin/env python3
"""
Generate 10 days of BookWellNow Facebook Page content:
  each day = 3 photo-album posts (4 slides each).
Writes bookwellnow_facebook_batch_YYYYMMDD.json

Facebook-native copy for a new Page: introduce every current product
feature (free + Pro, from bookwellnow.com + WordPress.org 4.0.10),
grow followers, and end every product caption with a UTM link.
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

from bookwellnow_links import docs_url, ensure_tracked_footer, site_url, wporg_url

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

SITE_URL = site_url("facebook")
DOCS_URL = docs_url("facebook")
WP_URL = wporg_url("facebook")
FOOTER = f"Start free: {SITE_URL}"
CHANNEL = "facebook"

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
if os.path.exists("bookwellnow-facebook-run-log.json"):
    try:
        for e in json.load(open("bookwellnow-facebook-run-log.json"))[-40:]:
            if e.get("topic"):
                used.append(e["topic"])
            if e.get("topics"):
                used.extend(e["topics"])
    except Exception:
        pass

# 3 Facebook posts/day. New Page: cover every live feature, then ask people to Follow.
DAY_PLAN = [
    [
        ("WordPress service businesses", "PAGE_INTRO"),
        ("salons and barbershops", "UNLIMITED_CORE"),
        ("any appointment business", "CLIENT_JOURNEY"),
    ],
    [
        ("WordPress site owners", "SETUP_WIZARD"),
        ("multi-staff clinics and salons", "STAFF_SHIFTS"),
        ("service catalogs", "SERVICES_DUP"),
    ],
    [
        ("WordPress agencies", "SHORTCODES"),
        ("repeat clients", "CUSTOMER_PANEL"),
        ("paid appointments", "PAYMENTS_FREE"),
    ],
    [
        ("coaches, tutors, and online clinics", "ZOOM_FREE"),
        ("front-desk calendars", "CALENDAR_AVAIL"),
        ("intake forms", "FORM_FIELDS"),
    ],
    [
        ("branded booking pages", "APPEARANCE"),
        ("late-night and overnight shops", "OVERNIGHT"),
        ("phone-first customers", "SPEED_MOBILE"),
    ],
    [
        ("teams juggling Google Calendar", "PRO_GCAL"),
        ("online sessions", "PRO_MEET"),
        ("custom intake questions", "PRO_FIELDS"),
    ],
    [
        ("prep time between clients", "PRO_BUFFER"),
        ("no-show heavy clinics", "PRO_RESCHEDULE"),
        ("reminder follow-up", "PRO_NOTIFY"),
    ],
    [
        ("WooCommerce shops", "PRO_WOO"),
        ("add-on upsells", "PRO_EXTRAS"),
        ("classes and group slots", "PRO_CAPACITY"),
    ],
    [
        ("owners who need a human", "SUPPORT_DOCS"),
        ("first-time installers", "EXPERT_INSTALL"),
        ("spas, gyms, clinics, tutors, pet care", "INDUSTRIES"),
    ],
    [
        ("this Facebook community", "FOLLOW_GROW"),
        ("WordPress.org downloaders", "FREE_DOWNLOAD"),
        ("agencies building client sites", "AGENCY_BUILD"),
    ],
]

ARCHETYPE_BRIEFS = {
    "PAGE_INTRO": "This is a NEW Facebook Page. Introduce BookWellNow as the WordPress appointment booking plugin. Ask people to Follow for daily booking tips. Name unlimited staff/services/bookings in the free core. No hiring post.",
    "UNLIMITED_CORE": "Free core: unlimited staff, unlimited services, unlimited bookings. No per-seat fee, no monthly booking cap. Contrast with most booking plugins that charge as you grow. Never name a competitor.",
    "CLIENT_JOURNEY": "Customer flow: 1) choose a service with price and duration 2) pick staff + date/time from live availability 3) name and contact, no login 4) confirm, pay online or on arrival, instant confirmation email.",
    "SETUP_WIZARD": "Install from WordPress.org ZIP or Plugins > Add New. Activate. Booking Setup Wizard: Basic Info to Service to Staff to Finish. Live in about 5 to 10 minutes. PHP 8.1+ recommended (7.4 min), WordPress 6.2+ recommended (5.3 min). Link docs.",
    "STAFF_SHIFTS": "Free staff shift management: working hours, breaks, holidays, special days per staff. Overnight shifts (example 2:00 PM to 2:00 AM). Duplicate Staff on the admin list. No staff seat limit.",
    "SERVICES_DUP": "Unlimited services, packages, classes. Duration and price per service. Assign services to staff. Duplicate Service on the admin list. Auto-select when only one service or staff applies.",
    "SHORTCODES": "Be specific: [bookwell_booking] inline form. [bookwell_booking_button] popup, optional service_id, staff_id, label. [bookwellnow_customer_panel] for the logged-in customer area. Works in Elementor, Gutenberg, most themes. Shortcode Generator in admin.",
    "CUSTOMER_PANEL": "Free customer panel: login, history, profile, cancel when enabled. Optional WordPress user creation on booking. Guest cancel via %cancel_appointment_link% in emails. Shortcode [bookwellnow_customer_panel].",
    "PAYMENTS_FREE": "Free PayPal Checkout sandbox and live. Cash on arrival / manual. PayPal unsupported currencies are hidden. Pro adds WooCommerce / Stripe / cards. Do not claim Stripe is free.",
    "ZOOM_FREE": "Free Zoom via Settings > Integrations, Server-to-Server OAuth. Enable per staff (assign Zoom user) and per service. Meeting created on booking. Admin Start Zoom. Customer Join Zoom from the panel. Email placeholders %zoom_join_url% and %zoom_host_url%.",
    "CALENDAR_AVAIL": "Real-time slots. Overlapping times for the same staff are blocked twice (list + save). Week Starts On setting (default Monday). Day Calendar. Working hours, breaks, holidays, special days control what is offered.",
    "FORM_FIELDS": "Form Fields admin: phone, first name, last name, email, note, terms. Required, label, placeholder, error, hide/show, drag-and-drop order, full width or half width. Phone country flags. Terms checkbox with custom link.",
    "APPEARANCE": "Booking form appearance: 10 themes plus Light Theme, Light Blue, Light Sage, Light Plum, Light Teal presets (plugin 4.0.10) for white websites. Form type: Small Booking Wizard or Service List with Popup. Hide service description, show staff designation.",
    "OVERNIGHT": "Overnight booking: set Start and End across midnight, treated as one continuous shift, frontend +1 day slot labels. Special/Holiday Days with start/end using Default Date Format.",
    "SPEED_MOBILE": "Under 15KB footprint. Mobile-friendly booking, no separate app. Spam protection. Multi-language. Plugin 4.0.10 styling fixes for light sidebars and translation encoding.",
    "PRO_GCAL": "Mark as PRO. Google Calendar two-way sync to stop double-bookings. Do not say it is free.",
    "PRO_MEET": "Mark as PRO. Auto Google Meet links for online services. Free Zoom stays in the free core; Meet is Pro.",
    "PRO_FIELDS": "Mark as PRO. Extra custom intake fields beyond the free Form Fields page. Color formula, pet breed, injury notes examples.",
    "PRO_BUFFER": "Mark as PRO. Buffer time auto-blocks padding between appointments for prep and cleaning.",
    "PRO_RESCHEDULE": "Mark as PRO. Clients reschedule without calling or DMing. Free core has cancel; reschedule is Pro.",
    "PRO_NOTIFY": "Mark as PRO. Scheduled notifications and automated reminders. Free core still sends confirmation and status emails.",
    "PRO_WOO": "Mark as PRO. WooCommerce payment gateways and credit cards. Free PayPal stays free.",
    "PRO_EXTRAS": "Mark as PRO. Service extras, add-ons, and selection rules to raise revenue per appointment.",
    "PRO_CAPACITY": "Mark as PRO. Multiple quantity and maximum capacity for classes and group slots.",
    "SUPPORT_DOCS": "24/7 ticketing, average first response under 2 hours. Knowledge base. Automatic updates. Name the docs installing guide.",
    "EXPERT_INSTALL": "Free expert install and configuration on the site (Claim Slot / Expert Config). 14 day money-back on paid plans. Data remains yours.",
    "INDUSTRIES": "Name real fits from the site: barbershops, beauty, spa, gym, yoga, dental, pet grooming, cleaning, tutors, consultants, events, boat rental, smart queuing. One concrete booking example each, not a dump.",
    "FOLLOW_GROW": "New Page growth post. Ask to Follow BookWellNow, Share the post, Comment the business type. Promise upcoming setup tips. No hype words.",
    "FREE_DOWNLOAD": "WordPress.org plugin bookwellnow-appointment-booking. Free core, 4.0.10. Duplicate Service and Staff. Overnight shifts. Point to the plugin directory URL.",
    "AGENCY_BUILD": "If you are building a website for a salon or clinic, you do not need monthly booking SaaS. Drop in [bookwell_booking], hand the client unlimited staff in the free core.",
}

PRODUCT_FACTS = """
LIVE PRODUCT FACTS (scraped Sep 2026 from bookwellnow.com + WordPress.org plugin 4.0.10):
FREE: unlimited staff, services, bookings; Zoom S2S OAuth; PayPal Checkout + cash on arrival; staff shifts/breaks/holidays/special days; overnight shifts; customer panel + cancel; duplicate service/staff; [bookwell_booking], [bookwell_booking_button] (service_id, staff_id, label), [bookwellnow_customer_panel]; Form Fields admin; appearance themes including 5 new light presets; Week Starts On; full/half width fields; Day Calendar; under 15KB; Elementor/Gutenberg; no login to book.
PRO: Google Calendar two-way sync; Google Meet; extra custom fields; buffer time; client reschedule; scheduled notifications; WooCommerce/Stripe; extras/rules; quantity and max capacity.
Setup: ZIP from WordPress.org, Plugins > Upload > Activate, wizard in minutes. PHP 8.1+ rec / 7.4 min. WP 6.2+ rec / 5.3 min. MySQL 5.7+ / MariaDB 10.3+. 256M memory rec.
Support: 24/7 tickets, first response under 2 hours. Free expert config. 14-day money-back on paid.
"""

SYSTEM = f"""You are the Facebook Page ghostwriter for BookWellNow, a WordPress appointment booking plugin.
This Facebook Page is NEW. Goal: teach every real feature, get Follows, comments, and shares, then free installs.
Company voice only: we / our / BookWellNow team. Never solo "I".

FACEBOOK (not LinkedIn):
- Conversational, specific, short paragraphs. First line must earn the click in 125 characters.
- Ask people to Follow the BookWellNow Page on every post.
- Share this if..., not Repost.
- Comment with a one-word business type (salon, clinic, gym, tutor).
- Max 3 hashtags, at the end. No LinkedIn hiring posts. No Comment BOOK as the only CTA.
- Always end product captions with a blank line then {FOOTER}
- Name real UI: shortcodes, Settings > Integrations, Form Fields, plugin 4.0.10 when relevant.
- Mark Pro features as Pro. Do not call Google Calendar / Meet / buffer / reschedule / WooCommerce free.
- No em-dashes. Banned: game-changer, cutting-edge, leverage, synergy, unlock, delve, disruptive, revolutionary.
- Never name a competitor plugin.
- Carousel: 4 slides. Slide 1 hook + stat. Slides 2-3 teach named features. Slide 4 Follow + start-free CTA.
- Each slide headline uses one <em>accent</em> word.
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
                        "X-Title": "BookWellNowFacebook",
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
    caption = ensure_tracked_footer(caption, CHANNEL, hiring=hiring)
    caption = caption.replace("—", "-").replace("–", "-")
    caption = re.sub(r"[ \t]+\n", "\n", caption)
    caption = re.sub(r"\n{3,}", "\n\n", caption)
    return caption


LAYOUT_ROTATION = [
    ["hook_stat", "list", "cards", "cta"],
    ["hook_stat", "split", "list", "cta"],
    ["hook_stat", "cards", "list", "cta"],
]


def densify_carousel(car, slot_i=0, hiring=False):
    car["caption"] = ensure_site(car.get("caption", ""), hiring=hiring)
    layouts = LAYOUT_ROTATION[slot_i % 3]
    slides = car.get("slides") or []
    while len(slides) < 4:
        slides.append({
            "headline": "Follow us for <em>booking</em> tips",
            "body": "Follow BookWellNow, then comment your business type for a setup checklist.",
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
                "Follow BookWellNow on Facebook",
                "Unlimited staff in the free core",
                "Comment your business type",
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
            s.setdefault("left_items", sb[:3] if sb else ["WhatsApp chaos", "No-shows", "Double books"])
            s.setdefault("right_items", ["24/7 WordPress booking", "Staff shifts", "Customer panel"])
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
            f"{i}) carousel_{i} audience={industry} archetype={arch} -> {ARCHETYPE_BRIEFS.get(arch, '')}"
        )
    user = f"""PRODUCT PROFILE:
{profile[:3800]}

{PRODUCT_FACTS}

Install docs: {DOCS_URL}
Site URL (required at end of every caption): {SITE_URL}
WordPress.org: {WP_URL}

BANNED topics: {json.dumps(used[-50:])}

Generate ONE day of BookWellNow FACEBOOK Page content for {date_obj.isoformat()} ({date_obj.strftime('%A')}).
Three DISTINCT carousel posts. Different features. Do not recycle the same hook.
This is a new Facebook Page. Teach the feature, then ask people to Follow and Share.

{chr(10).join(slots_txt)}

Return JSON:
{{
  "topic": "short unique day theme covering all three posts",
  "carousels": [
    {{
      "industry": "from plan",
      "archetype": "from plan",
      "caption": "Facebook caption with newlines + bullets + Follow + Share + comment prompt + {FOOTER}",
      "stat": "short hero number if any e.g. 15KB or 0 or 4 or 10m",
      "stat_label": "what the number means",
      "slides": [
        {{
          "kick": "short kicker",
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
        {{"cta": true, "headline": "Follow BookWellNow for <em>booking</em> tips", "body": "Follow the page. Comment your business type. Start free on WordPress.", "bullets": ["Follow this Page","Share with an owner still on WhatsApp","{SITE_URL}"]}}
      ]
    }}
  ]
}}

Rules:
- carousels array length EXACTLY 3, order matching the plan
- Exactly 4 slides per carousel; last is Follow CTA
- Captions use real newlines and "- " bullets
- Topics distinct from banned list
- Company voice throughout
- Teaching slides must name a real BookWellNow control, shortcode, or setting
"""
    raw = call_llm(user)
    data = parse_json(raw)
    cars = data.get("carousels") or []
    if len(cars) < 3:
        alt = [data.get(f"carousel_{i}") for i in range(1, 4)]
        if all(alt):
            cars = alt
    if len(cars) < 3:
        raise ValueError(f"expected 3 carousels, got {len(cars)}")
    out_cars = []
    for i, (industry, arch) in enumerate(plan):
        car = cars[i]
        car = densify_carousel(car, slot_i=i, hiring=False)
        car["industry"] = car.get("industry") or industry
        car["archetype"] = arch
        out_cars.append(car)
    data["carousels"] = out_cars
    data["day"] = day_i
    data["date"] = date_obj.isoformat()
    data["industry"] = out_cars[0]["industry"]
    data["industries"] = [c["industry"] for c in out_cars]
    data["slots"] = {f"carousel_{i+1}": plan[i][1] for i in range(3)}
    data["carousel"] = out_cars[0]
    data["carousel_am"] = out_cars[0]
    data["carousel_mid"] = out_cars[1]
    data["carousel_pm"] = out_cars[2]
    return data


days_out = []
date_compact = datetime.date.today().isoformat().replace("-", "")
out_path = f"bookwellnow_facebook_batch_{date_compact}.json"


def save_partial():
    payload = {
        "generated": datetime.date.today().isoformat(),
        "days": DAYS,
        "postsPerDay": 3,
        "channel": "facebook",
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
    print(f"Generating Facebook day {i+1}/{DAYS} {d.isoformat()} {[p[1] for p in plan]}...")
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
    "postsPerDay": 3,
    "channel": "facebook",
    "format": "carousel-only-4slides",
    "start": START.isoformat(),
    "end": (START + datetime.timedelta(days=DAYS - 1)).isoformat(),
    "posts": days_out,
}
json.dump(payload, open(out_path, "w"), indent=2)
print(f"Wrote {out_path} ({DAYS} days, {DAYS*3} Facebook posts)")

log_path = "bookwellnow-facebook-run-log.json"
try:
    log = json.load(open(log_path)) if os.path.exists(log_path) else []
except Exception:
    log = []
log.append({
    "date": datetime.date.today().isoformat(),
    "mode": f"{DAYS}-day-3posts-facebook-features",
    "file": out_path,
    "topics": [p.get("topic") for p in days_out],
    "industries": [ind for p in days_out for ind in (p.get("industries") or [p.get("industry")])],
})
json.dump(log[-80:], open(log_path, "w"), indent=2)
print("Updated bookwellnow-facebook-run-log.json")
