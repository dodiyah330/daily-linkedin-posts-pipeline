import json
import datetime

LOG_PATH = "./infographic-run-log.json"

try:
    with open(LOG_PATH) as f:
        log = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    log = []

entry = {
    "date": datetime.date.today().isoformat(),
    "topic": "E-commerce Conversion Gap: Desktop vs Mobile (2026)",
    "format": "COMPARISON_SPLIT",
    "generated_at": datetime.datetime.utcnow().isoformat() + "Z"
}
log.append(entry)

# Keep last 30 entries
log = log[-30:]

with open(LOG_PATH, "w") as f:
    json.dump(log, f, indent=2)

print(f"Infographic run-log updated: {entry['topic']} ({entry['format']})")
