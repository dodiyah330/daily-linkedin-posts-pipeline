# Daily LinkedIn Posts Pipeline

> Complete automation system for generating, building, and scheduling LinkedIn content for Founders Wing: 16 posts per day (4 Reddit-based + 7 AI news + 5 report-driven performance posts) with carousel PDFs, infographic PNGs, and Slack delivery.

> **Content positioning — the "Varun Mayya of LinkedIn."** As of 2026-06-14, every stream is governed by [`content-doctrine.md`](content-doctrine.md): we write for ambitious generalists who want to know where AI is going and how to get ahead, framed around AI's impact on work, income, skills, and the future. Technical tutorials, indie-hacker tactics, and tool how-tos are out (they underperform); future-of-work, opportunity, and accessible explainers are in. FounderWing stays the brand. The doctrine overrides older topic guidance in any skill file.

---

## Prerequisites

### Software
- **Node.js** ≥ 18 (for Puppeteer scripts and carousel rendering)
- **Python 3.10+** (for data fetching and LLM generation)
- **agent-browser** CLI (for LinkedIn scheduling via browser automation)
- **puppeteer-core** npm package (global or in `carousel-routine/`)

### API Keys (stored in `.env`)
```
OPENROUTER_API_KEY=...      # For LLM post generation
ANTHROPIC_API_KEY=...       # Alternative LLM provider
SLACK_BOT_TOKEN=...         # For Slack delivery
SLACK_CHANNEL_ID=...        # Target Slack channel
SCRAPINGDOG_API_KEY=...     # Optional: for X/Twitter research
```

### NPM Dependencies
```bash
cd carousel-routine && npm install
```

---

## Pipeline Overview (16 posts = 4 Reddit + 7 AI News + 5 Performance)

```
┌─────────────────────────────────────────────────────┐
│  PHASE 1: DATA FETCHING                              │
│  ├── Reddit: 6 subreddits via RSS/JSON/Apify         │
│  ├── AI News: 9 sources (newsletters, blogs, PH)     │
│  └── Infographic dataset: 1 fresh dataset via search  │
├─────────────────────────────────────────────────────┤
│  PHASE 2: CONTENT GENERATION (via LLM)               │
│  ├── 4 Reddit posts: Collab Article, Poll, Carousel,  │
│  │   Infographic                                      │
│  ├── 7 AI News posts: 7 archetypes                    │
│  └── 5 Performance posts: report-driven winners       │
├─────────────────────────────────────────────────────┤
│  PHASE 3: VISUAL ASSET CREATION                      │
│  ├── Carousel: 7 slides → PNG → PDF                  │
│  └── Infographic: HTML → PNG screenshot               │
├─────────────────────────────────────────────────────┤
│  PHASE 4: SLACK DELIVERY                             │
│  ├── All 11 post texts to Slack                       │
│  ├── Carousel PDF upload                              │
│  └── Infographic PNG upload                           │
├─────────────────────────────────────────────────────┤
│  PHASE 5: LINKEDIN SCHEDULING                        │
│  ├── Launch agent-browser with LinkedIn session       │
│  ├── Run schedule_all_posts.cjs                       │
│  └── 11 posts → 3 days × 4 posts/day                 │
└─────────────────────────────────────────────────────┘
```

---

## File Reference

### 🧠 Skill Instructions (the brain)
| File | Purpose |
|------|---------|
| `content-doctrine.md` | **North star** — the "Varun Mayya of LinkedIn" positioning, broadened audience, topic filter, and DROP/AMPLIFY lists that govern every stream |
| `daily-linkedin-posts/SKILL.md` | Master orchestration skill — the full pipeline steps |
| `commands/linkedin-content.md` | Reddit post writing rules, output format, banned words |
| `skills/linkedin-ai-news-engine/SKILL.md` | AI news engine — 7 archetype post generation |
| `skills/linkedin-performance-engine/SKILL.md` | Performance engine — 5 posts modeled on @founderswing's own analytics |
| `founderswing_linkedin_content_report.md` | Live LinkedIn analytics report — the performance engine reads this each run; drop in an updated report to refresh the winning patterns |
| `skills/branded-carousel/SKILL.md` | Carousel design system, slide layouts, brand research |
| `skills/branded-carousel/FORMATS.md` | 6 carousel format templates (Brand Story, Listicle, etc.) |
| `skills/illustration-formats/SKILL.md` | 5 infographic formats (Ranked Bars, Donut, Timeline, etc.) |
| `voice-profile.md` | Prithal's writing voice, tone, banned words |

### 📡 Data Fetching Scripts
| File | Purpose |
|------|---------|
| `fetch_reddit_apify.py` | Primary: Fetch Reddit via Apify API (paid, most reliable) |
| `fetch_reddit_fallback.py` | Fallback: Fetch Reddit JSON endpoints directly |
| `fetch_reddit_rss.py` | Last resort: Fetch Reddit RSS feeds (no engagement metrics) |
| `fetch_reddit_puppeteer.cjs` | Browser-based Reddit fetch (bypasses rate limits) |
| `fetch_ai_news_rss.py` | Fetch AI news from newsletter RSS feeds |

### ✍️ Content Generation Scripts
| File | Purpose |
|------|---------|
| `generate_posts_via_openrouter.py` | Generate 4 Reddit-based posts via OpenRouter/Claude API |
| `generate_posts_via_anthropic.py` | Alternative: Generate posts via Anthropic API directly |
| `generate_ai_news.py` | Generate 7 AI news posts |
| `generate_ai_news_part2.py` | Continuation script for AI news generation |
| `write_today_data.py` | Master script: combines all posts into daily output file |
| `correct_posts.py` | Post-processing: fix formatting, remove banned words |

### 🎨 Carousel Generation
| File | Purpose |
|------|---------|
| `generate_branded_carousel.py` | Generate carousel slide content from LLM |
| `generate_carousel_today.py` | Today's carousel generation with brand research |
| `generate_carousel_run.py` | Carousel run orchestrator |
| `build_carousel_today.cjs` | Build carousel HTML slides from content |
| `build_carousel_core.cjs` | Core carousel HTML builder |
| `carousel-routine/render.js` | Puppeteer: screenshot each slide to PNG |
| `carousel-routine/render-pdf.js` | Puppeteer: render slides directly to PDF |
| `carousel-routine/compile_pdf.js` | Combine slide PNGs into single PDF |
| `carousel-routine/screenshot_all.js` | Screenshot all 7 slide HTML files |
| `carousel-routine/brand-kit.html` | Founders Wing brand design system HTML |
| `carousel-routine/package.json` | Node dependencies (puppeteer, pdf-lib) |

### 📊 Infographic Generation
| File | Purpose |
|------|---------|
| `generate_infographic_today.py` | Generate infographic HTML from dataset |
| `linkedin-infographic-template.html` | Base HTML template for infographics |
| `linkedin-infographic.html` | Latest generated infographic HTML |
| `cap_infographic_today.cjs` | Screenshot infographic HTML → 1080×1080 PNG |
| `cap_infographic.cjs` | Alternative screenshot script |

### 📨 Slack Delivery
| File | Purpose |
|------|---------|
| `send_to_slack.py` | Master Slack delivery: texts + PDF + PNG |
| `send_slack_message.py` | Simple text message to Slack |
| `check_slack_for_posts.py` | Check Slack for previously sent posts |

### 📅 LinkedIn Scheduling
| File | Purpose |
|------|---------|
| `schedule_all_posts.cjs` | Schedule ALL 11 posts (4/day × 3 days) |
| `schedule_four_posts.cjs` | Schedule 4 Reddit-based posts only |
| `schedule_other_posts.cjs` | Schedule remaining AI news posts |
| `delete_all_scheduled.cjs` | Delete all scheduled posts |
| `edit_scheduled_posts.cjs` | Edit existing scheduled posts |
| `verify_scheduled_posts.cjs` | Verify scheduled posts are correct |
| `get_scheduled_contents.cjs` | Extract content from scheduled posts |

### 📋 State & Log Files
| File | Purpose |
|------|---------|
| `carousel-hook-log.json` | History of carousel hook styles (for rotation) |
| `infographic-run-log.json` | History of infographic topics (for deduplication) |
| `performance-run-log.json` | History of performance-engine subjects (contrarian belief, poll, etc.) so they don't repeat day to day |
| `scheduled_history.json` | History of scheduled posts |
| `reddit_data.json` | Latest fetched Reddit data |
| `ai_news_data.json` | Latest fetched AI news data |

---

## How to Run (Step by Step)

### Phase 1: Fetch Data
```bash
# Try Apify first (most reliable, requires API key)
python3 fetch_reddit_apify.py

# If Apify fails, try JSON endpoints
python3 fetch_reddit_fallback.py

# If JSON blocked (403/429), fall back to RSS
python3 fetch_reddit_rss.py
```

### Phase 2: Generate Content
The content generation is handled by the AI agent (Antigravity/Claude) following the skill instructions in:
- `commands/linkedin-content.md` → 4 Reddit posts
- `skills/linkedin-ai-news-engine/SKILL.md` → 7 AI news posts

The agent reads `reddit_data.json`, selects topics, and writes all 11 posts following the voice profile and writing rules.

Output: `linkedin_posts_YYYYMMDD.txt`

### Phase 3: Build Visual Assets

**Carousel:**
```bash
# 1. Agent generates slide HTML files in carousel-routine/temp/
# 2. Screenshot slides to PNG
cd carousel-routine && node screenshot_all.js
# 3. Compile PNGs to PDF
node compile_pdf.js
```

**Infographic:**
```bash
# 1. Agent generates linkedin-infographic.html
# 2. Screenshot to 1080×1080 PNG
node cap_infographic_today.cjs
```

### Phase 4: Send to Slack
```bash
python3 send_to_slack.py
```

### Phase 5: Schedule on LinkedIn
```bash
# 1. Launch browser with LinkedIn session
agent-browser --session-name linkedin_bot open https://www.linkedin.com/feed/

# 2. Run the scheduling script (schedules all 11 posts)
node schedule_all_posts.cjs
```

---

## Post Schedule (4 posts/day × 3 days)

| Day | Time (IST) | Post Type | Content Source |
|-----|-----------|-----------|---------------|
| Day 1 | 9:00 AM | 🎠 Carousel (PDF) | Reddit |
| Day 1 | 12:00 PM | 📊 Infographic (PNG) | Reddit + Data |
| Day 1 | 3:00 PM | 📝 Collaborative Article | Reddit |
| Day 1 | 6:00 PM | 📊 Poll | Reddit |
| Day 2 | 9:00 AM | ✍️ Tool Spotlight | AI News |
| Day 2 | 12:00 PM | ✍️ Weekly Roundup | AI News |
| Day 2 | 3:00 PM | ✍️ Plain English Breakdown | AI News |
| Day 2 | 6:00 PM | ✍️ Unfair Advantage | AI News |
| Day 3 | 9:00 AM | ✍️ Career/Income Angle | AI News |
| Day 3 | 12:00 PM | ✍️ Hot Take | AI News |
| Day 3 | 3:00 PM | ✍️ Steal This | AI News |

> **Note:** The 5 report-driven performance posts (STEP 7) are **delivered to Slack for review/manual posting but are not yet wired into the LinkedIn auto-scheduler.** Scheduling them automatically is a separate task. See the cadence caveat below.

### ⚠️ Cadence caveat (from the analytics report)

The `founderswing_linkedin_content_report.md` is explicit that the account's current ~25-35 posts/week is **suppressing reach** and recommends **≤7 posts/week**. This pipeline produces 16 posts/day, which runs against that finding. The performance posts were added per an explicit "add on top" decision; the volume-reduction recommendation is intentionally **deferred, not resolved.** Revisit whether to cut overall cadence before scaling output further.

---

## Deduplication Rules

- **Carousel hooks**: Read `carousel-hook-log.json` before picking a style. Last used style is banned. Any style with 3+ uses in last 7 entries is also banned.
- **Infographic topics**: Read `infographic-run-log.json`. Never repeat a topic from the last 30 days.
- **Post topics**: No two posts in the same batch can cover the same Reddit thread or story.
- **Performance posts**: Read `performance-run-log.json` before writing. The contrarian belief and poll topic from the last 14 runs are banned. All 5 performance subjects must be distinct from each other and from the day's other 11 posts (16 unique subjects total).

---

## Sample Outputs

The `sample-outputs/` folder contains a complete set from the June 12, 2026 run:
- `linkedin_posts_20260612.txt` — All 11 posts in text format
- `linkedin_posts_20260612.html` — Carousel HTML slides
- `linkedin_posts_20260612.pdf` — Compiled carousel PDF
- `linkedin-infographic-20260612.png` — Infographic PNG
