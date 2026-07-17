---
name: openxcode-linkedin
description: Generates 1 LinkedIn company-page post per day for OpenXcode (web/mobile/UI/AI software company) with rotating archetypes, Slack review, and schedule JSON for LinkedIn.
---

# OpenXcode Company LinkedIn — 1 post/day

Generates **1 post per day** for the **OpenXcode company LinkedIn page** ([openxcode.com](https://openxcode.com) / [linkedin.com/company/open-xcode](https://www.linkedin.com/company/open-xcode)).

Posts use **company voice** (`we` / `our`) and aim to attract **project inquiries** (web apps, mobile apps, UI/UX, websites, AI features).

## Ideal buyer (ICP)

- Founders who need a reliable product build partner
- SMBs replacing WhatsApp/spreadsheet chaos with a real app
- Enterprises needing a focused customer-facing module
- Agencies needing overflow / white-label engineering

## Daily archetype rotation (by weekday)

| Day | Archetype | Purpose |
|-----|-----------|---------|
| Mon | **News → Build** | Fresh tech news → what to ship → soft CTA |
| Tue | **Case Study** | Problem → what we built → outcome |
| Wed | **Myth Bust** | Bust a software/outsourcing myth |
| Thu | **Build Tip** | One practical tip from client work |
| Fri | **Service Spotlight** | One service + who it is for |
| Sat | **Pain → Product** | Ops pain → focused product |
| Sun | **Direct Offer** | Discovery / proposal CTA |

## Voice

- **We / our / OpenXcode team** only (never solo freelancer "I")
- Specific platforms and outcomes over buzzwords
- Soft lead CTAs: Comment **BUILD**, DM us, or request a proposal
- No FounderWing / personal @handles
- No em-dashes; banned hype words listed in `openxcode_profile.md`

## Peak times (this week / weekly batch)

B2B LinkedIn peaks (IST account timezone):

| Day | Time | Why |
|-----|------|-----|
| Tue | **11:00 AM** | Core midweek morning peak |
| Wed | **12:00 PM** | Midday peak |
| Thu | **11:00 AM** | Core midweek morning peak |
| Fri | **1:00 PM** | Early-afternoon Friday peak |

Weekends are **skipped by default** (lowest B2B engagement). Set `OPENXCODE_INCLUDE_WEEKENDS=1` to include them.

### Schedule this week's remaining peak posts

```bash
python3 fetch_ai_news_rss.py
OPENROUTER_MODEL=google/gemini-2.5-flash python3 generate_openxcode_week.py
python3 prepare_openxcode_schedule.py
python3 send_openxcode_to_slack.py

# LinkedIn must be logged in (Chrome profile Default works for Hitesh + OpenXCode admin)
agent-browser --session linkedin_bot --profile Default open "https://www.linkedin.com/company/108839748/admin/dashboard/"
SCHEDULE_FILE=schedule_openxcode.json POST_AS=OpenXCode node schedule_all_posts.cjs
```

Company admin URL: `https://www.linkedin.com/company/108839748/admin/dashboard/`

## Run (single day)

```bash
./run_openxcode_posts.sh
```

Or step by step:

```bash
python3 fetch_ai_news_rss.py          # optional shared news (Mon archetype)
python3 generate_openxcode_posts.py
python3 prepare_openxcode_schedule.py
python3 send_openxcode_to_slack.py
SCHEDULE_FILE=schedule_openxcode.json node schedule_all_posts.cjs
```

Override schedule time (LinkedIn account timezone):

```bash
OPENXCODE_POST_TIME='11:00 AM' python3 prepare_openxcode_schedule.py
```

## Outputs

| File | Purpose |
|------|---------|
| `openxcode_posts_YYYYMMDD.txt` | Today's generated post |
| `schedule_openxcode.json` | 1 text post scheduled for **tomorrow** |
| `openxcode-run-log.json` | Dedup log (topics + archetypes) |
| `openxcode_profile.md` | Company brief for the generator |

## Notes

- This stream is **separate** from FoundersWing daily content and the automation-leads stream.
- Default schedule: **tomorrow at 10:00 AM** in the LinkedIn account timezone.
- Text-only for v1 (no carousel/infographic). Add visuals later if needed.
