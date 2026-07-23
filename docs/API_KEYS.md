# API Keys & Credentials Setup

Step-by-step guide to obtain every credential used in the repo-root `.env` file.

Copy this template into `.env` (never commit real values):

```bash
# LLM
OPENROUTER_API_KEY=
GEMINI_API_KEY=
ANTHROPIC_TOKEN=

# Slack
SLACK_BOT_TOKEN=
SLACK_CHANNEL_ID=

# Data fetch
APIFY_API_KEY=
SCRAPINGDOG_API_KEY=

# Freelancer bid bot
FLN_OAUTH_TOKEN=
# Optional sandbox:
# FLN_URL=https://www.freelancer-sandbox.com

# LinkedIn (optional — prefer agent-browser logged-in session)
LINKEDIN_EMAIL=
LINKEDIN_PASSWORD=
```

| Variable | Required for | Optional / fallback |
|----------|--------------|---------------------|
| `GEMINI_API_KEY` | OpenXcode batch, automation leads, US images, bid bot (preferred) | — |
| `OPENROUTER_API_KEY` | AI news posts, some generators | Fallback when Gemini missing |
| `ANTHROPIC_TOKEN` | `generate_posts_via_anthropic.py` only | Skip if using Gemini/OpenRouter |
| `SLACK_BOT_TOKEN` + `SLACK_CHANNEL_ID` | All Slack delivery scripts | — |
| `APIFY_API_KEY` | Reddit fetch via Apify | Use RSS/JSON fallbacks instead |
| `SCRAPINGDOG_API_KEY` | Optional X/Twitter research | Skip if unused |
| `FLN_OAUTH_TOKEN` | Freelancer bid bot | Skip if not running bid bot |
| `LINKEDIN_EMAIL` / `LINKEDIN_PASSWORD` | Rare login helpers | Prefer `agent-browser` session |

---

## 1. Google Gemini — `GEMINI_API_KEY`

**Used by:** OpenXcode batch, automation leads, US image posts, Freelancer bid bot, several generators.

### Steps
1. Open [Google AI Studio](https://aistudio.google.com/apikey) (same account as Google Cloud / Gemini).
2. Sign in with your Google account.
3. Click **Create API key**.
4. Choose an existing Google Cloud project, or create a new one (e.g. `linkedin-pipeline`).
5. Copy the key (starts with `AIza…` or similar).
6. Paste into `.env`:
   ```bash
   GEMINI_API_KEY=your_key_here
   ```

### Optional
```bash
GEMINI_MODEL=gemini-2.5-flash   # override default model name in scripts
```

### Notes
- Enable billing on the Cloud project if you hit free-tier quotas.
- Keep the key private; restrict by HTTP referrer / IP in Google Cloud if you expose it outside this machine.

### Quick test
```bash
curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=$GEMINI_API_KEY" | head -c 200
```

---

## 2. OpenRouter — `OPENROUTER_API_KEY`

**Used by:** AI news generation, several content scripts, fallback LLM for OpenXcode / automation / bid bot.

### Steps
1. Open [OpenRouter](https://openrouter.ai/) and create an account.
2. Go to [Keys](https://openrouter.ai/keys).
3. Click **Create Key**, name it (e.g. `daily-linkedin-pipeline`).
4. Copy the key (`sk-or-v1-…`).
5. Add credits under [Credits](https://openrouter.ai/settings/credits) if the free allowance is exhausted.
6. Paste into `.env`:
   ```bash
   OPENROUTER_API_KEY=sk-or-v1-...
   ```

### Optional
```bash
OPENROUTER_MODEL=google/gemini-2.5-flash
```

### Quick test
```bash
curl -s https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" | head -c 200
```

---

## 3. Anthropic — `ANTHROPIC_TOKEN`

**Used by:** `generate_posts_via_anthropic.py` (direct Anthropic API). Most pipelines prefer Gemini or OpenRouter.

### Steps
1. Open [Anthropic Console](https://console.anthropic.com/).
2. Sign up / sign in.
3. Go to **API Keys** → **Create Key**.
4. Copy the key (`sk-ant-…`).
5. Ensure the org has billing / credits enabled.
6. Paste into `.env`:
   ```bash
   ANTHROPIC_TOKEN=sk-ant-...
   ```

> Scripts expect the name `ANTHROPIC_TOKEN` (not `ANTHROPIC_API_KEY`).

### Quick test
```bash
curl -s https://api.anthropic.com/v1/models \
  -H "x-api-key: $ANTHROPIC_TOKEN" \
  -H "anthropic-version: 2023-06-01" | head -c 200
```

---

## 4. Slack — `SLACK_BOT_TOKEN` + `SLACK_CHANNEL_ID`

**Used by:** All `send_*_to_slack.py` / `send_to_slack.py` delivery scripts.

### A. Create a Slack app + bot token
1. Open [Slack API Apps](https://api.slack.com/apps) → **Create New App** → **From scratch**.
2. Name it (e.g. `LinkedIn Pipeline`) and pick your workspace.
3. In the left sidebar: **OAuth & Permissions**.
4. Under **Bot Token Scopes**, add at least:
   - `chat:write` — post messages
   - `files:write` — upload carousel PDFs / PNGs
   - `channels:read` — resolve channel IDs (helpful)
   - `channels:history` — used by check/read helpers (optional)
5. Click **Install to Workspace** → allow.
6. Copy **Bot User OAuth Token** (`xoxb-…`) into `.env`:
   ```bash
   SLACK_BOT_TOKEN=xoxb-...
   ```

### B. Invite the bot to the channel
1. In Slack, open the target channel (e.g. `#linkedin-content`).
2. Type `/invite @LinkedIn Pipeline` (your app’s bot name).

### C. Get the channel ID
1. In Slack Desktop: right-click the channel → **View channel details** → copy **Channel ID** at the bottom.  
   Or in a browser: open the channel; the URL contains `/C0XXXXXXX`.
2. Paste into `.env`:
   ```bash
   SLACK_CHANNEL_ID=C0XXXXXXX
   ```

### Quick test
```bash
curl -s -X POST https://slack.com/api/auth.test \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN"
# Then post a test message:
curl -s -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"channel\":\"$SLACK_CHANNEL_ID\",\"text\":\"Pipeline key check ✅\"}"
```

---

## 5. Apify — `APIFY_API_KEY`

**Used by:** `fetch_reddit_apify.py` (primary Reddit fetch). Fallbacks: `fetch_reddit_fallback.py`, `fetch_reddit_rss.py`.

### Steps
1. Open [Apify](https://console.apify.com/) and create an account.
2. Go to **Settings** → **Integrations** / **API & Integrations** → **API tokens**  
   Direct: [https://console.apify.com/settings/integrations](https://console.apify.com/settings/integrations)
3. Create or copy a personal API token (`apify_api_…`).
4. Paste into `.env`:
   ```bash
   APIFY_API_KEY=apify_api_...
   ```
5. Confirm you have enough Apify credits for the Reddit scraper actor (`trudax/reddit-scraper-lite` or similar used in the skill).

### Quick test
```bash
curl -s "https://api.apify.com/v2/users/me?token=$APIFY_API_KEY" | head -c 300
```

---

## 6. ScrapingDog — `SCRAPINGDOG_API_KEY`

**Used by:** Optional X/Twitter (or other scrape) research. Safe to leave blank if unused.

### Steps
1. Open [ScrapingDog](https://www.scrapingdog.com/) → sign up.
2. Open the dashboard and copy your **API Key**.
3. Paste into `.env`:
   ```bash
   SCRAPINGDOG_API_KEY=your_key_here
   ```

### Quick test
```bash
curl -s "https://api.scrapingdog.com/linkedin?api_key=$SCRAPINGDOG_API_KEY&type=profile&link=https://www.linkedin.com/in/williamhgates" | head -c 200
```
(Endpoint/params vary by product — use ScrapingDog’s docs for the exact call you need.)

---

## 7. Freelancer.com — `FLN_OAUTH_TOKEN`

**Used by:** `freelancer-bid-bot/bid_bot.py`.

### Steps
1. Create / log into a [Freelancer.com](https://www.freelancer.com/) account (the bidder account).
2. Open the developer portal: [https://developers.freelancer.com/](https://developers.freelancer.com/).
3. Go to account developer settings (also linked from [accounts → developer](https://accounts.freelancer.com/settings/develop)).
4. **Create an app / client**:
   - App name: e.g. `bid-bot`
   - Redirect URI: `http://127.0.0.1:8080/authorized` (or any URI you control for OAuth)
5. Note **Client ID** and **Client Secret**.
6. Authorize the app for your user and obtain an **OAuth access token** (authorization-code flow against Freelancer’s OAuth endpoints).  
   Sandbox testing uses [accounts.freelancer-sandbox.com](https://accounts.freelancer-sandbox.com) and:
   ```bash
   FLN_URL=https://www.freelancer-sandbox.com
   ```
7. Paste the access token into `.env`:
   ```bash
   FLN_OAUTH_TOKEN=your_oauth_access_token
   ```

### Notes
- The bid bot reads `FLN_OAUTH_TOKEN` from repo-root `.env` (see `freelancer-bid-bot/bid_bot.py`).
- Prefer starting with `python3 bid_bot.py --once --dry-run`.
- Keep `config.json` `dry_run` true until proposals look good, then use `--live`.

### Quick test
```bash
cd freelancer-bid-bot
python3 bid_bot.py --once --dry-run
```

---

## 8. LinkedIn — `LINKEDIN_EMAIL` / `LINKEDIN_PASSWORD`

**Used by:** Optional helpers. Primary LinkedIn automation uses a **logged-in Chrome session via agent-browser**, not these passwords.

### Recommended (no password in `.env`)
```bash
agent-browser --session linkedin_bot --profile Default open https://www.linkedin.com/feed/
# Log in manually once in that Chrome profile; reuse the session afterwards.
```

### If you still store credentials
1. Use the LinkedIn email/password for the account that owns the personal profile (and/or admin rights on the OpenXcode company page).
2. Paste into `.env` only on a private machine:
   ```bash
   LINKEDIN_EMAIL=you@example.com
   LINKEDIN_PASSWORD=...
   ```
3. Prefer an app password / dedicated automation account if available; 2FA may block scripted login.

> Do not commit LinkedIn credentials. Prefer session reuse over storing passwords.

---

## Setup checklist

1. Create `.env` at the repo root from the template above.
2. Fill **at least**:
   - `GEMINI_API_KEY` **or** `OPENROUTER_API_KEY`
   - `SLACK_BOT_TOKEN` + `SLACK_CHANNEL_ID` (if using Slack delivery)
3. Add `APIFY_API_KEY` if you want Apify Reddit (else use RSS fallbacks).
4. Add `FLN_OAUTH_TOKEN` only if running the Freelancer bid bot.
5. Confirm `.env` is listed in `.gitignore` (it already is).
6. Run a smoke check per section above before a full pipeline.

### Minimum sets by pipeline

| Pipeline | Minimum keys |
|----------|----------------|
| OpenXcode batch | `GEMINI_API_KEY` or `OPENROUTER_API_KEY` (+ Slack optional) |
| Automation leads | same |
| FoundersWing daily | LLM key + Slack; Apify recommended |
| US connections / DMs | None in `.env` — need `agent-browser` LinkedIn session |
| Freelancer bid bot | `FLN_OAUTH_TOKEN` + `GEMINI_API_KEY` (or OpenRouter) |

---

## Security

- Never commit `.env`, tokens, or screenshots that show keys.
- Rotate any key that was pasted into chat, committed, or shared.
- Use separate keys per environment (laptop vs CI) when possible.
- Revoke unused keys in each provider’s dashboard.
