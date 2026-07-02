#!/usr/bin/env python3
"""Deliver the 2026-06-13 LinkedIn content batch (16 posts + visuals) to #linkedin-content.
Text via chat.postMessage, files via the external-upload flow. Bot token from .env."""
import json, os, subprocess, urllib.request, urllib.parse, time, sys

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
TOKEN = subprocess.check_output("grep '^SLACK_BOT_TOKEN=' .env | cut -d'=' -f2", shell=True).decode().strip()
CHANNEL = subprocess.check_output("grep '^SLACK_CHANNEL_ID=' .env | cut -d'=' -f2", shell=True).decode().strip() or "C0BEG7HAXHQ"
DATE = "June 13, 2026"

def api(method, payload, json_body=True):
    url = f"https://slack.com/api/{method}"
    if json_body:
        data = json.dumps(payload).encode("utf-8")
        ct = "application/json; charset=utf-8"
    else:
        data = urllib.parse.urlencode(payload).encode("utf-8")
        ct = "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=data, headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": ct})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode("utf-8"))

def post_text(label, text):
    r = api("chat.postMessage", {"channel": CHANNEL, "text": text, "unfurl_links": False, "unfurl_media": False})
    print(f"  [{label}] {'OK' if r.get('ok') else 'ERR ' + str(r.get('error'))}")
    time.sleep(0.8)
    return r.get("ok")

def upload(label, path, title, comment):
    if not os.path.exists(path):
        print(f"  [{label}] MISSING {path}"); return False
    size = os.path.getsize(path)
    g = api("files.getUploadURLExternal", {"filename": os.path.basename(path), "length": size}, json_body=False)
    if not g.get("ok"):
        print(f"  [{label}] getURL ERR {g.get('error')}"); return False
    subprocess.run(["curl", "-s", "-F", f"file=@{path}", g["upload_url"]], stdout=subprocess.DEVNULL)
    c = api("files.completeUploadExternal", {"files": [{"id": g["file_id"], "title": title}], "channel_id": CHANNEL, "initial_comment": comment})
    print(f"  [{label}] {os.path.basename(path)} {'OK' if c.get('ok') else 'ERR ' + str(c.get('error'))}")
    time.sleep(0.8)
    return c.get("ok")

# ---------------- TEXT POSTS ----------------
HEADER = f"📅 *LinkedIn Content Drop — {DATE}*\n16 posts ready (4 Reddit-based + 7 AI News + 5 performance-driven). Carousel PDFs and infographics attached below."

COLLAB = """A pattern keeps showing up in founder threads, and it explains why so many first products launch to silence.

Most founders building their first real product start with a list. Twelve features for launch. An admin dashboard. A mobile app. Three integrations. The plan looks responsible and it feels like progress. It quietly kills the company before a single customer shows up.

The problem is not ambition. Every feature on that list is a guess, and building twelve guesses takes six months. Building the one thing a customer actually asked for takes two weeks. The founders who stall are usually the ones who confused a long roadmap with a validated one.

There is a simpler path that keeps working. Pick the single feature that solves the most painful version of the problem. Ship only that. Put it in front of ten real people who have the problem and watch where they get confused or where they lean in. Let their reaction write the next feature instead of a roadmap built alone in a doc.

What changes when this clicks is the speed of learning. Instead of six months to first feedback there is feedback in week one. The product stops being a bet and turns into a conversation. Revenue tends to show up earlier because something useful exists earlier.

The founders who win their first market rarely build the most. They build the least, learn the fastest, and let demand pull the rest of the product out of them.

What is the one feature you could cut this week and still have something people would pay for?

Follow @founderswing for more."""

POLL = """A question keeps coming up from people sitting at the same fork. A few years into a job they do not love, with a little savings and real doubt about whether the safe move is actually the safe one.

Some say get the MBA and the network. Some say the degree is a slow expensive detour and the real education is building something that can fail. Nobody standing at the fork can see which road pays off until years later.

What is the smartest move for someone 26, unsatisfied, and ready for a change?

☐ Get the MBA for the network and the reset
☐ Keep the job, build on the side until it replaces the salary
☐ Quit and build full time while the risk is still cheap
☐ Stay put, the timing and the savings are not there yet

Drop the path you took and whether it actually worked in the comments."""

AINEWS_HEADER = f"📰 *AI News Posts — {DATE}*\n7 plain-text posts from the linkedin-ai-news-engine:"

AI1 = """Zoom quietly shipped the meeting feature people have wanted for years.

It is called ZoomMate, and it sits inside your live calls.

Not a bot that joins and writes notes after everyone leaves. It listens while you talk and connects what gets decided to the tools where the work actually happens.

You can use it to turn a "we should follow up with that client" moment into a task in your project tool before the call even ends. You can ask it mid-meeting what was agreed last time and get the answer without digging through old notes. It links into Salesforce, Jira, ServiceNow, and Slack, so the decision and the action stop living in two different places.

The impressive part is the timing. Most meeting AI summarizes after everyone has moved on. This one acts while the conversation is still warm, which is the only moment that summary is actually useful.

It runs about 20 dollars per user a month, so it is built for teams, not free for solo use yet.

For anyone who runs five plus calls a day, what would you want it handling automatically while you stay in the conversation?

Follow @founderswing for more tools worth knowing."""

AI2 = """Four of the biggest AI labs shipped new models in the same four weeks.

Big month. Here is what actually matters, without the jargon.

1. OpenAI released GPT-5.5, its new flagship for harder reasoning and coding. The kind of task that used to need three tries now tends to land in one.

2. Google rolled out Gemini 3.5 Pro and made the faster Flash version the default in Search. If you use Google, you are already using it.

3. Anthropic shipped Claude Sonnet 4.8, the cheaper everyday model most people will actually run day to day.

4. Microsoft entered the ring with MAI-Code-1-Flash, a model that turns a plain description into working code for a site or app. They are no longer just reselling other people's models.

5. xAI finally released the long delayed Grok 5.

The pattern under all of it: the frontier is not one company anymore. Five labs are trading the lead every few weeks, and that competition is why prices keep dropping while quality climbs.

Which of these have you actually tried, and did it change anything in your week?

Save this so you can come back to the list."""

AI3 = """The US just told an AI company who is allowed to use its best model.

Here is what happened, in plain terms.

Anthropic, the company behind Claude, recently launched its most capable model yet, called Fable 5. On June 12 the US government issued a directive ordering the company to cut off access to that model, and the larger Mythos 5, for foreign nationals.

So a tool that was open to almost anyone a week ago is now gated by nationality, not by what you are willing to pay.

Why this matters for you. The best AI is starting to follow the same rules as advanced chips. Where you live and what passport you hold may decide which models you can legally use to build your business. For a founder outside the US, the "just use the best tool available" advice now comes with a footnote.

The honest caveat. This is one directive, early and likely to shift as it gets challenged and clarified. It does not mean every model is about to be locked down. Capable cheaper models are still widely available, and most everyday work does not need the absolute frontier.

Does where you are based change which AI tools you reach for, or have you not had to think about it yet?

Follow @founderswing for more breakdowns."""

AI4 = """Most people paying 200 dollars a month for an AI coder do not know this exists.

The tool is called Goose, and it does the core of what the expensive AI coding agents do, for free.

It runs on your own machine, takes a plain instruction like "add login to this app," and actually writes and edits the files instead of just suggesting snippets in a chat window.

Why it is still under the radar. The paid agents have big marketing budgets and Goose is the quiet open option, so it rarely shows up in the feeds where most founders look.

What you can do with it. If you are a non-technical founder shipping a small product, you can wire up real features without a 200 dollar monthly bill before you have a single paying customer. If you already build, you can run it next to your paid tools and keep the simple work off the meter.

The edge is the price. Same category of result, no subscription, no lock-in to one company.

This is exactly the kind of thing we track at FounderWing, the cheaper tool that quietly does the expensive tool's job.

Who in your network is overpaying for AI tooling and should see this?

Follow @founderswing for more."""

AI5 = """If your job lives inside Slack, an AI agent just moved into the building.

Salesforce rolled out a new Slackbot agent that does real work inside the chat tool millions of people use all day.

What it actually is. Not a search box. An agent that can pull up customer records, answer questions about a deal, and take small actions without you leaving the conversation or opening five tabs.

The real impact. A chunk of the work in sales, support, and operations has been about being the person who knows where things live and can fetch them fast. That specific value just got automated. Honestly, that is the part to take seriously.

What you keep. The judgment. Deciding what to do with the information, reading the human on the other end, owning the messy calls a bot will not touch. The fetch-and-summarize layer shrinks. The decide-and-act layer grows.

The practical move this week. Pick the one task you do most that is really just looking something up and relaying it. Write down the steps. That is the first thing to hand to an agent, and the skill of handing work off cleanly is about to be worth more than doing it yourself.

For anyone in sales or ops, which part of your week is mostly fetching information for other people?

Follow @founderswing for more."""

AI6 = """The smartest AI model is about to stop being the one that wins.

Everyone is watching the benchmark race. GPT-5.5, Gemini 3.5, Claude, Grok 5, all trading the top spot every few weeks. That race matters less than people think.

Here is the take. For almost every founder, the winning model will not be the smartest one. It will be the one you can actually access and afford.

Two things this month proved it. First, the US ordered Anthropic to cut its best model off from foreign nationals, so raw capability now comes with a passport check. Second, free and cheap tools keep matching last year's premium ones, so paying for the absolute frontier buys less edge every quarter.

What most people get wrong. They obsess over which model scored highest on a test that has nothing to do with their business. The founder using a good enough model inside a sharp workflow beats the one chasing the leaderboard with no system around it.

Capability is getting commoditized. Access, cost, and the workflow you build around the model are the real moat. That is the whole reason FounderWing exists, to help founders pick the tool that fits instead of the one that trends.

Am I wrong, or has the benchmark race stopped mattering for normal businesses?

Follow @founderswing for more takes."""

AI7 = """Steal this: a recurring AI agent that does your Monday research while you sleep.

Anthropic just added scheduled agents to Claude, so an agent can run on a set schedule on its own.

Set this one up once:

"Every Monday at 7am, search for the latest news on [my 3 competitors] and [my industry]. Summarize anything new in 5 bullet points, flag what matters for a founder, and send it to me."

Now the weekly scan that used to eat an hour of your Monday just shows up done.

The result: you start every week informed without lifting a finger, and you stop forgetting to check.

Save this.

Which recurring task would you hand to an agent first?"""

PERF_HEADER = f"📈 *Performance Posts — {DATE}*\n5 posts modeled on your own top-performing analytics (founderswing report):"

PERF1 = """Most founders talk their startups to death.

The advice everyone repeats is to share your goals. Tell your friends, post the plan, announce the launch date. It is supposed to keep you accountable.

What actually happens is quieter and worse. Every time you explain the idea and watch someone nod, your brain books a small hit of the reward you were supposed to earn by building the thing. You feel the progress without making any. The energy that should have gone into the work leaks out through your mouth.

The founders who ship are usually the ones being a little secretive. Not because they are guarding some genius idea. Because they know the buzz of talking about the work is the same buzz that should only come from doing it, and they refuse to spend it early.

If you have ever felt strangely flat after a great conversation about your big plan, that is not random. You already spent the fuel.

Talk less about what you are building. Build it, then let the thing speak for you.

What is one project you announced loudly and then never finished?

Repost to remind a founder who keeps announcing instead of shipping."""

PERF2 = """Going solo looks like freedom from the outside. From the inside it is four hard things at once, and most people only warn you about one of them.

The income swing gets all the attention. But ask anyone a year in and the thing that nearly broke them is usually something quieter.

What is the hardest part of going solo full time?

☐ The income that swings every single month
☐ Having no one to think out loud with
☐ Being the only person who can do any of it
☐ The silence when nobody notices your wins

Drop the one that hit you hardest and how you got through it."""

PERF3 = """Google just changed its search box for the first time in 25 years.

What changed. The plain text box is turning into an AI-first entry point. Less typing keywords, more asking full questions and getting the answer directly, with the old list of blue links pushed down.

Why it matters for founders and anyone who sells online:

• The free traffic playbook is shifting. Ranking number one means less when the answer shows up before anyone clicks.
• Getting mentioned inside AI answers is becoming the new getting found. Your reviews, your reputation, and where you get talked about start to matter more than your meta tags.
• The businesses that win discovery will be the ones AI tools choose to quote, not the ones who gamed an algorithm.

This does not kill search traffic overnight. But the slow version of this change has already started, and the founders who notice early get a head start on the ones who wait for their numbers to drop.

If half your customers found you through Google search, what would you do differently starting this month?

Follow @founderswing for more."""

# Captions for file uploads
CAP_CAROUSEL = """━━━ CAROUSEL (Reddit) ━━━

A year of building in public, distilled into 5 honest lessons.
The messy middle builds more trust than any launch ever will.
Which lesson hits hardest for where you are right now?
Save this for your next build."""

CAP_INFOGRAPHIC = """━━━ INFOGRAPHIC (Reddit) ━━━

The AI skills market has split into tiers, and the gap is wider than most freelancers expect.
AI agent developers now command up to 300 dollars an hour while general prompt work sits near 70.
The premium is not for knowing AI exists. It is for building systems most people cannot.
Which of these skills are you closest to charging for?
Follow @founderswing for more data."""

CAP_PERF_CAROUSEL = """━━━ PERFORMANCE CAROUSEL ━━━

A founder scaled a Shopify store past 1 million dollars, then walked away from it.
Not because it failed. Because a shinier idea pulled his focus.
The costliest mistake is rarely a bad bet. It is abandoning a good one too early.
Which project of yours deserved more patience than you gave it?
Save this for the next time a new idea calls."""

CAP_PERF_DATAVIZ = """━━━ PERFORMANCE DATA VISUAL ━━━

85 percent of the ways people use AI at work create no real business value.
Most of it is busywork dressed up as progress. Summaries, rewrites, tidy emails.
The founders pulling ahead live in the other 15 percent, using AI to make decisions and money, not just to look busy faster.
Are you using AI to do real work, or just to do small work quicker?
Follow @founderswing for more data."""

def main():
    print("== Section A: header + Reddit text posts ==")
    post_text("header", HEADER)
    post_text("collab", COLLAB)
    post_text("poll", POLL)

    print("== Section B: AI news posts ==")
    post_text("ai-header", AINEWS_HEADER)
    for i, t in enumerate([AI1, AI2, AI3, AI4, AI5, AI6, AI7], 1):
        post_text(f"ai-{i}", t)

    print("== Section C: performance text posts ==")
    post_text("perf-header", PERF_HEADER)
    post_text("perf-1", PERF1)
    post_text("perf-2", PERF2)
    post_text("perf-3", PERF3)

    print("== Files: Reddit carousel + infographic ==")
    bdir = "carousel-routine/output/2026-06-13/carousel-branded"
    upload("carousel-pdf", f"{bdir}/carousel-20260613.pdf", "carousel-build-in-public-20260613.pdf", CAP_CAROUSEL)
    for n in range(1, 8):
        upload(f"carousel-s{n}", f"{bdir}/slide-0{n}.png", f"slide-0{n}.png", f"Carousel slide {n}/7")
    upload("infographic", "linkedin-infographic-20260613.png", "freelance-ai-rates-20260613.png", CAP_INFOGRAPHIC)

    print("== Files: performance carousel + data visual ==")
    pdir = "carousel-routine/output/2026-06-13/carousel-performance"
    upload("perf-pdf", f"{pdir}/carousel-20260613.pdf", "carousel-1M-store-20260613.pdf", CAP_PERF_CAROUSEL)
    for n in range(1, 8):
        upload(f"perf-s{n}", f"{pdir}/slide-0{n}.png", f"perf-slide-0{n}.png", f"Performance slide {n}/7")
    upload("perf-dataviz", "linkedin-performance-infographic-20260613.png", "ai-value-gap-20260613.png", CAP_PERF_DATAVIZ)

    print("== DELIVERY COMPLETE ==")

if __name__ == "__main__":
    main()
