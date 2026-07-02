import urllib.request
import xml.etree.ElementTree as ET
import json
import ssl
import re
import html
import time


ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

subreddits = ["entrepreneur", "startups", "artificial", "SideProject", "ChatGPT", "passive_income"]
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

all_posts = []

for sub in subreddits:
    url = f"https://www.reddit.com/r/{sub}/top/.rss?t=week&limit=25"
    print(f"Fetching RSS for r/{sub}: {url}")
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            rss_content = response.read()
            # The XML uses namespace http://www.w3.org/2005/Atom
            root = ET.fromstring(rss_content)
            
            # Namespace map
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            entries = root.findall('atom:entry', ns)
            print(f"Found {len(entries)} entries in r/{sub}")
            
            for entry in entries:
                title_el = entry.find('atom:title', ns)
                title = title_el.text if title_el is not None else ""
                
                link_el = entry.find('atom:link', ns)
                link = link_el.attrib.get('href', '') if link_el is not None else ""
                
                content_el = entry.find('atom:content', ns)
                content_html = content_el.text if content_el is not None else ""
                
                # Convert HTML to clean text
                # We can strip tags
                clean_text = ""
                image_url = None
                if content_html:
                    # Unescape HTML entities
                    decoded_html = html.unescape(content_html)
                    
                    # Extract image url if any
                    img_match = re.search(r'<img[^>]+src="([^"]+)"', decoded_html)
                    if img_match:
                        image_url = img_match.group(1)
                    
                    # Also look for links that end with image extensions
                    link_match = re.search(r'href="([^"]+\.(?:png|jpg|jpeg|gif|webp))"', decoded_html, re.IGNORECASE)
                    if link_match and not image_url:
                        image_url = link_match.group(1)
                    
                    # Strip HTML tags to get plain text
                    # Replace <p>, <br> with newlines
                    text_with_newlines = re.sub(r'<(?:p|br|div)[^>]*>', '\n', decoded_html)
                    clean_text = re.sub(r'<[^>]+>', '', text_with_newlines)
                    clean_text = clean_text.strip()
                
                # We want to filter out posts that are just comments or authors starting with /u/ in title
                if not title or title.startswith("/u/"):
                    continue
                
                simplified_post = {
                    "subreddit": f"r/{sub}",
                    "title": title,
                    "selftext": clean_text,
                    "ups": 100, # Fake score since RSS doesn't give ups directly
                    "num_comments": 10, # Fake comments count
                    "url": link,
                    "image_url": image_url
                }
                all_posts.append(simplified_post)
    except Exception as e:
        print(f"Error fetching r/{sub}: {e}")
    time.sleep(3.0)


# Save to reddit_data.json
with open("./reddit_data.json", "w") as f:
    json.dump(all_posts, f, indent=2)

print(f"Saved {len(all_posts)} posts to ./reddit_data.json")
