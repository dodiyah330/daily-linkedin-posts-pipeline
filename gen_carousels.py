#!/usr/bin/env python3
"""Generate Founders Wing cream-design carousel slides (typography-forward) for both
the branded carousel and the performance carousel. Writes slide-01..07.html into
carousel-routine/temp/<dir>/."""
import os

BASE = os.path.dirname(os.path.abspath(__file__))

PAGE = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080"/>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800;900&family=Instrument+Serif:ital@1&display=swap" rel="stylesheet"/>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{width:1080px;height:1080px;overflow:hidden;background:#F8F7F3;color:#111;font-family:'Plus Jakarta Sans',sans-serif;position:relative}}
.header{{position:absolute;top:60px;left:70px;right:70px;display:flex;justify-content:space-between;align-items:center;z-index:10}}
.hleft{{display:flex;align-items:center;gap:12px;font-size:14px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:#111}}
.dot{{width:14px;height:14px;border-radius:50%;background:{accent}}}
.hright{{display:flex;align-items:center;gap:15px}}
.fw{{font-family:'Instrument Serif',serif;font-style:italic;font-size:26px;color:#999}}
.badge{{width:46px;height:46px;background:{accent};border-radius:50%;display:flex;justify-content:center;align-items:center;color:#fff;font-weight:800;font-size:17px}}
.content{{position:absolute;top:{top}px;left:70px;right:70px;z-index:5}}
.kick{{font-size:18px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:{accent};margin-bottom:22px}}
.headline{{font-size:{hsize}px;font-weight:900;letter-spacing:-2.5px;line-height:1.05}}
.headline em{{font-family:'Instrument Serif',serif;font-style:italic;color:{accent};font-weight:400;letter-spacing:0;padding-left:4px}}
.stat{{font-size:190px;font-weight:900;letter-spacing:-8px;line-height:0.9;color:{accent};margin-bottom:6px}}
.body{{font-size:29px;font-weight:500;color:#333;line-height:1.42;margin-top:30px;max-width:900px}}
.line{{width:64px;height:5px;background:{accent};margin-top:34px}}
.bottom{{position:absolute;bottom:68px;left:70px;right:70px;display:flex;justify-content:space-between;align-items:center;z-index:5}}
.swipe{{font-size:14px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:#111}}
.pill{{background:#111;color:#fff;padding:20px 38px;border-radius:50px;font-size:21px;font-weight:800}}
.pill em{{font-family:'Instrument Serif',serif;font-style:italic;color:{accent};font-weight:400;margin-left:6px}}
</style></head><body>
<div class="header"><div class="hleft"><span class="dot"></span>{kicker}</div>
<div class="hright"><div class="fw">founders wing / 2026</div><div class="badge">{num}</div></div></div>
<div class="content">{inner}</div>
<div class="bottom">{bottom}</div>
</body></html>"""


def build(slide, accent, kicker):
    num = slide["num"]
    inner = ""
    if slide.get("stat"):
        inner += f'<div class="stat">{slide["stat"]}</div>'
    if slide.get("eyebrow") and not slide.get("stat"):
        inner += f'<div class="kick">{slide["eyebrow"]}</div>'
    inner += f'<div class="headline">{slide["headline"]}</div>'
    if slide.get("cta"):
        inner += '<div class="line"></div>'
    if slide.get("body"):
        inner += f'<div class="body">{slide["body"]}</div>'
    if slide.get("cta"):
        bottom = '<div class="pill">follow @founderswing for daily <em>frameworks.</em></div>'
    else:
        bottom = '<div></div><div class="swipe">SWIPE &rarr;</div>'
    return PAGE.format(
        accent=accent, kicker=kicker, num=num,
        top=slide.get("top", 270), hsize=slide.get("hsize", 68),
        inner=inner, bottom=bottom,
    )


def write_set(dirname, accent, kicker, slides):
    outdir = os.path.join(BASE, "carousel-routine", "temp", dirname)
    os.makedirs(outdir, exist_ok=True)
    # clean old slides
    for f in os.listdir(outdir):
        if f.startswith("slide-") and f.endswith(".html"):
            os.remove(os.path.join(outdir, f))
    for s in slides:
        path = os.path.join(outdir, f'slide-{s["num"]}.html')
        open(path, "w").write(build(s, accent, kicker))
    print(f"{dirname}: wrote {len(slides)} slides -> {outdir}")


# ---- BRANDED CAROUSEL: 5 truths from a year building in public ----
BRANDED = [
    {"num": "01", "hsize": 78, "top": 300, "eyebrow": "Build in public",
     "headline": "5 truths from a <em>year</em> building in public"},
    {"num": "02", "eyebrow": "Truth 01", "headline": "Your audience becomes your <em>first</em> customers",
     "body": "Building in public grows an audience and a product at the same time. That audience quietly becomes the first ten customers most founders struggle to find."},
    {"num": "03", "eyebrow": "Truth 02", "headline": "The <em>messy</em> middle wins",
     "body": "Posts about what broke pull more replies and more trust than any polished launch announcement ever did."},
    {"num": "04", "eyebrow": "Truth 03", "headline": "Most of the roadmap was <em>wrong</em>",
     "body": "Nearly half the features planned on day one got cut once real users actually ignored them."},
    {"num": "05", "eyebrow": "Truth 04", "headline": "Distribution compounds <em>slower</em> than code",
     "body": "The product was ready in months. The audience that made it sell took the full year to build."},
    {"num": "06", "eyebrow": "Truth 05", "headline": "Public progress forces <em>accountability</em>",
     "body": "Sharing the work in the open made it much harder to quit on the weeks when nothing seemed to work."},
    {"num": "07", "hsize": 74, "top": 300, "cta": True,
     "headline": "Build it, then let it <em>speak.</em>",
     "body": "A year of building in public, distilled. Save this for your next project."},
]

# ---- PERFORMANCE CAROUSEL: why he walked away from a $1M store ----
PERF = [
    {"num": "01", "hsize": 76, "top": 300, "eyebrow": "Founder story",
     "headline": "Why he walked away from a <em>$1M</em> store"},
    {"num": "02", "eyebrow": "The build", "headline": "From zero to <em>$1M</em> in a year",
     "body": "He launched a Shopify store and scaled it hard. Within twelve months it crossed a million dollars in revenue."},
    {"num": "03", "stat": "$1M", "top": 230, "headline": "then he <em>stopped</em>",
     "body": "Not because sales dropped. Because a newer, shinier idea started pulling his attention away."},
    {"num": "04", "eyebrow": "The drift", "headline": "The new idea felt more <em>exciting</em>",
     "body": "The working business became boring. The blank new project felt like the real opportunity. It usually does."},
    {"num": "05", "eyebrow": "The cost", "headline": "A working machine left to <em>rust</em>",
     "body": "Months later the store that printed money sat half abandoned, while the shiny idea went nowhere."},
    {"num": "06", "eyebrow": "The lesson", "headline": "The costliest mistake is <em>quitting</em> a winner",
     "body": "Most founders do not fail on bad bets. They fail by abandoning good ones the moment they stop feeling new."},
    {"num": "07", "hsize": 64, "top": 300, "cta": True,
     "headline": "Boring and working beats <em>new</em> and unproven.",
     "body": "Save this for the next time a shiny idea calls."},
]

write_set("carousel-branded", "#D9785B", "Founders Wing / build in public", BRANDED)
write_set("carousel-performance", "#E16259", "Founders Wing / founder story", PERF)
print("done")
