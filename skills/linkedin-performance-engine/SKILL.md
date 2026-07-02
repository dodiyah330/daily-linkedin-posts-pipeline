---
name: linkedin-performance-engine
description: Generates 5 LinkedIn posts modeled on @founderswing's OWN top-performing analytics — founder-psychology contrarian, loaded poll, AI-news-with-implications, story carousel, and data-visual-with-hook. Reads the live performance report each run, so the winning patterns update automatically as new analytics come in. This is the data-driven stream — every archetype here earned its place from real impression/engagement numbers, not theory.
allowed-tools: WebFetch, WebSearch, Bash, Read, Write
---

# LinkedIn Performance Engine

You generate the **5 report-driven posts** for the daily Founders Wing batch. Unlike the other engines (which are built on general best-practice), every archetype here is reverse-engineered from **@founderswing's actual LinkedIn analytics**. The brief is simple: do more of exactly what already worked on this specific account.

The five archetypes, in the report's proven priority order:

1. **Founder Psychology Contrarian** (text) — the #1 performer. Not yet a distinct type anywhere else in the pipeline.
2. **Loaded Poll** (text) — the highest-impression format on the account.
3. **AI News + Implications** (text) — news with a business angle, never plain relay.
4. **Story-based Carousel** (visual) — real case study, real numbers, swipeable lessons.
5. **Data Visual + Hook** (visual) — one striking stat, sharp founder interpretation.

> **Path note:** This skill is designed to run as STEP 7 of `daily-linkedin-posts/SKILL.md`, with the working directory at the **repo root**. All `./` paths below resolve from there. If you run it standalone from `skills/linkedin-performance-engine/`, prefix the paths with `../../`.

---

## PHASE 0 — Bootstrap

### 0A: Load the content doctrine + the live performance report

```bash
cat ./content-doctrine.md
cat ./founderswing_linkedin_content_report.md
```

**`content-doctrine.md` is the north star** — it sets the lane (the Varun Mayya of LinkedIn) and the broadened audience (ambitious generalists, not just founders). The report is the brain for *craft* — which formats win. Hold both: write the report's winning formats, but aim them at the doctrine's wider audience and topics. Re-read the report every run; when the user drops in an updated one, the winning patterns change automatically. Every post must pass the doctrine topic filter and honor its DROP list.

From the report, extract and hold in working memory:
- **WINNING_ARCHETYPES** — section 5 priority order + section 8 content mix
- **WINNING_HOOKS** — section 9 sample hooks (model the *style*, never copy verbatim — they are already used)
- **ANTI_PATTERNS** — section 4 "What's not working"
- **BRAND_VOICE** — section 7 "What to preserve in generated content"
- **AUDIENCE** — section 6 (solo founders, freelancers leaving employment, AI-curious, side-hustlers chasing first income)

### 0B: Load voice + banned-word rules

```bash
cat ./voice-profile.md 2>/dev/null
cat ./commands/linkedin-content.md 2>/dev/null
```

The hard formatting rules from `commands/linkedin-content.md` still apply to every post here:
- **No em-dashes anywhere.** (The report mentions bullet "•" characters — those are fine. The `—` em-dash is still banned.)
- Banned vocabulary list applies in full (delve, leverage, game-changer, supercharge, etc.)
- Banned LinkedIn patterns apply ("No X. No Y. Just Z.", "It's not just X, it's Y", "And here's the kicker", etc.)
- Specific numbers over adjectives.

**Voice reconciliation:** Write in the declarative, observational @founderswing LinkedIn voice — the same voice the report's winning posts use ("Every founder wants to be CEO until they actually are"). This is third-person/observational and brand-signed, NOT the personal "I"-led Twitter voice in `voice-profile.md` (that profile is for Twitter). When in doubt, match the cadence of the WINNING_HOOKS verbatim examples.

### 0C: Load deduplication state

```bash
# Today's already-written posts (the 11 from the main batch) — for zero topic overlap
cat ./linkedin_posts_$(date +%Y%m%d).txt 2>/dev/null
cat ./ai_news_posts_$(date +%Y%m%d).txt 2>/dev/null

# This engine's own recent history — so the contrarian/poll angles don't repeat day to day
cat ./performance-run-log.json 2>/dev/null || echo "[]"

# The infographic topic log (the data-visual archetype must avoid these too)
cat ./infographic-run-log.json 2>/dev/null || echo "[]"
```

Extract:
- **USED_BATCH_TOPICS** — every subject already covered by today's 11 posts
- **USED_PERF_BELIEFS** — the `contrarian_belief` field from the last 14 entries of `performance-run-log.json` (banned this run)
- **USED_PERF_POLLS** — the `poll_topic` field from the last 14 entries (banned this run)
- **USED_INFOGRAPHIC_TOPICS** — `topic` field from the last 14 infographic-run-log entries

### 0D: Reuse existing research (do not re-fetch)

By the time this step runs, `./reddit_data.json` and the AI-news research already exist from earlier in the pipeline. Reuse them. Only run a fresh `WebSearch` if a specific archetype needs a data point not already gathered (e.g. a fresh stat for the data visual). Budget: 3 WebSearch calls max.

---

## PHASE 1 — Select 5 distinct topics (MANDATORY before writing)

**Every topic must pass the content-doctrine topic filter (Reach, Stakes, Altitude, Edge) and avoid the DROP list — even the contrarian and the poll.** Aim them at ambitious generalists in the AI age, not founders only.

Pick one subject per archetype. Write them out explicitly first:

```
PERFORMANCE TOPIC SELECTION:
1. FOUNDER PSYCHOLOGY CONTRARIAN → [the romanticized belief being challenged] — angle: [one phrase]
2. LOADED POLL                   → [the dilemma] — 4 emotionally-loaded options
3. AI NEWS + IMPLICATIONS        → [story] from [source] — business angle: [one phrase]
4. STORY CAROUSEL                → [case study / real numbers] — format: [HOW_THEY_DID_IT / DATA_STORY / MYSTERY_REVEAL]
5. DATA VISUAL + HOOK            → [dataset] — format: [from illustration-formats]
```

**Zero-overlap check (do not skip):**
- None of the 5 may share a subject with USED_BATCH_TOPICS (the existing 11 posts). 16 unique subjects per day total.
- The contrarian belief must not be in USED_PERF_BELIEFS. The poll topic must not be in USED_PERF_POLLS.
- Archetype 3's story must differ from all 7 AI-news posts already written.
- Archetype 5's dataset must not be in USED_INFOGRAPHIC_TOPICS, and must differ from the main infographic generated in STEP 2/5.

The contrarian (1) and poll (2) are **evergreen founder-psychology** — they do NOT need a fresh news peg, which is what makes 16 unique daily subjects feasible. Pull these from timeless founder/freelancer tensions, not the news cycle.

> **Note on the outlier:** Report post #22 (2,218 impressions) is logged as "Unknown format / Unknown topic." It is a data hole — you cannot model what isn't described. Do not try to reverse-engineer it. Build only on the archetypes the report actually characterizes.

---

## PHASE 2 — Write the 5 posts

Apply every rule from PHASE 0B. Each archetype's formula is lifted directly from the report.

---

### Archetype 1 — Founder Psychology Contrarian (text)

**Why it wins (report data):** Top performer on the account — 413 impressions, the strongest emotional engagement. People resonate deeply with an uncomfortable truth about the moment they are living through.

**Doctrine widening (keep, reframe broader):** Keep the emotional contrarian power, but widen the belief beyond founder life to anyone ambitious in the AI age — professionals, creators, career-switchers. Challenge a belief about AI, work, status, or getting ahead, framed so a non-founder feels just as seen. A founder angle is still allowed when it is genuinely the sharpest, but it is no longer the default.

**Formula:** Challenge a widely-held belief → validate the reader's quiet frustration → end with a reframe + question.

**Structure:**
```
[HOOK — 3 to 8 words. A bold, declarative claim that punctures a romanticized belief.
 Model the rhythm of: "Every founder wants to be CEO until they actually are."]

[THE BELIEF — Name what everyone tells founders. One or two sentences.]

[THE REAL Y — The uncomfortable truth underneath it. This is the "no one talks about this" payload.
 Be specific and grounded, not abstract motivation.]

[VALIDATION — Name the quiet frustration the reader feels but rarely says out loud.
 Make them feel seen.]

[REFRAME — What to actually do or believe instead. Concrete.]

[QUESTION — A pointed debate prompt. Not "what do you think?" — something they can answer in one line.]

[CTA — "Follow @founderswing for more" OR "Repost to help a founder who needs to hear this."]
```

**Voice note:** Blunt, declarative, professional but not corporate. One uncomfortable truth per post. No hedging. This is the format that earns comments — make the reader want to argue or confess.

**Emotion target:** validation → reframe ("this person gets it")

---

### Archetype 2 — Loaded Poll (text)

**Why it wins (report data):** Highest-impression format on the account — the freelancing-transition poll hit 511 impressions and 11 votes. LinkedIn's algorithm rewards interactive content, and emotionally-loaded options drive both votes and reach.

**Formula (report section 3C):** State a hot-button belief or dilemma → ask "which one hits closest?" → make all four options emotionally loaded so people *want* to respond.

**Doctrine widening:** Make the dilemma a future-of-work / AI-age tension everyone feels (which skill survives, will AI take this role, is this still worth learning, are you the one using AI or the one being replaced), not a founder-only dilemma.

**Structure:**
```
[SETUP — 2 to 3 sentences framing a real founder/freelancer dilemma. Establish the tension
 without revealing a "correct" answer. The reader should recognize themselves in it.]

[POLL QUESTION — one standalone line, e.g. "Which one hits closest right now?"]

☐ [Option A — emotionally loaded]
☐ [Option B — emotionally loaded]
☐ [Option C — emotionally loaded]
☐ [Option D — emotionally loaded]

[One line inviting people to explain their vote in the comments.]
```

**Voice note:** Every option must be a real, felt position — no obvious throwaway answers. The best polls have no "right" choice; the split *is* the content. Topics that worked: freelancing transition pain, hustle-culture, AI-tool overwhelm, business decisions.

**Emotion target:** recognition + the itch to weigh in

---

### Archetype 3 — AI News + Implications (text)

**Why it wins (report data):** Interpreted AI news performs well (Microsoft AI-agents tool → 230 impressions; Anthropic $65B → 126). But the report is explicit: **plain news relay underperforms** (most stay under 40 impressions). The win comes entirely from the "why this matters for you" layer.

**Formula (report section 3B):** State the news fact → give 2-3 concrete business implications → end with a debate-prompting question.

**Structure:**
```
[HOOK — The news, stated plainly. One line. Under 120 characters.]

[WHAT HAPPENED — 1 to 2 sentences. The fact, no jargon.]

[WHAT IT MEANS FOR YOU — 2 to 3 implications, bullets allowed (use "•" not "-").
 Each implication is a concrete consequence for a solo founder, freelancer, or
 side-hustler. THIS is the part that earns the impressions. Not the headline.]

[DEBATE QUESTION — invites a real position, not agreement.]

[CTA — "Follow @founderswing for more" or save-prompt.]
```

**Anti-pattern guard (mandatory):** Before finalizing, check this post against ANTI_PATTERNS. If it reads as "Company X announced Y" with no founder consequence, it is a plain relay — rewrite it or pick a different story. Every fact must carry a "so what for *you*."

**Emotion target:** informed + slightly ahead of the curve

---

### Archetype 4 — Story-based Carousel (visual)

**Why it wins (report data):** Carousels with bold titles + real case studies earn the highest *comment* counts (the Reddit Ads Mistake carousel → 3 comments, the most on the account). Story beats listicle.

**Build:** Reuse the existing **branded-carousel** skill — do not reinvent rendering.
1. Pick the format from `./skills/branded-carousel/FORMATS.md` decision tree. Prefer `HOW_THEY_DID_IT`, `DATA_STORY`, or `MYSTERY_REVEAL` (story-driven beats listicle for this archetype).
2. Pick a non-banned hook style via the `./carousel-hook-log.json` rotation (same rules as the main carousel — the last-used style is banned).
3. Run the branded-carousel engine (`./skills/branded-carousel/SKILL.md`) with a **distinct output directory** so it does not overwrite the main carousel:
   - `CAROUSEL_DIR = ./carousel-routine`
   - Render to subdir **`carousel-performance`** (i.e. `temp/carousel-performance/slide-*.html` → `output/$DATE/carousel-performance/`).
   - Render: `cd ./carousel-routine && node render.js "$(date +%Y-%m-%d)" "carousel-performance"`
   - PDF: `cd ./carousel-routine && node render-pdf.js "$(date +%Y-%m-%d)" "carousel-performance"`
4. The carousel TOPIC must differ from the main carousel (Step 4 of the master skill) and from the other 4 performance posts.

Write a caption following the carousel-caption rules (hook line → one-sentence summary → engagement question → save/repost CTA).

---

### Archetype 5 — Data Visual + Hook (visual)

**Why it wins (report data):** Stat visuals are moderate performers ("Why startups fail" CB Insights → 53 impressions, 3 reactions) but build brand identity — and they spike when paired with a sharp interpretive hook in the text.

**Build:** Reuse the existing **illustration-formats** skill — do not reinvent.
1. Find one fresh dataset (6-10 data points, 2025-2026, AI/founder/freelancer/creator-economy niche). It must NOT be in USED_INFOGRAPHIC_TOPICS and must differ from the main infographic.
2. Pick the format via `./skills/illustration-formats/SKILL.md` decision tree based on the data shape.
3. Generate the HTML to a **distinct file** so it does not collide with the main infographic:
   - Write to `./linkedin-performance-infographic.html`
   - Screenshot to `./linkedin-performance-infographic-$(date +%Y%m%d).png` at 1080×1080 (reuse the puppeteer capture pattern from the master skill's STEP 5, pointing at the performance HTML file and a free port like 8767).

Write a caption where the **hook is one striking stat** and the body is a sharp founder/freelancer interpretation of what the number means.

---

## PHASE 3 — Self-check

Verify every post before output:

**Hard rules:**
- [ ] No em-dashes (`—`) anywhere. Bullet "•" is allowed.
- [ ] No banned vocabulary (full list from `commands/linkedin-content.md`).
- [ ] No banned LinkedIn patterns.
- [ ] Every text post ends with a specific debate question + exactly one CTA.

**Report-alignment checks:**
- [ ] Contrarian post challenges a real belief and lands one uncomfortable truth (not generic motivation).
- [ ] Poll has 4 genuinely emotionally-loaded options with no obvious "right" answer.
- [ ] AI-news post passes the anti-relay guard: every fact has a founder consequence.
- [ ] Carousel is story-based with real numbers, not a generic listicle.
- [ ] Data visual hook is a single striking stat with a sharp interpretation.

**Dedup checks:**
- [ ] All 5 subjects are distinct from each other AND from the existing 11 posts (16 unique total).
- [ ] Contrarian belief ∉ USED_PERF_BELIEFS. Poll topic ∉ USED_PERF_POLLS. Dataset ∉ USED_INFOGRAPHIC_TOPICS.

**Voice check:**
- [ ] Declarative @founderswing voice, matches the cadence of the report's WINNING_HOOKS.
- [ ] At least one post uses the "Repost to help a [founder/freelancer]" CTA variant (per report section 7).

---

## PHASE 4 — Output + save

Print all 5 posts in this format, then save:

```
═══════════════════════════════════════════════
LINKEDIN PERFORMANCE ENGINE — [DATE]
Source report: founderswing_linkedin_content_report.md (analysis date inside)
═══════════════════════════════════════════════

━━━ PERF 1 — FOUNDER PSYCHOLOGY CONTRARIAN ━━━
[full post text]
Belief challenged: [one line]   | Target: 200-500+ impressions

━━━ PERF 2 — LOADED POLL ━━━
[full post text with 4 options]
Dilemma: [one line]   | Target: 200-500+ impressions

━━━ PERF 3 — AI NEWS + IMPLICATIONS ━━━
[full post text]
Story: [one line] | Source: [url]   | Target: 100-250 impressions

━━━ PERF 4 — STORY CAROUSEL ━━━
[caption text]
Carousel topic: [one line] | Format: [X] | Hook style: [X]
PDF: ./carousel-routine/output/[DATE]/carousel-performance/*.pdf   | Target: 70-150 impressions

━━━ PERF 5 — DATA VISUAL + HOOK ━━━
[caption text]
Dataset: [one line] | Format: [X]
PNG: ./linkedin-performance-infographic-[DATE].png   | Target: 50-100 impressions
═══════════════════════════════════════════════
```

Save all 5 text/captions to:
```
./performance_posts_$(date +%Y%m%d).txt
```

---

## PHASE 5 — Write run-log (deduplication for future runs)

```bash
python3 - << 'PYEOF'
import json, datetime

LOG_PATH = "./performance-run-log.json"
try:
    with open(LOG_PATH) as f:
        log = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    log = []

entry = {
    "date": datetime.date.today().isoformat(),
    "contrarian_belief": "CONTRARIAN_BELIEF_PLACEHOLDER",
    "poll_topic": "POLL_TOPIC_PLACEHOLDER",
    "news_story": "NEWS_STORY_PLACEHOLDER",
    "carousel_topic": "CAROUSEL_TOPIC_PLACEHOLDER",
    "data_visual_topic": "DATA_VISUAL_TOPIC_PLACEHOLDER"
}
log.append(entry)
log = log[-30:]  # keep last 30 runs

with open(LOG_PATH, "w") as f:
    json.dump(log, f, indent=2)
print(f"Performance run-log updated for {entry['date']}")
PYEOF
```

**Before running:** replace each `*_PLACEHOLDER` with the actual subject you used this run. This prevents the contrarian/poll/data angles from repeating across days.

---

## Edge cases

- **Report file missing:** Fall back to the archetypes documented in PHASE 0A from memory, and note `[Note: report file not found — used cached archetypes]` in the output. Re-request the report from the user.
- **Can't find 5 non-overlapping topics:** The contrarian and poll are evergreen — pull from a different founder tension. Never duplicate a subject just to fill a slot; a strong 4-post batch beats a padded 5.
- **Second carousel render is too expensive today:** The carousel and data-visual are the report's *moderate* performers. If render capacity is constrained, the 3 text posts (contrarian, poll, news) carry the highest-impression formats and can ship alone. Flag the skipped visuals in the output.
- **Slow news week:** Archetype 3 can stretch to the last 10 days. Archetypes 1 and 2 are evergreen and never blocked by a slow news cycle.
