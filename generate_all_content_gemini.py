import json
import urllib.request
import ssl
import sys
import os
import datetime
import time
import traceback

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Read OpenRouter API key from .env
openrouter_key = None
with open("./.env") as f:
    for line in f:
        if line.startswith("OPENROUTER_API_KEY="):
            openrouter_key = line.strip().split("=", 1)[1]
            break

if not openrouter_key:
    print("Error: OPENROUTER_API_KEY not found in .env")
    exit(1)

# API Endpoint URL for OpenRouter
url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {openrouter_key}",
    "Content-Type": "application/json"
}

def call_gemini(system_prompt, prompt, max_tokens=4000):
    # Rename to call_gemini to avoid altering downstream calls, but route to OpenRouter
    payload = {
        "model": "google/gemma-4-31b-it:free",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 4000
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    
    # Retry logic for rate limits (429)
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, context=ctx) as res:
                resp = json.loads(res.read().decode("utf-8"))
                if resp and "choices" in resp and len(resp["choices"]) > 0:
                    text = resp["choices"][0]["message"]["content"]
                    return text
                else:
                    print(f"OpenRouter returned unexpected response format: {resp}")
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"Rate limited (429) on OpenRouter. Retrying in {10 * (attempt + 1)}s...")
                time.sleep(10 * (attempt + 1))
            else:
                print(f"HTTP Error calling OpenRouter: {e.code} - {e.reason}")
                try:
                    print("Error body:", e.read().decode("utf-8"))
                except:
                    pass
                break
        except Exception as e:
            traceback.print_exc()
            print(f"Error calling OpenRouter: {e}")
            break
        time.sleep(2)
    return None

# Load context data for references
reddit_posts = []
if os.path.exists("./reddit_data.json"):
    with open("./reddit_data.json") as f:
        reddit_posts = json.load(f)[:15]

ai_news = []
if os.path.exists("./ai_news_data.json"):
    with open("./ai_news_data.json") as f:
        ai_news = json.load(f)[:12]

# Shared writing instructions based on content-doctrine.md and voice-profile.md
writing_rules = """
WRITING RULES:
1. Third-person observer voice, no "I" or "my" or "we" statements. (Except in CTAs: "follow me for daily AI breakdowns", "follow me for more").
2. Exciting but grounded tone. Excitement should feel earned. Use sentence fragments, casual contractions, or conversational pivots.
3. No jargon: no LLM, parameters, tokens, inference, fine-tuning, multimodal, latency, hallucination, RAG, prompt engineering. Explain these concepts simply.
4. No em-dashes anywhere. Use normal commas, semicolons, or periods instead.
5. Do NOT include any headline, title, or header for the posts (like 'Headline: ...' or bold title lines). Start the content of the post directly with its first sentence/hook.
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
"""

system_prompt_main = f"""You are Prithal Bhardwaj's AI copywriter. Write a single, highly engaging LinkedIn post based on the instructions.
{writing_rules}
"""

posts_to_generate = [
    {
        "id": "1. COLLABORATIVE ARTICLE",
        "prompt": f"""Write a COLLABORATIVE ARTICLE post.
Topic: Service business cash flow vs accounting.
Prose: Write about a founder running a subcontractor-heavy service business doing 3 million dollars in revenue, who constantly feels broke because they collect from customers upfront and pay subcontractors on net-30 terms. Explain that accounting and cash allocation are different. The breakthrough is to allocate deposits immediately into segments (Subcontractors, Tax, OpEx, Profit) to feel secure.
Write exactly 1500 to 2000 characters of flowing prose. Start directly with the hook. No titles.
"""
    },
    {
        "id": "2. POLL",
        "prompt": f"""Write a POLL post.
Topic: MBA vs. Entrepreneurship for early career.
Setup: Ask early career professionals whether to pursue a Tier-1 MBA (to gain network, exposure, and credibility) or skip it to take the entrepreneurial risk and build a business directly.
Question: What is the most reliable path for early career professionals aiming to build their own business?
Options:
☐ Pursue Tier-1 MBA first
☐ Build startup directly now
☐ Work in startups for 2 years first
☐ Do MBA part-time while building
Provide the Setup, the Question, the 4 Options, and an Explanation prompt. Do not include any title.
"""
    },
    {
        "id": "3. CAROUSEL",
        "prompt": f"""Write a CAROUSEL post content.
Topic: College dorm to stage panel (the long unsexy journey of credibility).
Chosen Hook Style: Before-After (6-8 words max, curiosity gap).
Slide 1 Hook: "From ignored student to panel speaker"
Slides 2-6: Step-by-step process of a student building a company in their dorm room, losing pitch competitions, being ignored by professors, doing 6 years of unsexy private work, and finally being invited back to speak on an innovation panel alongside VCs. Emphasize that credibility doesn't come first; the work does. Maximum 2 sentences per slide.
Slide 7 CTA: "Follow for more posts on startup loops."
Caption: Slide 1 hook, what the carousel covers, engagement question, CTA to save/repost. Max 4 lines.
Format clearly labeled with Slide 1, Slide 2, etc. and CAROUSEL CAPTION:
"""
    },
    {
        "id": "4. INFOGRAPHIC",
        "prompt": f"""Write an INFOGRAPHIC caption.
Topic: Focus fragmentation and workplace interruptions (Microsoft Work Trend Index).
Caption: Hook, insight beyond the chart (employees get interrupted every 2 minutes or 275 times/day, average worker receives 117 emails and 153 Teams messages daily, 40% are online at 6 AM. The shift from execution to being an "agent boss" overseeing digital labor), engagement question, CTA. Do not include titles.
"""
    },
    {
        "id": "5. POST 1",
        "prompt": f"""Write POST 1 (Tool Spotlight).
Tool: Deezer's new AI music detector.
Description: It can identify AI-generated music tracks across major platforms (Spotify, Apple Music) to protect artists and maintain catalog integrity.
Archetype: Tool Spotlight | Emotion: WOW.
Start directly with the hook. No titles.
"""
    },
    {
        "id": "6. POST 2",
        "prompt": f"""Write POST 2 (Weekly Roundup).
Summarize these 4 major updates from the past week:
1. Meta reportedly unwinds its 2 billion dollar Manus AI acquisition deal following government pressure.
2. Jeff Bezos's Prometheus raises a massive 12 billion dollars to build generalist physical-world engineering robots.
3. KPMG pulls its flagship AI usage report after discovery of severe hallucinated data.
4. Theker raises 85 million dollars for generalist factory robots that learn arbitrary manual tasks without specialization.
Archetype: Weekly Roundup | Emotion: OHHH.
Format: Intro hook, numbered list (each item max 2 lines), closing, question. No titles.
"""
    },
    {
        "id": "7. POST 3",
        "prompt": f"""Write POST 3 (Plain English Breakdown).
Topic: Jeff Bezos's Prometheus 12 billion dollar raise.
Explain the raise: Prometheus raised 12 billion dollars to build an "artificial general engineer" for the physical world. Explain in plain English what this means: they are building robots that don't just do one task (like pick a box) but can troubleshoot, repair, and engineer physical systems like human mechanics or technicians.
Archetype: Plain English Breakdown | Emotion: OHHH.
Start directly with the hook. No titles.
"""
    },
    {
        "id": "8. POST 4",
        "prompt": f"""Write POST 4 (Unfair Advantage).
Tool: Theker's generalist factory robot.
Description: Theker raised 85 million dollars to build robots that don't specialize in a single task, allowing small factories to deploy them for arbitrary manual operations that traditionally required custom, expensive automation programming.
MUST naturally mention "FounderWing" in the body text or call to action.
Archetype: Unfair Advantage | Emotion: WOW.
Start directly with the hook. No titles.
"""
    },
    {
        "id": "9. POST 5",
        "prompt": f"""Write POST 5 (Career/Income).
Topic: KPMG pulling its AI usage report due to hallucinations.
Description: KPMG had to retract its flagship AI usage report because the data was generated by hallucinating models. This proves that relying on pure AI generation without human verification is a major liability. Professionals must stack AI productivity with strict human-centric judgment.
Archetype: Career/Income | Emotion: AHA.
Start directly with the hook. No titles.
"""
    },
    {
        "id": "10. POST 6",
        "prompt": f"""Write POST 6 (Hot Take).
Topic: Meta's new AI unit being called a "soul-crushing gulag" by its engineers.
Hot Take: The race for AGI has created a toxic work culture where engineers are treated as disposable inputs. True startup moats are built on sustainable engineering cultures and distribution, not by burning out talent in a compute race.
MUST naturally mention "FounderWing" in the body text.
Archetype: Hot Take | Emotion: THINK.
Start directly with the hook. No titles.
"""
    },
    {
        "id": "11. POST 7",
        "prompt": f"""Write POST 7 (Steal This).
Topic: How to audit business reports for AI hallucinations.
Description: Provide a specific workflow/prompt to copy: how to set up a two-agent audit loop where one LLM generates a draft and a second "critic" agent audits it against raw source documents to prevent KPMG-style public relations failures.
Length: Under 120 words.
Archetype: Steal This | Emotion: WOW.
Start directly with the hook. No titles.
"""
    }
]

generated_posts = {}
all_output_text = ""

print("Generating 11 Main Posts...")
for item in posts_to_generate:
    print(f"Generating {item['id']}...")
    result = call_gemini(system_prompt_main, item["prompt"], max_tokens=4000)
    if not result:
        print(f"Error: Failed to generate {item['id']}.")
        sys.exit(1)
    
    generated_posts[item["id"]] = result
    
    # Format text block
    all_output_text += "==================================================\n"
    all_output_text += f"{item['id']}\n"
    all_output_text += "==================================================\n"
    all_output_text += result.strip() + "\n\n"
    time.sleep(1)

# Write output text files
date_compact = datetime.date.today().isoformat().replace("-", "")
with open("linkedin_posts_today.txt", "w") as f:
    f.write(all_output_text)
with open(f"linkedin_posts_{date_compact}.txt", "w") as f:
    f.write(all_output_text)
print(f"11 Main Posts saved to linkedin_posts_{date_compact}.txt")


# Now generate the Carousel JSON
print("Generating Carousel JSON...")
carousel_json_prompt = f"""
You are Prithal Bhardwaj's AI visual content designer.
Based on the generated Carousel post (Post 3) below, you must generate the structured JSON configuration for the Carousel slides.

Post Content:
{generated_posts.get("3. CAROUSEL", "")}

Format your output as a single valid JSON object. Do NOT wrap it in any markdown code block, and do NOT include any other text before or after the JSON.
Your JSON must strictly follow this structure:
{{
  "1": {{
    "HEADER_LABEL": "FOUNDER JOURNEY",
    "HOOK_PART_1": "From ignored student",
    "HOOK_PART_2": "to stage panel",
    "HOOK_EMPHASIS": "STAGE PANEL",
    "SUBTITLE": "A student spent 6 years in a dorm room building a medical startup while being ignored by professors. Yesterday, they returned to speak on a panel next to VCs."
  }},
  "2": {{
    "PILL_LABEL": "THE GRIND",
    "EYEBROW": "YEAR ONE",
    "HEADLINE_PART_1": "Ignored in the",
    "HEADLINE_PART_2": "college dorm room",
    "HEADLINE_EMPHASIS": "IGNORED",
    "SUBHEAD": "Losing pitch competitions and dismissed by professors.",
    "BODY_TEXT": "The early days were spent cutting up metal cans in a dorm, trying to figure out how to send electricity through tape."
  }},
  "3": {{
    "HEADER_LABEL": "THE SHIFT",
    "HUGE_STAT": "6 Yrs",
    "CIRCLE_WORD_1": "Unsexy",
    "CIRCLE_WORD_2": "Work",
    "HEADLINE_PART_1": "The long road",
    "HEADLINE_PART_2": "to build credibility",
    "HEADLINE_EMPHASIS": "CREDIBILITY",
    "BODY_TEXT": "No venture funding, no public applause. Just years of private execution making the product undeniable."
  }},
  "4": {{
    "PILL_LABEL": "THE RETURN",
    "EYEBROW": "YEAR SIX",
    "HEADLINE_PART_1": "Invited back to",
    "HEADLINE_PART_2": "speak on stage",
    "HEADLINE_EMPHASIS": "STAGE",
    "SUBHEAD": "Sitting between VCs and executives.",
    "BODY_TEXT": "The very professor who watched them lose pitch competitions years ago reached out to invite them back to teach others."
  }},
  "5": {{
    "HEADER_LABEL": "THE LESSON",
    "HUGE_STAT": "Work",
    "CIRCLE_WORD_1": "First",
    "CIRCLE_WORD_2": "Always",
    "HEADLINE_PART_1": "Credibility does not",
    "HEADLINE_PART_2": "come before the product",
    "HEADLINE_EMPHASIS": "PRODUCT",
    "BODY_TEXT": "You don't get the seat by being interesting. You get it by doing unsexy work that nobody is watching."
  }},
  "6": {{
    "HEADER_LABEL": "THE ADVICE",
    "HUGE_STAT": "Trust",
    "HEADLINE_PART_1": "People won't see",
    "HEADLINE_PART_2": "your future early on",
    "HEADLINE_EMPHASIS": "FUTURE",
    "SUBHEAD": "Most people can't see the future from where they stand.",
    "BODY_TEXT": "That is not their fault. It is just the geometry of being early. Keep building anyway."
  }},
  "7": {{
    "HEADLINE_PART_1": "Build the future",
    "HEADLINE_PART_2": "and protect your stack",
    "HEADLINE_EMPHASIS": "BUILD",
    "SUBHEAD": "Follow @founderswing for more breakdowns on startup loops and strategy."
  }}
}}
Generate slide JSON configs reflecting today's Carousel content. Make sure all values are filled in.
"""

carousel_json_str = call_gemini("You are a JSON writer. Only output raw JSON.", carousel_json_prompt, max_tokens=4000)
if carousel_json_str:
    carousel_json_str = carousel_json_str.strip()
    if carousel_json_str.startswith("```json"):
        carousel_json_str = carousel_json_str[7:]
    elif carousel_json_str.startswith("```"):
        carousel_json_str = carousel_json_str[3:]
    if carousel_json_str.endswith("```"):
        carousel_json_str = carousel_json_str[:-3]
    carousel_json_str = carousel_json_str.strip()
    
    try:
        carousel_data = json.loads(carousel_json_str)
        with open("./carousel_data.json", "w") as f:
            json.dump(carousel_data, f, indent=2)
        print("Saved carousel_data.json successfully!")
    except Exception as e:
        print(f"Error parsing Carousel JSON: {e}")
        print("Raw text:", carousel_json_str)

# Now generate the Infographic JSON
print("Generating Infographic JSON...")
infographic_json_prompt = f"""
You are Prithal Bhardwaj's AI visual content designer.
Based on the generated Infographic post (Post 4) below, you must generate the structured JSON configuration for the Infographic.

Post Content:
{generated_posts.get("4. INFOGRAPHIC", "")}

Format your output as a single valid JSON object. Do NOT wrap it in any markdown code block, and do NOT include any other text before or after the JSON.
Your JSON must strictly follow this structure:
{{
  "title_main": "The Daily Workplace Noise Index",
  "title_span": "Workplace Interruption Stats",
  "subtitle": "How the constant stream of emails, chats, and meetings fragments the modern workday.",
  "badge": "📊 WORKPLACE NOISE",
  "date_label": "2025 Microsoft Report",
  "takeaway_num": "2 Mins",
  "takeaway_text": "is the average time between interruptions for a typical employee, leading to severe focus fragmentation.",
  "source": "Source: Microsoft Work Trend Index | @founderswing",
  "bars": [
    {{ "label": "Daily Interruptions (Meetings/Chats) - 275", "value": "91%", "color": "#E63946" }},
    {{ "label": "Lack of Time/Energy to Finish Work", "value": "80%", "color": "#D9785B" }},
    {{ "label": "Teams Messages Received Daily - 153", "value": "51%", "color": "#E8A33D" }},
    {{ "label": "Checking Email Before 6:00 AM", "value": "40%", "color": "#5E6AD2" }},
    {{ "label": "Emails Received Daily - 117", "value": "39%", "color": "#5A5A5A" }}
  ]
}}
Generate a similar JSON for the infographic based on the Microsoft Work Trend Index data.
"""

infographic_json_str = call_gemini("You are a JSON writer. Only output raw JSON.", infographic_json_prompt, max_tokens=4000)
if infographic_json_str:
    infographic_json_str = infographic_json_str.strip()
    if infographic_json_str.startswith("```json"):
        infographic_json_str = infographic_json_str[7:]
    elif infographic_json_str.startswith("```"):
        infographic_json_str = infographic_json_str[3:]
    if infographic_json_str.endswith("```"):
        infographic_json_str = infographic_json_str[:-3]
    infographic_json_str = infographic_json_str.strip()
    
    try:
        infographic_data = json.loads(infographic_json_str)
        with open("./infographic_data.json", "w") as f:
            json.dump(infographic_data, f, indent=2)
        print("Saved infographic_data.json successfully!")
    except Exception as e:
        print(f"Error parsing Infographic JSON: {e}")
        print("Raw text:", infographic_json_str)


# Now generate the 5 Performance posts
print("Generating 5 Performance Posts...")
performance_system_prompt = f"""You are the Founders Wing Performance Engine. Write 5 report-driven posts reverse-engineered from actual analytics.
{writing_rules}
"""

perf_posts_list = [
    {
        "id": "1. FOUNDER PSYCHOLOGY CONTRARIAN",
        "prompt": f"""Write the FOUNDER PSYCHOLOGY CONTRARIAN performance post.
Topic: Stop talking about your startup before it's real. Explain that most founders leak execution energy by telling everyone about their ideas, using external validation to convince themselves. Real builders shut up, keep their heads down, and let the product speak for itself.
Start directly with the hook. No titles.
"""
    },
    {
        "id": "2. LOADED POLL",
        "prompt": f"""Write the LOADED POLL performance post.
Topic: "What is the best way to validate a startup idea in 2026?"
Question: What is the most reliable way to validate market demand before building a single feature?
Options:
☐ Charging upfront for a waitlist
☐ Running cold outreach campaigns
☐ Getting 10 letter-of-intent (LOIs)
☐ Analyzing search volume data
Provide Setup, Question, Options, and Explanation. No titles.
"""
    },
    {
        "id": "3. AI NEWS + IMPLICATIONS",
        "prompt": f"""Write the AI NEWS + IMPLICATIONS performance post.
Topic: KPMG pulling its AI usage report due to hallucinations.
Implication: Businesses are learning the hard way that AI-generated content is a massive liability. The new operational baseline is "trust but audit." Verification is now the primary bottleneck, and companies need strict human-in-the-loop protocols.
Start directly with the hook. No titles.
"""
    },
    {
        "id": "4. STORY CAROUSEL",
        "prompt": f"""Write the STORY CAROUSEL performance post content.
Topic: Copying an existing business vs. inventing a new one.
Slide 1: "The copycat advantage"
Slides 2-6: Case study of how a founder spent 12 months trying to build a unique Web3 platform and failed, then pivoted to building a simple, localized CRM for mechanic shops (copying existing software but focusing on local sales execution) and scaled to $50k/mo in 6 months.
Slide 7: "Execution beats originality every time."
CAROUSEL CAPTION: [prose caption]
No titles. Format clearly labeled.
"""
    },
    {
        "id": "5. DATA VISUAL + HOOK",
        "prompt": f"""Write the DATA VISUAL + HOOK performance post.
Topic: "Employees are interrupted every 2 minutes."
Caption: Explain that companies blame remote work for productivity drops, but the real culprit is communication overload (Teams, Slack, email). Focus is the ultimate competitive advantage.
Start directly with the hook. No titles.
"""
    }
]

print("Generating 5 Performance Posts sequentially...")
performance_posts_text = ""
for item in perf_posts_list:
    print(f"Generating {item['id']}...")
    result = call_gemini(performance_system_prompt, item["prompt"], max_tokens=4000)
    if not result:
        print(f"Error: Failed to generate {item['id']}.")
        sys.exit(1)
        
    # Format text block
    performance_posts_text += "==================================================\n"
    performance_posts_text += f"{item['id']}\n"
    performance_posts_text += "==================================================\n"
    performance_posts_text += result.strip() + "\n\n"
    time.sleep(1)

with open(f"performance_posts_{date_compact}.txt", "w") as f:
    f.write(performance_posts_text)
print(f"5 Performance Posts saved to performance_posts_{date_compact}.txt")

print("\n--- Content Generation Completed Successfully ---")
