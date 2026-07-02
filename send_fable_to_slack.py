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
        
        req = urllib.request.Request(
            upload_url,
            data=file_data,
            method="POST"
        )
        with urllib.request.urlopen(req) as res:
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

# Define paths
pdf_dir = f"./carousel-routine/output/{date_str}/carousel-branded"
pdf_path = os.path.join(pdf_dir, f"linkedin-carousel-{date_str}.pdf")

# Header message
header_msg = f"🎨 *Claude Fable 5 Launch Carousel — {date_str}*\nHere is the custom-built Claude Fable carousel (Cream & Bronze theme) with the Curiosity Gap hook."
send_slack_message(header_msg)

# Upload the PDF carousel
upload_slack_file(
    pdf_path,
    f"claude-fable-carousel-{date_str}.pdf",
    f"━━━ CLAUDE FABLE 5 CAROUSEL PDF ━━━"
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

print("Slack notification and file upload completed successfully.")
