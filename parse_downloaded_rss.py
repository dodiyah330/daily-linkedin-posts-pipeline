import xml.etree.ElementTree as ET
import json
import re
import html
import os

files_mapping = {
    "entrepreneur": "/Users/prithal/.gemini/antigravity/brain/38ead829-acea-4d7d-a827-f9956f33c3e3/.system_generated/steps/648/content.md",
    "startups": "/Users/prithal/.gemini/antigravity/brain/38ead829-acea-4d7d-a827-f9956f33c3e3/.system_generated/steps/664/content.md",
    "artificial": "/Users/prithal/.gemini/antigravity/brain/38ead829-acea-4d7d-a827-f9956f33c3e3/.system_generated/steps/666/content.md",
    "SideProject": "/Users/prithal/.gemini/antigravity/brain/38ead829-acea-4d7d-a827-f9956f33c3e3/.system_generated/steps/668/content.md",
    "ChatGPT": "/Users/prithal/.gemini/antigravity/brain/38ead829-acea-4d7d-a827-f9956f33c3e3/.system_generated/steps/670/content.md",
    "passive_income": "/Users/prithal/.gemini/antigravity/brain/38ead829-acea-4d7d-a827-f9956f33c3e3/.system_generated/steps/672/content.md"
}

all_posts = []

for sub, filepath in files_mapping.items():
    if not os.path.exists(filepath):
        print(f"File for r/{sub} not found at {filepath}")
        continue
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Split out markdown headers
        parts = content.split("---", 1)
        xml_content = parts[1].strip() if len(parts) > 1 else content
        
        # Clean up XML string if it contains markdown formatting
        if xml_content.startswith("```"):
            # Strip code blocks if any
            lines = xml_content.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            xml_content = "\n".join(lines).strip()

        root = ET.fromstring(xml_content)
        
        # Namespace map
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        entries = root.findall('atom:entry', ns)
        print(f"r/{sub}: Found {len(entries)} entries")
        
        for entry in entries:
            title_el = entry.find('atom:title', ns)
            title = title_el.text if title_el is not None else ""
            
            link_el = entry.find('atom:link', ns)
            link = link_el.attrib.get('href', '') if link_el is not None else ""
            
            content_el = entry.find('atom:content', ns)
            content_html = content_el.text if content_el is not None else ""
            
            # Clean HTML to text
            clean_text = ""
            image_url = None
            if content_html:
                decoded_html = html.unescape(content_html)
                
                # Image URL
                img_match = re.search(r'<img[^>]+src="([^"]+)"', decoded_html)
                if img_match:
                    image_url = img_match.group(1)
                
                link_match = re.search(r'href="([^"]+\.(?:png|jpg|jpeg|gif|webp))"', decoded_html, re.IGNORECASE)
                if link_match and not image_url:
                    image_url = link_match.group(1)
                
                text_with_newlines = re.sub(r'<(?:p|br|div)[^>]*>', '\n', decoded_html)
                clean_text = re.sub(r'<[^>]+>', '', text_with_newlines)
                clean_text = clean_text.strip()
            
            if not title or title.startswith("/u/"):
                continue
            
            simplified_post = {
                "subreddit": f"r/{sub}",
                "title": title,
                "selftext": clean_text,
                "ups": 100,
                "num_comments": 10,
                "url": link,
                "image_url": image_url
            }
            all_posts.append(simplified_post)
            
    except Exception as e:
        print(f"Error parsing r/{sub}: {e}")

# Save to reddit_data.json
with open("./reddit_data.json", "w", encoding="utf-8") as f:
    json.dump(all_posts, f, indent=2)

print(f"Saved total of {len(all_posts)} posts to ./reddit_data.json")
