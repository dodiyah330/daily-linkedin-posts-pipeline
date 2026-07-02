import os
import json
import urllib.request
import urllib.parse
import ssl
import sys
import datetime
import traceback

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Read Gemini API key from .env
gemini_key = None
env_path = "./.env"
with open(env_path) as f:
    for line in f:
        if line.startswith("GEMINI_API_KEY="):
            gemini_key = line.strip().split("=", 1)[1]
            break

if not gemini_key:
    print("Error: GEMINI_API_KEY not found in .env")
    exit(1)

# Load Reddit posts data (keep top 15 posts to stay within context limits and keep focus)
reddit_posts = []
if os.path.exists("./reddit_data.json"):
    try:
        with open("./reddit_data.json") as f:
            all_r = json.load(f)
            # Sort by simulated popularity/score or just take top
            reddit_posts = all_r[:15]
    except Exception as e:
        print(f"Error loading reddit_data.json: {e}")

# Load AI News data
ai_news = []
if os.path.exists("./ai_news_data.json"):
    try:
        with open("./ai_news_data.json") as f:
            all_n = json.load(f)
            ai_news = all_n[:12]
    except Exception as e:
        print(f"Error loading ai_news_data.json: {e}")

# Load infographic run-log and calculate banned formats/topics
banned_infographic_formats = []
banned_infographic_topics = []
try:
    if os.path.exists("./infographic-run-log.json"):
        with open("./infographic-run-log.json") as f:
            info_log = json.load(f)
            
        # Last 14 topics are banned
        banned_infographic_topics = [entry["topic"] for entry in info_log[-14:] if "topic" in entry]
        
        # Last 5 formats tally
        recent_formats = [entry["format"] for entry in info_log[-5:] if "format" in entry]
        if recent_formats:
            # Last format is banned
            banned_infographic_formats.append(recent_formats[-1])
            # 3+ times count in last 5 runs
            from collections import Counter
            counts = Counter(recent_formats)
            for fmt, count in counts.items():
                if count >= 3 and fmt not in banned_infographic_formats:
                    banned_infographic_formats.append(fmt)
except Exception as e:
    print(f"Error loading infographic log: {e}")

# Load carousel hook log and calculate banned hook styles
banned_carousel_hooks = []
try:
    if os.path.exists("./carousel-hook-log.json"):
        with open("./carousel-hook-log.json") as f:
            car_log = json.load(f)
            
        recent_hooks = [entry["hook_style"] for entry in car_log[-7:] if "hook_style" in entry]
        if recent_hooks:
            # Last hook is banned
            banned_carousel_hooks.append(recent_hooks[-1])
            # 3+ times count in last 7 runs
            from collections import Counter
            counts = Counter(recent_hooks)
            for hook, count in counts.items():
                if count >= 3 and hook not in banned_carousel_hooks:
                    banned_carousel_hooks.append(hook)
except Exception as e:
    print(f"Error loading carousel log: {e}")

print("Banned Infographic Formats:", banned_infographic_formats)
print("Banned Infographic Topics:", banned_infographic_topics)
print("Banned Carousel Hook Styles:", banned_carousel_hooks)

# Format context strings
reddit_context = ""
for i, post in enumerate(reddit_posts):
    reddit_context += f"Post {i+1} [Subreddit: {post['subreddit']}]:\nTitle: {post['title']}\nContent: {post['selftext'][:400]}...\n---\n"

ai_news_context = ""
for i, item in enumerate(ai_news):
    ai_news_context += f"News {i+1} [Source: {item['source']}]:\nTitle: {item['title']}\nDescription: {item['description'][:400]}...\nURL: {item['url']}\nDate: {item['pubDate']}\n---\n"

system_prompt = """
You are Prithal Bhardwaj's AI copywriter and content orchestrator. Write a daily LinkedIn batch of exactly 11 posts (Collaborative Article, Poll, Carousel caption & slides, Infographic caption, and 7 AI news posts) based on today's feeds.

WRITING RULES:
1. Third-person observer voice, no "I" or "my" or "we" statements. (Except for CTA/Footer follow @founderswing, etc. But the post prose must be third-person).
2. Exciting but grounded tone. Excitement should feel earned. Use sentence fragments, casual contractions, or conversational pivots.
3. No jargon: no LLM, parameters, tokens, inference, fine-tuning, multimodal, latency, hallucination, RAG, prompt engineering. Explain these concepts simply.
4. No em-dashes anywhere. Use normal commas, semicolons, or periods instead.
5. Do NOT include any headline, title, or header for the posts (like 'Headline: ...' or bold title lines). Start the content of each post directly with its first sentence/hook.
6. Post structure: Hook (1-2 lines) -> Pain point -> Actionable value -> Dream picture -> Engagement question -> CTA.
7. Banned words (NEVER USE ANY): delve, underscore, vibrant, tapestry, interplay, intricate, garner, pivotal, showcase, foster, align with, landscape, key (as adjective), leverages, encompasses, facilitates, utilized, commenced, subsequent to, prior to, in order to, stands as, serves as, is a testament to, plays a vital role, plays a significant role, plays a crucial role, enduring legacy, lasting impact, indelible mark, it's important to note, it's worth noting, no discussion would be complete without, moreover, furthermore, in addition, setting the stage for, marking a shift, evolving landscape, reflects broader trends, game-changer, supercharge, real results, real strategy, real conversations, disruptive, hustle, grind, crush it, synergy, paradigm shift, thought leader, go viral, revolutionary, groundbreaking, unprecedented, cutting-edge, state-of-the-art, next-generation, empower, unlock, journey, ecosystem, world-class, comprehensive, curated, innovative, transformative, passionate, excited to share.
8. Banned LinkedIn patterns:
   - "No X. No Y. Just Z."
   - "It's not just about X. It's about Y."
   - "If you're serious about X, [do this]"
   - "And here's the kicker"
   - "X changed everything"
   - "Enter:"
   - "The best part? [short answer]"
   - Email sign-off language ("To your success")
9. Banned contrast constructions:
   - "This isn't about X, it's about Y"
   - "Not because of X. But because of Y."
   - "Rather than X, do Y"
   - "But rather"
   - "Not just X, but also Y"
   - "Not only X, but Y"
10. Varied sentence lengths. Specific numbers over adjectives. No bullets where flowing prose works better.

CONTENT SELECTION RULES:
- Post 1 (COLLABORATIVE ARTICLE): Select one hot startup/platform risk, security issue, or developer operations failure from the Reddit posts. Write 1500 to 2000 characters of prose.
- Post 2 (POLL): Select a workplace, remote work, or developer lifestyle dilemma from the Reddit posts. Provide a setup, question, 4 options, and explanation.
- Post 3 (CAROUSEL): Select a startup growth loop, marketing experiment, paywall/onboarding optimization, or product design shift from the Reddit posts. Slide 1 must have a Specific Result hook (6-8 words max).
- Post 4 (INFOGRAPHIC): Select a sector failure rate, market budget data, or startup stats from the Reddit posts (or general industry benchmarks).
- Posts 5-11 (AI NEWS POSTS 1-7): Choose the most interesting/important 7 stories from the AI News feed.
  - Post 5 (Post 1 in news list): Tool Spotlight (archetype: Tool Spotlight | emotion: WOW).
  - Post 6 (Post 2 in news list): Weekly Roundup summarizing 5 updates (archetype: Weekly Roundup | emotion: OHHH).
  - Post 7 (Post 3 in news list): Plain English Breakdown of an enterprise/complex announcement with 1 limitation/caveat (archetype: Plain English Breakdown | emotion: OHHH).
  - Post 8 (Post 4 in news list): Unfair Advantage of a new tool. MUST naturally mention "FounderWing" (archetype: Unfair Advantage | emotion: WOW).
  - Post 9 (Post 5 in news list): Career/Income shift analysis with concrete action (archetype: Career/Income | emotion: AHA).
  - Post 10 (Post 6 in news list): Hot Take/contrarian review of a fundraise or announcement. MUST naturally mention "FounderWing" (archetype: Hot Take | emotion: THINK).
  - Post 11 (Post 7 in news list): Steal This prompt/workflow under 120 words (archetype: Steal This | emotion: WOW).

OUTPUT FORMAT:
Generate the 11 posts using the exact separators and headers. Do not include any other content.

==================================================
1. COLLABORATIVE ARTICLE
==================================================
[Prose]

==================================================
2. POLL
==================================================
[Setup]

[Question]

☐ [Option A]
☐ [Option B]
☐ [Option C]
☐ [Option D]

[Explanation prompt]

==================================================
3. CAROUSEL
==================================================
CAROUSEL HOOK SELECTION:
  Banned styles: Before-After
  Chosen style: Specific Result
  Hook text: "[Hook]"

Slide 1 (Hook):
[Hook]

Slide 2:
[Slide 2 Text]

Slide 3:
[Slide 3 Text]

Slide 4:
[Slide 4 Text]

Slide 5:
[Slide 5 Text]

Slide 6:
[Slide 6 Text]

Slide 7:
[Slide 7 Text]

CAROUSEL CAPTION:
[Caption]

==================================================
4. INFOGRAPHIC
==================================================
INFOGRAPHIC CAPTION:
[Caption]

==================================================
5. POST 1
==================================================
[Post text]

Tool featured: [Name]
Source: [Source]
Archetype: Tool Spotlight | Emotion: WOW
Why this works: [Brief explanation]
Word count: [N] words

==================================================
6. POST 2
==================================================
[Post text]

Tools/stories featured: [Names]
Source: [Source]
Archetype: Weekly Roundup | Emotion: OHHH
Why this works: [Brief explanation]
Word count: [N] words

==================================================
7. POST 3
==================================================
[Post text]

Tools/stories featured: [Names]
Source: [Source]
Archetype: Plain English Breakdown | Emotion: OHHH
Why this works: [Brief explanation]
Word count: [N] words

==================================================
8. POST 4
==================================================
[Post text]

Tools/stories featured: [Names]
Source: [Source]
Archetype: Unfair Advantage | Emotion: WOW
Why this works: [Brief explanation]
Word count: [N] words

==================================================
9. POST 5
==================================================
[Post text]

Tools/stories featured: [Names]
Source: [Source]
Archetype: Career/Income | Emotion: AHA
Why this works: [Brief explanation]
Word count: [N] words

==================================================
10. POST 6
==================================================
[Post text]

Tools/stories featured: [Names]
Source: [Source]
Archetype: Hot Take | Emotion: THINK
Why this works: [Brief explanation]
Word count: [N] words

==================================================
11. POST 7
==================================================
[Post text]

What's being shared: [Workflow/Prompt]
Source: [Source]
Archetype: Steal This | Emotion: WOW
Why this works: [Brief explanation]
Word count: [N] words

CRITICAL: Do NOT write any reasoning, chain of thought, drafts, or preamble. Do NOT explain your choices. Only output the final generated posts in the exact format requested. Begin your response directly with '==================================================' and the first post separator.
"""

prompt = f"""
Here are today's feeds:

REDDIT FEED:
{reddit_context}

AI NEWS FEED:
{ai_news_context}

BANNED CAROUSEL HOOK STYLES (DO NOT USE THESE FOR POST 3 CAROUSEL SLIDE 1):
{', '.join(banned_carousel_hooks) if banned_carousel_hooks else 'None'}
Please select one of the following hook styles instead: Bold Claim, Mistake Call-Out, Myth Buster, Curiosity Gap, Number Reveal, Before-After, Checklist Promise, Framework Authority, Relatable Pain.

BANNED INFOGRAPHIC FORMATS (DO NOT USE THESE FOR POST 4 INFOGRAPHIC CAPTION & VISUAL DESIGN):
{', '.join(banned_infographic_formats) if banned_infographic_formats else 'None'}
Please select one of the following formats instead: DONUT_BREAKDOWN, TIMELINE_SHIFT, COMPARISON_SPLIT, HERO_NUMBER.

BANNED INFOGRAPHIC TOPICS (DO NOT OVERLAP WITH THESE SUBJECTS FOR THE INFOGRAPHIC):
{json.dumps(banned_infographic_topics, indent=2)}

Write the 11 posts now. Remember to strictly apply all rules (third-person, no banned words, FounderWing mentions in Post 8 and Post 10).
Ensure the Carousel and Infographic captions explicitly output their chosen styles/formats (e.g. Chosen style: [style] and Chosen format: [format]) and make sure they are NOT banned!
"""

system_prompt_json = """
You are Prithal Bhardwaj's AI visual content designer.
Based on the 11 LinkedIn posts generated for today, you must generate the structured JSON configuration for the Carousel (Post 3) and the Infographic (Post 4).

Format your output as a single valid JSON object. Do NOT wrap it in any markdown code block, and do NOT include any other text before or after the JSON.
Your JSON must strictly follow this structure:
{
  "carousel": {
    "1": {
      "HEADER_LABEL": "[Slide 1 category, e.g. DISTRIBUTION]",
      "HOOK_PART_1": "[Slide 1 Hook line 1, 3-4 words]",
      "HOOK_PART_2": "[Slide 1 Hook line 2, 3-4 words]",
      "HOOK_EMPHASIS": "[Slide 1 Highlighted word]",
      "SUBTITLE": "[Slide 1 detailed explanation, under 25 words]"
    },
    "2": {
      "PILL_LABEL": "[Pill text]",
      "EYEBROW": "[Eyebrow category]",
      "HEADLINE_PART_1": "[Title start]",
      "HEADLINE_PART_2": "[Title end]",
      "HEADLINE_EMPHASIS": "[Title emphasis]",
      "SUBHEAD": "[Short subhead sentence]",
      "BODY_TEXT": "[Description sentence]"
    },
    "3": {
      "HEADER_LABEL": "[Category]",
      "HUGE_STAT": "[Stat, e.g. 90% or $1k]",
      "CIRCLE_WORD_1": "[Circle label 1]",
      "CIRCLE_WORD_2": "[Circle label 2]",
      "HEADLINE_PART_1": "[Title start]",
      "HEADLINE_PART_2": "[Title end]",
      "HEADLINE_EMPHASIS": "[Title emphasis]",
      "BODY_TEXT": "[Description sentence]"
    },
    "4": {
      "PILL_LABEL": "[Pill text]",
      "EYEBROW": "[Eyebrow category]",
      "HEADLINE_PART_1": "[Title start]",
      "HEADLINE_PART_2": "[Title end]",
      "HEADLINE_EMPHASIS": "[Title emphasis]",
      "SUBHEAD": "[Short subhead sentence]",
      "BODY_TEXT": "[Description sentence]"
    },
    "5": {
      "HEADER_LABEL": "[Category]",
      "HUGE_STAT": "[Stat, e.g. 5x]",
      "CIRCLE_WORD_1": "[Circle label 1]",
      "CIRCLE_WORD_2": "[Circle label 2]",
      "HEADLINE_PART_1": "[Title start]",
      "HEADLINE_PART_2": "[Title end]",
      "HEADLINE_EMPHASIS": "[Title emphasis]",
      "BODY_TEXT": "[Description sentence]"
    },
    "6": {
      "HEADER_LABEL": "[Category]",
      "HUGE_STAT": "[Stat]",
      "HEADLINE_PART_1": "[Title start]",
      "HEADLINE_PART_2": "[Title end]",
      "HEADLINE_EMPHASIS": "[Title emphasis]",
      "SUBHEAD": "[Short subhead sentence]",
      "BODY_TEXT": "[Description sentence]"
    },
    "7": {
      "HEADLINE_PART_1": "[Title start]",
      "HEADLINE_PART_2": "[Title end]",
      "HEADLINE_EMPHASIS": "[Title emphasis]",
      "SUBHEAD": "[Concluding call to action subhead]"
    }
  },
  "infographic": {
    "title_main": "[Main Title]",
    "title_span": "[Highlighted Word]",
    "subtitle": "[Subtext description]",
    "badge": "📊 [Badge label]",
    "date_label": "[Month Year Report]",
    "takeaway_num": "[Stat, e.g. 95%]",
    "takeaway_text": "[Summary insight sentence]",
    "source": "Source: [Sources] | @founderswing",
    "bars": [
      { "label": "[Row 1 Label]", "value": "95%", "color": "#E63946" },
      { "label": "[Row 2 Label]", "value": "80%", "color": "#D9785B" },
      { "label": "[Row 3 Label]", "value": "75%", "color": "#E8A33D" },
      { "label": "[Row 4 Label]", "value": "64%", "color": "#5E6AD2" },
      { "label": "[Row 5 Label]", "value": "63%", "color": "#5A5A5A" },
      { "label": "[Row 6 Label]", "value": "40%", "color": "#111111" }
    ]
  }
}
"""

gemini_model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={gemini_key}"
headers = {
    "Content-Type": "application/json"
}

def make_call(system_p, user_p, max_t=4000):
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": user_p
                    }
                ]
            }
        ],
        "systemInstruction": {
            "parts": [
                {
                    "text": system_p
                }
            ]
        },
        "generationConfig": {
            "maxOutputTokens": max_t
        }
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    
    try:
        print("Calling Google Gemini 3.5 Flash...")
        with urllib.request.urlopen(req, context=ctx) as res:
            resp = json.loads(res.read().decode("utf-8"))
            if resp and isinstance(resp, dict) and "candidates" in resp and len(resp["candidates"]) > 0:
                return resp["candidates"][0]["content"]["parts"][0]["text"]
            else:
                print(f"Gemini returned unexpected response: {resp}")
    except urllib.error.HTTPError as e:
        print(f"HTTP Error calling Gemini: {e.code} - {e.reason}")
        try:
            print("Response body:", e.read().decode("utf-8"))
        except Exception as read_err:
            print("Failed to read error body:", read_err)
    except Exception as e:
        traceback.print_exc()
        print(f"Error calling Gemini: {e}")
    return None

# Step 1: Generate LinkedIn text posts
print("Starting Step 1: Generating text posts...")
post_text = make_call(system_prompt, prompt, max_t=4000)

if not post_text:
    print("Error: Failed to generate LinkedIn posts.")
    sys.exit(1)

# Save posts text
date_compact = datetime.date.today().isoformat().replace("-", "")
with open("./linkedin_posts_today.txt", "w") as f:
    f.write(post_text)
with open(f"./linkedin_posts_{date_compact}.txt", "w") as f:
    f.write(post_text)
print(f"Text posts saved to linkedin_posts_{date_compact}.txt")

# Step 2: Extract visuals JSON data based on generated text posts
print("Starting Step 2: Extracting visuals layout JSON...")
json_prompt = f"Here are the generated LinkedIn posts:\n\n{post_text}\n\nGenerate the Carousel and Infographic JSON now."
json_data_str = make_call(system_prompt_json, json_prompt, max_t=4000)

if json_data_str:
    try:
        # Clean up code blocks markdown if LLM wrapped it
        json_data_str = json_data_str.strip()
        if json_data_str.startswith("```json"):
            json_data_str = json_data_str[7:]
        elif json_data_str.startswith("```"):
            json_data_str = json_data_str[3:]
        if json_data_str.endswith("```"):
            json_data_str = json_data_str[:-3]
        json_data_str = json_data_str.strip()
        
        layout_data = json.loads(json_data_str)
        
        # Save carousel_data.json
        with open("./carousel_data.json", "w") as f:
            json.dump(layout_data.get("carousel", {}), f, indent=2)
        print("Saved carousel_data.json")
        
        # Save infographic_data.json
        with open("./infographic_data.json", "w") as f:
            json.dump(layout_data.get("infographic", {}), f, indent=2)
        print("Saved infographic_data.json")
        
    except Exception as e:
        print(f"Error parsing JSON block from response: {e}")
        print("Raw JSON string attempted:")
        print(json_data_str[:1000])
else:
    print("Warning: No JSON data generated in Step 2.")
