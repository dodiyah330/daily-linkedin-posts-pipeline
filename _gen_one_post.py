#!/usr/bin/env python3
"""Generate one personal LinkedIn text post and write schedule_one_post.json."""
import json
import ssl
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
env_text = (BASE / ".env").read_text(encoding="utf-8")
gemini_key = openrouter_key = None
for line in env_text.splitlines():
    if line.startswith("GEMINI_API_KEY="):
        gemini_key = line.split("=", 1)[1].strip().strip('"').strip("'")
    elif line.startswith("OPENROUTER_API_KEY="):
        openrouter_key = line.split("=", 1)[1].strip().strip('"').strip("'")

prompt = (
    "Write one LinkedIn post for a personal profile "
    "(software / AI automation freelancer).\n"
    "Rules: plain text only, no emojis, no hashtags, no em dashes. "
    "120-180 words.\n"
    "Hook in first line. One concrete insight. "
    "End with a short question and Follow me.\n"
    "Output ONLY the post text."
)

caption = None
errors = []

if gemini_key:
    body = json.dumps(
        {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.8, "maxOutputTokens": 600},
        }
    ).encode()
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={gemini_key}"
    )
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=90) as r:
            data = json.load(r)
        caption = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        print("Generated via Gemini")
    except Exception as e:
        errors.append(f"gemini: {e}")

if not caption and openrouter_key:
    body = json.dumps(
        {
            "model": "google/gemini-2.5-flash",
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openrouter_key}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            data = json.load(r)
        caption = data["choices"][0]["message"]["content"].strip()
        print("Generated via OpenRouter")
    except Exception as e:
        errors.append(f"openrouter: {e}")

if not caption:
    raise SystemExit("Failed to generate post: " + "; ".join(errors))

# Schedule ~90 minutes from now so LinkedIn accepts a future slot
when = datetime.now() + timedelta(minutes=90)
# Snap to a clean clock time LinkedIn likes (top of next hour after +90m)
when = when.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
hour = when.hour
suffix = "AM" if hour < 12 else "PM"
h12 = hour % 12 or 12
time_str = f"{h12}:00 {suffix}"
date_str = when.strftime("%m/%d/%Y")

schedule = {
    "posts": [
        {
            "id": 1,
            "type": "regular",
            "date": date_str,
            "time": time_str,
            "caption": caption,
            "title": "Personal profile post",
        }
    ]
}
out = BASE / "schedule_one_post.json"
out.write_text(json.dumps(schedule, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Wrote {out.name}")
print(f"Schedule: {date_str} {time_str}")
print("---")
print(caption)
