#!/usr/bin/env python3
"""Deliver the 2026-06-14 Varun-lane batch (16 posts + visuals) to #linkedin-content."""
import json, os, subprocess, urllib.request, urllib.parse, time

BASE = os.path.dirname(os.path.abspath(__file__)); os.chdir(BASE)
TOKEN = subprocess.check_output("grep '^SLACK_BOT_TOKEN=' .env | cut -d'=' -f2", shell=True).decode().strip()
CHANNEL = subprocess.check_output("grep '^SLACK_CHANNEL_ID=' .env | cut -d'=' -f2", shell=True).decode().strip() or "C0BEG7HAXHQ"

def api(method, payload, json_body=True):
    if json_body:
        data = json.dumps(payload).encode("utf-8"); ct = "application/json; charset=utf-8"
    else:
        data = urllib.parse.urlencode(payload).encode("utf-8"); ct = "application/x-www-form-urlencoded"
    req = urllib.request.Request(f"https://slack.com/api/{method}", data=data,
                                 headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": ct})
    return json.loads(urllib.request.urlopen(req).read().decode("utf-8"))

def post(label, text):
    r = api("chat.postMessage", {"channel": CHANNEL, "text": text, "unfurl_links": False, "unfurl_media": False})
    print(f"  [{label}] {'OK' if r.get('ok') else 'ERR ' + str(r.get('error'))}"); time.sleep(0.7)

def upload(label, path, title, comment):
    if not os.path.exists(path): print(f"  [{label}] MISSING {path}"); return
    g = api("files.getUploadURLExternal", {"filename": os.path.basename(path), "length": os.path.getsize(path)}, json_body=False)
    if not g.get("ok"): print(f"  [{label}] getURL ERR {g.get('error')}"); return
    subprocess.run(["curl", "-s", "-F", f"file=@{path}", g["upload_url"]], stdout=subprocess.DEVNULL)
    c = api("files.completeUploadExternal", {"files": [{"id": g["file_id"], "title": title}], "channel_id": CHANNEL, "initial_comment": comment})
    print(f"  [{label}] {os.path.basename(path)} {'OK' if c.get('ok') else 'ERR ' + str(c.get('error'))}"); time.sleep(0.7)

HEADER = ("📅 *LinkedIn Content Drop — June 14, 2026*\n16 posts ready (4 Reddit-based + 7 AI News + 5 performance), "
          "all in the new Varun lane with first-person CTAs. Carousels (incl. a real-image ElevenLabs brand-story) "
          "and infographics attached below.")

COLLAB = """For most of history, the people who got ahead were the ones who knew things. The doctor who had memorized the conditions. The lawyer who knew the cases. The analyst who could find the number nobody else could find.

That moat just disappeared.

AI now hands the answer to anyone who asks, in seconds, for free. The information advantage that used to take a decade to build is now a text box. And the professionals feeling the most anxious right now are usually the ones whose entire value was being the person who knew the thing.

Here is what did not get commoditized. Knowing which question to ask. Judging whether the answer is any good. Deciding what to actually do with it, and owning the call when it matters. AI can tell you what the data says. It cannot tell you whether to bet the company on it.

The shift is quiet but total. Value is moving from having the answer to having the judgment. From recall to taste. From knowing to deciding.

The people who will be fine are not the ones racing to memorize more. They are the ones building the judgment to tell which answers are worth trusting, and the nerve to act on them.

What is one part of your work that is pure judgment, the part AI cannot hand to your competitor?

Follow me for more on where AI is taking work."""

POLL = """Every week someone announces that another skill is now obsolete. Learn to code. No wait, AI codes now. Learn to write. No wait, AI writes now. It is exhausting, and most of the advice cancels out the advice from last month.

So strip it back. In a world where AI does the doing, one human ability holds its value better than the rest.

Which skill is the most future-proof in the AI age?

☐ Judgment, knowing what is actually worth doing
☐ Taste, knowing what is good and what is not
☐ People, trust and relationships a bot cannot fake
☐ Adaptability, how fast you pick up whatever comes next

Drop the one you are betting your next five years on, and why."""

AINEWS_HEADER = "📰 *AI News Posts — June 14, 2026*\n7 plain-English posts, impact-framed:"

AI1 = """OpenAI will now teach you to use AI, for free.

It launched OpenAI Academy, a set of free courses on actually using AI, and it is not built for engineers. It is for normal people who can feel this stuff mattering and do not know where to start.

Here is why it matters. The gap stopped being about access a while ago. Everyone has the tools now. The real gap is knowing how to use them well, and that is exactly what structured, free learning closes.

What to do with it. Pick the one task you do most in your week, the repetitive one you quietly dread. Take the course that touches it. Apply it the same day. The advantage is not that the courses exist. It is that most people will bookmark them and never open them.

For anyone who keeps meaning to "get good at AI" and never does, what is the one task you would point it at first?

Follow me for more tools worth knowing."""

AI2 = """The AI money and model news this month is genuinely staggering. Here is what matters without the jargon.

1. Anthropic is shipping Claude Fable 5, its most capable model made safe for everyday use, with the bigger Mythos 5 behind it.

2. OpenAI's GPT-5.5 and Google's Gemini 3.5 Pro keep trading the top spot every few weeks.

3. Meta said it will spend 115 to 135 billion dollars on AI this year. Nearly double last year. Microsoft, Google and Amazon are all in the same range.

4. Anthropic put an unreleased frontier model inside AWS, Apple, Google and JPMorgan to hunt for security holes in their software.

The pattern under all of it: the biggest companies on earth are betting their budgets on this being the platform shift of the decade. That is not hype, that is where the money already went.

Which of these do you think actually changes a normal person's job within a year?

Save this so you can come back to it."""

AI3 = """Anthropic just put an unreleased AI inside Apple, Google and JPMorgan.

Here is what happened, plainly. A program called Project Glasswing gave a handful of giant companies early access to an unreleased, frontier Claude model with one job: find and fix critical security holes in their software before attackers do.

Why this matters for you. The same AI that can write code at scale can now audit it at scale. The apps, banks and accounts you use every day are about to get genuinely harder to break into. That is a quiet win that touches everyone.

The honest caveat. The exact capability that finds a flaw to patch it can also find a flaw to exploit it. This tech cuts both ways. The defenders just got a head start, not a permanent lead, and the attackers have the same kind of tools.

Knowing AI now guards the systems you rely on, do you trust them more or less than you did last week?

Follow me for more breakdowns."""

AI4 = """Most people paying 200 dollars a month for an AI coder do not know this free one exists.

It is called Goose, and it does the core of what the expensive AI coding agents do, for free, on your own machine. You give it a plain instruction and it writes and edits the actual files, not just suggestions in a chat box.

Why it stays under the radar. No marketing budget. It is the quiet open option, so it rarely shows up where most people look.

What you can do with it. A non-technical founder can wire up real features without a subscription, before there is a single paying customer. Same category of result, no monthly bill, no lock-in.

This is exactly the kind of thing we hunt for at FounderWing, the cheaper tool quietly doing the expensive one's job.

Who in your network is overpaying for AI tooling and should see this?

Follow me for more."""

AI5 = """Meta is about to spend up to 135 billion dollars in a single year, most of it on AI.

That is nearly double last year, and Microsoft, Google and Amazon are all spending in the same range.

Here is what that means for you. When the most powerful companies on earth pour that kind of money into one thing, they are not buying a feature. They are betting the next decade runs on it. And where that money flows, jobs and opportunity follow close behind.

The careers being created are not all technical. The scarce, well-paid people are the ones who can take these tools and point them at a real business problem, not the ones building the models. Applied beats theoretical.

The practical move this week. Stop waiting to see if AI sticks. The smartest money on the planet already placed the bet. Pick the corner of it closest to what you already do, and go deep.

If you knew AI was the safe bet for the next ten years, what would you start learning this month?

Follow me for more."""

AI6 = """Everyone uses AI now. Almost nobody uses it well. That gap is the entire opportunity.

80 percent of employees now use AI at work, up from 53 percent two years ago. But dig in and only about 1 in 5 use it regularly, and most of that is asking it to tidy an email.

Here is the take. "Using AI" already became table stakes. It is the new baseline, not a differentiator. The edge moved, and most people did not notice it move.

It is no longer whether you use AI. It is whether you have built it into how you actually work, on the tasks that move money. The person doing real work with AI is now quietly competing against people doing busywork with AI and calling it the same thing. It is not the same thing.

That gap, between using it and using it well, is the whole reason FounderWing exists.

Are you using AI to do real work, or just to do small work faster?

Follow me for more takes."""

AI7 = """Steal this: a 3-question test for whether AI is coming for your job.

Run your role through these, honestly:

1. Is most of my value knowing or fetching information? If yes, that part is going to AI. It already went.

2. Does my work need judgment, taste, or someone to own the outcome when it goes wrong? If yes, that part is safe, and getting more valuable every month.

3. Am I the one using AI, or the one who could be replaced by someone who does?

Where you land tells you exactly what to lean into and what to drop this year. It turns a vague fear into a plan.

Save this, and run one person you care about through it too.

Which of the three hit hardest for you?

Follow me for daily AI breakdowns."""

PERF_HEADER = "📈 *Performance Posts — June 14, 2026*\n5 posts modeled on your top-performing analytics:"

PERF1 = """Everyone is bracing for AI to take their job. Almost nobody is bracing for the opposite problem.

The fear is loud and everywhere. Will the robot replace me. Should I be scared. What happens to my career. It feels responsible to worry about it.

Here is the uncomfortable part. For most people, getting replaced is not the real risk. Staying exactly the same size is. AI just handed a single person the output of a small team, and the majority are using it to write slightly faster emails.

The person who should worry you is not the AI. It is the colleague who quietly figured out how to do three people's work with it, and is now impossible to let go of while everyone else debates whether to be scared.

Defense against AI is a losing game. The tools are not going back in the box. Offense is the only move that pays. Stop asking how do I protect what I do. Start asking what could I do now that was impossible for one person a year ago.

The people who win the next five years are not the ones who survived AI. They are the ones who used it to become impossible to ignore.

What is one thing you could do this month that needed a whole team a year ago?

Repost to push a friend from defense to offense."""

PERF2 = """AI at work sounds exciting in the keynote and terrifying at 2am. Most people carry a version of the same quiet fear and never say it out loud.

So say it. No judgment, everyone is feeling at least one of these.

What scares you most about AI at work?

☐ That it will quietly make my role unnecessary
☐ That I am already behind and cannot catch up
☐ That I will have to relearn everything every year
☐ Honestly nothing, I am more excited than scared

Drop the one that is most true for you right now."""

PERF3 = """Google just redesigned its search box for the first time in 25 years.

What changed. It is turning into an AI-first answer engine. You ask a full question, you get the answer, and the ten blue links get pushed down or disappear.

Why it matters for anyone who sells, creates, or gets found online:

• Ranking number one means less when the answer shows up before anyone clicks.
• Getting quoted by the AI is the new getting found. Your reputation and where you are mentioned matter more than your keywords.
• The brands that win are the ones AI chooses to cite, not the ones who gamed the old algorithm.

This does not happen overnight, but the slow version already started. The people who adjust early get a head start on the ones who wait for their traffic to drop.

If half your customers found you through Google, what would you change this month?

Follow me for more."""

CAP_CAROUSEL = """━━━ CAROUSEL (Reddit) — ElevenLabs, real source images ━━━

Any voice can now be cloned from a few seconds of audio.
The same tech that lets creators dub a video into 30 languages also lets a stranger fake your voice on a phone call. ElevenLabs is the tool behind both.
The opportunity and the threat are the exact same product.
Have you heard an AI voice you genuinely could not tell was fake?
Follow me for daily AI breakdowns."""

CAP_INFOGRAPHIC = """━━━ INFOGRAPHIC (Reddit) ━━━

The average worker is interrupted 275 times a day. That is once every two minutes.
We built tools that can do hours of work in seconds, then filled every one of those seconds with a notification.
In the AI age the bottleneck is not how fast you can produce. It is whether you can focus long enough to think.
Attention just became the most valuable thing you own.
How many of your 275 daily interruptions actually needed you?
Follow me for more on working in the AI age."""

CAP_PERF_CAROUSEL = """━━━ PERFORMANCE CAROUSEL ━━━

5 skills you were told to master that AI just made worthless.
And the one thing that replaced each of them. The pattern repeats every time: the doing got automated, the deciding got valuable.
None of this means you are behind. It means the game changed and most people are still studying the old rulebook.
Which of these did you spend years getting good at?
Save this and follow me for more on where work is heading."""

CAP_PERF_DATAVIZ = """━━━ PERFORMANCE DATA VISUAL ━━━

80 percent of workers now use AI. Almost none of them use it well.
Two years ago it was 53 percent. Today nearly everyone has access, but only about 1 in 5 use it regularly, and most of that is tidying up emails.
Using AI stopped being the edge. Using it on the work that actually matters is the edge now.
Are you in the 80 percent who touch it, or the few who build their week around it?
Follow me for more data on the AI shift."""

BR = "carousel-routine/output/2026-06-14/carousel-branded"
PF = "carousel-routine/output/2026-06-14/carousel-performance"

def main():
    print("== A: header + Reddit text ==")
    post("header", HEADER); post("collab", COLLAB); post("poll", POLL)
    print("== B: AI news ==")
    post("ai-header", AINEWS_HEADER)
    for i, t in enumerate([AI1, AI2, AI3, AI4, AI5, AI6, AI7], 1): post(f"ai-{i}", t)
    print("== C: performance text ==")
    post("perf-header", PERF_HEADER); post("perf-1", PERF1); post("perf-2", PERF2); post("perf-3", PERF3)
    print("== Files: Reddit carousel (ElevenLabs) + infographic ==")
    upload("carousel-pdf", f"{BR}/carousel-20260614.pdf", "elevenlabs-any-voice-faked.pdf", CAP_CAROUSEL)
    for n in range(1, 8): upload(f"car-s{n}", f"{BR}/slide-0{n}.png", f"slide-0{n}.png", f"Carousel slide {n}/7")
    upload("infographic", "linkedin-infographic-20260614.png", "digital-distraction-crisis.png", CAP_INFOGRAPHIC)
    print("== Files: performance carousel + data visual ==")
    upload("perf-pdf", f"{PF}/carousel-20260614.pdf", "5-skills-ai-made-worthless.pdf", CAP_PERF_CAROUSEL)
    for n in range(1, 8): upload(f"perf-s{n}", f"{PF}/slide-0{n}.png", f"perf-slide-0{n}.png", f"Perf slide {n}/7")
    upload("perf-dataviz", "linkedin-performance-infographic-20260614.png", "ai-adoption-gap.png", CAP_PERF_DATAVIZ)
    print("== DONE ==")

if __name__ == "__main__":
    main()
