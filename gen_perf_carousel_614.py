#!/usr/bin/env python3
"""Performance thesis carousel (typography-forward, no stock): '5 skills AI just made worthless'.
Writes 7 slides to temp/carousel-performance/."""
import os
BASE = os.path.dirname(os.path.abspath(__file__))
ACCENT = "#E63946"
KICK = "Founders Wing / future of work"

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
.kick{{font-size:18px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:{accent};margin-bottom:20px}}
.headline{{font-size:{hsize}px;font-weight:900;letter-spacing:-2.5px;line-height:1.05}}
.headline em{{font-family:'Instrument Serif',serif;font-style:italic;color:{accent};font-weight:400;letter-spacing:0;padding-left:4px}}
.body{{font-size:29px;font-weight:500;color:#333;line-height:1.42;margin-top:28px;max-width:900px}}
.line{{width:64px;height:5px;background:{accent};margin-top:32px}}
.bottom{{position:absolute;bottom:68px;left:70px;right:70px;display:flex;justify-content:space-between;align-items:center;z-index:5}}
.swipe{{font-size:14px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:#111}}
.pill{{background:#111;color:#fff;padding:20px 40px;border-radius:50px;font-size:22px;font-weight:800}}
.pill em{{font-family:'Instrument Serif',serif;font-style:italic;color:{accent};font-weight:400;margin-left:6px}}
</style></head><body>
<div class="header"><div class="hleft"><span class="dot"></span>{kick}</div>
<div class="hright"><div class="fw">founders wing / 2026</div><div class="badge">{num}</div></div></div>
<div class="content">{inner}</div>
<div class="bottom">{bottom}</div>
</body></html>"""

S = [
    {"num":"01","top":300,"hsize":76,"kick":"Future of work",
     "headline":'5 skills AI just made <em>worthless</em>',
     "body":"And the one thing that replaced each. The doing got automated. The deciding got valuable."},
    {"num":"02","top":270,"kick":"01 · out: recall","headline":'Knowing the <em>answer</em>',
     "body":"Memorizing facts used to be a career. Now it is a text box. Asking the sharp question is the skill that replaced it."},
    {"num":"03","top":270,"kick":"02 · out: the first draft","headline":'Producing the <em>output</em>',
     "body":"AI fills the blank page in seconds. The taste to know what is good, and cut the rest, is what is rare now."},
    {"num":"04","top":270,"kick":"03 · out: speed","headline":'Doing the task <em>fast</em>',
     "body":"Everything is fast now. Choosing the right task to do at all beats doing the wrong one quickly."},
    {"num":"05","top":270,"kick":"04 · out: tool mastery","headline":'Mastering the <em>software</em>',
     "body":"The tool changes every quarter. Knowing what you actually want to build with it outlasts any single one."},
    {"num":"06","top":270,"kick":"05 · out: being smartest","headline":'Being the <em>smartest</em>',
     "body":"AI knows more facts than the whole room. Being the one who decides and ships is the edge that is left."},
    {"num":"07","top":300,"hsize":70,"cta":True,
     "headline":'The doing is done. <em>Decide.</em>',
     "body":"Save this for the next time someone tells you to learn the old skill."},
]

def build(s):
    inner = f'<div class="kick">{s["kick"]}</div>' if s.get("kick") else ""
    inner += f'<div class="headline" style="font-size:{s.get("hsize",60)}px">{s["headline"]}</div>'
    if s.get("cta"): inner += '<div class="line"></div>'
    if s.get("body"): inner += f'<div class="body">{s["body"]}</div>'
    bottom = ('<div class="pill">follow me for more on <em>work.</em></div>' if s.get("cta")
              else '<div></div><div class="swipe">SWIPE &rarr;</div>')
    return PAGE.format(accent=ACCENT, kick=KICK, num=s["num"], top=s["top"], hsize=s.get("hsize",60), inner=inner, bottom=bottom)

outdir = os.path.join(BASE, "carousel-routine", "temp", "carousel-performance")
os.makedirs(outdir, exist_ok=True)
for f in os.listdir(outdir):
    if f.startswith("slide-") and f.endswith(".html"): os.remove(os.path.join(outdir, f))
for s in S:
    open(os.path.join(outdir, f'slide-{s["num"]}.html'), "w").write(build(s))
print(f"wrote {len(S)} thesis slides -> {outdir}")
