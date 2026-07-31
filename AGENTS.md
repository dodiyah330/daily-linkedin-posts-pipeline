# AGENTS.md

## Cursor Cloud specific instructions

This repo is an automation toolkit (not a long-running web app / API server and no database). It is a
collection of batch scripts: Python for fetch/generate/Slack/Freelancer, Node for Puppeteer rendering
and LinkedIn scheduling. See `README.md` and `docs/API_KEYS.md` for the full command list and env keys.

### What actually runs in the cloud VM (no secrets needed)
- The **carousel visual renderer** under `carousel-routine/` is the core pipeline that runs fully
  locally. It uses full `puppeteer` (its own Chromium, downloaded by `npm install`). Example, using the
  committed sample slides:
  - Render HTML → PNG: `node render.js 2026-07-31 carousel-branded`
    (reads `temp/<dir>/slide-*.html`, writes `output/<date>/<dir>/slide-*.png`)
  - Stitch PNGs → PDF: `node render-pdf.js 2026-07-31 carousel-branded`
    (`render-pdf.js` uses ImageMagick `magick` if present, otherwise falls back to Puppeteer; ImageMagick
    is not installed here, so the Puppeteer path is used.)
- Python scripts import cleanly (mostly stdlib). The optional Freelancer bid bot exits gracefully with
  `Missing FLN_OAUTH_TOKEN` when no secrets are set.

### What is blocked in the cloud VM
- **Root `*.cjs` LinkedIn scripts** (`schedule_all_posts.cjs`, `send_connections.cjs`,
  `build_carousel_today.cjs`, etc.) require BOTH a logged-in LinkedIn session via the `agent-browser`
  CLI (not installed) AND, in several scripts, a **hard-coded macOS Chrome path**
  (`/Applications/Google Chrome.app/...`). They cannot run unmodified on this Linux VM.
- **Most content pipelines** need `.env` API keys (Gemini / OpenRouter / Slack / Apify) and/or a
  LinkedIn login, so end-to-end generation + publishing is blocked without those secrets.

### Non-obvious setup notes
- There is **no root `package.json` in the original repo**; root scripts `require('puppeteer-core')`.
  A minimal root `package.json` declaring `puppeteer-core` was added so those `require`s resolve.
  Root `puppeteer-core` relies on a system Chrome (`/usr/local/bin/google-chrome` here), unlike
  `carousel-routine` which bundles its own Chromium via `puppeteer`.
- The optional **Freelancer bid bot venv** (`freelancer-bid-bot/.venv`) needs the system package
  `python3-venv` (`sudo apt-get install -y python3.12-venv`), which is NOT part of the update script.
  After that: `python3 -m venv freelancer-bid-bot/.venv && freelancer-bid-bot/.venv/bin/pip install -r freelancer-bid-bot/requirements.txt`.
- `node_modules/` (root and `carousel-routine/`) and `.venv/` are gitignored; the update script
  re-creates the Node deps on each start.
