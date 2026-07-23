# Daily LinkedIn Posts Pipeline

Multi-stream automation for LinkedIn content, outreach, and Freelancer.com bidding. One repo drives several independent pipelines that share data fetchers, LLM keys, Slack delivery, and a Puppeteer-based LinkedIn scheduler.

| Stream | Audience / page | Cadence | Entry script |
|--------|-----------------|---------|--------------|
| **FoundersWing daily** | Personal brand (`@founderswing`) | Reddit + AI news + performance posts → Slack → schedule | Agent skill: `daily-linkedin-posts/SKILL.md` |
| **OpenXcode batch** | Company page ([OpenXcode](https://www.linkedin.com/company/open-xcode)) | Default **10 days × 2 posts/day** (image + carousel) | `./run_openxcode_batch.sh` |
| **Automation leads** | Personal profile (AI automation ICP) | **14 posts/week** (image + text each day) | `./run_automation_leads.sh` |
| **US image posts** | Personal profile, US Eastern peak | Daily US-angled infographic | `./run_us_image_posts.sh` |
| **US connections** | LinkedIn search → invites (no notes) | Until weekly limit | `./run_us_connections.sh` |
| **Connection DMs** | 1st-degree connections outside India | Caps per run/day | `./run_connection_dms.sh` |
| **Freelancer bid bot** | Freelancer.com projects | Poll + AI proposal + bid | `freelancer-bid-bot/bid_bot.py` |

---

## Prerequisites

### Software
- **Node.js** ≥ 18 (Puppeteer scripts, carousel render, LinkedIn automation)
- **Python** 3.10+ (fetch, generation, Slack, Freelancer bot)
- **[agent-browser](https://github.com/vercel-labs/agent-browser)** CLI (Chrome session for LinkedIn)
- Chromium via `puppeteer` / `puppeteer-core` (repo root `node_modules` + `carousel-routine/`)

### Install
```bash
# Carousel / PDF renderer
cd carousel-routine && npm install && cd ..

# Freelancer bid bot (optional)
python3 -m venv freelancer-bid-bot/.venv
source freelancer-bid-bot/.venv/bin/activate
pip install -r freelancer-bid-bot/requirements.txt
```

### Environment (`.env` at repo root)

```bash
# LLM
OPENROUTER_API_KEY=...
GEMINI_API_KEY=...          # preferred for OpenXcode batch + bid bot
ANTHROPIC_TOKEN=...         # optional alternate

# Slack
SLACK_BOT_TOKEN=...
SLACK_CHANNEL_ID=...        # e.g. C0AVBBTD529 / C0BEG7HAXHQ

# Data fetch
APIFY_API_KEY=...           # Reddit scraper
SCRAPINGDOG_API_KEY=...     # optional X/Twitter research

# Freelancer.com bid bot
FLN_OAUTH_TOKEN=...

# Optional LinkedIn login helpers (prefer agent-browser session)
LINKEDIN_EMAIL=...
LINKEDIN_PASSWORD=...
```

**How to get every key (step by step):** see [`docs/API_KEYS.md`](docs/API_KEYS.md).

Never commit `.env`. Runtime logs, caches, and venvs are gitignored.

---

## Shared architecture

```
Fetch (Reddit / AI news RSS)
        │
        ▼
Generate (Gemini / OpenRouter / agent skills)
        │
        ├── Visuals: HTML → PNG / carousel PDF (carousel-routine)
        ├── Slack review upload
        └── schedule_*.json
                │
                ▼
agent-browser (logged-in Chrome)
                │
                ▼
SCHEDULE_FILE=... [POST_AS=OpenXCode] node schedule_all_posts.cjs
```

**LinkedIn session (required before any schedule / invite / DM script):**
```bash
agent-browser --session linkedin_bot --profile Default open https://www.linkedin.com/feed/
# Company page (OpenXcode):
agent-browser --session linkedin_bot --profile Default open \
  "https://www.linkedin.com/company/108839748/admin/dashboard/"
```

**Scheduler env vars:**

| Variable | Purpose |
|----------|---------|
| `SCHEDULE_FILE` | Path to schedule JSON (required for non-default batches) |
| `POST_AS` | e.g. `OpenXCode` to post as company page |
| `LINKEDIN_START_URL` | Override start URL (personal feed vs company admin) |
| `START_POST_ID` | Resume from a given post id |
| `FORCE_GENERAL_BATCH=1` | Override general-batch pause guard |

---

## 1. FoundersWing daily content

Agent-orchestrated batch for the FoundersWing personal brand. Follow:

- `daily-linkedin-posts/SKILL.md` — master steps
- `commands/linkedin-content.md` — Reddit post rules
- `skills/linkedin-ai-news-engine/SKILL.md` — 7 AI-news archetypes
- `skills/linkedin-performance-engine/SKILL.md` — 5 report-driven posts
- `skills/branded-carousel/SKILL.md` + `FORMATS.md` — carousel system
- `skills/illustration-formats/SKILL.md` — infographic formats

### Typical flow
```bash
# Data
python3 fetch_reddit_apify.py    # or fetch_reddit_fallback.py / fetch_reddit_rss.py
python3 fetch_ai_news_rss.py

# Content + visuals are produced via the skill (agent) or helper scripts:
# generate_posts_via_openrouter.py, generate_ai_news.py, generate_branded_carousel.py,
# build_carousel_today.cjs, carousel-routine/screenshot_all.js + compile_pdf.js,
# cap_infographic_today.cjs

python3 send_to_slack.py
node schedule_all_posts.cjs      # uses schedule_today.json by default
```

Outputs land as `linkedin_posts_YYYYMMDD.txt`, carousel PDF under `carousel-routine/output/`, and infographic PNGs at repo root / dated folders. Sample artifacts: `sample-outputs/`.

---

## 2. OpenXcode company page

**Preferred path (multi-day visuals):** 10 days starting tomorrow, **2 posts/day** — morning image + afternoon carousel PDF.

```bash
./run_openxcode_batch.sh
# Override length:
OPENXCODE_DAYS=7 ./run_openxcode_batch.sh
```

Pipeline steps:
1. `fetch_ai_news_rss.py`
2. `generate_openxcode_batch.py` → `openxcode_batch_YYYYMMDD.json`
3. `build_openxcode_assets.py` → `openxcode-images/<date>/` + carousel PDFs
4. `prepare_openxcode_schedule.py` → `schedule_openxcode.json`
5. Slack summary (inline in the shell script)

Schedule:
```bash
agent-browser --session linkedin_bot --profile Default open \
  "https://www.linkedin.com/company/108839748/admin/dashboard/"
SCHEDULE_FILE=schedule_openxcode.json POST_AS=OpenXCode node schedule_all_posts.cjs
```

Time overrides (LinkedIn account timezone):
```bash
OPENXCODE_IMAGE_TIME='11:00 AM' OPENXCODE_CAROUSEL_TIME='4:00 PM' \
  python3 prepare_openxcode_schedule.py
```

**Legacy single text post/day:** `./run_openxcode_posts.sh` (`generate_openxcode_posts.py`). Company brief: `openxcode_profile.md`. Skill: `skills/openxcode-linkedin/SKILL.md`. Dedup log: `openxcode-run-log.json`.

---

## 3. Automation leads (personal)

14 posts for the next Mon–Sun: **1 image + 1 text per day**, first-person voice, lead CTAs (`AUTO` / DM / audit). Profile: `automation_profile.md`. Skill: `skills/automation-leads-engine/SKILL.md`.

```bash
./run_automation_leads.sh

# Then schedule on personal profile:
agent-browser --session linkedin_bot --profile Default open https://www.linkedin.com/feed/
LINKEDIN_START_URL='https://www.linkedin.com/feed/' \
  SCHEDULE_FILE=schedule_automation_leads.json \
  node schedule_all_posts.cjs
```

Force week start: `START_DATE=2026-07-20 python3 prepare_automation_schedule.py`.

---

## 4. US image posts

US-angled daily infographics at Eastern peak (default schedule note: ~6:00 PM IST / 8:30 AM ET).

```bash
./run_us_image_posts.sh
SCHEDULE_FILE=schedule_us_image_posts.json node schedule_all_posts.cjs
```

---

## 5. US connection requests

Searches LinkedIn for US SaaS/ops ICP and sends **invites without notes**. Skill: `skills/us-connections/SKILL.md`.

```bash
agent-browser --session linkedin_bot open https://www.linkedin.com/feed/
./run_us_connections.sh
DRY_RUN=1 ./run_us_connections.sh
```

| Env | Default (via shell) | Purpose |
|-----|---------------------|---------|
| `RUN_UNTIL_WEEKLY_LIMIT` | `1` | Keep going until LinkedIn weekly cap |
| `MAX_CONNECTIONS_PER_RUN` / `_DAY` | high when weekly mode | Soft caps |
| `CONNECTION_DELAY_MS` | `10000`–`12000` | Pause between invites |
| `CONNECTION_SEARCH_QUERIES` | built-in SaaS/ops list | Pipe-separated queries |

Logs: `connections-run-log.json`, `searched-prospects-cache.json`. Slack report: `send_connections_to_slack.py`.

---

## 6. Connection DMs (non-India)

Messages 1st-degree connections in major markets **outside India**. Templates: `connection_dm_templates.json` (`hook` | `founder` | `ops` | `short`).

```bash
agent-browser --session linkedin_bot open https://www.linkedin.com/feed/
./run_connection_dms.sh
DRY_RUN=1 MAX_DMS_PER_RUN=5 ./run_connection_dms.sh

# Prefer when invite bots may fight for the same browser session:
./run_connection_dms_guarded.sh
```

| Env | Default | Purpose |
|-----|---------|---------|
| `MAX_DMS_PER_RUN` | `10` | Cap per run |
| `MAX_DMS_PER_DAY` | `20` | Cap per calendar day |
| `DM_DELAY_MS` | `18000` | Pause between sends |
| `DM_VARIANT` | `hook` | Template key |
| `DM_USE_CACHE` | `1` (guarded) | Reuse target cache |

Logs: `connection-dms-run-log.json`, `connection-dms-targets-cache.json`.

---

## 7. Freelancer.com bid bot

Polls new projects, writes proposals with Gemini (or OpenRouter), bids near budget midpoint. Config: `freelancer-bid-bot/config.json`. Portfolio picks: `freelancer-bid-bot/portfolio_projects.json`.

```bash
cd freelancer-bid-bot
# Dry / one cycle:
python3 bid_bot.py --once --dry-run

# Live continuous poll (respects config dry_run / --live):
python3 bid_bot.py --live
```

Requires `FLN_OAUTH_TOKEN` plus `GEMINI_API_KEY` or `OPENROUTER_API_KEY` in repo-root `.env`. State file `bid_state.json` is gitignored.

---

## Skill index

| Path | Role |
|------|------|
| `daily-linkedin-posts/SKILL.md` | FoundersWing daily orchestration |
| `commands/linkedin-content.md` | Reddit post writing rules |
| `skills/linkedin-ai-news-engine/SKILL.md` | AI news text posts |
| `skills/linkedin-performance-engine/SKILL.md` | Analytics-modeled posts |
| `skills/branded-carousel/SKILL.md` | Carousel design system |
| `skills/branded-carousel/FORMATS.md` | Carousel format templates |
| `skills/illustration-formats/SKILL.md` | Infographic formats |
| `skills/openxcode-linkedin/SKILL.md` | OpenXcode company posts |
| `skills/automation-leads-engine/SKILL.md` | Automation lead-gen week |
| `skills/us-connections/SKILL.md` | US connection outreach |

Profiles: `openxcode_profile.md`, `automation_profile.md`.

---

## Key scripts by role

### Data
| Script | Purpose |
|--------|---------|
| `fetch_reddit_apify.py` | Reddit via Apify (primary) |
| `fetch_reddit_fallback.py` / `fetch_reddit_rss.py` / `fetch_reddit_puppeteer.cjs` | Fallbacks |
| `fetch_ai_news_rss.py` | AI newsletter / blog RSS → `ai_news_data.json` |

### Generate & build
| Script | Purpose |
|--------|---------|
| `generate_posts_via_openrouter.py` / `generate_posts_via_anthropic.py` | Reddit-based posts |
| `generate_ai_news.py` | AI news posts |
| `generate_openxcode_batch.py` / `build_openxcode_assets.py` | OpenXcode 10-day visuals |
| `generate_openxcode_posts.py` / `generate_openxcode_week.py` | OpenXcode text (legacy / week) |
| `generate_automation_leads.py` / `build_automation_images.py` | Automation week |
| `generate_us_image_posts.py` / `build_us_image_posts.py` | US image stream |
| `prepare_*_schedule.py` | Build schedule JSON for each stream |
| `carousel-routine/screenshot_all.js` / `compile_pdf.js` / `render.js` | Slide PNG + PDF |

### Deliver & schedule
| Script | Purpose |
|--------|---------|
| `send_to_slack.py` / `send_*_to_slack.py` | Slack review delivery |
| `schedule_all_posts.cjs` | Universal LinkedIn scheduler |
| `verify_scheduled_posts.cjs` / `edit_scheduled_posts.cjs` / `delete_all_scheduled.cjs` | Schedule maintenance |
| `send_connections.cjs` / `send_connection_dms.cjs` | Outreach |

### Shell runners
| Script | Pipeline |
|--------|----------|
| `run_openxcode_batch.sh` | OpenXcode multi-day image + carousel |
| `run_openxcode_posts.sh` | OpenXcode single text post |
| `run_automation_leads.sh` | Automation leads week |
| `run_us_image_posts.sh` | US image posts |
| `run_us_connections.sh` | US connection invites |
| `run_connection_dms.sh` | Connection DMs |
| `run_connection_dms_guarded.sh` | DMs + browser lock / invite-bot watchdog |

---

## Important data / log files

| File | Purpose |
|------|---------|
| `reddit_data.json` / `ai_news_data.json` | Latest fetched source content |
| `schedule_today.json` | FoundersWing schedule payload |
| `schedule_openxcode.json` | OpenXcode schedule |
| `schedule_automation_leads.json` | Automation leads schedule |
| `schedule_us_image_posts.json` | US image schedule |
| `openxcode_batch_*.json` | Generated OpenXcode multi-day content |
| `openxcode-run-log.json` | OpenXcode topic / archetype dedup |
| `automation-leads-run-log.json` | Automation run history |
| `connections-run-log.json` | Connection invite results |
| `connection-dms-run-log.json` | DM send results |
| `searched-prospects-cache.json` | Connection search dedup |
| `connection-dms-targets-cache.json` | DM target cache |
| `connection_dm_templates.json` | DM copy variants |
| `freelancer-bid-bot/bid_state.json` | Bid bot state (local only) |

---

## Compliance notes

- LinkedIn rate-limits and may restrict accounts for bulk invites or messaging. Prefer low caps (`MAX_CONNECTIONS_PER_RUN=5`, `MAX_DMS_PER_RUN=5`) when testing; use `DRY_RUN=1` first.
- Freelancer bids: keep `dry_run` / `--dry-run` until proposal quality looks right, then `--live`.
- Do not commit secrets, OAuth tokens, or live bid/session state.

---

## Sample outputs

`sample-outputs/` includes a FoundersWing run snapshot (posts text, carousel HTML/PDF, infographic PNG) from 2026-06-12.
