---
name: automation-leads-engine
description: Generates 14 LinkedIn lead-gen posts per week (2/day Mon–Sun) for a full-stack AI automation developer — one image/infographic + one text post each day. Uses fresh AI news from ai_news_data.json.
---

# Automation Leads Engine

Generates **14 posts/week** for your **personal LinkedIn profile**:
- **2 posts/day, Monday–Sunday**
- **1 image (infographic) + 1 text** every day

## Ideal client (ICP)

- SaaS founders who need AI features or internal automations built
- Ops/sales/support teams drowning in manual handoffs between tools
- Agencies white-labeling automations for clients
- Teams that outgrew Zapier/Make and need custom API + SaaS integrations

## Weekly mix (14 slots)

| Day | Image post | Text post |
|-----|------------|-----------|
| Mon | News → Automation | Builder tip |
| Tue | Case study | Myth bust |
| Wed | Qualifying poll | Steal this workflow |
| Thu | Workflow card | Client lesson |
| Fri | Direct offer | Tool angle |
| Sat | Pain → Automation | FAQ |
| Sun | Mini win | Soft offer |

Default peak times (IST): image mid-morning/midday, text mid-afternoon.

## Voice

- **First person** allowed ("I've built…", "I wire agents into…")
- News hook stays accessible — no jargon
- Every post ends with a **lead CTA**: Comment **AUTO**, DM your stack, or book an audit
- Do NOT use @handles or third-party brand promotion

## Run

```bash
./run_automation_leads.sh
```

Or step by step:

```bash
python3 fetch_ai_news_rss.py
python3 generate_automation_leads.py
python3 build_automation_images.py
python3 prepare_automation_schedule.py   # next Mon–Sun by default
python3 send_automation_leads_to_slack.py

agent-browser --session linkedin_bot --profile Default open https://www.linkedin.com/feed/
LINKEDIN_START_URL='https://www.linkedin.com/feed/' \
  SCHEDULE_FILE=schedule_automation_leads.json \
  node schedule_all_posts.cjs
```

Force a specific week start:

```bash
START_DATE=2026-07-20 python3 prepare_automation_schedule.py
```

## US image stream (separate)

Daily **US-specific** infographic posts at **US Eastern peak**:

```bash
bash run_us_image_posts.sh
SCHEDULE_FILE=schedule_us_image_posts.json node schedule_all_posts.cjs
```

## US connection requests (outreach)

```bash
./run_us_connections.sh
DRY_RUN=1 ./run_us_connections.sh
```

See `skills/us-connections/SKILL.md`.
