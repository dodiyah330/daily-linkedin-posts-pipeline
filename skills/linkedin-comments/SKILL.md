---
name: linkedin-comments
description: Searches LinkedIn content for hiring posts and skill-matched asks, then comments with interest plus a relevant portfolio link.
---

# LinkedIn skill / hiring comments

Finds posts that are **remote hiring** and ask for work matching your **automation + freelancer skill stack**, then leaves a short comment showing interest and a portfolio URL.

Only posts with both a hiring signal and a remote signal are commented on (`require_remote_hiring: true`). Onsite-only posts are skipped.

No Slack approval — comments post directly (use `DRY_RUN=1` to preview).

## What it matches

| Signal | Examples |
|--------|----------|
| Hiring | hiring, looking for, need a developer, join our team, open role |
| Skills | WordPress, Shopify, Elementor, Next.js, n8n, Zapier, Make, AI agents, Figma, ecommerce, APIs |

Config: `linkedin_comments_config.json`  
Portfolio picks: `freelancer-bid-bot/portfolio_projects.json` (plus `portfolio_hub` fallback)

## Run

```bash
# 1. Open logged-in LinkedIn session
agent-browser --session linkedin_bot open https://www.linkedin.com/feed/

# 2. Comment (default 15/run and 15/day)
./run_linkedin_comments.sh

# 3. Preview without posting
DRY_RUN=1 ./run_linkedin_comments.sh
```

### Direct

```bash
node comment_on_posts.cjs
```

## Env vars

| Variable | Default | Purpose |
|----------|---------|---------|
| `MAX_COMMENTS_PER_RUN` | `15` | Cap per run |
| `MAX_COMMENTS_PER_DAY` | `15` | Cap per calendar day |
| `COMMENT_DELAY_MS` | `20000` | Pause between comments |
| `COMMENT_SCROLLS` | `6` | Scrolls per search page |
| `COMMENT_SEARCH_BATCH` | `40` | Max posts to collect before scoring |
| `COMMENT_QUERIES` | (from config) | Pipe-separated content search queries |
| `COMMENT_VARIANT` | `auto` | `auto` \| `hiring` \| `skills` \| `both` |
| `DRY_RUN` | `0` | Set `1` to search/fill without posting |

## Comment shape

Templates insert matched skills + one portfolio project URL, e.g.:

> Saw the ask for WordPress, Shopify and I'm interested. Relevant work: CarbonCryp (https://carboncryp.com/). Glad to jump on a quick chat if useful.

## Logs

| File | Purpose |
|------|---------|
| `linkedin-comments-run-log.json` | Sent / dry_run / failed per post |
| `linkedin-comments-cache.json` | Posts already touched |

## Compliance

LinkedIn restricts bulk engagement. Start with `DRY_RUN=1`, then `MAX_COMMENTS_PER_RUN=5` before full 15/day. Account restrictions are possible with any automation.
