---
name: bookwellnow-facebook
description: Generates and schedules a 10-day BookWellNow Facebook Page batch (3 native feature-intro posts/day) via the Graph API, with utm_source=facebook post on every product link.
---

# BookWellNow Facebook Page — 3 posts/day for 10 days

Native Facebook copy for a **new Page**. Teaches every live plugin feature (free + Pro from bookwellnow.com and WordPress.org 4.0.10), asks people to **Follow / Share / comment their business type**, and ends product captions with:

`https://bookwellnow.com/?utm_source=facebook+post`

Each post is a **4-slide photo album** (Facebook cannot take LinkedIn PDFs).

Company voice: `we` / `our`. LinkedIn stays 2 carousel posts/day with `utm_source=linkedin+post`.

## Cadence (IST, Facebook peaks)

| Day | 1 | 2 | 3 |
|-----|---|---|---|
| Mon–Fri | 11:00 AM | 3:30 PM | 8:00 PM |
| Sat / Sun | 11:00 AM | 4:00 PM | 7:00 PM |

Override: `FACEBOOK_AM_TIME` / `FACEBOOK_MID_TIME` / `FACEBOOK_PM_TIME`.

## Run

```bash
./run_bookwellnow_facebook.sh
DELETE_SCHEDULED=1 python3 schedule_all_facebook_posts.py   # drop old queue, then post the new 30
```

Or:

```bash
python3 generate_bookwellnow_facebook_batch.py
BOOKWELLNOW_BATCH=$(ls bookwellnow_facebook_batch_*.json | sort | tail -1) \
  python3 build_bookwellnow_assets.py
python3 prepare_bookwellnow_facebook_schedule.py
DRY_RUN=1 python3 schedule_all_facebook_posts.py
DELETE_SCHEDULED=1 python3 schedule_all_facebook_posts.py
```

## Outputs

| File | Purpose |
|------|---------|
| `bookwellnow_facebook_batch_YYYYMMDD.json` | 10 days × 3 albums |
| `schedule_bookwellnow_facebook.json` | 30 Graph API posts |
| `carousel-routine/output/.../bookwellnow-fb-day-NN-a..c/` | Slide PNGs |

## Env

| Variable | Purpose |
|----------|---------|
| `FACEBOOK_PAGE_ACCESS_TOKEN` | Required Page token |
| `DELETE_SCHEDULED=1` | Delete unpublished Page posts, then schedule the JSON |
| `DRY_RUN=1` / `POST_NOW=1` / `START_POST_ID` | Same as LinkedIn scheduler |
