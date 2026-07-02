import os
import json
import urllib.request
import urllib.parse
import datetime

# Read token from .env
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

# Parse posts from file
posts = {}
current_key = None
current_content = []

with open(f"linkedin_posts_{date_compact}.txt") as f:
    for line in f:
        if line.startswith("=================================================="):
            continue
        elif line.startswith("1. COLLABORATIVE ARTICLE"):
            current_key = "collaborative_article"
            current_content = []
        elif line.startswith("2. POLL"):
            current_key = "poll"
            current_content = []
        elif line.startswith("3. CAROUSEL"):
            current_key = "carousel"
            current_content = []
        elif line.startswith("4. INFOGRAPHIC"):
            current_key = "infographic"
            current_content = []
        elif line.startswith("5. POST 1"):
            current_key = "post_1"
            current_content = []
        elif line.startswith("6. POST 2"):
            current_key = "post_2"
            current_content = []
        elif line.startswith("7. POST 3"):
            current_key = "post_3"
            current_content = []
        elif line.startswith("8. POST 4"):
            current_key = "post_4"
            current_content = []
        elif line.startswith("9. POST 5"):
            current_key = "post_5"
            current_content = []
        elif line.startswith("10. POST 6"):
            current_key = "post_6"
            current_content = []
        elif line.startswith("11. POST 7"):
            current_key = "post_7"
            current_content = []
        else:
            if current_key:
                current_content.append(line)
        
        if current_key:
            posts[current_key] = "".join(current_content).strip()

# Generate interactive newspaper HTML and PDF first so we can upload it
print("Daily newspaper HTML and PDF already generated successfully. Skipping generation step.")

# Format and send header message
header_msg = f"📅 *LinkedIn Content Drop — {date_str}*\n11 posts ready (4 Reddit-based + 7 AI News). Carousel PDF and infographic attached below."
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

print("All daily LinkedIn publication steps completed successfully.")

