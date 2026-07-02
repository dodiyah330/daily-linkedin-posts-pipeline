import json
import datetime

LOG_PATH = "./carousel-hook-log.json"

try:
    with open(LOG_PATH) as f:
        log = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    log = []

entry = {
    "date": datetime.date.today().isoformat(),
    "hook_style": "Bold Claim",
    "hook_text": "Building is no longer a moat",
    "carousel_topic": "Software distribution vs building product",
    "carousel_format": "HOT_TAKE"
}
log.append(entry)

# Keep last 30 entries
log = log[-30:]

with open(LOG_PATH, "w") as f:
    json.dump(log, f, indent=2)

print(f"Carousel hook log updated: {entry['hook_style']} — {entry['hook_text']}")
