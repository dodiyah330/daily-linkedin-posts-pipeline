import os
import json
import urllib.request
import urllib.parse
import ssl

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

system_prompt = """
You are Prithal Bhardwaj's AI news content generator. Write 3 LinkedIn posts (Posts 1-3) about the week's AI developments.

Apply the following style rules strictly:
- Third-person observer voice, no "I" statements.
- Exciting but grounded tone. Excitement should feel earned. Use sentence fragments, casual contractions, or conversational pivots.
- No jargon: no LLM, parameters, tokens, inference, fine-tuning, multimodal, API, latency, hallucination, RAG, prompt engineering.
- Every technical fact must be followed immediately by its human consequence (the "so what" rule).
- No em-dashes anywhere. Use normal commas, semicolons, or periods instead.
- 150-300 words for each post.
- Sentence case headings.
- Hook under 120 characters, never start with "I".
- Line break after every 1-2 sentences. Use white space between blocks.
- No external links in post body ("link in comments" if needed).
- No hashtags or maximum 1 at the very end.
- Every post must end with a specific question (never "what do you think?").
- Avoid banned words: game-changer, disruptive, hustle, grind, crush it, synergy, paradigm shift, thought leader, go viral, revolutionary, groundbreaking, unprecedented, cutting-edge, state-of-the-art, next-generation.

Here are the news items of the week (June 1-4, 2026) to cover:
- Post 1 (Tool Spotlight): MWM AI launched "AI Mobile Squad" (Designer, PM, Developer agents) that builds production-ready apps in minutes.
- Post 2 (Weekly Roundup): 5 updates (Anthropic confidential IPO filing, IBM & Google Cloud partnership to scale enterprise agents, S&P Global's Credit Memo Builder agentic platform, NVIDIA's RTX Spark PC chips, DARPA/NSF's AI Forge program).
- Post 3 (Plain English Breakdown): IBM & Google Cloud partnership to scale enterprise agent platforms. Translate this enterprise news into human terms. Include one honest limitation or caveat.

Structure the output EXACTLY like the previous posts file format:
==================================================
5. POST 1
==================================================
Headline: [Post 1 Headline]

[Post 1 Text]

Tool featured: [Name]
Source: [Source]
Archetype: Tool Spotlight | Emotion: WOW
Why this works: [Brief explanation]
Word count: [N] words

==================================================
6. POST 2
==================================================
Headline: [Post 2 Headline]

[Post 2 Text]

Tools/stories featured: [Names]
Source: [Source]
Archetype: Weekly Roundup | Emotion: OHHH
Why this works: [Brief explanation]
Word count: [N] words

==================================================
7. POST 3
==================================================
Headline: [Post 3 Headline]

[Post 3 Text]

Tools/stories featured: [Names]
Source: [Source]
Archetype: Plain English Breakdown | Emotion: OHHH
Why this works: [Brief explanation]
Word count: [N] words
"""

prompt = "Write Post 1, Post 2, and Post 3 now. Do not include any intro or outro conversational text, just output the posts formatted exactly as requested."

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {openrouter_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": "~anthropic/claude-sonnet-latest",
    "max_tokens": 1500,
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
}

req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers=headers,
    method="POST"
)

try:
    print("Calling OpenRouter Claude 3.5 Sonnet to generate AI news posts...")
    with urllib.request.urlopen(req, context=ctx) as res:
        resp = json.loads(res.read().decode("utf-8"))
        text = resp["choices"][0]["message"]["content"]
        
        # Save to file
        out_path = "./ai_news_posts_today.txt"
        with open(out_path, "w") as f:
            f.write(text)
        print(f"AI news posts generated and saved to {out_path}")
        
except urllib.error.HTTPError as e:
    print(f"HTTP Error calling OpenRouter API: {e.code} {e.reason}")
    try:
        print("Response body:", e.read().decode("utf-8"))
    except Exception:
        pass
except Exception as e:
    print(f"Error calling OpenRouter API: {e}")
