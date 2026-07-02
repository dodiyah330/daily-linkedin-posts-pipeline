#!/usr/bin/env python3
"""Sample Varun-lane carousel WITH real images + first-person CTA.
'5 jobs AI is quietly rewriting'. Writes 7 slides to carousel-routine/temp/carousel-sample/.
Images already downloaded to that dir's assets/."""
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
.content{{position:absolute;top:230px;left:70px;right:70px;bottom:150px;z-index:5;display:flex;align-items:center;gap:54px}}
.col{{flex:1;min-width:0}}
.kick{{font-size:18px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:{accent};margin-bottom:20px}}
.headline{{font-size:{hsize}px;font-weight:900;letter-spacing:-2.5px;line-height:1.05}}
.headline em{{font-family:'Instrument Serif',serif;font-style:italic;color:{accent};font-weight:400;letter-spacing:0;padding-left:4px}}
.body{{font-size:27px;font-weight:500;color:#333;line-height:1.42;margin-top:26px}}
.line{{width:64px;height:5px;background:{accent};margin-top:30px}}
.imgwrap{{flex-shrink:0;width:380px;height:460px;border-radius:30px;overflow:hidden;box-shadow:0 24px 50px rgba(0,0,0,0.16);position:relative}}
.imgwrap img{{width:100%;height:100%;object-fit:cover}}
.imgwrap::after{{content:"";position:absolute;inset:0;border-radius:30px;border:1px solid rgba(0,0,0,0.06);box-shadow:inset 0 0 0 6px rgba(248,247,243,0.0)}}
.imgtag{{position:absolute;left:16px;bottom:16px;background:rgba(17,17,17,0.78);color:#fff;font-size:14px;font-weight:700;letter-spacing:1px;text-transform:uppercase;padding:8px 14px;border-radius:30px}}
.bottom{{position:absolute;bottom:62px;left:70px;right:70px;display:flex;justify-content:space-between;align-items:center;z-index:5}}
.swipe{{font-size:14px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:#111}}
.pill{{background:#111;color:#fff;padding:20px 40px;border-radius:50px;font-size:22px;font-weight:800}}
.pill em{{font-family:'Instrument Serif',serif;font-style:italic;color:{accent};font-weight:400;margin-left:6px}}
.cta-content{{position:absolute;top:300px;left:70px;right:70px;z-index:5}}
</style></head><body>
<div class="header"><div class="hleft"><span class="dot"></span>{kicker}</div>
<div class="hright"><div class="fw">founders wing / 2026</div><div class="badge">{num}</div></div></div>
{main}
<div class="bottom">{bottom}</div>
</body></html>"""

ACCENT = "#5E6AD2"
KICKER = "Founders Wing / future of work"

SLIDES = [
    {"num":"01","hsize":62,"img":"hero.jpg","tag":"the shift","kick":"Future of work",
     "headline":"5 jobs AI is quietly <em>rewriting</em>",
     "body":"Not replacing. Rewriting. Here is which half of your job just changed."},
    {"num":"02","img":"marketing.jpg","tag":"marketers","kick":"01 · Marketers",
     "headline":"Making it is <em>automated</em>",
     "body":"The asset creation goes to AI. Knowing what will actually land is worth more than ever."},
    {"num":"03","img":"lawyer.jpg","tag":"lawyers","kick":"02 · Lawyers",
     "headline":"Drafting is <em>minutes</em> now",
     "body":"AI writes and reviews fast. Judgment, strategy, and the hard client call stay human."},
    {"num":"04","img":"developer.jpg","tag":"developers","kick":"03 · Developers",
     "headline":"Code is the <em>easy</em> part",
     "body":"Writing it is mostly solved. Deciding what to build, and why, is the actual job now."},
    {"num":"05","img":"designer.jpg","tag":"designers","kick":"04 · Designers",
     "headline":"The canvas <em>fills</em> itself",
     "body":"AI generates in seconds. Taste, and knowing what to cut, became the whole skill."},
    {"num":"06","img":"accountant.jpg","tag":"accountants","kick":"05 · Accountants",
     "headline":"The math runs <em>itself</em>",
     "body":"Number crunching is automated. Reading the story behind the numbers is the value."},
    {"num":"07","cta":True,"hsize":74,
     "headline":"Find your <em>human</em> half.",
     "body":"AI is coming for the half of your job you did not enjoy anyway. Lean hard into the other half."},
]

def build(s):
    if s.get("cta"):
        main = (f'<div class="cta-content"><div class="headline" style="font-size:{s.get("hsize",74)}px">'
                f'{s["headline"]}</div><div class="line"></div><div class="body">{s["body"]}</div></div>')
        bottom = '<div class="pill">follow me for daily AI <em>breakdowns.</em></div>'
    else:
        img = (f'<div class="imgwrap"><img src="assets/{s["img"]}"/>'
               f'<div class="imgtag">{s.get("tag","")}</div></div>')
        col = (f'<div class="col"><div class="kick">{s["kick"]}</div>'
               f'<div class="headline" style="font-size:{s.get("hsize",60)}px">{s["headline"]}</div>'
               f'<div class="body">{s["body"]}</div></div>')
        main = f'<div class="content">{col}{img}</div>'
        bottom = '<div></div><div class="swipe">SWIPE &rarr;</div>'
    return PAGE.format(accent=ACCENT, kicker=KICKER, num=s["num"], hsize=s.get("hsize",60), main=main, bottom=bottom)

outdir = os.path.join(BASE, "carousel-routine", "temp", "carousel-sample")
os.makedirs(outdir, exist_ok=True)
for f in os.listdir(outdir):
    if f.startswith("slide-") and f.endswith(".html"): os.remove(os.path.join(outdir, f))
for s in SLIDES:
    open(os.path.join(outdir, f'slide-{s["num"]}.html'), "w").write(build(s))
print(f"wrote {len(SLIDES)} image-enabled sample slides -> {outdir}")
