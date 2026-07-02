#!/usr/bin/env python3
"""Brand-story carousel renderer — real source screenshots framed in a browser window.
Reference implementation of the free real-source-image technique. This run: ElevenLabs.
Writes 7 slides to temp/carousel-branded/ (assets captured there by capture_source.js)."""
import os
BASE = os.path.dirname(os.path.abspath(__file__))
ACCENT = "#7C3AED"
KICK = "Founders Wing / the shift"
OUTDIR_NAME = "carousel-branded"

PAGE = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080"/>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800;900&family=Instrument+Serif:ital@1&display=swap" rel="stylesheet"/>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{width:1080px;height:1080px;overflow:hidden;background:#F8F7F3;color:#111;font-family:'Plus Jakarta Sans',sans-serif;position:relative}}
.header{{position:absolute;top:56px;left:70px;right:70px;display:flex;justify-content:space-between;align-items:center;z-index:10}}
.hleft{{display:flex;align-items:center;gap:12px;font-size:14px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:#111}}
.dot{{width:14px;height:14px;border-radius:50%;background:{accent}}}
.hright{{display:flex;align-items:center;gap:14px}}
.fw{{font-family:'Instrument Serif',serif;font-style:italic;font-size:24px;color:#999}}
.badge{{width:46px;height:46px;background:{accent};border-radius:50%;display:flex;justify-content:center;align-items:center;color:#fff;font-weight:800;font-size:17px}}
.top{{position:absolute;top:165px;left:70px;right:70px;z-index:5}}
.kick{{font-size:18px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:{accent};margin-bottom:18px}}
.headline{{font-weight:900;letter-spacing:-2.5px;line-height:1.05}}
.headline em{{font-family:'Instrument Serif',serif;font-style:italic;color:{accent};font-weight:400;letter-spacing:0;padding-left:4px}}
.subline{{font-size:25px;font-weight:500;color:#444;margin-top:18px;max-width:850px;line-height:1.4}}
.win{{position:absolute;left:70px;right:70px;bottom:78px;height:430px;border-radius:18px;overflow:hidden;box-shadow:0 30px 70px rgba(0,0,0,0.18);background:#fff;z-index:4;border:1px solid rgba(0,0,0,0.06)}}
.winbar{{height:40px;background:#ECEAE5;display:flex;align-items:center;gap:9px;padding:0 18px}}
.wd{{width:12px;height:12px;border-radius:50%}}
.winurl{{margin-left:14px;font-size:14px;color:#8A8275;font-weight:600}}
.winshot{{height:calc(100% - 40px);overflow:hidden}}
.winshot img{{width:100%;height:100%;object-fit:cover;object-position:center top}}
.center{{position:absolute;top:300px;left:70px;right:70px;z-index:5}}
.body{{font-size:31px;font-weight:500;color:#333;line-height:1.42;margin-top:28px;max-width:880px}}
.line{{width:64px;height:5px;background:{accent};margin-top:32px}}
.bottom{{position:absolute;bottom:60px;left:70px;right:70px;display:flex;justify-content:space-between;align-items:center;z-index:6}}
.swipe{{font-size:14px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:#111}}
.pill{{background:#111;color:#fff;padding:20px 40px;border-radius:50px;font-size:22px;font-weight:800}}
.pill em{{font-family:'Instrument Serif',serif;font-style:italic;color:{accent};font-weight:400;margin-left:6px}}
</style></head><body>
<div class="header"><div class="hleft"><span class="dot"></span>{kick}</div>
<div class="hright"><div class="fw">founders wing</div><div class="badge">{num}</div></div></div>
{main}
<div class="bottom">{bottom}</div>
</body></html>"""

WIN = ('<div class="top"><div class="kick">{kick}</div>'
       '<div class="headline" style="font-size:{hsize}px">{headline}</div>'
       '<div class="subline">{sub}</div></div>'
       '<div class="win"><div class="winbar"><span class="wd" style="background:#FF5F57"></span>'
       '<span class="wd" style="background:#FEBC2E"></span><span class="wd" style="background:#28C840"></span>'
       '<span class="winurl">{src}</span></div><div class="winshot"><img src="assets/{img}"/></div></div>')

CEN = ('<div class="center"><div class="kick">{kick}</div>'
       '<div class="headline" style="font-size:{hsize}px">{headline}</div>'
       '<div class="body">{body}</div></div>')

S = [
    {"num":"01","img":"shot-hero.png","src":"elevenlabs.io","hsize":60,"kick":"The shift",
     "headline":'Any voice can now be <em>faked</em>',
     "sub":"From a few seconds of audio, AI can clone a voice well enough to fool your own family."},
    {"num":"02","img":"shot-2.png","src":"elevenlabs.io","hsize":58,"kick":"What it is",
     "headline":'Type text, get a <em>voice</em>',
     "sub":"ElevenLabs turns writing into studio-quality speech, in almost any voice and language, in seconds."},
    {"num":"03","center":True,"hsize":62,"kick":"The upside",
     "headline":'A superpower for <em>creators</em>',
     "body":"Dub a video into 30 languages. Narrate a book. Give a product a voice. Work that needed a studio now needs a sentence."},
    {"num":"04","img":"hero.png","src":"elevenlabs.io","hsize":56,"kick":"The other side",
     "headline":'And a weapon for <em>scammers</em>',
     "sub":"The same tool clones a boss or a parent for a fake emergency call. The threat and the product are identical."},
    {"num":"05","center":True,"hsize":60,"kick":"What it means for you",
     "headline":'Stop trusting a voice <em>alone</em>',
     "body":"A familiar voice is no longer proof of who is calling. Agree on a code word with family. Verify any money request another way."},
    {"num":"06","center":True,"hsize":58,"kick":"The honest take",
     "headline":'This is <em>not</em> going back',
     "body":"The tech is out and improving fast. The people who stay safe will treat audio like email: useful, powerful, and never trusted on its own."},
    {"num":"07","cta":True,"hsize":68},
]

def build(s):
    if s.get("cta"):
        main = ('<div class="center"><div class="kick">The takeaway</div>'
                '<div class="headline" style="font-size:66px">Trust your eyes, not your <em>ears.</em></div>'
                '<div class="line"></div>'
                '<div class="body">The one AI shift that matters, explained in plain English, every day.</div></div>')
        bottom = '<div class="pill">follow me for daily AI <em>breakdowns.</em></div>'
    elif s.get("center"):
        main = CEN.format(kick=s["kick"], hsize=s["hsize"], headline=s["headline"], body=s["body"])
        bottom = '<div></div><div class="swipe">SWIPE &rarr;</div>'
    else:
        main = WIN.format(kick=s["kick"], hsize=s["hsize"], headline=s["headline"], sub=s["sub"], src=s["src"], img=s["img"])
        bottom = '<div></div><div class="swipe">SWIPE &rarr;</div>'
    return PAGE.format(accent=ACCENT, kick=KICK, num=s["num"], main=main, bottom=bottom)

outdir = os.path.join(BASE, "carousel-routine", "temp", OUTDIR_NAME)
os.makedirs(outdir, exist_ok=True)
for f in os.listdir(outdir):
    if f.startswith("slide-") and f.endswith(".html"): os.remove(os.path.join(outdir, f))
for s in S:
    open(os.path.join(outdir, f'slide-{s["num"]}.html'), "w").write(build(s))
print(f"wrote {len(S)} brand-story slides -> {outdir}")
