import json
import datetime
import os

# Update Carousel log
car_log_path = "./carousel-hook-log.json"
try:
    with open(car_log_path) as f:
        car_log = json.load(f)
except Exception:
    car_log = []

# Try to load carousel data
try:
    with open("carousel_data.json") as f:
        car_data = json.load(f)
    hook_p1 = car_data.get("1", {}).get("HOOK_PART_1", "")
    hook_p2 = car_data.get("1", {}).get("HOOK_PART_2", "")
    hook_text = f"{hook_p1} {hook_p2}".strip()
    carousel_topic = car_data.get("1", {}).get("HEADER_LABEL", "Founder Journey")
except Exception as e:
    print(f"Error reading carousel_data.json: {e}")
    hook_text = "From ignored student to panel speaker"
    carousel_topic = "From dorm room to panel speaker"

car_entry = {
    "date": datetime.date.today().isoformat(),
    "hook_style": "Story",
    "hook_text": hook_text,
    "carousel_topic": carousel_topic,
    "carousel_format": "STORY"
}
car_log.append(car_entry)
car_log = car_log[-30:]

with open(car_log_path, "w") as f:
    json.dump(car_log, f, indent=2)

print(f"Carousel hook log updated: {car_entry['hook_style']} - {car_entry['hook_text']}")

# Update Infographic log
info_log_path = "./infographic-run-log.json"
try:
    with open(info_log_path) as f:
        info_log = json.load(f)
except Exception:
    info_log = []

try:
    with open("infographic_data.json") as f:
        info_data = json.load(f)
    info_topic = info_data.get("title_main", "The Digital Distraction Crisis")
except Exception as e:
    print(f"Error reading infographic_data.json: {e}")
    info_topic = "The Digital Distraction Crisis"

info_entry = {
    "date": datetime.date.today().isoformat(),
    "topic": info_topic,
    "format": "RANKED_BARS",
    "generated_at": datetime.datetime.utcnow().isoformat() + "Z"
}
info_log.append(info_entry)
info_log = info_log[-30:]

with open(info_log_path, "w") as f:
    json.dump(info_log, f, indent=2)

print(f"Infographic run log updated: {info_entry['topic']} ({info_entry['format']})")
