---
name: digitalcard-linkedin
description: Generates a 10-day batch of Digital Card Creator company-page LinkedIn posts (2 images + 2 carousels per day) for the digital visiting card app, with niche-specific networking content, Slack review, and schedule JSON.
---

# Digital Card Creator Company LinkedIn — 4 posts/day for 10 days

Generates **2 image posts + 2 carousel posts per day** for the **Digital Card Creator** company LinkedIn page ([my.digitalcardcreator.com](https://my.digitalcardcreator.com/) / [linkedin.com/company/digitalcardcreator](https://www.linkedin.com/company/digitalcardcreator/)).

Posts use **company voice** (`we` / `our`) and aim to get professionals to **create a free digital visiting card** and share via QR / WhatsApp.

Company admin URL: `https://www.linkedin.com/company/135187143/admin/dashboard/`

## Niche rule (strict)

Every post must stay inside the **digital visiting card / professional networking** niche:
- QR share, save to contacts, WhatsApp Connect, card analytics, templates, update-anytime, paper-card replacement
- Audience moments: meetup, property showing, clinic desk, conference, campus event, sales call
- Do **not** drift into generic SaaS, software outsourcing, WordPress booking, or OpenXcode project sales

## Ideal buyer (ICP)

Sales pros, freelancers, real estate agents, business owners / teams, doctors and clinics, lawyers and consultants, event planners, students, influencers and creators.

## Audience rotation (one primary audience per day)

Sales professionals, freelancers, real estate agents, business owners, doctors and clinics, lawyers and consultants, event planners, students, influencers and creators, agency / team leads.

## Cadence (4 posts/day)

| Slot | Type | Typical IST window |
|------|------|--------------------|
| AM image | Infographic | ~10:00–10:30 AM |
| AM carousel | Document PDF | ~12:00–1:00 PM |
| PM image | Infographic | ~3:00–3:30 PM |
| PM carousel | Document PDF | ~5:00–6:00 PM |

Today's past slots are auto-bumped forward when preparing the schedule.

## Quality rules

- Captions: hook + short paragraphs + `- ` bullets + Comment CARD (never one wall of text)
- Every caption ends with web + Play Store URLs
- Images: 4 bars + 4 checklist bullets (dense, catchy)
- Carousel slides: body + 3 bullets each (less empty spacing)
- Prefer question hooks and named networking moments (analytics-proven)

## Voice

- **We / our / Digital Card Creator team** only
- Product words: digital visiting card, QR, WhatsApp, save to contacts, card views, scans
- CTA rotate: Comment **CARD**, DM us your role, create free at my.digitalcardcreator.com + Play Store
- No em-dashes; banned hype words in `digitalcard_profile.md`

## Run

```bash
./run_digitalcard_batch.sh
```

Starts **today** for 10 consecutive days (override with `DIGITALCARD_START=YYYY-MM-DD`).

Then schedule:

```bash
agent-browser --session linkedin_bot --profile Default open "https://www.linkedin.com/company/135187143/admin/dashboard/"
SCHEDULE_FILE=schedule_digitalcard.json POST_AS="Digital Card Creator" node schedule_all_posts.cjs
```

## Outputs

| File | Purpose |
|------|---------|
| `digitalcard_batch_YYYYMMDD.json` | 10 days × 4 posts |
| `digitalcard-images/YYYYMMDD/day-NN-{am,pm}.png` | Infographic PNGs |
| `carousel-routine/output/.../digitalcard-day-NN[-pm]/*.pdf` | Carousel PDFs |
| `schedule_digitalcard.json` | 40 scheduled posts with company meta |
| `digitalcard-run-log.json` | Dedup log |
| `digitalcard_profile.md` | Product brief |

## Notes

- Separate from OpenXcode, BookWellNow, and automation-leads streams.
- Brand accent `#536EFD`. CTA keyword **CARD**.
- Play Store: `https://play.google.com/store/apps/details?id=com.digital_card_creator_app`
