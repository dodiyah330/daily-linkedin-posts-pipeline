#!/usr/bin/env python3
"""
Build carousel PDFs from us_personal_carousel_week_*.json (carousel-only batches).
Supports 3-4 slides per carousel.
"""
import datetime
import glob
import html as html_lib
import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

ACCENT = "#5E6AD2"
PORTFOLIO = "hitesh-dodiya.netlify.app"

files = sorted(glob.glob("us_personal_carousel_week_*.json"))
if os.environ.get("US_PERSONAL_BATCH"):
    BATCH = os.environ["US_PERSONAL_BATCH"]
    if not os.path.exists(BATCH):
        sys.exit(f"US_PERSONAL_BATCH not found: {BATCH}")
elif not files:
    sys.exit("No us_personal_carousel_week_*.json found")
else:
    BATCH = files[-1]

data = json.load(open(BATCH))
posts = data["posts"]
date_compact = data.get("start", datetime.date.today().isoformat()).replace("-", "")

CAROUSEL_PAGE = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080"/>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800;900&family=Instrument+Serif:ital@1&display=swap" rel="stylesheet"/>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{width:1080px;height:1080px;overflow:hidden;background:#F7F7FB;color:#111;font-family:'Plus Jakarta Sans',sans-serif;position:relative}}
.header{{position:absolute;top:48px;left:64px;right:64px;display:flex;justify-content:space-between;align-items:center;z-index:10}}
.hleft{{display:flex;align-items:center;gap:12px;font-size:14px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:#111}}
.dot{{width:14px;height:14px;border-radius:50%;background:{accent}}}
.hright{{display:flex;align-items:center;gap:15px}}
.meta{{font-family:'Instrument Serif',serif;font-style:italic;font-size:22px;color:#999}}
.badge{{width:46px;height:46px;background:{accent};border-radius:50%;display:flex;justify-content:center;align-items:center;color:#fff;font-weight:800;font-size:17px}}
.content{{position:absolute;top:150px;left:64px;right:64px;bottom:120px;z-index:5;display:flex;flex-direction:column;justify-content:flex-start}}
.kick{{font-size:16px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:{accent};margin-bottom:12px}}
.headline{{font-size:{hsize}px;font-weight:900;letter-spacing:-2px;line-height:1.08;max-width:940px;flex-shrink:0}}
.headline em{{font-family:'Instrument Serif',serif;font-style:italic;color:{accent};font-weight:400;letter-spacing:0;padding-left:4px}}
.body{{font-size:22px;font-weight:500;color:#333;line-height:1.35;margin-top:14px;max-width:900px;flex-shrink:0}}
.bullets{{margin-top:18px;display:flex;flex-direction:column;gap:12px;flex:1;justify-content:space-evenly}}
.bullet{{display:flex;gap:14px;align-items:flex-start;background:#fff;border:1px solid #E6E5EF;border-radius:12px;padding:16px 18px;min-height:72px}}
.bnum{{width:28px;height:28px;border-radius:8px;background:{accent};color:#fff;font-size:14px;font-weight:800;display:flex;align-items:center;justify-content:center;flex-shrink:0}}
.btext{{font-size:22px;font-weight:600;color:#1a1a1a;line-height:1.3}}
.line{{width:64px;height:5px;background:{accent};margin-top:20px}}
.bottom{{position:absolute;bottom:48px;left:64px;right:64px;display:flex;justify-content:space-between;align-items:center;z-index:5}}
.swipe{{font-size:14px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:#111}}
.site{{font-size:14px;font-weight:700;color:#666}}
.pill{{background:#111;color:#fff;padding:18px 36px;border-radius:50px;font-size:20px;font-weight:800}}
.pill em{{font-family:'Instrument Serif',serif;font-style:italic;color:{accent};font-weight:400;margin-left:6px}}
</style></head><body>
<div class="header"><div class="hleft"><span class="dot"></span>Hitesh Dodiya</div>
<div class="hright"><div class="meta">{site}</div><div class="badge">{num}</div></div></div>
{main}
<div class="bottom">{bottom}</div>
</body></html>"""


def esc(s):
    return html_lib.escape(str(s or ""))


def bullets_html(bullets):
    items = []
    for i, b in enumerate((bullets or [])[:4], 1):
        items.append(
            f'<div class="bullet"><div class="bnum">{i}</div>'
            f'<div class="btext">{esc(b)}</div></div>'
        )
    return f'<div class="bullets">{"".join(items)}</div>' if items else ""


def build_slide_html(s, num):
    bullets = s.get("bullets") or []
    hsize = s.get("hsize") or (58 if s.get("cta") else 48)
    headline = str(s.get("headline", ""))
    body = esc(s.get("body", ""))
    if s.get("cta"):
        main = (
            f'<div class="content"><div class="headline" style="font-size:{hsize}px">'
            f'{headline}</div><div class="line"></div>'
            f'<div class="body">{body}</div>{bullets_html(bullets)}</div>'
        )
        bottom = (
            f'<div class="site">{PORTFOLIO}</div>'
            f'<div class="pill">Comment <em>AUTO</em> to start.</div>'
        )
    else:
        main = (
            f'<div class="content"><div class="kick">{esc(s.get("kick",""))}</div>'
            f'<div class="headline" style="font-size:{hsize}px">{headline}</div>'
            f'<div class="body">{body}</div>{bullets_html(bullets)}</div>'
        )
        bottom = f'<div class="site">{PORTFOLIO}</div><div class="swipe">SWIPE &rarr;</div>'
    return CAROUSEL_PAGE.format(
        accent=ACCENT,
        site=PORTFOLIO,
        num=f"{num:02d}",
        hsize=hsize,
        main=main,
        bottom=bottom,
    )


carousel_dirs = []
for i, day in enumerate(posts, 1):
    slides = (day.get("carousel") or {}).get("slides") or []
    if len(slides) < 3 or len(slides) > 4:
        sys.exit(f"Day {i}: carousel must have 3-4 slides, got {len(slides)}")
    if not slides[-1].get("cta"):
        sys.exit(f"Day {i}: last slide must be CTA")

    car_name = f"us-personal-day-{i:02d}"
    temp_dir = os.path.join(BASE, "carousel-routine", "temp", car_name)
    os.makedirs(temp_dir, exist_ok=True)
    for f in os.listdir(temp_dir):
        if f.startswith("slide-") and f.endswith(".html"):
            os.remove(os.path.join(temp_dir, f))
    for si, s in enumerate(slides, 1):
        open(os.path.join(temp_dir, f"slide-{si:02d}.html"), "w").write(build_slide_html(s, si))
    carousel_dirs.append(car_name)
    print(f"Carousel HTML {i}/{len(posts)} -> {temp_dir} ({len(slides)} slides)")

print("Rendering carousels (PNG + PDF)...")
for i, (day, car_name) in enumerate(zip(posts, carousel_dirs), 1):
    day_date = day.get("date") or datetime.date.today().isoformat()
    print(f"  Carousel {i}/{len(posts)} {car_name} @ {day_date}")
    subprocess.run(
        ["node", "render.js", day_date, car_name],
        cwd=os.path.join(BASE, "carousel-routine"),
        check=True,
        env={**os.environ, "PUPPETEER_EXECUTABLE_PATH": "/usr/bin/google-chrome"},
    )
    subprocess.run(
        ["node", "render-pdf.js", day_date, car_name],
        cwd=os.path.join(BASE, "carousel-routine"),
        check=True,
    )

missing = []
for i, day in enumerate(posts, 1):
    day_date = day.get("date") or datetime.date.today().isoformat()
    car_name = f"us-personal-day-{i:02d}"
    pdf_dir = os.path.join(BASE, "carousel-routine", "output", day_date, car_name)
    pdfs = glob.glob(os.path.join(pdf_dir, "*.pdf")) if os.path.isdir(pdf_dir) else []
    if not pdfs:
        missing.append(pdf_dir + "/*.pdf")
    day["_carousel_pdf"] = pdfs[0] if pdfs else None

if missing:
    sys.exit("Missing assets:\n" + "\n".join(missing))

data["assetBatch"] = date_compact
json.dump(data, open(BATCH, "w"), indent=2)
print(f"Done. {len(posts)} carousel PDFs ready. Updated {BATCH}")
