#!/usr/bin/env python3
"""
Build personal US assets from us_personal_batch_*.json:
  - denser infographic PNGs (4 bars + checklist bullets, less empty space)
  - content-rich carousels (body + bullet list per slide)
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
COLORS = ["#5E6AD2", "#2563EB", "#059669", "#D9785B", "#111111"]
SOURCE = "Hitesh Dodiya · hitesh-dodiya.netlify.app"
BRAND = "AI Automation"
PORTFOLIO = "hitesh-dodiya.netlify.app"

files = sorted(glob.glob("us_personal_batch_*.json"))
if os.environ.get("US_PERSONAL_BATCH"):
    BATCH = os.environ["US_PERSONAL_BATCH"]
    if not os.path.exists(BATCH):
        sys.exit(f"US_PERSONAL_BATCH not found: {BATCH}")
elif not files:
    sys.exit("No us_personal_batch_*.json — run generate_us_personal_batch.py first")
else:
    BATCH = files[-1]

data = json.load(open(BATCH))
posts = data["posts"]
date_compact = datetime.date.today().isoformat().replace("-", "")
img_dir = os.path.join(BASE, "us-personal-images", date_compact)
os.makedirs(img_dir, exist_ok=True)

INFOGRAPHIC_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>US Personal Infographic</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800;900&family=Instrument+Serif:ital@1&display=swap');
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    background: #F8F7F3;
    width: 1080px;
    height: 1080px;
    overflow: hidden;
  }}
  .card {{
    width: 1080px;
    height: 1080px;
    background: #F8F7F3;
    padding: 48px 56px 40px;
    display: flex;
    flex-direction: column;
    gap: 18px;
  }}
  .top-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-shrink: 0;
  }}
  .badge {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: {accent};
    color: #fff;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    padding: 7px 16px;
    border-radius: 4px;
  }}
  .date-label {{
    font-size: 15px;
    color: #6B6B6B;
    font-style: italic;
    font-family: 'Instrument Serif', Georgia, serif;
  }}
  .header-block {{ flex-shrink: 0; }}
  .title {{
    font-size: 54px;
    font-weight: 900;
    color: #111;
    line-height: 1.08;
    letter-spacing: -1.8px;
    margin-bottom: 10px;
  }}
  .title span {{
    color: {accent};
    font-style: italic;
    font-family: 'Instrument Serif', Georgia, serif;
    font-weight: 400;
  }}
  .subtitle {{
    font-size: 18px;
    color: #444;
    line-height: 1.35;
    max-width: 960px;
  }}
  .content-area {{
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    gap: 14px;
    min-height: 0;
  }}
  .bars {{
    display: flex;
    flex-direction: column;
    gap: 14px;
  }}
  .bar-row {{ display: flex; flex-direction: column; gap: 6px; }}
  .bar-info {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 17px;
    font-weight: 700;
    color: #111;
  }}
  .bar-value {{ font-size: 20px; font-weight: 900; }}
  .bar-track {{
    width: 100%;
    height: 22px;
    background: #E8E7E3;
    border-radius: 6px;
    overflow: hidden;
  }}
  .bar-fill {{ height: 100%; border-radius: 6px; }}
  .checklist {{
    background: #fff;
    border: 1px solid #E4E2DC;
    border-radius: 14px;
    padding: 18px 22px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px 20px;
  }}
  .check-item {{
    display: flex;
    align-items: flex-start;
    gap: 10px;
    font-size: 16px;
    font-weight: 600;
    color: #222;
    line-height: 1.3;
  }}
  .check {{
    width: 22px;
    height: 22px;
    border-radius: 6px;
    background: {accent};
    color: #fff;
    font-size: 13px;
    font-weight: 800;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    margin-top: 1px;
  }}
  .takeaway-box {{
    background: #111;
    color: #fff;
    border-radius: 14px;
    padding: 18px 24px;
    display: flex;
    align-items: baseline;
    gap: 14px;
    flex-shrink: 0;
  }}
  .takeaway-num {{
    font-family: 'Instrument Serif', Georgia, serif;
    font-style: italic;
    font-size: 36px;
    color: {accent};
    white-space: nowrap;
  }}
  .takeaway-text {{
    font-size: 20px;
    font-weight: 600;
    line-height: 1.3;
  }}
  .footer {{
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    border-top: 1px solid #E8E7E3;
    padding-top: 16px;
    flex-shrink: 0;
  }}
  .source {{ font-size: 12px; color: #9B8E7E; font-family: monospace; }}
  .brand {{ font-size: 16px; font-weight: 800; color: {accent}; }}
</style>
</head>
<body>
<div class="card">
  <div class="top-bar">
    <div class="badge">{badge}</div>
    <div class="date-label">{date_label}</div>
  </div>
  <div class="header-block">
    <div class="title">{title_main} <span>{title_span}</span></div>
    <div class="subtitle">{subtitle}</div>
  </div>
  <div class="content-area">
    <div class="bars">{bar_rows}</div>
    <div class="checklist">{bullet_rows}</div>
  </div>
  <div class="takeaway-box">
    <div class="takeaway-num">{takeaway_num}</div>
    <div class="takeaway-text">{takeaway_text}</div>
  </div>
  <div class="footer">
    <div class="source">{source}</div>
    <div class="brand">Follow for automations</div>
  </div>
</div>
</body>
</html>"""


def esc(s):
    return html_lib.escape(str(s or ""))


def render_infographic(spec, out_html):
    bar_rows = []
    for bar in (spec.get("bars") or [])[:4]:
        width = bar.get("width_pct", "70%")
        if not str(width).endswith("%"):
            width = f"{width}%"
        color = bar.get("color", ACCENT)
        bar_rows.append(
            f"""<div class="bar-row">
      <div class="bar-info">
        <span class="bar-label">{esc(bar.get('label',''))}</span>
        <span class="bar-value">{esc(bar.get('value',''))}</span>
      </div>
      <div class="bar-track">
        <div class="bar-fill" style="width: {width}; background-color: {color};"></div>
      </div>
    </div>"""
        )
    bullets = (spec.get("bullets") or [])[:4]
    while len(bullets) < 4:
        bullets.append("Map trigger → enrich → Slack brief")
    bullet_rows = []
    for i, b in enumerate(bullets, 1):
        bullet_rows.append(
            f'<div class="check-item"><div class="check">{i}</div>'
            f'<div>{esc(b)}</div></div>'
        )
    html = INFOGRAPHIC_PAGE.format(
        accent=ACCENT,
        badge=esc(spec.get("badge", BRAND)),
        date_label=esc(spec.get("date_label", datetime.date.today().strftime("%B %Y"))),
        title_main=esc(spec.get("title_main", "Automate the")),
        title_span=esc(spec.get("title_span", "busywork")),
        subtitle=esc(spec.get("subtitle", "")),
        bar_rows="\n".join(bar_rows),
        bullet_rows="\n".join(bullet_rows),
        takeaway_num=esc(spec.get("takeaway_num", "")),
        takeaway_text=esc(spec.get("takeaway_text", "")),
        source=esc(spec.get("source", SOURCE)),
    )
    with open(out_html, "w") as f:
        f.write(html)


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


def bullets_html(bullets, accent_unused=None):
    items = []
    for i, b in enumerate((bullets or [])[:4], 1):
        items.append(
            f'<div class="bullet"><div class="bnum">{i}</div>'
            f'<div class="btext">{esc(b)}</div></div>'
        )
    if not items:
        return ""
    return f'<div class="bullets">{"".join(items)}</div>'


def build_slide_html(s, num):
    bullets = s.get("bullets") or []
    hsize = s.get("hsize") or (58 if s.get("cta") else 48)
    # Allow limited HTML in headline (em only)
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


manifest_images = {"date": date_compact, "images": []}
carousel_dirs = []

for i, day in enumerate(posts, 1):
    spec = dict(day.get("image") or {})
    spec.setdefault("date_label", datetime.date.today().strftime("%B %Y"))
    spec.setdefault("source", SOURCE)
    spec.setdefault("badge", BRAND)
    for bi, bar in enumerate(spec.get("bars") or []):
        bar.setdefault("color", COLORS[bi % len(COLORS)])
        bar.setdefault("width_pct", f"{90 - bi * 12}%")
    html_path = os.path.join(img_dir, f"day-{i:02d}.html")
    png_path = os.path.join(img_dir, f"day-{i:02d}.png")
    render_infographic(spec, html_path)
    manifest_images["images"].append({"id": i, "html": html_path, "png": png_path})
    print(f"Image HTML {i}/{len(posts)} -> {html_path}")

    car_name = f"us-personal-day-{i:02d}"
    temp_dir = os.path.join(BASE, "carousel-routine", "temp", car_name)
    os.makedirs(temp_dir, exist_ok=True)
    for f in os.listdir(temp_dir):
        if f.startswith("slide-") and f.endswith(".html"):
            os.remove(os.path.join(temp_dir, f))
    slides = (day.get("carousel") or {}).get("slides") or []
    for si, s in enumerate(slides[:6], 1):
        open(os.path.join(temp_dir, f"slide-{si:02d}.html"), "w").write(build_slide_html(s, si))
    carousel_dirs.append(car_name)
    print(f"Carousel HTML {i}/{len(posts)} -> {temp_dir} ({min(6,len(slides))} slides)")

manifest_path = os.path.join(img_dir, "manifest.json")
json.dump(manifest_images, open(manifest_path, "w"), indent=2)

print("Screenshotting image PNGs...")
subprocess.run(["node", os.path.join(BASE, "cap_automation_images.cjs"), manifest_path], check=True)

print("Rendering carousels (PNG + PDF)...")
for i, (day, car_name) in enumerate(zip(posts, carousel_dirs), 1):
    day_date = day.get("date") or datetime.date.today().isoformat()
    print(f"  Carousel {i}/{len(posts)} {car_name} @ {day_date}")
    subprocess.run(
        ["node", "render.js", day_date, car_name],
        cwd=os.path.join(BASE, "carousel-routine"),
        check=True,
    )
    subprocess.run(
        ["node", "render-pdf.js", day_date, car_name],
        cwd=os.path.join(BASE, "carousel-routine"),
        check=True,
    )

missing = []
for i, day in enumerate(posts, 1):
    png = os.path.join(img_dir, f"day-{i:02d}.png")
    if not os.path.exists(png):
        missing.append(png)
    day_date = day.get("date") or datetime.date.today().isoformat()
    car_name = f"us-personal-day-{i:02d}"
    pdf_dir = os.path.join(BASE, "carousel-routine", "output", day_date, car_name)
    pdfs = glob.glob(os.path.join(pdf_dir, "*.pdf")) if os.path.isdir(pdf_dir) else []
    if not pdfs:
        missing.append(pdf_dir + "/*.pdf")
    day["_image_png"] = png
    day["_carousel_pdf"] = pdfs[0] if pdfs else None

if missing:
    sys.exit("Missing assets:\n" + "\n".join(missing))

data["assetDir"] = img_dir
json.dump(data, open(BATCH, "w"), indent=2)
print(f"Done. Assets ready for {len(posts)} days. Updated {BATCH}")
