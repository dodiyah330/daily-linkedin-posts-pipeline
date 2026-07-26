---
name: bookwellnow-linkedin
description: Generates a 10-day batch of BookWellNow company-page LinkedIn posts (1 image + 1 carousel per day) for the WordPress appointment booking plugin, with Slack review and a schedule JSON for the LinkedIn company page.
---

# BookWellNow Company LinkedIn — 2 posts/day for 10 days

Generates **1 image post + 1 carousel post per day** for the **BookWellNow company LinkedIn page** ([bookwellnow.com](https://bookwellnow.com) / [linkedin.com/company/bookwellnow](https://www.linkedin.com/company/bookwellnow/)).

Posts use **company voice** (`we` / `our`) and aim to get service business owners and WordPress agencies to **install the free plugin** or **ask for setup help**.

Company admin URL: `https://www.linkedin.com/company/130384348/admin/dashboard/`

## Ideal buyer (ICP)

- Service business owners on WordPress still booking by phone, DM, or WhatsApp
- Owners paying monthly for booking SaaS or a plugin that caps staff, services, or bookings
- WordPress agencies and freelancers building sites for salons, clinics, gyms, and coaches
- Multi-staff businesses needing shifts, breaks, and holidays per staff member
- Coaches and consultants selling online sessions who need automatic Zoom links

## Target industries (one primary industry per day)

Barbershop, beauty and salon, spa and wellness, fitness and gym, yoga studio, personal trainer, tutor and coach, dental and clinic, health and well-being, therapist and counsellor, pet grooming, cleaning service, maintenance and repair, auto detailing, consultant and agency, class and course scheduling, events and workshops, boat and equipment rental, smart queuing walk-ins.

The generator rotates the industry list so a 10-day batch never repeats a niche.

## Archetype pairs (image + carousel per day)

| Day | Image | Carousel |
|-----|-------|----------|
| 1 | `PAIN_NO_SHOW` | `FEATURE_CHECKLIST` |
| 2 | `INDUSTRY_SPOT` | `SETUP_STEPS` |
| 3 | `FREE_VS_PAID` | `WHY_BOOKWELLNOW` |
| 4 | `STAFF_SHIFTS` | `BEFORE_AFTER` |
| 5 | `ZOOM_ONLINE` | `CLIENT_JOURNEY` |
| 6 | `MYTH_BUST` | `PAYMENTS_STACK` |
| 7 | `SPEED_SEO` | `MISTAKE_FIX` |
| 8 | `AGENCY_ANGLE` | `MIGRATION_GUIDE` |
| 9 | `CUSTOMER_PANEL` | `INDUSTRY_LISTICLE` |
| 10 | `SOFT_CTA` | `LAUNCH_CHECKLIST` |

## Voice

- **We / our / BookWellNow team** only (never solo "I")
- Speak to the business owner: bookings, staff, no-shows, revenue — not developer jargon
- Lead with free features: unlimited staff, unlimited services, Zoom, PayPal, shifts, holidays, customer panel
- CTA rotate: Comment **BOOK**, DM us your industry and staff count, download the free version
- No named competitor bashing; contrast with "most booking plugins"
- No em-dashes; banned hype words listed in `bookwellnow_profile.md`
- No OpenXcode / FoundersWing / personal @handles

## Peak times (IST account timezone)

Image posts land mid-morning or midday, carousels in the afternoon:

| Weekday | Image | Carousel |
|---------|-------|----------|
| Mon | 1:00 PM | 4:00 PM |
| Tue | 11:00 AM | 4:00 PM |
| Wed | 12:00 PM | 4:00 PM |
| Thu | 11:00 AM | 4:00 PM |
| Fri | 1:00 PM | 4:00 PM |
| Sat | 11:00 AM | 3:00 PM |
| Sun | 11:00 AM | 3:00 PM |

Weekends are included: booking-business owners browse off-hours.

## Run

```bash
./run_bookwellnow_batch.sh
```

Then schedule on LinkedIn (Chrome profile `Default` is logged in as page admin):

```bash
agent-browser --session linkedin_bot --profile Default open "https://www.linkedin.com/company/130384348/admin/dashboard/"
SCHEDULE_FILE=schedule_bookwellnow.json POST_AS=BookWellNow node schedule_all_posts.cjs
```

Or step by step:

```bash
BOOKWELLNOW_DAYS=10 python3 generate_bookwellnow_batch.py
python3 build_bookwellnow_assets.py
python3 prepare_bookwellnow_schedule.py
```

Overrides:

```bash
BOOKWELLNOW_DAYS=5 ./run_bookwellnow_batch.sh
BOOKWELLNOW_IMAGE_TIME='10:00 AM' BOOKWELLNOW_CAROUSEL_TIME='5:00 PM' python3 prepare_bookwellnow_schedule.py
START_POST_ID=7 SCHEDULE_FILE=schedule_bookwellnow.json POST_AS=BookWellNow node schedule_all_posts.cjs
```

## Outputs

| File | Purpose |
|------|---------|
| `bookwellnow_batch_YYYYMMDD.json` | 10 days of image + carousel content |
| `bookwellnow-images/YYYYMMDD/day-NN.png` | Infographic PNGs |
| `carousel-routine/output/YYYY-MM-DD/bookwellnow-day-NN/*.pdf` | Carousel PDFs |
| `schedule_bookwellnow.json` | 20 scheduled posts with company page meta |
| `bookwellnow-run-log.json` | Dedup log (topics + industries) |
| `bookwellnow_profile.md` | Product brief for the generator |

## Notes

- This stream is **separate** from OpenXcode, FoundersWing, and the automation-leads streams.
- Batch starts **tomorrow** and runs for 10 consecutive days.
- Brand accent is `#5700B4`; carousels and infographics use BookWellNow branding.
- If a carousel caption is cleared by LinkedIn after the PDF upload, `schedule_all_posts.cjs` refills it automatically.
