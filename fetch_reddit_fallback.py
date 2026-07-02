import urllib.request
import json
import ssl
import time

# Disable SSL verification issues if any
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

urls = [
    "https://www.reddit.com/r/entrepreneur/top.json?limit=25&t=week&raw_json=1",
    "https://www.reddit.com/r/startups/top.json?limit=25&t=week&raw_json=1",
    "https://www.reddit.com/r/artificial/top.json?limit=25&t=week&raw_json=1",
    "https://www.reddit.com/r/SideProject/top.json?limit=20&t=week&raw_json=1",
    "https://www.reddit.com/r/ChatGPT/top.json?limit=20&t=week&raw_json=1",
    "https://www.reddit.com/r/passive_income/top.json?limit=20&t=week&raw_json=1"
]

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

all_posts = []

for url in urls:
    print(f"Fetching: {url}")
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            data = json.loads(response.read().decode('utf-8'))
            posts = data.get('data', {}).get('children', [])
            print(f"Found {len(posts)} posts")
            for post in posts:
                post_data = post.get('data', {})
                # Extract image URLs
                image_url = None
                if 'url_overridden_by_dest' in post_data and any(ext in post_data['url_overridden_by_dest'] for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                    image_url = post_data['url_overridden_by_dest']
                elif 'preview' in post_data and 'images' in post_data['preview'] and len(post_data['preview']['images']) > 0:
                    image_url = post_data['preview']['images'][0].get('source', {}).get('url')
                elif post_data.get('thumbnail') and post_data['thumbnail'].startswith('http'):
                    image_url = post_data['thumbnail']

                simplified_post = {
                    "subreddit": post_data.get("subreddit"),
                    "title": post_data.get("title"),
                    "selftext": post_data.get("selftext"),
                    "ups": post_data.get("ups"),
                    "num_comments": post_data.get("num_comments"),
                    "url": "https://www.reddit.com" + post_data.get("permalink", ""),
                    "image_url": image_url
                }
                all_posts.append(simplified_post)
        time.sleep(1) # Be nice to Reddit
    except Exception as e:
        print(f"Error fetching {url}: {e}")

# Save to reddit_data.json
with open("./reddit_data.json", "w") as f:
    json.dump(all_posts, f, indent=2)

print(f"Saved {len(all_posts)} posts to ./reddit_data.json")
