#!/usr/bin/env python3
"""Post US connection request run summary to Slack."""
import datetime
import json
import os
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

LOG_FILE = "connections-run-log.json"
RUN_UNTIL_WEEKLY = os.environ.get("RUN_UNTIL_WEEKLY_LIMIT", "1") != "0"

slack_token = slack_channel = None
with open(".env") as f:
    for line in f:
        if line.startswith("SLACK_BOT_TOKEN="):
            slack_token = line.strip().split("=", 1)[1]
        elif line.startswith("SLACK_CHANNEL_ID="):
            slack_channel = line.strip().split("=", 1)[1]

if not slack_token:
    print("Error: SLACK_BOT_TOKEN not found")
    exit(1)

channel = slack_channel or "C0BEG7HAXHQ"
today = datetime.date.today().isoformat()


def send(text):
    req = urllib.request.Request(
        "https://slack.com/api/chat.postMessage",
        data=json.dumps({"channel": channel, "text": text, "unfurl_links": False}).encode(),
        headers={"Authorization": f"Bearer {slack_token}", "Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req) as res:
        resp = json.loads(res.read().decode())
        if not resp.get("ok"):
            print(f"Slack error: {resp.get('error')}")
        else:
            print("Slack message sent")


log = []
if os.path.exists(LOG_FILE):
    with open(LOG_FILE) as f:
        log = json.load(f)

today_entries = [e for e in log if e.get("date") == today]
sent = [e for e in today_entries if e.get("status") in ("sent", "dry_run")]
skipped = [e for e in today_entries if e.get("status") in ("already_connected", "pending")]
failed = [e for e in today_entries if e.get("status") == "failed"]
limits = [e for e in today_entries if e.get("status") == "limit_reached"]

audience = "US SaaS founders & ops leaders (auto-searched on LinkedIn)"

mode = "until weekly limit" if RUN_UNTIL_WEEKLY else "daily cap"
lines = [
    f"🤝 *US Connection Requests — {today}*",
    f"Audience: {audience}",
    f"Mode: {mode} | No notes",
    f"Sent today: *{len(sent)}* | Skipped: {len(skipped)} | Failed: {len(failed)}",
]
if limits:
    lines.append("⚠️ LinkedIn weekly invitation limit was hit.")

if sent:
    lines.append("\n*Sent:*")
    for e in sent[-10:]:
        lines.append(f"• {e.get('name', e.get('prospect_id'))} — {e.get('linkedin_url', '')}")

if failed:
    lines.append("\n*Failed:*")
    for e in failed[-5:]:
        lines.append(f"• {e.get('name', e.get('prospect_id'))}: {e.get('error', 'unknown')}")

if not today_entries:
    lines.append("\nNo connection activity logged today.")

send("\n".join(lines))
print("Done.")
