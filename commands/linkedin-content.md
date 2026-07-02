# linkedin-content

Fetches trending AI-impact content from Reddit, finds shareable visuals, researches data for an infographic, and generates ready-to-publish LinkedIn posts. Output is posts only — no preamble, no explanations, no extra words.

---

## STEP 0 — Load the content doctrine (do this first)

```bash
cat ./content-doctrine.md
```

`content-doctrine.md` is the north star and overrides any older topic guidance in this file. Two hard rules before you pick anything:
- **The DROP list is banned.** No technical tutorials, tool config, "steal this prompt" tactics, SaaS metrics, indie-hacker build-in-public / MVP / validation / agency tactics, or dry news relay. These are exactly the posts that underperform.
- **Every topic must pass the 4-part topic filter** (Reach, Stakes, Altitude, Edge). We write for ambitious generalists who want to know where AI is going and how to get ahead, not for founders or engineers chasing tactics.

The formats below stay (article, poll, carousel, infographic). The subject matter moves up to AI's impact on work, income, skills, and the future.

---

## STEP 1 — Fetch Reddit content via Apify (primary source)

Run this Bash command. It starts the actor and waits synchronously for results:

```bash
curl -s -X POST \
  "https://api.apify.com/v2/acts/trudax~reddit-scraper-lite/run-sync-get-dataset-items?token=YOUR_APIFY_API_KEY&timeout=120&memory=1024" \
  -H "Content-Type: application/json" \
  -d '{
    "startUrls": [
      {"url": "https://www.reddit.com/r/artificial/top/?t=week"},
      {"url": "https://www.reddit.com/r/ChatGPT/top/?t=week"},
      {"url": "https://www.reddit.com/r/singularity/top/?t=week"},
      {"url": "https://www.reddit.com/r/Futurology/top/?t=week"},
      {"url": "https://www.reddit.com/r/technology/top/?t=week"},
      {"url": "https://www.reddit.com/r/OpenAI/top/?t=week"}
    ],
    "maxItems": 80
  }'
```

If Apify returns an error, is empty, or times out, fall back immediately to these free Reddit JSON endpoints via WebFetch (fetch all in parallel):

- https://www.reddit.com/r/artificial/top.json?limit=25&t=week&raw_json=1
- https://www.reddit.com/r/ChatGPT/top.json?limit=25&t=week&raw_json=1
- https://www.reddit.com/r/singularity/top.json?limit=25&t=week&raw_json=1
- https://www.reddit.com/r/Futurology/top.json?limit=20&t=week&raw_json=1
- https://www.reddit.com/r/technology/top.json?limit=20&t=week&raw_json=1
- https://www.reddit.com/r/OpenAI/top.json?limit=20&t=week&raw_json=1

From all fetched content, extract for each post: title, body/selftext, upvotes, comment count, URL, and any image URLs found in url_overridden_by_dest, preview.images, or thumbnail fields.

---

## STEP 2 — Find a shareable image

Scan all fetched Reddit posts for one that contains a high-quality image (look for fields: `url_overridden_by_dest`, `preview.images[0].source.url`, `thumbnail`). Prioritise images that are:

- Charts, graphs, data visualisations, or ranked lists
- Screenshots of tools, revenue dashboards, or growth stats
- Infographics with clear data
- Comparison visuals or before/after results

If no strong image is found on Reddit, use WebSearch to find one recent, shareable visual in the AI/startups/business niche from a credible source (Statista, a16z, YC, Forbes, etc.).

Store: the direct image URL and the post/source context that surrounds it.

---

## STEP 3 — Research data for the infographic

Use WebSearch to find ONE concrete ranked dataset published or updated in 2025 or 2026 in the niche. Target datasets with 6 to 10 comparable categories and specific numbers. Good targets:

- Top AI tools ranked by active user count or growth rate
- Online business models ranked by median monthly revenue
- Startup survival rates by category after 3 years
- AI adoption rates by industry sector
- Best-performing LinkedIn content formats by engagement rate
- Fastest-growing SaaS categories by ARR

Pick the dataset with the sharpest numbers. Note the exact source URL and publication date.

---

## STEP 4 — Select source material for each post type

From all gathered content, pick the single best match for each. **Every post type must use a different source thread or topic, and every one must pass the content-doctrine topic filter (Reach, Stakes, Altitude, Edge).** Reframe each around AI's impact on work, income, skills, or the future — never startup tactics or how-to.

- **COLLABORATIVE ARTICLE**: The sharpest take on how AI is changing work or life — a contrarian thread, a "this job is changing" discussion, or a real story about AI reshaping someone's career or options. Pick meaning and consequence, not mechanics.
- **POLL**: A future-of-work or AI-age dilemma people genuinely feel and split on (which skill survives, will AI take this role, is this still worth learning). No obvious right answer. Different thread than the Collaborative Article.
- **CAROUSEL**: A shift worth explaining or mapping — "the jobs AI is quietly rewriting," "what work looks like by 2027," "the skills that just lost their value." A thesis or story across 5+ slides, never a tactical listicle. Different thread than above.
- **INFOGRAPHIC**: Use the data found in Step 3. One striking "this is the shift" stat about AI's impact on work, income, or skills. Topic must differ from all other posts.

Before writing, list the chosen sources, confirm no two share the same thread or topic, and confirm each passes the topic filter.

---

## STEP 5 — Write all 5 posts and generate the infographic

Apply every writing rule below without exception to every post. Then output all 5 in the exact format specified at the end. Nothing before the first separator. Nothing after the last post.

---

## WRITING RULES — APPLY TO EVERY POST

### Voice and perspective

Write in third-person observer voice. The author is a sharp, informed solo entrepreneur reporting on patterns, data, and founder behaviour. No "I" statements anywhere.

### Human realism (human-like imperfections)

To ensure the posts sound authentically human and not AI-generated:
- Mimic casual human writing habits: occasionally miss a comma or omit a full stop at the end of a line.
- Incorporate natural, conversational slang or informal transitions where appropriate (e.g., "made cash faster than" instead of "generated revenue quicker than").
- Keep the style informal and conversational, avoiding overly polished, clinical sentence structures.

Good examples of the voice (note: AI-impact lane, broad audience — not founder tactics):
- "Most people using AI at work right now are making the same quiet mistake."
- "A thread on r/Futurology this week laid out something most people are not ready to hear about their jobs."
- "The people who got ahead with AI this year all did one specific thing differently."

### Post structure (all text posts must follow this in order)

1. **Hook** — 1 or 2 lines. Makes the reader stop scrolling. Grounded in a specific number, surprising finding, or pattern.
2. **Pain point** — Name the specific frustration. Concrete and recognisable, not abstract. Use the language real people use when complaining about this problem.
3. **Actionable value** — What to do about it. Specific enough to apply within 24 hours.
4. **Dream picture** — What changes once someone actually applies this. Make it tangible: more leads, less time wasted, a specific outcome.
5. **Engagement question** — One pointed question that is easy to answer in one sentence. Never "What do you think?" — make it specific.
6. **CTA** — One only. Follow, save, or repost. Never stack more than one.

### Hook styles — rotate each time the skill runs

Pick the most fitting style for the topic:

- **Curiosity**: "The way most solo entrepreneurs approach [topic] is exactly why they stay stuck at [problem]."
- **Contrarian**: "Most people teaching [topic] online have never actually done it themselves."
- **Transformation**: "[Metric] went from [low number] to [high number] in [time period]. Here is what actually moved it."
- **Question**: "What separates the solo entrepreneurs who [succeed] from the ones still stuck at [problem] three years later?"
- **Story**: "A founder posted something on Reddit this week about [topic] that reframes the whole conversation."
- **Listicle**: "Five things nobody mentions before you start [topic]."

### Carousel hook styles — rotate each time the skill runs

The carousel slide 1 hook is the most important element. It must stop the scroll in milliseconds. Use 6 to 8 words max on the cover slide. Maintain a curiosity gap: never give the answer on slide 1.

Read `./carousel-hook-log.json` before picking a hook style. The log tracks which styles have been used recently. Apply these rotation rules:

1. The style used in the **last run** is **banned** this run
2. If any style appears **3+ times in the last 7 entries**, it is also banned this run
3. Pick the most fitting non-banned style for today's topic
4. After generating the carousel, append an entry to `./carousel-hook-log.json`

Pick the most fitting non-banned style for the carousel topic:

- **Bold Claim**: A provocative stat or statement that creates immediate tension. Keep it under 6 words. Example: "The pricing mistake costing you $50k/year."
- **Specific Result**: A concrete before-after transformation with hard numbers. Example: "0 to 40% conversion in 90 days."
- **Mistake Call-Out**: Name the exact mistake the reader is probably making. Example: "5 hiring mistakes killing your startup."
- **Myth Buster**: Challenge an accepted belief head-on. Example: "Why your morning routine is sabotaging your business."
- **Curiosity Gap**: Withhold the punchline to force the swipe. Example: "I lost a $500k deal because of one thing."
- **Number Reveal**: Promise a finite, specific list that delivers clear value. Example: "7 marketing blindspots costing you customers."
- **Before-After**: Show a dramatic contrast between problem and outcome. Example: "From $50k to $500k in 18 months."
- **Checklist Promise**: Signal immediately actionable, saveable content. Example: "The 10-point checklist for high-converting landing pages."
- **Framework Authority**: Position a proprietary structured method. Example: "The 3-step framework that doubled our leads."
- **Relatable Pain**: Agitate a specific pain point the reader feels right now. Example: "Stop doing this on LinkedIn (it kills your reach)."

#### Carousel hook log format

Each entry in `./carousel-hook-log.json` follows this structure:
```json
{
  "date": "2026-05-30",
  "hook_style": "Bold Claim",
  "hook_text": "The pricing mistake costing you $50k/year",
  "carousel_topic": "SaaS pricing strategy",
  "carousel_format": "DATA_STORY"
}
```

Keep last 30 entries. Trim older ones on each write.

### Banned vocabulary — never use any of these words or phrases

delve, underscore, vibrant, tapestry, interplay, intricate, garner, pivotal, showcase, foster, align with, landscape (used abstractly), key (as a vague adjective), leverages, encompasses, facilitates, utilized, commenced, subsequent to, prior to, in order to, stands as, serves as, is a testament to, plays a vital role, plays a significant role, plays a crucial role, enduring legacy, lasting impact, indelible mark, it's important to note, it's worth noting, no discussion would be complete without, moreover, furthermore, in addition, setting the stage for, marking a shift, evolving landscape, reflects broader trends, game-changer, supercharge, real results, real strategy, real conversations

### Banned LinkedIn-specific patterns — never use any of these

- "No X. No Y. Just Z." triple-denial hooks
- "It's not just about X. It's about Y." reframes
- "If you're serious about X, [do this]" closes
- "And here's the kicker"
- "X changed everything"
- "Enter:" followed by a framework name
- "The best part? [short answer]"
- Email sign-off language ("To your success", "To your freedom")

### Banned contrast constructions

- "This isn't about X, it's about Y"
- "Not because of X. But because of Y."
- "Rather than X, do Y" (unless substantially expanded)
- "But rather" anywhere
- "Not just X, but also Y"
- "Not only X, but Y"

### Formatting rules

- No em-dashes anywhere in any post
- Sentence case in all headings and slide labels (not Title Case)
- No bullet lists where flowing prose works better
- Specific numbers over adjectives: "grew 340% in 6 months" not "grew significantly"
- Varied sentence lengths deliberately — mix short punchy sentences with longer ones when the idea needs room
- One idea per paragraph
- Closing line lands on something new, never restates what came before
- No "-ing phrase" analysis tags: "highlighting the importance of", "underscoring its significance"
- No vague attributions like "experts say" or "many believe" without a named source

---

## OUTPUT FORMAT

Output exactly this. Nothing before the first separator. Nothing after the last block.

━━━ COLLABORATIVE ARTICLE ━━━

[Complete thought piece, 1500 to 2000 characters. Sentence-case subheadings. Grounded in the Reddit thread or insight selected. Full 6-part post structure embedded as flowing prose — hook opens the piece, pain point follows, actionable value forms the body, dream picture closes the main section, engagement question precedes the CTA. Write this as a complete article a solo entrepreneur in AI/startups/online business would be proud to publish under their name.]

━━━ POLL ━━━

[2 to 3 sentence setup caption that establishes the debate without giving away a preferred answer]

[Poll question as a single standalone line]

☐ [Option A]
☐ [Option B]
☐ [Option C]
☐ [Option D]

[One short line below that invites people to explain their vote in the comments]

━━━ CAROUSEL ━━━

Hook style used: [CAROUSEL_HOOK_STYLE from carousel-hook-log.json rotation]

Slide 1:
[Hook following the selected carousel hook style. 6 to 8 words max. Creates a curiosity gap. Never reveals the answer on this slide.]

Slide 2:
[First point with a specific number or concrete fact. 2 to 3 sentences.]

Slide 3:
[Second point with a specific number or concrete fact. 2 to 3 sentences.]

Slide 4:
[Third point with a specific number or concrete fact. 2 to 3 sentences.]

Slide 5:
[Fourth point with a specific number or concrete fact. 2 to 3 sentences.]

Slide 6:
[Fifth point or the single insight that ties the whole carousel together. 2 to 3 sentences.]

Slide 7:
[Single CTA. "Follow for more posts on [specific topic area]." Nothing else on this slide.]

Caption:
[Hook line. What the carousel covers in one sentence. Engagement question. CTA to save or repost. 4 lines max total.]

━━━ MULTI-IMAGE POST ━━━

Image: [Direct URL to the image]

Caption:
[Hook line that makes the image worth stopping for]
[2 to 3 sentences that add genuine insight beyond what the image shows on its own — context, implication, or what this means for solo entrepreneurs]
[Engagement question]
[Single CTA]

━━━ INFOGRAPHIC ━━━

[Generate a complete, self-contained HTML file. Save it to ./linkedin-infographic.html using the Write tool. Then output the full HTML inline here as well so the user can see it.

The HTML must:
- Have zero external dependencies (no Google Fonts, no CDN, no images)
- Use a system font stack: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif
- Be designed at 1080x1080px for LinkedIn square format
- Render as a clean, professional data visualisation matching the style of the example provided

Layout structure (top to bottom):
1. White background (#FFFFFF)
2. Bold title in sentence case, ~28px, near the top
3. Italic subtitle directly below, ~16px, grey (#555555)
4. Legend row: small coloured squares with category labels, centred
5. Horizontal bar chart: category labels left-aligned, bars, value circles on far right
6. For each bar row: alternating row background (#F9F9F9 and #FFFFFF), label on left (~160px wide), coloured bar filling proportionally to value, coloured circle on right with the number inside in white bold text
7. Small data source credit at bottom left in ~11px grey text

Colour scheme:
- Category 1 (first type): #D4A843 (warm gold)
- Category 2 (second type): #6BA368 (muted green)
- Category 3 (third type, if applicable): #6B6BB5 (slate blue)

The bar chart must be accurate — bars should be proportional to actual values. Value circles must be sized consistently (~38px diameter). The whole chart must look clean and be directly screenshottable for LinkedIn without any cropping needed.

After saving the file, output a one-line note as part of this block only: "Open ./linkedin-infographic.html in a browser and screenshot it for LinkedIn." Then no further text.]
