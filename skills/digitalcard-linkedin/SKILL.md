---
name: digitalcard-linkedin
description: Generates a 10-day batch of Digital Card Creator company-page LinkedIn posts (1 image + 1 carousel per day) for the digital visiting card app, with niche-specific networking content, Slack review, and schedule JSON.
---

# Digital Card Creator Company LinkedIn — 2 posts/day for 10 days

Generates **1 image post + 1 carousel post per day** for the **Digital Card Creator** company LinkedIn page ([my.digitalcardcreator.com](https://my.digitalcardcreator.com/) / [linkedin.com/company/digitalcardcreator](https://www.linkedin.com/company/digitalcardcreator/)).

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

## Archetype pairs (image + carousel)

| Day | Image | Carousel |
|-----|-------|----------|
| 1 | `PAPER_CARD_PAIN` | `QR_SHARE_CHECKLIST` |
| 2 | `NETWORKING_MOMENT` | `SETUP_STEPS` |
| 3 | `SALES_FOLLOWUP` | `ANALYTICS_STACK` |
| 4 | `AUDIENCE_SPOT` | `BEFORE_AFTER` |
| 5 | `WHATSAPP_CONNECT` | `CLIENT_JOURNEY` |
| 6 | `MYTH_BUST` | `FEATURE_LISTICLE` |
| 7 | `TEAM_BRANDING` | `MISTAKE_FIX` |
| 8 | `EVENT_NETWORKING` | `UPDATE_ANYTIME` |
| 9 | `COST_OF_PRINT` | `WHY_DCC` |
| 10 | `SOFT_CTA` | `LAUNCH_CHECKLIST` |

## Voice

- **We / our / Digital Card Creator team** only
- Product words: digital visiting card, QR, WhatsApp, save to contacts, card views, scans
- CTA rotate: Comment **CARD**, DM us your role, create free at my.digitalcardcreator.com
- No em-dashes; banned hype words in `digitalcard_profile.md`

## Peak times (IST)

Same weekday peaks as BookWellNow / OpenXcode batch: image mid-morning/midday, carousel afternoon.

## Run

```bash
./run_digitalcard_batch.sh
```

Then schedule:

```bash
agent-browser --session linkedin_bot --profile Default open "https://www.linkedin.com/company/135187143/admin/dashboard/"
SCHEDULE_FILE=schedule_digitalcard.json POST_AS="Digital Card Creator" node schedule_all_posts.cjs
```

## Outputs

| File | Purpose |
|------|---------|
| `digitalcard_batch_YYYYMMDD.json` | 10 days of image + carousel content |
| `digitalcard-images/YYYYMMDD/day-NN.png` | Infographic PNGs |
| `carousel-routine/output/.../digitalcard-day-NN/*.pdf` | Carousel PDFs |
| `schedule_digitalcard.json` | 20 scheduled posts with company meta |
| `digitalcard-run-log.json` | Dedup log |
| `digitalcard_profile.md` | Product brief |

## Notes

- Separate from OpenXcode, BookWellNow, and automation-leads streams.
- Brand accent `#536EFD`. CTA keyword **CARD**.
- Batch starts tomorrow for 10 consecutive days.
