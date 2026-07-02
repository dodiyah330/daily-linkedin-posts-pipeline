import os
import json
import urllib.request
import urllib.error
import datetime
import time

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
    print(json.dumps({"error": f"Could not read .env: {e}"}))
    exit(1)

if not slack_token:
    print(json.dumps({"error": "SLACK_BOT_TOKEN not found in .env"}))
    exit(1)

channel = slack_channel or "C0BEG7HAXHQ"
download_dir = "./slack_downloads"
history_file = "./scheduled_history.json"

os.makedirs(download_dir, exist_ok=True)

# Load history
scheduled_history = []
if os.path.exists(history_file):
    try:
        with open(history_file) as f:
            scheduled_history = json.load(f)
    except:
        pass

# 24 hours ago timestamp
oldest_ts = str(int(time.time() - 86400))

def slack_api_call(method, params=None):
    url = f"https://slack.com/api/{method}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {slack_token}"})
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode("utf-8"))

def download_file(url_private, dest_path):
    req = urllib.request.Request(url_private, headers={"Authorization": f"Bearer {slack_token}"})
    with urllib.request.urlopen(req) as res, open(dest_path, "wb") as out:
        out.write(res.read())

try:
    history = slack_api_call("conversations.history", {"channel": channel, "oldest": oldest_ts, "limit": 100})
    if not history.get("ok"):
        print(json.dumps({"error": history.get("error")}))
        exit(1)
    
    messages = history.get("messages", [])
    
    # We are looking for messages with files in the last 24 hours
    # Specifically: the text file, the carousel PDF, and the infographic PNG.
    text_file_info = None
    carousel_file_info = None
    infographic_file_info = None
    
    # Sort messages chronologically
    messages.sort(key=lambda x: float(x.get("ts", 0)))
    
    for msg in messages:
        if "files" in msg:
            for f in msg["files"]:
                name = f.get("name", "")
                if name.endswith(".txt") and "linkedin_posts_" in name:
                    text_file_info = f
                elif name.endswith(".pdf") and "carousel" in name.lower():
                    carousel_file_info = f
                elif name.endswith(".png") and "infographic" in name.lower():
                    infographic_file_info = f
    
    if not text_file_info:
        print(json.dumps({"status": "no_new_posts"}))
        exit(0)
        
    post_id = text_file_info["id"]
    if post_id in scheduled_history:
        print(json.dumps({"status": "no_new_posts", "reason": "already_scheduled"}))
        exit(0)
        
    # Download them
    txt_path = os.path.join(download_dir, text_file_info["name"])
    download_file(text_file_info["url_private_download"], txt_path)
    
    files_downloaded = {"text": txt_path}
    
    if carousel_file_info:
        pdf_path = os.path.join(download_dir, carousel_file_info["name"])
        download_file(carousel_file_info["url_private_download"], pdf_path)
        files_downloaded["carousel_pdf"] = pdf_path
        
    if infographic_file_info:
        png_path = os.path.join(download_dir, infographic_file_info["name"])
        download_file(infographic_file_info["url_private_download"], png_path)
        files_downloaded["infographic_png"] = png_path
        
    # Update history
    scheduled_history.append(post_id)
    with open(history_file, "w") as f:
        json.dump(scheduled_history, f)
        
    print(json.dumps({
        "status": "success",
        "files": files_downloaded,
        "message": "Files downloaded successfully. Proceed to invoke browser agent to schedule."
    }))

except Exception as e:
    print(json.dumps({"error": str(e)}))
    exit(1)
