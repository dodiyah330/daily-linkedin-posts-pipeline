#!/usr/bin/env bash
# Local project setup for daily-linkedin-posts-pipeline
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

echo "==> Checking prerequisites"
command -v node >/dev/null || { echo "Node.js >= 18 required"; exit 1; }
command -v npm >/dev/null || { echo "npm required"; exit 1; }
command -v python3 >/dev/null || { echo "Python 3.10+ required"; exit 1; }

NODE_MAJOR="$(node -p "process.versions.node.split('.')[0]")"
if [[ "$NODE_MAJOR" -lt 18 ]]; then
  echo "Node.js >= 18 required (found $(node -v))"
  exit 1
fi

echo "    node $(node -v)"
echo "    npm  $(npm -v)"
echo "    python $(python3 --version 2>&1)"

if [[ ! -f .env ]]; then
  echo ""
  echo "WARNING: .env not found at repo root."
  echo "Copy keys into .env before running fetch/generate/Slack scripts."
  echo "See docs/API_KEYS.md and README.md."
else
  echo "    .env found"
fi

echo ""
echo "==> Installing root Node deps (puppeteer-core for schedule/cap scripts)"
npm install

echo ""
echo "==> Installing carousel-routine Node deps (puppeteer + Chromium)"
(cd carousel-routine && npm install)

echo ""
echo "==> Setting up Freelancer bid bot venv (optional)"
python3 -m venv freelancer-bid-bot/.venv
# shellcheck disable=SC1091
source freelancer-bid-bot/.venv/bin/activate
pip install --upgrade pip
pip install -r freelancer-bid-bot/requirements.txt
deactivate

echo ""
if command -v agent-browser >/dev/null 2>&1; then
  echo "==> agent-browser already installed: $(command -v agent-browser)"
else
  echo "==> Installing agent-browser (LinkedIn session CLI)"
  if npm install -g agent-browser 2>/dev/null; then
    echo "    installed globally"
  else
    mkdir -p "$HOME/.local"
    if npm install -g agent-browser --prefix "$HOME/.local"; then
      export PATH="$HOME/.local/bin:$PATH"
      echo "    installed to $HOME/.local/bin"
      echo "    Add to your shell profile if needed:"
      echo "      export PATH=\"\$HOME/.local/bin:\$PATH\""
    else
      echo "WARNING: agent-browser install failed."
      echo "Install manually: npm install -g agent-browser"
      echo "Docs: https://github.com/vercel-labs/agent-browser"
    fi
  fi
fi

echo ""
echo "==> Smoke checks"
node -e "require('puppeteer-core'); console.log('puppeteer-core: ok')"
node -e "require('./carousel-routine/node_modules/puppeteer'); console.log('puppeteer: ok')"
python3 -c "import json, urllib.request; print('python stdlib: ok')"
freelancer-bid-bot/.venv/bin/python -c "import requests; print('freelancer venv: ok')"

echo ""
echo "Setup complete."
echo ""
echo "Next:"
echo "  1. Confirm .env keys (OPENROUTER/GEMINI, SLACK, APIFY, ...)"
echo "  2. Fetch AI news:  python3 fetch_ai_news_rss.py"
echo "  3. LinkedIn session (when scheduling):"
echo "       agent-browser --session linkedin_bot --profile Default open https://www.linkedin.com/feed/"
