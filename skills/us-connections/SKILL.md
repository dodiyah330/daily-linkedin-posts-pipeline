---
name: us-connections
description: Searches LinkedIn for US SaaS automation ICP prospects and sends connection requests without notes, respecting daily and weekly LinkedIn limits.
---

# US Connection Requests (Auto-Search)

Automatically **searches LinkedIn** for people matching the automation-leads ICP and sends **connection invites without notes**.

No prospect CSV or manual list required.

## Target audience (searched on LinkedIn)

| Filter | Value |
|--------|-------|
| Location | United States (`geoUrn: 103644278`) |
| Keywords (rotated) | SaaS founder CEO, VP Operations SaaS, Head of RevOps B2B, COO software startup, Director of Operations SaaS |

Matches the same ICP as `automation_profile.md` and the US image post stream.

## Run

```bash
# 1. Open logged-in LinkedIn session
agent-browser --session linkedin_bot open https://www.linkedin.com/feed/

# 2. Search + send (default: 10/run, 15/day, no notes)
./run_us_connections.sh

# 3. Preview without sending
DRY_RUN=1 ./run_us_connections.sh
```

### Direct

```bash
node send_connections.cjs
python3 send_connections_to_slack.py
```

## Env vars

| Variable | Default | Purpose |
|----------|---------|---------|
| `RUN_UNTIL_WEEKLY_LIMIT` | `1` (in `run_us_connections.sh`) | Keep sending until LinkedIn weekly cap |
| `MAX_CONNECTIONS_PER_RUN` | `999` when weekly mode | Per-run cap (disabled in weekly mode) |
| `MAX_CONNECTIONS_PER_DAY` | `999` when weekly mode | Daily cap (disabled in weekly mode) |
| `CONNECTION_DELAY_MS` | `12000` | Pause between invites |
| `CONNECTION_SEARCH_QUERIES` | (built-in list) | Pipe-separated queries, e.g. `SaaS founder\|VP Ops` |
| `DRY_RUN` | `0` | Set `1` to search without sending |

## Logs

| File | Purpose |
|------|---------|
| `connections-run-log.json` | Sent / skipped / failed per profile |
| `searched-prospects-cache.json` | Profiles already discovered (avoids repeats) |

## LinkedIn limits

- Script stops at **daily cap** (default 15) and **weekly limit** if LinkedIn shows the limit modal
- Sends **without notes** — clicks "Send without a note" when a modal appears
- Skips profiles that require email, are already connected, or pending

## Compliance

LinkedIn restricts bulk invites. Start with `MAX_CONNECTIONS_PER_RUN=5`. Account restrictions are possible with any automation.
