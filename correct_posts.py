import os
import json
import urllib.request
import urllib.parse
import ssl
import datetime
import time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Read OpenRouter API key from .env
openrouter_key = None
env_path = "./.env"
with open(env_path) as f:
    for line in f:
        if line.startswith("OPENROUTER_API_KEY="):
            openrouter_key = line.strip().split("=", 1)[1]
            break

if not openrouter_key:
    print("Error: OPENROUTER_API_KEY not found in .env")
    exit(1)

# Read the current draft
with open("./linkedin_posts_today.txt", "r") as f:
    draft_content = f.read()

correction_prompt = """
You are a professional LinkedIn editor. Edit the following draft of 11 LinkedIn posts to make the following corrections:

1. Remove any mention of FounderWing, Founders Wing, or @founderswing from all posts.

2. End every post CTA with exactly "Follow me." (not "Follow for more" or "@founderswing").

3. Banned Word Cleanups:
   - In Post 2 (Poll), change "key developer" (since "key" as an adjective is banned) to "senior developer" or just "developer".
   - In Post 2 (AI News, which is Post 6 in the output list), change "supercharge AI research" to "accelerate AI research" or "support AI research".
   - In Post 7 (AI News, which is Post 11 in the output list), change "leverage AI" to "use AI".
   - Ensure the word "leverage", "leverages", "leveraging", "supercharge", "key" (as adjective), and other banned words from this list are NOT in the text: delve, underscore, vibrant, tapestry, interplay, intricate, garner, pivotal, showcase, foster, align with, landscape, leverages, encompasses, facilitates, utilized, commenced, subsequent to, prior to, in order to, stands as, serves as, is a testament to, plays a vital role, plays a significant role, plays a crucial role, enduring legacy, lasting impact, indelible mark, it's important to note, it's worth noting, no discussion would be complete without, moreover, furthermore, in addition, setting the stage for, marking a shift, evolving landscape, reflects broader trends, game-changer, supercharge, real results, real strategy, real conversations, disruptive, hustle, grind, crush it, synergy, paradigm shift, thought leader, go viral, revolutionary, groundbreaking, unprecedented, cutting-edge, state-of-the-art, next-generation, empower, unlock, journey, ecosystem, world-class, comprehensive, curated, innovative, transformative, passionate, excited to share.

4. Keep the exact output formatting, separators, and headings. Output ONLY the 11 posts, with no other text.

Here is the current draft:
""" + draft_content

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {openrouter_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": "google/gemma-4-31b-it:free",
    "max_tokens": 4000,
    "messages": [
        {"role": "user", "content": correction_prompt}
    ]
}

req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers=headers,
    method="POST"
)

# Retry logic for OpenRouter transient errors and rate limits
success = False
for attempt in range(5):
    try:
        print(f"Calling OpenRouter to apply corrections (attempt {attempt+1}/5)...")
        with urllib.request.urlopen(req, context=ctx) as res:
            resp = json.loads(res.read().decode("utf-8"))
            corrected_text = resp["choices"][0]["message"]["content"]
            
            # Save to today and date_compact paths
            date_compact = datetime.date.today().isoformat().replace("-", "")
            with open("./linkedin_posts_today.txt", "w") as f:
                f.write(corrected_text)
            with open(f"./linkedin_posts_{date_compact}.txt", "w") as f:
                f.write(corrected_text)
            print(f"Corrected posts saved to linkedin_posts_today.txt and linkedin_posts_{date_compact}.txt")
            success = True
            break
    except urllib.error.HTTPError as e:
        if e.code == 429:
            wait_time = 15 * (attempt + 1)
            print(f"Rate limited (429) on OpenRouter. Retrying in {wait_time}s...")
            time.sleep(wait_time)
        else:
            print(f"HTTP Error correcting posts: {e.code} - {e.reason}")
            try:
                print("Error body:", e.read().decode("utf-8"))
            except:
                pass
            time.sleep(5)
    except Exception as e:
        print(f"Transient error correcting posts: {e}. Retrying in 5s...")
        time.sleep(5)

if not success:
    print("Error: Failed to apply corrections after 5 attempts.")
    exit(1)
