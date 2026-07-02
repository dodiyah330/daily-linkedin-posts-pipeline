import os
import json
import urllib.request
import urllib.parse
import time
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

env_path = "./.env"
apify_token = None
with open(env_path) as f:
    for line in f:
        if line.startswith("APIFY_API_KEY="):
            apify_token = line.strip().split("=", 1)[1]
            break

if not apify_token:
    print("Error: APIFY_API_KEY not found in .env")
    exit(1)

# StartUrls for the actor
payload = {
    "startUrls": [
        {"url": "https://www.reddit.com/r/entrepreneur/top/?t=week"},
        {"url": "https://www.reddit.com/r/startups/top/?t=week"},
        {"url": "https://www.reddit.com/r/artificial/top/?t=week"},
        {"url": "https://www.reddit.com/r/SideProject/top/?t=week"},
        {"url": "https://www.reddit.com/r/ChatGPT/top/?t=week"},
        {"url": "https://www.reddit.com/r/passive_income/top/?t=week"}
    ],
    "maxItems": 80
}

url = f"https://api.apify.com/v2/acts/trudax~reddit-scraper-lite/runs?token={apify_token}"
req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    print("Triggering Apify Reddit scraper run...")
    with urllib.request.urlopen(req, context=ctx) as res:
        resp = json.loads(res.read().decode("utf-8"))
        run_id = resp["data"]["id"]
        dataset_id = resp["data"]["defaultDatasetId"]
        print(f"Run started. Run ID: {run_id}, Dataset ID: {dataset_id}")
        
    # Poll for completion
    status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={apify_token}"
    while True:
        req_status = urllib.request.Request(status_url)
        with urllib.request.urlopen(req_status, context=ctx) as res:
            run_data = json.loads(res.read().decode("utf-8"))["data"]
            status = run_data["status"]
            print(f"Current status: {status}")
            if status in ["SUCCEEDED", "FAILED", "TIMED-OUT", "ABORTED"]:
                break
        time.sleep(5)
        
    if status == "SUCCEEDED":
        # Get items
        items_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={apify_token}&limit=100"
        req_items = urllib.request.Request(items_url)
        with urllib.request.urlopen(req_items, context=ctx) as res:
            items = json.loads(res.read().decode("utf-8"))
            print(f"Fetched {len(items)} raw items from Apify.")
            
            all_posts = []
            for item in items:
                # We want actual posts, not comments
                if item.get("dataType") == "comment" or item.get("category") == "comment":
                    continue
                title = item.get("title")
                if not title or title.startswith("/u/"):
                    continue
                
                # Check for images
                image_url = None
                if item.get("image_url"):
                    image_url = item["image_url"]
                elif item.get("url") and any(ext in item["url"].lower() for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]):
                    image_url = item["url"]
                
                permalink = item.get("url") or item.get("permalink") or ""
                if permalink.startswith("/"):
                    permalink = "https://www.reddit.com" + permalink
                
                simplified_post = {
                    "subreddit": item.get("communityName") or item.get("subreddit") or item.get("subreddit_name_prefixed") or "r/SideProject",
                    "title": title,
                    "selftext": item.get("body") or item.get("selftext") or item.get("text") or "",
                    "ups": item.get("score") or item.get("ups") or 0,
                    "num_comments": item.get("num_comments") or 0,
                    "url": permalink,
                    "image_url": image_url
                }
                all_posts.append(simplified_post)
            
            # Save to reddit_data.json
            with open("./reddit_data.json", "w") as f:
                json.dump(all_posts, f, indent=2)
            print(f"Saved {len(all_posts)} posts to ./reddit_data.json")
    else:
        print("Apify run failed.")
except Exception as e:
    print(f"Error fetching from Apify: {e}")
