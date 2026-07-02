#!/usr/bin/env python3
"""Build performance carousel slides + infographic PNG from today's posts file."""
import datetime
import glob
import os
import re
import subprocess

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
.body{{font-size:29px;font-weight:500;color:#333;line-height:1.42;margin-top:30px;max-width:900px}}
.line{{width:64px;height:5px;background:{accent};margin-top:34px}}
.bottom{{position:absolute;bottom:68px;left:70px;right:70px;display:flex;justify-content:space-between;align-items:center;z-index:5}}
.swipe{{font-size:14px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:#111}}
.pill{{background:#111;color:#fff;padding:20px 38px;border-radius:50px;font-size:21px;font-weight:800}}
.pill em{{font-family:'Instrument Serif',serif;font-style:italic;color:{accent};font-weight:400;margin-left:6px}}
</style></head><body>
<div class="header"><div class="hleft"><span class="dot"></span></div>
<div class="hright"><div class="badge">{num}</div></div></div>
<div class="content">{inner}</div>
<div class="bottom">{bottom}</div>
</body></html>"""


def resolve_posts_file():
    date_compact = datetime.date.today().isoformat().replace("-", "")
    path = os.path.join(BASE, f"linkedin_posts_{date_compact}.txt")
    if os.path.exists(path):
        return path
    candidates = sorted(
        f for f in os.listdir(BASE)
        if f.startswith("linkedin_posts_") and f.endswith(".txt") and f != "linkedin_posts_today.txt"
    )
    if not candidates:
        raise SystemExit("No linkedin_posts_*.txt file found")
    return os.path.join(BASE, candidates[-1])


def posts_date_from_path(path):
    m = re.search(r"linkedin_posts_(\d{8})\.txt", os.path.basename(path))
    if not m:
        return datetime.date.today().isoformat(), datetime.date.today().isoformat().replace("-", "")
    compact = m.group(1)
    return f"{compact[:4]}-{compact[4:6]}-{compact[6:8]}", compact


def build_slide(slide, accent, kicker):
    inner = ""
    if slide.get("eyebrow"):
        inner += f'<div class="kick">{slide["eyebrow"]}</div>'
    inner += f'<div class="headline">{slide["headline"]}</div>'
    if slide.get("cta"):
        inner += '<div class="line"></div>'
    if slide.get("body"):
        inner += f'<div class="body">{slide["body"]}</div>'
    bottom = (
        '<div class="pill">Follow me</div>'
        if slide.get("cta")
        else '<div></div><div class="swipe">SWIPE &rarr;</div>'
    )
    return PAGE.format(
        accent=accent,
        kicker=kicker,
        num=slide["num"],
        top=slide.get("top", 270),
        hsize=slide.get("hsize", 68),
        inner=inner,
        bottom=bottom,
    )


def write_perf_carousel_slides():
    accent = "#E16259"
    kicker = ""
    slides = [
        {
            "num": "01",
            "hsize": 72,
            "top": 300,
            "eyebrow": "Founder story",
            "headline": 'One person did the work of a <em>whole team</em>',
            "body": "And almost nobody noticed until the results showed up.",
        },
        {
            "num": "02",
            "eyebrow": "No fanfare",
            "headline": "No new headcount. <em>No announcement.</em>",
            "body": "Just one operator quietly rewiring how the work got done.",
        },
        {
            "num": "03",
            "eyebrow": "The wiring",
            "headline": "AI took the <em>boring</em> parts",
            "body": "The repetitive tasks got automated first. That freed hours every week.",
        },
        {
            "num": "04",
            "eyebrow": "The payoff",
            "headline": "Time went to work that <em>moves</em> things",
            "body": "Decisions, relationships, and output that actually show up in the numbers.",
        },
        {
            "num": "05",
            "eyebrow": "The fear",
            "headline": "Most people brace for <em>replacement</em>",
            "body": "The headline story is AI taking jobs. That is not the only story playing out.",
        },
        {
            "num": "06",
            "eyebrow": "The quiet story",
            "headline": "A few people became <em>impossible</em> to replace",
            "body": "They did not study AI harder. They pointed it at real work and kept going.",
        },
        {
            "num": "07",
            "hsize": 64,
            "top": 300,
            "cta": True,
            "headline": "Which part of your week could you <em>hand off?</em>",
            "body": "Save this for the task you keep doing manually out of habit.",
        },
    ]
    outdir = os.path.join(BASE, "carousel-routine", "temp", "carousel-performance")
    os.makedirs(outdir, exist_ok=True)
    for fn in os.listdir(outdir):
        if fn.startswith("slide-") and fn.endswith(".html"):
            os.remove(os.path.join(outdir, fn))
    for slide in slides:
        path = os.path.join(outdir, f'slide-{slide["num"]}.html')
        with open(path, "w") as f:
            f.write(build_slide(slide, accent, kicker))
    print(f"Wrote 7 performance carousel slides -> {outdir}")


def render_carousel(date_iso):
    cr = os.path.join(BASE, "carousel-routine")
    for cmd in (
        f"node render.js {date_iso} carousel-performance",
        f"node render-pdf.js {date_iso} carousel-performance",
    ):
        print(f"Running: {cmd}")
        subprocess.run(cmd, shell=True, cwd=cr, check=True)


def capture_perf_infographic(date_compact):
    script = os.path.join(BASE, "cap_performance_infographic.cjs")
    subprocess.run(["node", script, date_compact], cwd=BASE, check=True)


def main():
    posts_path = resolve_posts_file()
    date_iso, date_compact = posts_date_from_path(posts_path)
    print(f"Building performance assets for {date_iso} from {os.path.basename(posts_path)}")
    write_perf_carousel_slides()
    render_carousel(date_iso)
    capture_perf_infographic(date_compact)
    pdf_glob = os.path.join(
        BASE, "carousel-routine", "output", date_iso, "carousel-performance", "*.pdf"
    )
    png_path = os.path.join(BASE, f"linkedin-performance-infographic-{date_compact}.png")
    pdfs = glob.glob(pdf_glob)
    print(f"Performance PDF: {pdfs[0] if pdfs else 'missing'}")
    print(f"Performance PNG: {png_path} ({'ok' if os.path.exists(png_path) else 'missing'})")


if __name__ == "__main__":
    main()
