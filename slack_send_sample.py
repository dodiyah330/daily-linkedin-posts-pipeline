#!/usr/bin/env python3
"""Send the Varun-lane SAMPLE (1 contrarian text post + 1 carousel) to #linkedin-content
for voice review. Not the scheduled drop."""
import json, os, subprocess, urllib.request, urllib.parse, time

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
TOKEN = subprocess.check_output("grep '^SLACK_BOT_TOKEN=' .env | cut -d'=' -f2", shell=True).decode().strip()
CHANNEL = subprocess.check_output("grep '^SLACK_CHANNEL_ID=' .env | cut -d'=' -f2", shell=True).decode().strip() or "C0BEG7HAXHQ"

def api(method, payload, json_body=True):
    url = f"https://slack.com/api/{method}"
    if json_body:
        data = json.dumps(payload).encode("utf-8"); ct = "application/json; charset=utf-8"
    else:
        data = urllib.parse.urlencode(payload).encode("utf-8"); ct = "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=data, headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": ct})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode("utf-8"))

def post_text(label, text):
    r = api("chat.postMessage", {"channel": CHANNEL, "text": text, "unfurl_links": False, "unfurl_media": False})
    print(f"  [{label}] {'OK' if r.get('ok') else 'ERR ' + str(r.get('error'))}"); time.sleep(0.8)

def upload(label, path, title, comment):
    if not os.path.exists(path): print(f"  [{label}] MISSING {path}"); return
    g = api("files.getUploadURLExternal", {"filename": os.path.basename(path), "length": os.path.getsize(path)}, json_body=False)
    if not g.get("ok"): print(f"  [{label}] getURL ERR {g.get('error')}"); return
    subprocess.run(["curl", "-s", "-F", f"file=@{path}", g["upload_url"]], stdout=subprocess.DEVNULL)
    c = api("files.completeUploadExternal", {"files": [{"id": g["file_id"], "title": title}], "channel_id": CHANNEL, "initial_comment": comment})
    print(f"  [{label}] {os.path.basename(path)} {'OK' if c.get('ok') else 'ERR ' + str(c.get('error'))}"); time.sleep(0.8)

HEADER = "🧪 *Varun-lane SAMPLE for review — June 14, 2026*\nNew positioning (the \"Varun Mayya of LinkedIn\"). 1 contrarian text post + 1 carousel. This is a voice check, not the scheduled drop."

CONTRARIAN = """Most people learning AI are quietly falling behind.

They are buying the courses. Bookmarking the prompt libraries. Watching another two hour video on a tool they will never open again. It feels like progress. It feels responsible. It is the safest way to stay exactly where you are.

Here is the uncomfortable part. Almost nobody is getting ahead by studying AI. They are getting ahead by pointing it at one real thing they already do, and refusing to do that thing the slow way ever again.

The marketer who fed it her actual campaigns is now weeks ahead of the one who finished the certification. The teacher who runs his lesson plans through it every Sunday is not smarter, he just started. While everyone else collects tutorials, a smaller group is collecting reps.

The gap forming right now is not between people who understand AI and people who do not. It is between people who used it this morning and people who are still getting ready to begin.

You do not need another course. You need to take the one task you dread most this week and do it with AI sitting right next to you.

What is the one task you would hand to AI tomorrow if you stopped waiting to feel ready?

Follow @founderswing for more."""

CAROUSEL_CAPTION = """━━━ CAROUSEL — "5 jobs AI is quietly rewriting" ━━━

AI is not deleting jobs. It is quietly rewriting the tasks inside them.
The asset-making, the drafting, the number crunching is going to AI. The judgment, the taste, and knowing what to build is becoming the whole job.
Which half of your work just changed?
Save this and follow @founderswing for more."""

SDIR = "carousel-routine/output/2026-06-14/carousel-sample"

print("== sample delivery ==")
post_text("header", HEADER)
post_text("contrarian", CONTRARIAN)
upload("carousel-pdf", f"{SDIR}/carousel-20260614.pdf", "5-jobs-ai-rewriting-20260614.pdf", CAROUSEL_CAPTION)
for n in range(1, 8):
    upload(f"slide-{n}", f"{SDIR}/slide-0{n}.png", f"slide-0{n}.png", f"Slide {n}/7")
print("== done ==")
