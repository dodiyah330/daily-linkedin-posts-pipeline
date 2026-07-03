# Automation Lead Profile — Hitesh Dodiya

Used by `generate_automation_leads.py` for case studies and proof lines.

## About you
- **Name:** Hitesh Dodiya
- **Role:** Full-stack AI web developer
- **GitHub:** github.com/dodiyah330
- **Core stack:** Next.js, React, Node.js, Python, PostgreSQL, REST/GraphQL APIs, Stripe, webhooks
- **AI stack:** Gemini / OpenRouter / Anthropic APIs, custom agents, Puppeteer browser automation, Slack & Apify integrations
- **What you ship:** Full-stack SaaS products, websites, SaaS modules (auth, billing, dashboards), and production AI automations

## Real projects

### Project 1 — LinkedIn content & scheduling automation (this pipeline)
- **Client type:** Personal brand / founder-led GTM (built for own use, productizable for clients)
- **Problem:** Manually writing 16 posts/day, building carousels, uploading to Slack, and scheduling on LinkedIn took 4+ hours daily and broke whenever LinkedIn UI changed.
- **Stack:** Python (content gen, RSS/Apify fetch), Node.js + Puppeteer (carousel render, LinkedIn scheduler), Gemini API, Slack API, agent-browser (Chrome session automation)
- **What you built:**
  - End-to-end pipeline: Reddit + AI news fetch → LLM post generation → carousel PDF + infographic PNG → Slack delivery → scheduled LinkedIn posting via browser automation
  - Separate **automation-leads** stream: 5 posts/week with news hooks → automation offer → DM AUTO CTA
  - Shadow-DOM resilient LinkedIn scheduler with poll/carousel/document upload support
- **Outcome:** Daily content production dropped from ~4 hours to ~15 minutes of review. 16 posts + visuals delivered and scheduled with one command run.

### Project 2 — B2B SaaS sales prep automation
- **Client type:** B2B SaaS (~40 employees, HubSpot + Calendly stack)
- **Problem:** SDRs spent ~15 hrs/week researching prospects before demo calls. Notes lived in 3 tabs (LinkedIn, CRM, company site). No-shows and weak discovery hurt close rate.
- **Stack:** Node.js, HubSpot API, Calendly webhooks, Apollo enrichment API, OpenAI/Gemini for summarization, Slack incoming webhooks
- **What you built:**
  - Webhook on Calendly booking → enrich company domain via Apollo → scrape public site → AI draft 3 talking points + likely pain points → post structured brief to rep's Slack 10 min before call
  - Admin dashboard module (Next.js) to tune prompt templates and view automation logs
- **Outcome:** ~12 hrs/week saved per rep. Demo-to-close rate up ~14% in first 30 days. Client expanded scope to onboarding automation (Project 3 pattern).

### Project 3 — SaaS client onboarding automation
- **Client type:** Same B2B SaaS after Project 2 upsell
- **Problem:** After DocuSign contract signed, CS manually created Slack channel, provisioned tenant in Postgres, copied deal terms into HubSpot, and sent welcome email. Average 45 min per client, frequent data entry errors.
- **Stack:** DocuSign Connect webhooks, Python FastAPI worker, PostgreSQL multi-tenant schema, HubSpot API, Slack API, React admin panel
- **What you built:**
  - Signed contract trigger → AI extracts seat count, SLA tier, contract value from PDF → auto-provision tenant + roles → create `#client-{name}` Slack channel → draft personalized welcome sequence in HubSpot for CS review
  - Idempotent webhook handler with retry queue (Redis) for failed provisioning steps
- **Outcome:** Onboarding handoff cut from 45 min to under 3 min. Zero wrong-tier provisioning in 8 weeks post-launch.

### Project 4 — Support triage agent for a productized SaaS module
- **Client type:** Subscription SaaS selling workflow templates to agencies
- **Problem:** 200+ support tickets/week. Team copied answers from Notion docs manually. First response time averaged 11 hours.
- **Stack:** Next.js SaaS module, Intercom webhooks, Notion API, vector search over help docs, Gemini for draft replies, PostgreSQL ticket audit log
- **What you built:**
  - Incoming ticket → classify intent → retrieve top 3 Notion articles → AI draft reply with links → human approves/edits in Slack before send
  - Embedded "AI assist" panel inside existing SaaS admin (auth + billing module reused from prior build)
- **Outcome:** Median first response dropped to 47 minutes. ~60% of L1 tickets handled with AI draft + one-click approve.

### Project 5 — Internal ops reporting automation
- **Client type:** E-commerce SaaS (Shopify-adjacent analytics product)
- **Problem:** Founder wanted daily KPI snapshot (MRR, churn, top support themes) but engineering spent 2 hrs/day pulling SQL + formatting Slack updates.
- **Stack:** PostgreSQL, Stripe API, Metabase SQL queries, Python cron, Gemini for narrative summary, Slack Block Kit messages
- **What you built:**
  - Nightly job: pull metrics → chart PNG → AI writes 5-bullet executive summary → posts to `#leadership` at 8 AM IST
  - Configurable thresholds: alert channel if churn spike > X%
- **Outcome:** Eliminated 10+ hrs/week of manual reporting. Leadership adopted it as daily standup anchor.

## Services you sell
1. **Custom AI automation builds** — agents wired into CRM, support, billing, and ops stacks
2. **Full-stack SaaS modules** — auth (NextAuth/Clerk), Stripe billing, dashboards, AI feature layers dropped into existing products
3. **Zapier/Make escape plans** — when no-code hits API limits, you build the custom glue in Node/Python
4. **Browser + API hybrid automations** — when no official API exists (LinkedIn scheduling, legacy portals)
5. **Free 15-minute automation audit** → scoped fixed-price build or monthly retainer

## Ideal clients
- SaaS founders (seed to Series A) who need AI features or ops automation without hiring a full team
- Agencies productizing AI workflows for their clients
- Ops/sales leaders who outgrew Zapier and need custom integrations

## CTA preference
- Primary: **Comment AUTO** — "I'll suggest 3 automations for your stack"
- Secondary: **DM your stack** (CRM + chat + project tool)
- Offer: **2 build slots per month** + free 15-min audit

## Tone notes for posts
- First person OK for proof ("I built…", "I wired…")
- Name real tools (HubSpot, Slack, Stripe, Notion, Calendly, DocuSign)
- Always tie news → business pain → automation you'd build → proof from projects above
- Never use @handles or third-party personal brands
