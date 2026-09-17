---
name: bookwellnow-linkedin
description: Generates a 10-day batch of BookWellNow company-page LinkedIn posts (2 carousels/day, 3-4 slides) for the WordPress appointment booking plugin, with a schedule JSON for the LinkedIn company page.
---

# BookWellNow Company LinkedIn — 2 carousel posts/day for 10 days

Generates **2 carousel posts per day** (3-4 slides each) for the **BookWellNow company LinkedIn page** ([bookwellnow.com](https://bookwellnow.com) / [linkedin.com/company/bookwellnow](https://www.linkedin.com/company/bookwellnow/)).

Posts use **company voice** (`we` / `our`) and aim to get service business owners and WordPress agencies to **install the free plugin**, **comment**, **reshare**, or **ask for setup help**.

Company admin URL: `https://www.linkedin.com/company/130384348/admin/dashboard/`

## Analytics doctrine (from page export Aug 1-30 2026)

Hiring still carries comments and reach. Four hiring posts = 1,373 impressions and 7 comments vs 122 product posts = 2,103 impressions and 5 comments. The Aug 19 **4-carousel days averaged 12 product impressions**. Two stronger posts beat four thin ones.

Product that still worked:

- Dental mistake-fix and site-speed (the only product comments)
- Pet-grooming agency-builder
- Physio reschedule / missed appointments (highest product CTR)
- Veterinary operations
- WordPress agency go-live checklist (the only August product comment)
- Beauty "If you are building a website for…"

Skip yoga filler, tutor Zoom questions, and thin "are you ready" hooks. Named industry + a concrete loss (empty chair, 3-second bounce, per-seat fee).

Each day uses **two different industries**. Two hiring carousels sit in the 10-day mix (WordPress Developer + SEO Executive).

## Voice

- **We / our / BookWellNow team** only (never solo "I")
- Speak to the business owner: bookings, staff, no-shows, revenue
- Named industry in the first 8 words of every product caption
- Dual CTA: Comment **BOOK** + a one-line debate question + "Repost if you know a [industry] still on WhatsApp"
- No named competitor bashing; contrast with "most booking plugins"
- No em-dashes; banned hype words listed in `bookwellnow_profile.md`

## Peak times (IST)

| Weekday | 1 | 2 |
|---------|---|---|
| Mon / Wed / Fri | 10:30 AM | 3:30 PM |
| Tue / Thu | 10:00 AM | 3:00 PM |
| Sat / Sun | 10:00 AM | 3:00 PM |

## Run

```bash
BOOKWELLNOW_START=YYYY-MM-DD ./run_bookwellnow_batch.sh
```

Same batch can also go to Facebook: `skills/bookwellnow-facebook/SKILL.md` / `./run_bookwellnow_facebook.sh`.

Then schedule on LinkedIn (Chrome profile `Default` is logged in as page admin):

```bash
agent-browser --session linkedin_bot --profile Default open "https://www.linkedin.com/company/130384348/admin/dashboard/"
SCHEDULE_FILE=schedule_bookwellnow.json POST_AS=BookWellNow FORCE_GENERAL_BATCH=1 node schedule_all_posts.cjs
```

Or step by step:

```bash
BOOKWELLNOW_DAYS=10 BOOKWELLNOW_START=YYYY-MM-DD python3 generate_bookwellnow_batch.py
python3 build_bookwellnow_assets.py
python3 prepare_bookwellnow_schedule.py
```

## Outputs

| File | Purpose |
|------|---------|
| `bookwellnow_batch_YYYYMMDD.json` | 10 days of 2 carousels |
| `carousel-routine/output/YYYY-MM-DD/bookwellnow-day-NN-a..b/*.pdf` | Carousel PDFs (4 slides) |
| `schedule_bookwellnow.json` | 20 scheduled posts with company page meta |
| `bookwellnow-run-log.json` | Dedup log |
| `bookwellnow_profile.md` | Product brief for the generator |

## Notes

- This stream is **separate** from OpenXcode and the automation-leads streams.
- Batch starts **tomorrow** unless `BOOKWELLNOW_START` is set.
- Brand accent is `#5700B4`. Slide layouts rotate: color-block hook, numbered list, 2×2 cards, before/after split, dark CTA.
- If a carousel caption is cleared by LinkedIn after the PDF upload, `schedule_all_posts.cjs` refills it automatically.
