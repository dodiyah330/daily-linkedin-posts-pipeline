#!/usr/bin/env python3
"""Send the Cursor brand-story carousel demo (free real-source images) to #linkedin-content."""
import json, os, subprocess, urllib.request, urllib.parse, time

BASE = os.path.dirname(os.path.abspath(__file__)); os.chdir(BASE)
TOKEN = subprocess.check_output("grep '^SLACK_BOT_TOKEN=' .env | cut -d'=' -f2", shell=True).decode().strip()
CHANNEL = subprocess.check_output("grep '^SLACK_CHANNEL_ID=' .env | cut -d'=' -f2", shell=True).decode().strip() or "C0BEG7HAXHQ"

def api(method, payload, json_body=True):
    if json_body:
        data = json.dumps(payload).encode("utf-8"); ct = "application/json; charset=utf-8"
    else:
        data = urllib.parse.urlencode(payload).encode("utf-8"); ct = "application/x-www-form-urlencoded"
    req = urllib.request.Request(f"https://slack.com/api/{method}", data=data,
                                 headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": ct})
    return json.loads(urllib.request.urlopen(req).read().decode("utf-8"))

def post(label, text):
    r = api("chat.postMessage", {"channel": CHANNEL, "text": text, "unfurl_links": False, "unfurl_media": False})
    print(f"  [{label}] {'OK' if r.get('ok') else 'ERR ' + str(r.get('error'))}"); time.sleep(0.7)

def upload(label, path, title, comment):
    if not os.path.exists(path): print(f"  [{label}] MISSING {path}"); return
    g = api("files.getUploadURLExternal", {"filename": os.path.basename(path), "length": os.path.getsize(path)}, json_body=False)
    if not g.get("ok"): print(f"  [{label}] getURL ERR {g.get('error')}"); return
    subprocess.run(["curl", "-s", "-F", f"file=@{path}", g["upload_url"]], stdout=subprocess.DEVNULL)
    c = api("files.completeUploadExternal", {"files": [{"id": g["file_id"], "title": title}], "channel_id": CHANNEL, "initial_comment": comment})
    print(f"  [{label}] {os.path.basename(path)} {'OK' if c.get('ok') else 'ERR ' + str(c.get('error'))}"); time.sleep(0.7)

HEADER = ("🧪 *Brand-story carousel demo — free real-source images (June 14)*\n"
          "Topic: Cursor. Every image is a real screenshot pulled *free* from cursor.com via headless browser, "
          "framed in a browser window. This is the \"free images only\" approach for brand-story carousels. "
          "New first-person CTA (\"follow me\") is in too.")

CAPTION = """Learn to code is quietly becoming optional.

The tool the best engineers use (Stripe, OpenAI, Figma and Adobe all build with it) now writes and ships the software for you. You describe what you want in plain English.

The wall that kept non-builders out for decades is coming down fast.

It will not make you a senior engineer overnight. But the founder who used to wait months on developers can ship a working version this weekend.

What would you build first if code stopped being the blocker?

Follow me for daily AI breakdowns."""

D = "carousel-routine/output/2026-06-14/carousel-brandstory"
print("== brand-story carousel delivery ==")
post("header", HEADER)
post("caption", CAPTION)
upload("pdf", f"{D}/carousel-20260614.pdf", "cursor-learn-to-code-optional.pdf", "Full carousel (7 slides) — swipe on mobile")
for n in range(1, 8):
    upload(f"slide-{n}", f"{D}/slide-0{n}.png", f"slide-0{n}.png", f"Slide {n}/7")
print("== done ==")
