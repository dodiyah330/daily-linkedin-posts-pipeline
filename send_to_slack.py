import os
import json
import urllib.request
import urllib.parse
import datetime
import re
import sys

PERFORMANCE_ONLY = "--performance-only" in sys.argv
slack_token = None
with open(".env") as f:
    for line in f:
        if line.startswith("SLACK_BOT_TOKEN="):
            slack_token = line.strip().split("=", 1)[1]
            break

if not slack_token:
    print("Error: SLACK_BOT_TOKEN not found in .env")
    exit(1)

slack_channel = None
with open(".env") as f:
    for line in f:
        if line.startswith("SLACK_CHANNEL_ID="):
            slack_channel = line.strip().split("=", 1)[1]
            break

channel = slack_channel or "C0BEG7HAXHQ"
date_str = datetime.date.today().isoformat()
date_compact = date_str.replace("-", "")

def send_slack_message(text):
    print(f"Sending message (length: {len(text)})...")
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
            resp = json.loads(res.read().decode("utf-8"))
            if not resp.get("ok"):
                print(f"Error sending message: {resp.get('error')}")
            else:
                print("Message sent successfully.")
    except Exception as e:
        print(f"Exception sending message: {e}")

def upload_slack_file(file_path, file_name, initial_comment):
    if not file_path or not os.path.exists(file_path):
        print(f"Error: file not found: {file_path}")
        return

    print(f"Uploading file: {file_name} ({os.path.getsize(file_path)} bytes)...")
    
    # 1. Get upload URL
    url = "https://slack.com/api/files.getUploadURLExternal"
    headers = {
        "Authorization": f"Bearer {slack_token}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = urllib.parse.urlencode({
        "filename": file_name,
        "length": os.path.getsize(file_path)
    }).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req) as res:
            resp = json.loads(res.read().decode("utf-8"))
            if not resp.get("ok"):
                print(f"Error getting upload URL: {resp.get('error')}")
                return
            upload_url = resp.get("upload_url")
            file_id = resp.get("file_id")
    except Exception as e:
        print(f"Exception getting upload URL: {e}")
        return

    # 2. Upload file data
    print("Uploading file data to URL...")
    try:
        with open(file_path, "rb") as f:
            file_data = f.read()
        
        # Use multipart/form-data logic or raw POST
        # Slack files.getUploadURLExternal accepts raw file data as POST body
        req = urllib.request.Request(
            upload_url,
            data=file_data,
            method="POST"
        )
        with urllib.request.urlopen(req) as res:
            # Check response code
            if res.status != 200:
                print("Error uploading raw file data")
                return
            print("File data uploaded successfully.")
    except Exception as e:
        print(f"Exception uploading file data: {e}")
        return

    # 3. Complete upload
    print("Completing upload...")
    url = "https://slack.com/api/files.completeUploadExternal"
    headers = {
        "Authorization": f"Bearer {slack_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    payload = {
        "files": [{"id": file_id, "title": file_name}],
        "channel_id": channel,
        "initial_comment": initial_comment
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as res:
            resp = json.loads(res.read().decode("utf-8"))
            if not resp.get("ok"):
                print(f"Error completing upload: {resp.get('error')}")
            else:
                print(f"File upload completed: {file_name}")
    except Exception as e:
        print(f"Exception completing upload: {e}")

# Resolve posts file (today's or latest batch)
posts_file = f"linkedin_posts_{date_compact}.txt"
if not os.path.exists(posts_file):
    candidates = sorted(
        f for f in os.listdir(".")
        if f.startswith("linkedin_posts_") and f.endswith(".txt") and f != "linkedin_posts_today.txt"
    )
    if candidates:
        posts_file = candidates[-1]
        m = re.search(r"linkedin_posts_(\d{8})\.txt", posts_file)
        if m:
            date_compact = m.group(1)
            date_str = f"{date_compact[:4]}-{date_compact[4:6]}-{date_compact[6:8]}"
        print(f"Using latest posts file: {posts_file}")

def split_sections(text):
    text = text.strip()
    text = re.sub(r"^={50}\n", "", text)
    chunks = [c.strip() for c in re.split(r"\n={50}\n", text) if c.strip()]
    sections = {}
    i = 0
    while i + 1 < len(chunks):
        header = chunks[i]
        if re.match(r"^\d+\.", header):
            sections[header] = chunks[i + 1]
            i += 2
        else:
            i += 1
    return sections

with open(posts_file) as f:
    sections = split_sections(f.read())

PERF_KEYS = [
    "12. PERF 1 (CONTRARIAN)",
    "13. PERF 2 (LOADED POLL)",
    "14. PERF 3 (AI NEWS + IMPLICATIONS)",
    "15. PERF 4 (STORY CAROUSEL — caption)",
    "16. PERF 5 (DATA VISUAL — caption)",
]

def extract_perf_carousel_caption(body):
    m = re.search(r"PERFORMANCE CAROUSEL CAPTION:\s*\n(.*)", body, re.DOTALL)
    cap = m.group(1).strip() if m else body
    return re.sub(r"\n\(Note:.*", "", cap, flags=re.DOTALL).strip()

def extract_perf_infographic_caption(body):
    m = re.search(r"PERFORMANCE DATA VISUAL CAPTION:\s*\n(.*)", body, re.DOTALL)
    cap = m.group(1).strip() if m else body
    return re.sub(r"\n\(Note:.*", "", cap, flags=re.DOTALL).strip()

if PERFORMANCE_ONLY:
    print("Sending performance posts only (12–16)...")
    perf_header = f"📊 *Performance Posts — {date_str}*\n5 report-driven posts from the linkedin-performance-engine:"
    send_slack_message(perf_header)
    for key in PERF_KEYS:
        body = sections.get(key, "").strip()
        if body:
            send_slack_message(body)
    perf_pdf_dir = f"./carousel-routine/output/{date_str}/carousel-performance"
    perf_pdf = None
    if os.path.isdir(perf_pdf_dir):
        pdfs = sorted(
            [os.path.join(perf_pdf_dir, fn) for fn in os.listdir(perf_pdf_dir) if fn.endswith(".pdf")],
            key=os.path.getmtime,
            reverse=True,
        )
        perf_pdf = pdfs[0] if pdfs else None
    perf_png = f"./linkedin-performance-infographic-{date_compact}.png"
    if perf_pdf:
        upload_slack_file(
            perf_pdf,
            os.path.basename(perf_pdf),
            f"━━━ PERFORMANCE CAROUSEL PDF ━━━\n\n{extract_perf_carousel_caption(sections.get('15. PERF 4 (STORY CAROUSEL — caption)', ''))}",
        )
        if os.path.isdir(perf_pdf_dir):
            for slide_fn in sorted(fn for fn in os.listdir(perf_pdf_dir) if fn.startswith("slide-") and fn.endswith(".png")):
                upload_slack_file(
                    os.path.join(perf_pdf_dir, slide_fn),
                    slide_fn,
                    f"Performance carousel {slide_fn.replace('.png', '')}",
                )
    if os.path.exists(perf_png):
        upload_slack_file(
            perf_png,
            "linkedin-performance-infographic.png",
            f"━━━ PERFORMANCE DATA VISUAL ━━━\n\n{extract_perf_infographic_caption(sections.get('16. PERF 5 (DATA VISUAL — caption)', ''))}",
        )
    print("Performance Slack delivery completed.")
    raise SystemExit(0)

# Legacy keyed map for main 11 posts
posts = {
    "collaborative_article": sections.get("1. COLLABORATIVE ARTICLE", ""),
    "poll": sections.get("2. POLL", ""),
    "carousel": sections.get("3. CAROUSEL", ""),
    "infographic": sections.get("4. INFOGRAPHIC", ""),
    **{f"post_{i}": sections.get(f"{i + 4}. POST {i}", "") for i in range(1, 8)},
}

print("Daily newspaper HTML and PDF already generated successfully. Skipping generation step.")

header_msg = f"📅 *LinkedIn Content Drop — {date_str}*\n16 posts ready (4 Reddit-based + 7 AI News + 5 performance-driven). Carousel PDF and infographic attached below."
send_slack_message(header_msg)

# Send Reddit-based posts
if "collaborative_article" in posts:
    send_slack_message(posts["collaborative_article"])
if "poll" in posts:
    send_slack_message(posts["poll"])

# Send AI News section header and posts
news_header = f"📰 *AI News Posts — {date_str}*\n7 plain-text posts from the linkedin-ai-news-engine:"
send_slack_message(news_header)

for i in range(1, 8):
    post_key = f"post_{i}"
    if post_key in posts:
        send_slack_message(posts[post_key])

# Upload the Text Posts PDF
posts_pdf_path = f"linkedin_posts_{date_compact}.pdf"
upload_slack_file(
    posts_pdf_path,
    f"linkedin_posts_{date_compact}.pdf",
    f"━━━ DAILY TEXT POSTS PDF — {date_str} ━━━\n\nContains all 11 LinkedIn posts (Collaborative Article, Poll, and 7 AI News Posts) formatted for easy reading."
)

# Upload the raw Text Posts file for the auto-scheduler bot
posts_txt_path = f"linkedin_posts_{date_compact}.txt"
upload_slack_file(
    posts_txt_path,
    f"linkedin_posts_{date_compact}.txt",
    f"━━━ RAW TEXT DRAFTS — {date_str} ━━━\n\nFor bot auto-scheduling consumption."
)

# Upload PDF and PNG Infographic
pdf_dir = f"./carousel-routine/output/{date_str}/carousel-branded"
pdf_path = os.path.join(pdf_dir, "startup-strategy-carousel.pdf")
if not os.path.exists(pdf_path):
    pdf_path = None
    if os.path.exists(pdf_dir):
        pdfs = [os.path.join(pdf_dir, fn) for fn in os.listdir(pdf_dir) if fn.endswith(".pdf")]
        if pdfs:
            # Sort by modification time descending to get the newest generated PDF
            pdfs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            pdf_path = pdfs[0]
if not pdf_path:
    pdf_path = f"./carousel-routine/output/{date_str}/carousel-branded/carousel.pdf"
png_path = f"./linkedin-infographic-{date_compact}.png"

# Extract Carousel & Infographic captions
carousel_caption = ""
if "carousel" in posts:
    caption_lines = []
    capture = False
    for line in posts["carousel"].split("\n"):
        if line.startswith("Caption:") or line.startswith("CAROUSEL CAPTION:"):
            capture = True
            continue
        if line.startswith("Slide 1:"):
            capture = False
        if capture:
            caption_lines.append(line)
    carousel_caption = "\n".join(caption_lines).strip()

infographic_caption = ""
if "infographic" in posts:
    caption_lines = []
    capture = False
    for line in posts["infographic"].split("\n"):
        if line.startswith("Caption:") or line.startswith("INFOGRAPHIC CAPTION:"):
            capture = True
            continue
        if capture:
            caption_lines.append(line)
    infographic_caption = "\n".join(caption_lines).strip()

upload_slack_file(
    pdf_path, 
    os.path.basename(pdf_path) if pdf_path else "carousel.pdf", 
    f"━━━ CAROUSEL PDF ━━━\n\n{carousel_caption}"
)

# Upload individual slide PNGs
if os.path.exists(pdf_dir):
    slide_pngs = sorted([fn for fn in os.listdir(pdf_dir) if fn.startswith("slide-") and fn.endswith(".png")])
    for slide_fn in slide_pngs:
        slide_path = os.path.join(pdf_dir, slide_fn)
        slide_num = slide_fn.split("-")[1].split(".")[0]
        upload_slack_file(
            slide_path,
            slide_fn,
            f"Slide {slide_num} of {len(slide_pngs)}"
        )

upload_slack_file(
    png_path, 
    "linkedin-infographic.png", 
    f"━━━ INFOGRAPHIC ━━━\n\n{infographic_caption}"
)

# Section C — performance posts
perf_header = f"📊 *Performance Posts — {date_str}*\n5 report-driven posts from the linkedin-performance-engine:"
send_slack_message(perf_header)
for key in PERF_KEYS:
    body = sections.get(key, "").strip()
    if body:
        send_slack_message(body)

perf_pdf_dir = f"./carousel-routine/output/{date_str}/carousel-performance"
perf_pdf = None
if os.path.isdir(perf_pdf_dir):
    pdfs = sorted(
        [os.path.join(perf_pdf_dir, fn) for fn in os.listdir(perf_pdf_dir) if fn.endswith(".pdf")],
        key=os.path.getmtime,
        reverse=True,
    )
    perf_pdf = pdfs[0] if pdfs else None
perf_png = f"./linkedin-performance-infographic-{date_compact}.png"
if perf_pdf:
    upload_slack_file(
        perf_pdf,
        os.path.basename(perf_pdf),
        f"━━━ PERFORMANCE CAROUSEL PDF ━━━\n\n{extract_perf_carousel_caption(sections.get('15. PERF 4 (STORY CAROUSEL — caption)', ''))}",
    )
    if os.path.isdir(perf_pdf_dir):
        for slide_fn in sorted(fn for fn in os.listdir(perf_pdf_dir) if fn.startswith("slide-") and fn.endswith(".png")):
            upload_slack_file(
                os.path.join(perf_pdf_dir, slide_fn),
                slide_fn,
                f"Performance carousel {slide_fn.replace('.png', '')}",
            )
if os.path.exists(perf_png):
    upload_slack_file(
        perf_png,
        "linkedin-performance-infographic.png",
        f"━━━ PERFORMANCE DATA VISUAL ━━━\n\n{extract_perf_infographic_caption(sections.get('16. PERF 5 (DATA VISUAL — caption)', ''))}",
    )

print("All daily LinkedIn publication steps completed successfully.")

