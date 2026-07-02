---
name: daily-linkedin-posts
description: Generates 4 LinkedIn posts from Reddit trends + branded carousel + 7 plain-text AI news posts + 5 report-driven performance posts (modeled on @founderswing's own analytics via linkedin-performance-engine), sends all text posts + PDFs + infographics to #linkedin-content on Slack
---


# Daily LinkedIn Content → Slack

Generate today's LinkedIn content batch and send everything to #linkedin-content (channel ID: C0AVBBTD529). Text posts go as messages. Carousel PDF and images go as actual file uploads via the Slack API.

Load the Slack token first:
```bash
export SLACK_TOKEN=$(grep '^SLACK_BOT_TOKEN=' ./.env | cut -d'=' -f2)
CHANNEL="C0AVBBTD529"
```

---

## STEP 0 — Load the content doctrine (governs every post)

```bash
cat ./content-doctrine.md
```

`content-doctrine.md` is the north star: we are the **Varun Mayya of LinkedIn**. Every topic in every step below — the 4 Reddit posts, the carousel, the infographic, the 7 AI-news posts, and the 5 performance posts — must pass its **topic filter (Reach, Stakes, Altitude, Edge)** and avoid its **DROP list** (technical tutorials, tool config, copy-paste prompt/workflow tactics, SaaS metrics, indie-hacker build-in-public / MVP / agency tactics, dry news relay). Aim everything at ambitious generalists who want to know where AI is going and how to get ahead, not at founders or engineers chasing tactics.

---

## STEP 1 — Fetch Reddit content via Apify

```bash
export APIFY_TOKEN=$(grep '^APIFY_API_KEY=' ./.env | cut -d'=' -f2)
RUN_RESP=$(curl -s -X POST \
  "https://api.apify.com/v2/acts/trudax~reddit-scraper-lite/runs?token=${APIFY_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"startUrls":[{"url":"https://www.reddit.com/r/artificial/top/?t=week"},{"url":"https://www.reddit.com/r/ChatGPT/top/?t=week"},{"url":"https://www.reddit.com/r/singularity/top/?t=week"},{"url":"https://www.reddit.com/r/Futurology/top/?t=week"},{"url":"https://www.reddit.com/r/technology/top/?t=week"},{"url":"https://www.reddit.com/r/OpenAI/top/?t=week"}],"maxItems":80}')
RUN_ID=$(echo "$RUN_RESP" | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['id'])")
until [ "$(curl -s "https://api.apify.com/v2/actor-runs/$RUN_ID?token=${APIFY_TOKEN}" | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['status'])")" = "SUCCEEDED" ]; do sleep 10; done
DATASET_ID=$(curl -s "https://api.apify.com/v2/actor-runs/$RUN_ID?token=${APIFY_TOKEN}" | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['defaultDatasetId'])")
curl -s "https://api.apify.com/v2/datasets/$DATASET_ID/items?token=${APIFY_TOKEN}&limit=80" > ./reddit_data.json
```

If Apify fails use WebFetch on these fallback URLs:
- https://www.reddit.com/r/artificial/top.json?limit=25&t=week&raw_json=1
- https://www.reddit.com/r/ChatGPT/top.json?limit=25&t=week&raw_json=1
- https://www.reddit.com/r/singularity/top.json?limit=25&t=week&raw_json=1
- https://www.reddit.com/r/Futurology/top.json?limit=20&t=week&raw_json=1
- https://www.reddit.com/r/technology/top.json?limit=20&t=week&raw_json=1
- https://www.reddit.com/r/OpenAI/top.json?limit=20&t=week&raw_json=1

---

## STEP 2 — Research infographic data + select format

### 2A. Load infographic run-log (deduplication)

```bash
cat ./infographic-run-log.json 2>/dev/null || echo "[]"
```

Parse the JSON array. Extract:
- **USED_INFOGRAPHIC_TOPICS**: the `topic` field from the last **14 entries** (= last 14 daily runs)
- **USED_FORMATS_RECENT**: the `format` field from the last **5 entries**

**Deduplication rules (mandatory — do not skip):**
1. Any dataset whose subject overlaps >50% with a topic in USED_INFOGRAPHIC_TOPICS is disqualified. This means: if "AI adoption by industry" was used 10 days ago it cannot be reused. Be strict — "AI tool usage rates" and "AI adoption survey" are the same theme.
2. Tally format counts in USED_FORMATS_RECENT. The format used most recently (last entry) is **banned** this run. If one format appears 3+ times in the last 5 runs, also ban it this run. This forces visual variety across the week.

Store the list of banned topics as BANNED_TOPICS and the banned format(s) as BANNED_FORMATS.

### 2B. Find the dataset

Per `content-doctrine.md`, the dataset must be a "this is the shift" stat about AI's impact on work, income, skills, or the future — not SaaS metrics or developer data. Use WebSearch to find one dataset published 2025-2026 with 6-10 data points and specific numbers. The topic must **not** appear in BANNED_TOPICS and must pass the topic filter (Reach, Stakes, Altitude, Edge).

Cast wide across these AI-impact areas each run so the infographic feed covers diverse ground:
- Which jobs / tasks AI is automating or augmenting
- Skills that pay now vs skills losing their value
- AI adoption in the workplace and what workers actually do with it
- Income and earning shifts in the AI economy (creators, freelancers, new roles)
- How AI is reshaping hiring, careers, and the future of work
- Time and productivity gains people get from AI
- Where AI is creating new opportunities and money

If the first dataset you find is a banned topic, search again with a different angle. Do not give up until you have a fresh topic.

### 2C. Pick the infographic format

Read `./skills/illustration-formats/SKILL.md` and apply its decision tree based on the SHAPE of the dataset you found:

- Ranked list of 6-10 categories → `RANKED_BARS`
- Parts-of-a-whole breakdown → `DONUT_BREAKDOWN`
- Change over time (year-over-year, growth) → `TIMELINE_SHIFT`
- Head-to-head comparison → `COMPARISON_SPLIT`
- One hero stat with supporting context → `HERO_NUMBER`

**Format ban check:** If the naturally-selected format is in BANNED_FORMATS, pick the next-best format that fits the data shape (e.g. if data is a ranked list and RANKED_BARS is banned, check if it can be reframed as a COMPARISON_SPLIT or HERO_NUMBER). Do not use a banned format just because it's the obvious fit — forced variety makes the feed look richer.

Record the chosen format and topic as INFOGRAPHIC_FORMAT and INFOGRAPHIC_TOPIC. Step 3 will generate the HTML using this format's design recipe (warm cream bg `#F5EFE8`, coral red `#E63946`, Inter sans + Instrument Serif italic accents, `@founderswing` in footer).

---

## STEP 3 — Select 4 distinct topics, then write all 4 posts

### Step 3A — Topic selection (MANDATORY — do before writing any post)

From the Reddit data, pick **4 completely distinct threads/stories** — one per post type. **Each must pass the content-doctrine topic filter and sit in the lane (AI's impact on work, income, skills, the future), not startup tactics.** Write them out explicitly before writing any post:

```
TOPIC SELECTION:
1. COLLABORATIVE ARTICLE → [thread title] from r/[sub] — subject: [one phrase]
2. POLL               → [thread title] from r/[sub] — subject: [one phrase]
3. CAROUSEL           → [thread title] from r/[sub] — subject: [one phrase]
4. INFOGRAPHIC        → [INFOGRAPHIC_TOPIC from Step 2] — format: [INFOGRAPHIC_FORMAT]
```

**Zero-overlap check:** Read back the 4 subjects. If any two share the same industry, tool, concept, or pain point, swap one out for a different thread. The infographic topic is already locked from Step 2 — if it overlaps with a Reddit post you selected, swap the Reddit post instead (the infographic went through deduplication, the Reddit posts did not). Do not proceed to Step 3B until all 4 subjects are genuinely different.

- No two posts may draw from the same Reddit thread or story.
- No two posts may share the same subject matter angle (e.g., two posts about AI tools, two about burnout, two about SaaS pricing — all forbidden).

### Step 3B — Write the posts

Apply every rule from ./commands/linkedin-content.md:
- Third-person observer voice, no "I" statements
- All banned words/phrases avoided (see skill file)
- No em-dashes anywhere
- 6-part structure: Hook → Pain point → Actionable value → Dream picture → Engagement question → CTA
- Sentence case headings
- Specific numbers over adjectives

Post types: COLLABORATIVE ARTICLE, POLL, CAROUSEL (7 slides + caption), INFOGRAPHIC (data chart + caption)

Each post must use only its assigned topic from Step 3A. If a post feels underdeveloped on its assigned topic, search for supplementary data — do not borrow subject matter from another post's topic.

Save all posts to ./linkedin_posts_$(date +%Y%m%d).txt

Generate infographic HTML → save to ./linkedin-infographic.html using Write tool.

---

## STEP 4 — Run branded-carousel with format selection + hook rotation

### 4A. Pick the carousel format
Read `./skills/branded-carousel/FORMATS.md` and apply its decision tree to the CAROUSEL topic from Step 3A. The six formats are:

- `BRAND_STORY` (topic features a specific brand/product with imagery)
- `LISTICLE` (numbered list like "5 ways", "7 tools")
- `DATA_STORY` (stats-driven, no specific brand)
- `HOW_THEY_DID_IT` (marketing case study)
- `HOT_TAKE` (contrarian opinion, myth-buster)
- `MYSTERY_REVEAL` (curiosity hook, story-driven)

Record the chosen format and palette in the Art Direction Brief.

### 4A-bis. Pick the carousel hook style (mandatory)

Load `./carousel-hook-log.json` and apply the carousel hook rotation rules from `./commands/linkedin-content.md`. Specifically:

```bash
cat ./carousel-hook-log.json 2>/dev/null || echo "[]"
```

Parse the JSON array. Extract:
- **LAST_HOOK_STYLE**: the `hook_style` from the most recent entry — this style is **banned** this run
- **OVERUSED_STYLES**: any `hook_style` appearing 3+ times in the last 7 entries — also **banned** this run

From the 10 carousel hook styles in `./commands/linkedin-content.md`, pick the most fitting **non-banned** style for today's carousel topic. Store as `CAROUSEL_HOOK_STYLE`.

Write the selected hook following that style's formula. The slide 1 hook text must be:
- 6 to 8 words maximum
- A curiosity gap (never reveal the answer on slide 1)
- Specific enough that the reader knows what value awaits

Print the selection before proceeding:
```
CAROUSEL HOOK SELECTION:
  Banned styles: [list banned styles]
  Chosen style:  [CAROUSEL_HOOK_STYLE]
  Hook text:     "[the actual slide 1 headline]"
```

### 4B. Source images first (mandatory)
Before writing any HTML, complete the image sourcing per FORMATS.md image strategy. Required minimum: 4 valid images >10KB in `$ASSETS_DIR/` from:
- OG image / press kit / brand favicon for branded topics
- `https://source.unsplash.com/1080x1080/?[theme-keyword]` for data/general topics
- `https://logo.clearbit.com/[brand].com` for tool logos

Do not proceed to slide HTML until image verification passes.

### 4C. Run branded-carousel
Run `./skills/branded-carousel/SKILL.md` with:
- CAROUSEL_DIR = `./carousel-routine`
- CHOSEN_FORMAT = the format picked in 4A
- CAROUSEL_HOOK_STYLE = the hook style picked in 4A-bis
- Real images pre-sourced in 4B

Pass `CAROUSEL_HOOK_STYLE` to the branded-carousel engine so it uses the selected hook formula for slide 1.

⚠️ **PDF generation rule:** The carousel PDF must always be built FROM the rendered PNGs (via `render-pdf.js`), never by re-rendering HTML into a PDF. The PNGs are the source of truth. The branded-carousel skill's Phase 5 handles this — do NOT attempt to generate the PDF any other way (e.g. puppeteer `page.pdf()` on HTML). Doing so produces broken/tiny PDFs.

PDF output: `./carousel-routine/output/$(date +%Y-%m-%d)/carousel-branded/*.pdf`

### 4D. Writing rules (applied to every slide)
- No em-dashes anywhere
- Lowercase starts and skipped periods allowed (human voice)
- Maximum 2 sentences per slide
- Italic serif emphasis on one word per headline (Instrument Serif)
- Real image visible on minimum 4 of 7 slides

### 4E. Write carousel hook entry to run-log

```bash
python3 - << 'PYEOF'
import json, os, datetime

LOG_PATH = "./carousel-hook-log.json"

try:
    with open(LOG_PATH) as f:
        log = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    log = []

entry = {
    "date": datetime.date.today().isoformat(),
    "hook_style": "CAROUSEL_HOOK_STYLE_PLACEHOLDER",
    "hook_text": "CAROUSEL_HOOK_TEXT_PLACEHOLDER",
    "carousel_topic": "CAROUSEL_TOPIC_PLACEHOLDER",
    "carousel_format": "CAROUSEL_FORMAT_PLACEHOLDER"
}
log.append(entry)

# Keep last 30 entries
log = log[-30:]

with open(LOG_PATH, "w") as f:
    json.dump(log, f, indent=2)

print(f"Carousel hook log updated: {entry['hook_style']} — {entry['hook_text']}")
PYEOF
```

**Before running:** replace `CAROUSEL_HOOK_STYLE_PLACEHOLDER` with the actual chosen hook style, `CAROUSEL_HOOK_TEXT_PLACEHOLDER` with the actual slide 1 hook text, `CAROUSEL_TOPIC_PLACEHOLDER` with the carousel topic, and `CAROUSEL_FORMAT_PLACEHOLDER` with the carousel format from Step 4A.

---

## STEP 5 — Screenshot infographic (1080×1080 PNG)


```bash
cat > ./cap_infographic.js << 'JSEOF'
const puppeteer = require('puppeteer');
const http = require('http');
const fs = require('fs');
(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1080 });
  const server = http.createServer((req, res) => {
    res.writeHead(200, {'Content-Type': 'text/html'});
    res.end(fs.readFileSync('./linkedin-infographic.html'));
  });
  await new Promise(r => server.listen(8766, r));
  await page.goto('http://localhost:8766', { waitUntil: 'networkidle0' });
  const d = new Date().toISOString().slice(0,10).replace(/-/g,'');
  await page.screenshot({ path: `./linkedin-infographic-${d}.png`, clip:{x:0,y:0,width:1080,height:1080} });
  server.close();
  await browser.close();
})();
JSEOF
PATH="/usr/local/bin:$PATH" node ./cap_infographic.js
```

---

## STEP 5B — Write infographic entry to run-log

```bash
python3 - << 'PYEOF'
import json, os, datetime

LOG_PATH = "./infographic-run-log.json"

try:
    with open(LOG_PATH) as f:
        log = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    log = []

entry = {
    "date": datetime.date.today().isoformat(),
    "topic": "INFOGRAPHIC_TOPIC_PLACEHOLDER",
    "format": "INFOGRAPHIC_FORMAT_PLACEHOLDER",
    "generated_at": datetime.datetime.utcnow().isoformat() + "Z"
}
log.append(entry)

# Keep last 30 entries (≈ 30 daily runs)
log = log[-30:]

with open(LOG_PATH, "w") as f:
    json.dump(log, f, indent=2)

print(f"Infographic run-log updated: {entry['topic']} ({entry['format']})")
PYEOF
```

**Before running:** replace `INFOGRAPHIC_TOPIC_PLACEHOLDER` with the actual INFOGRAPHIC_TOPIC value and `INFOGRAPHIC_FORMAT_PLACEHOLDER` with the actual INFOGRAPHIC_FORMAT value from Step 2.

---

## STEP 6 — Generate 7 plain-text AI news posts (linkedin-ai-news-engine)

Run the linkedin-ai-news-engine skill:

```bash
cat ./skills/linkedin-ai-news-engine/SKILL.md
```

Execute the full skill (Phase 0 through Phase 5). Save the complete output to `./ai_news_posts_$(date +%Y%m%d).txt`.

**Topic uniqueness rule for this step:** Before finalising the 7 AI news posts, check their topics against the 4 subjects selected in Step 3A. If any AI news post covers the same topic as one of the Reddit-based posts, swap it for a different AI story from the research. Every post across the entire daily batch — both the 4 Reddit posts and the 7 AI news posts — must cover a unique subject.

---

## STEP 7 — Generate 5 report-driven performance posts (linkedin-performance-engine)

Run the linkedin-performance-engine skill — the data-driven stream modeled on @founderswing's OWN top-performing analytics:

```bash
cat ./skills/linkedin-performance-engine/SKILL.md
```

Execute the full skill (Phase 0 through Phase 5). It reads `./founderswing_linkedin_content_report.md` fresh each run, so the winning patterns update automatically whenever the user drops in a newer report. Save the complete output to `./performance_posts_$(date +%Y%m%d).txt`.

The 5 posts (in the report's proven priority order):
- PERF 1 — Founder Psychology Contrarian (text) — the report's #1 format, not produced anywhere else in the pipeline
- PERF 2 — Loaded Poll (text)
- PERF 3 — AI News + Implications (text)
- PERF 4 — Story Carousel (PDF → `output/$DATE/carousel-performance/`)
- PERF 5 — Data Visual + Hook (PNG → `./linkedin-performance-infographic-$DATE.png`)

**Topic uniqueness rule for this step:** All 5 performance posts must cover subjects distinct from each other AND from the 11 posts already written (the 4 Reddit posts in Step 3A and the 7 AI news posts in Step 6). That is **16 unique subjects** across the full daily batch. The contrarian and poll archetypes are evergreen founder-psychology — pull them from timeless founder/freelancer tensions, not the news cycle, which keeps 16 unique subjects feasible.

⚠️ **Render cost note:** PERF 4 and PERF 5 produce a SECOND carousel and a SECOND infographic for the day, written to distinct output paths (`carousel-performance` and `linkedin-performance-infographic-*`) so they never overwrite the main ones. If render capacity is constrained, the 3 text posts carry the report's highest-impression formats and can ship without the two visuals.

---

## STEP 8 — Send text posts to Slack (via Slack MCP tool)

Use slack_send_message (channel_id: C0AVBBTD529) for these messages in order:

**Section A — Reddit-based posts (4 posts):**
1. Header: `📅 *LinkedIn Content Drop — {DATE}*\n16 posts ready (4 Reddit-based + 7 AI News + 5 performance-driven). Carousel PDFs and infographics attached below.`
2. Full COLLABORATIVE ARTICLE text
3. Full POLL text with all 4 options

**Section B — AI News plain-text posts (7 posts):**
4. Section header: `📰 *AI News Posts — {DATE}*\n7 plain-text posts from the linkedin-ai-news-engine:`
5. POST 1 — Tool Spotlight (full text)
6. POST 2 — Weekly Roundup (full text)
7. POST 3 — Plain English Breakdown (full text)
8. POST 4 — Unfair Advantage (full text)
9. POST 5 — Career/Income Angle (full text)
10. POST 6 — Hot Take (full text)
11. POST 7 — Steal This (full text)

**Section C — Performance-driven posts (5 posts, from linkedin-performance-engine):**
12. Section header: `📈 *Performance Posts — {DATE}*\n5 posts modeled on your own top-performing analytics (founderswing report):`
13. PERF 1 — Founder Psychology Contrarian (full text)
14. PERF 2 — Loaded Poll (full text with all 4 options)
15. PERF 3 — AI News + Implications (full text)
16. PERF 4 — Story Carousel caption (the PDF + slides upload in STEP 9)
17. PERF 5 — Data Visual caption (the PNG uploads in STEP 9)

Send each post as a separate Slack message so they are individually copyable.

---

## STEP 9 — Upload files to Slack (via API)

```bash
upload_to_slack() {
  local FILE_PATH="$1"
  local FILE_NAME="$2"
  local CAPTION="$3"
  local FILE_SIZE=$(wc -c < "$FILE_PATH" | tr -d ' ')

  UPLOAD_RESP=$(curl -s -X POST "https://slack.com/api/files.getUploadURLExternal" \
    -H "Authorization: Bearer $SLACK_TOKEN" \
    -F "filename=$FILE_NAME" \
    -F "length=$FILE_SIZE")
  local UPLOAD_URL=$(echo "$UPLOAD_RESP" | python3 -c "import json,sys; print(json.load(sys.stdin).get('upload_url',''))")
  local FILE_ID=$(echo "$UPLOAD_RESP" | python3 -c "import json,sys; print(json.load(sys.stdin).get('file_id',''))")

  curl -s -X POST "$UPLOAD_URL" -F "filename=@$FILE_PATH" > /dev/null

  # Write payload to temp file to avoid shell-escaping issues with captions
  python3 -c "
import json, sys
payload = json.dumps({
  'files': [{'id': sys.argv[1], 'title': sys.argv[2]}],
  'channel_id': sys.argv[3],
  'initial_comment': sys.argv[4]
})
open('./slack_upload_payload.json', 'w').write(payload)
" "$FILE_ID" "$FILE_NAME" "$CHANNEL" "$CAPTION"

  curl -s -X POST "https://slack.com/api/files.completeUploadExternal" \
    -H "Authorization: Bearer $SLACK_TOKEN" \
    -H "Content-Type: application/json" \
    -d @./slack_upload_payload.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(sys.argv[1]+('  OK' if d.get('ok') else '  ERROR: '+str(d.get('error',d))))" "$FILE_NAME"
}

YDATE=$(date +%Y-%m-%d)
DATE=$(date +%Y%m%d)
PDF=$(ls ./carousel-routine/output/$YDATE/carousel-branded/*.pdf 2>/dev/null | head -1)

upload_to_slack "$PDF" "$(basename $PDF)" "━━━ CAROUSEL PDF ━━━\n\n[CAROUSEL_CAPTION]"

# Upload individual slide PNGs in order
PDF_DIR="./carousel-routine/output/$YDATE/carousel-branded"
if [ -d "$PDF_DIR" ]; then
  for SLIDE_PNG in $(ls "$PDF_DIR"/slide-*.png 2>/dev/null | sort); do
    SLIDE_NAME=$(basename "$SLIDE_PNG")
    SLIDE_NUM=$(echo "$SLIDE_NAME" | cut -d'-' -f2 | cut -d'.' -f1)
    upload_to_slack "$SLIDE_PNG" "$SLIDE_NAME" "Slide $SLIDE_NUM"
  done
fi

upload_to_slack "./linkedin-infographic-${DATE}.png" "linkedin-infographic.png" "━━━ INFOGRAPHIC ━━━\n\n[INFOGRAPHIC_CAPTION]"

# --- Performance-engine visuals (from STEP 7) ---
PERF_PDF=$(ls ./carousel-routine/output/$YDATE/carousel-performance/*.pdf 2>/dev/null | head -1)
if [ -n "$PERF_PDF" ]; then
  upload_to_slack "$PERF_PDF" "$(basename $PERF_PDF)" "━━━ PERFORMANCE CAROUSEL ━━━\n\n[PERF_CAROUSEL_CAPTION]"
  PERF_DIR="./carousel-routine/output/$YDATE/carousel-performance"
  for SLIDE_PNG in $(ls "$PERF_DIR"/slide-*.png 2>/dev/null | sort); do
    SLIDE_NAME=$(basename "$SLIDE_PNG")
    SLIDE_NUM=$(echo "$SLIDE_NAME" | cut -d'-' -f2 | cut -d'.' -f1)
    upload_to_slack "$SLIDE_PNG" "perf-$SLIDE_NAME" "Performance slide $SLIDE_NUM"
  done
fi

if [ -f "./linkedin-performance-infographic-${DATE}.png" ]; then
  upload_to_slack "./linkedin-performance-infographic-${DATE}.png" "linkedin-performance-infographic.png" "━━━ PERFORMANCE DATA VISUAL ━━━\n\n[PERF_INFOGRAPHIC_CAPTION]"
fi

# Run daily newspaper HTML compiler
python3 generate_daily_paper.py "$DATE"
```

Replace [CAROUSEL_CAPTION] and [INFOGRAPHIC_CAPTION] with the actual captions from Step 3, and [PERF_CAROUSEL_CAPTION] and [PERF_INFOGRAPHIC_CAPTION] with the performance captions from Step 7.

---

## STEP 10 — Print completion report

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Daily LinkedIn Content — {DATE}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Reddit-based posts (4):
...
✓ Interactive Newspaper HTML → Generated (Downloads)
✓ Carousel → Slack (PDF + 7 PNGs uploaded)
✓ Infographic → Slack (PNG uploaded)
Performance-driven posts (5):
✓ Contrarian + Loaded Poll + AI-news (text) → Slack
✓ Story carousel → Slack (PDF + PNGs uploaded)
✓ Data visual → Slack (PNG uploaded)
...
```

