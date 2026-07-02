#!/usr/bin/env python3
"""Build carousel slides + infographic JSON from today's linkedin_posts file."""
import datetime
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
DATE = datetime.date.today().isoformat()
DATE_COMPACT = DATE.replace("-", "")

POSTS_PATH = os.path.join(BASE, f"linkedin_posts_{DATE_COMPACT}.txt")
if not os.path.exists(POSTS_PATH):
    POSTS_PATH = os.path.join(BASE, "linkedin_posts_today.txt")

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


def build_slide(slide, accent, kicker):
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
    bottom = (
        '<div class="pill">follow @founderswing for daily <em>frameworks.</em></div>'
        if slide.get("cta")
        else '<div></div><div class="swipe">SWIPE &rarr;</div>'
    )
    return PAGE.format(
        accent=accent,
        kicker=kicker,
        num=num,
        top=slide.get("top", 270),
        hsize=slide.get("hsize", 68),
        inner=inner,
        bottom=bottom,
    )


def headline_with_emphasis(text):
    words = text.split()
    if len(words) <= 3:
        return f'{text} <em>now</em>'
    mid = len(words) // 2
    return " ".join(words[:mid]) + f' <em>{" ".join(words[mid:])}</em>'


def parse_carousel_slides(content):
    m = re.search(
        r"3\. CAROUSEL\s*=+\s*(.*?)\s*=+\s*4\. INFOGRAPHIC",
        content,
        re.DOTALL,
    )
    if not m:
        raise SystemExit("Could not find carousel section in posts file")
    block = m.group(1)
    slides = []
    for i in range(1, 8):
        sm = re.search(rf"Slide {i}(?: \(Hook\))?:\s*\n(.*?)(?=\nSlide |\nCAROUSEL CAPTION:|\Z)", block, re.DOTALL)
        if sm:
            slides.append(sm.group(1).strip())
    if len(slides) < 7:
        raise SystemExit(f"Expected 7 carousel slides, found {len(slides)}")
    return slides


def write_carousel(slides):
    outdir = os.path.join(BASE, "carousel-routine", "temp", "carousel-branded")
    os.makedirs(outdir, exist_ok=True)
    accent = "#D9785B"
    kicker = "Founders Wing / AI access"
    specs = [
        {"num": "01", "hsize": 72, "top": 300, "eyebrow": "Curiosity gap",
         "headline": headline_with_emphasis(slides[0])},
        {"num": "02", "eyebrow": "What happened", "headline": headline_with_emphasis(slides[1][:60]),
         "body": slides[1]},
        {"num": "03", "stat": "90m", "top": 230, "headline": headline_with_emphasis(slides[2][:40]),
         "body": slides[2]},
        {"num": "04", "eyebrow": "The lockout", "headline": headline_with_emphasis(slides[3][:50]),
         "body": slides[3]},
        {"num": "05", "eyebrow": "The lesson", "headline": headline_with_emphasis(slides[4][:50]),
         "body": slides[4]},
        {"num": "06", "eyebrow": "Your move", "headline": headline_with_emphasis(slides[5][:50]),
         "body": slides[5]},
        {"num": "07", "hsize": 64, "top": 300, "cta": True,
         "headline": headline_with_emphasis(slides[6][:50]),
         "body": slides[6]},
    ]
    for spec in specs:
        path = os.path.join(outdir, f'slide-{spec["num"]}.html')
        with open(path, "w") as f:
            f.write(build_slide(spec, accent, kicker))
    print(f"Wrote 7 carousel slides -> {outdir}")


def write_infographic_json():
    import json

    data = {
        "title_main": "AI-heavy companies",
        "title_span": "grew headcount",
        "subtitle": "Heavy AI adopters expanded teams while most assumed AI would shrink them",
        "badge": "📊 Future of work",
        "date_label": "July 2026 Report",
        "takeaway_num": "10.2%",
        "takeaway_text": "Headcount rose at the heaviest AI adopters; entry-level roles grew 12%",
        "source": "Source: workplace AI adoption reports | @founderswing",
        "bars": [
            {"label": "Headcount growth (heavy AI adopters)", "value": "10.2%", "color": "#5E6AD2"},
            {"label": "Entry-level role growth", "value": "12%", "color": "#D9785B"},
            {"label": "Workers using AI at work", "value": "80%", "color": "#E8A33D"},
            {"label": "Using AI on real revenue work", "value": "15%", "color": "#111111"},
        ],
    }
    path = os.path.join(BASE, "infographic_data.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Wrote {path}")


def main():
    with open(POSTS_PATH) as f:
        content = f.read()
    slides = parse_carousel_slides(content)
    write_carousel(slides)
    write_infographic_json()
    os.system(f"cd {BASE} && python3 generate_infographic_today.py")
    print("Asset build complete.")


if __name__ == "__main__":
    main()
