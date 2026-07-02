import sys
import json
import urllib.request

if len(sys.argv) < 2:
    print("Usage: python send_slack_message.py 'Message text'")
    exit(1)

text = sys.argv[1]

# Read token from .env
slack_token = None
slack_channel = None
env_path = "./.env"
try:
    with open(env_path) as f:
        for line in f:
            if line.startswith("SLACK_BOT_TOKEN="):
                slack_token = line.strip().split("=", 1)[1]
            elif line.startswith("SLACK_CHANNEL_ID="):
                slack_channel = line.strip().split("=", 1)[1]
except Exception as e:
    exit(1)

channel = slack_channel or "C0BEG7HAXHQ"

url = "https://slack.com/api/chat.postMessage"
headers = {
    "Authorization": f"Bearer {slack_token}",
    "Content-Type": "application/json; charset=utf-8"
}
payload = {
    "channel": channel,
    "text": text,
    "unfurl_links": False,
    "unfurl_media": False
}
req = urllib.request.Request(
    url, 
    data=json.dumps(payload).encode("utf-8"), 
    headers=headers,
    method="POST"
)
try:
    with urllib.request.urlopen(req) as res:
        pass
except Exception as e:
    pass
