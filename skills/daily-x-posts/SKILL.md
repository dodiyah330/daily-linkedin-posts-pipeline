---
name: daily-x-posts
description: Generates a short daily batch of personal X (Twitter) posts (text + optional image), writes x_posts_YYYYMMDD.txt, optionally sends to Slack, builds schedule_x.json, and schedules via native X Schedule UI (agent-browser + schedule_all_x_posts.cjs). Use when the user wants X/Twitter posts scheduled like LinkedIn.
---

# Daily X (Twitter) Posts → Schedule

Generate a compact personal X batch, review in Slack (optional), then queue into X’s native Schedule UI — same browser pattern as LinkedIn.

**Hard limits**
- Native Schedule needs **X Premium** on desktop web. Without it use `POST_NOW=1`.
- Types: **text** and **image** (1–4 images = X swipe gallery). No LinkedIn PDF document carousels, no polls, no native scheduled threads.
- Soft cap **280 chars** unless `X_MAX_CHARS` is raised for Premium long-form.
- Voice: personal **"I"-led**, punchy, conversational (Twitter voice, not LinkedIn brand voice).
- **No dash punctuation in captions:** never write `—`, `–`, or `--`. Use a comma, period, or new line. `prepare_x_schedule.py` and the scheduler scrub these automatically.

Repo root = working directory for all commands below.

---

## STEP 0 — Doctrine + voice

```bash
cat ./content-doctrine.md 2>/dev/null
cat ./voice-profile.md 2>/dev/null
```

If present, `content-doctrine.md` still governs **topic** (Reach, Stakes, Altitude, Edge: AI’s impact on work/income/skills/future). Drop LinkedIn CTAs (“Follow me”, “Save this”, “Comment BUILD”). Prefer hooks, one clear take, optional question. Never use `—` / `--` in captions. No hype words (game-changer, revolutionary, groundbreaking, etc.).

---

## STEP 1 — Fetch fresh AI news (reuse shared fetcher)

```bash
python3 fetch_ai_news_rss.py
```

Optional research: ScrapingDog X search or WebSearch for today’s biggest AI stories (same sources as `skills/linkedin-ai-news-engine`). Prefer stories that pass the doctrine filter.

---

## STEP 2 — Write today’s X batch

Produce **1 post per day** (default) for the next calendar week at **6:00 PM IST ≈ 8:30 AM US Eastern** (account timezone is IST).

| Slot | Archetype | Notes |
|------|-----------|-------|
| 1 | **Hook / hot take** | One sharp claim + why it matters |
| 2 | **Image or gallery** | Short caption + 1 PNG, or up to **4 slide PNGs** (X swipe) |
| 3 | **Plain-English news** | What dropped + what it means for a normal career |
| 4 | **Steal-this / question** | One portable idea or closing question |

Rules:
- Each post ≤ `X_MAX_CHARS` (default 280). Prefer 120–220.
- No LinkedIn poll formats. No PDF uploads.
- Distinct subjects (no two posts on the same tool/story).
- **Carousel on X:** no PDF document carousel. Closest option is **up to 4 PNG/JPG slides** in one post (`IMAGES:` / `assetPaths`). Export LinkedIn carousel slides as PNGs under `carousel-routine/output/…` when possible.
- Image post: reuse today’s LinkedIn infographic PNG if it exists, else ship text-only for that slot.
- Captions must not contain `—` or `--`.

Write:

```
./x_posts_YYYYMMDD.txt
```

Format (must match `prepare_x_schedule.py`):

```
==================================================
1. HOOK
==================================================
Your post text here. Use commas, not dashes.

==================================================
2. WITH IMAGE
==================================================
IMAGE: path/to/image.png
CAPTION:
Caption under the image.

==================================================
3. GALLERY (optional carousel-style)
==================================================
IMAGES: slide1.png | slide2.png | slide3.png | slide4.png
CAPTION:
Swipe through these four frames.

==================================================
4. CLOSE
==================================================
…
```

---

## STEP 3 — Build schedule JSON

```bash
python3 prepare_x_schedule.py
# Optional overrides:
# START_DATE=2026-08-01 X_MAX_CHARS=280 X_TIMES="9:00 AM,12:00 PM,3:00 PM,6:00 PM"
```

Confirms `schedule_x.json` with `type` `text` | `image`, `date` `MM/DD/YYYY`, `time`, `caption`, optional `assetPath` or `assetPaths` (up to 4).

---

## STEP 4 — Slack review (optional but preferred)

```bash
python3 send_x_to_slack.py
```

Sends each post as a separate message to `SLACK_CHANNEL_ID` from `.env`. Wait for user OK before scheduling if they asked for review.

---

## STEP 5 — Schedule on X

```bash
/opt/homebrew/bin/agent-browser --session x_bot --profile Default open https://x.com/home
# Confirm logged-in home feed (SideNav Post button visible).

SCHEDULE_FILE=schedule_x.json node schedule_all_x_posts.cjs
```

Resume / post-now:

```bash
START_POST_ID=3 SCHEDULE_FILE=schedule_x.json node schedule_all_x_posts.cjs
POST_NOW=1 SCHEDULE_FILE=schedule_x.json node schedule_all_x_posts.cjs
```

Screenshots land under `slack_downloads/x_post_*`. Errors → `error_x_screenshot.png`.

**Preflight**
- `puppeteer-core` resolvable (install under repo or `carousel-routine/` and run with `NODE_PATH=…` if needed)
- X Premium for Schedule calendar icon
- Dates/times must be in the future in the account timezone

---

## Adapt from LinkedIn (fast path)

If today’s LinkedIn batch already exists and the user only wants X scheduling:

```bash
python3 prepare_x_schedule.py
# or: SCHEDULE_SOURCE=schedule_today.json python3 prepare_x_schedule.py
python3 send_x_to_slack.py   # optional
SCHEDULE_FILE=schedule_x.json node schedule_all_x_posts.cjs
```

`prepare_x_schedule.py` truncates captions, keeps PNG infographics, drops polls, turns carousel PDFs into text-only.

---

## Done checklist

```
✓ x_posts_YYYYMMDD.txt written (or LinkedIn source adapted)
✓ schedule_x.json built
✓ Slack review sent (if requested)
✓ agent-browser on x.com/home, logged in
✓ schedule_all_x_posts.cjs finished without errors
```
