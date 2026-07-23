#!/usr/bin/env python3
"""
Build OpenXcode assets from openxcode_batch_*.json:
  - 10 infographic PNGs (openxcode-images/DATE/day-NN.png)
  - 10 carousels (HTML → PNG → PDF via carousel-routine)
"""
import datetime
import glob
import json
import os
import re
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

ACCENT = "#1E40AF"
COLORS = ["#1E40AF", "#2563EB", "#3B82F6", "#0F766E", "#111111"]

files = sorted(glob.glob("openxcode_batch_*.json"))
if not files:
    sys.exit("No openxcode_batch_*.json — run generate_openxcode_batch.py first")
BATCH = files[-1]
data = json.load(open(BATCH))
posts = data["posts"]
date_compact = datetime.date.today().isoformat().replace("-", "")
img_dir = os.path.join(BASE, "openxcode-images", date_compact)
os.makedirs(img_dir, exist_ok=True)

# --- Infographic HTML (reuse automation template placeholders) ---
template_path = os.path.join(BASE, "linkedin-infographic-template.html")
with open(template_path) as f:
    INFO_TMPL = f.read()


def render_infographic(spec, out_html):
    bar_rows = []
    for bar in spec.get("bars", [])[:4]:
        width = bar.get("width_pct", "70%")
        if not str(width).endswith("%"):
            width = f"{width}%"
        color = bar.get("color", ACCENT)
        bar_rows.append(
            f"""    <div class="bar-row">
      <div class="bar-info">
        <span class="bar-label">{bar.get('label','')}</span>
        <span class="bar-value">{bar.get('value','')}</span>
      </div>
      <div class="bar-track">
        <div class="bar-fill" style="width: {width}; background-color: {color};"></div>
      </div>
    </div>"""
        )
    html = INFO_TMPL
    html = html.replace("{{BADGE}}", spec.get("badge", "OpenXcode"))
    html = html.replace("{{DATE_LABEL}}", spec.get("date_label", datetime.date.today().strftime("%B %Y")))
    html = html.replace("{{TITLE_MAIN}}", spec.get("title_main", "Build better"))
    html = html.replace("{{TITLE_SPAN}}", spec.get("title_span", "software"))
    html = html.replace("{{SUBTITLE}}", spec.get("subtitle", ""))
    html = html.replace("{{BAR_ROWS}}", "\n".join(bar_rows))
    html = html.replace("{{TAKEAWAY_NUM}}", str(spec.get("takeaway_num", "")))
    html = html.replace("{{TAKEAWAY_TEXT}}", spec.get("takeaway_text", ""))
    html = html.replace("{{SOURCE}}", spec.get("source", "OpenXcode · openxcode.com"))
    # Tint accent in template blues toward OpenXcode blue where hardcoded #5E6AD2
    html = html.replace("#5E6AD2", ACCENT)
    with open(out_html, "w") as f:
        f.write(html)


# Carousel slide template (typography-only, OpenXcode branded)
CAROUSEL_PAGE = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/>
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
.content{{position:absolute;top:240px;left:70px;right:70px;bottom:150px;z-index:5}}
.kick{{font-size:18px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:{accent};margin-bottom:22px}}
.headline{{font-size:{hsize}px;font-weight:900;letter-spacing:-2.5px;line-height:1.08;max-width:920px}}
.headline em{{font-family:'Instrument Serif',serif;font-style:italic;color:{accent};font-weight:400;letter-spacing:0;padding-left:4px}}
.body{{font-size:28px;font-weight:500;color:#333;line-height:1.42;margin-top:28px;max-width:860px}}
.line{{width:64px;height:5px;background:{accent};margin-top:32px}}
.bottom{{position:absolute;bottom:62px;left:70px;right:70px;display:flex;justify-content:space-between;align-items:center;z-index:5}}
.swipe{{font-size:14px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:#111}}
.pill{{background:#111;color:#fff;padding:20px 40px;border-radius:50px;font-size:22px;font-weight:800}}
.pill em{{font-family:'Instrument Serif',serif;font-style:italic;color:{accent};font-weight:400;margin-left:6px}}
</style></head><body>
<div class="header"><div class="hleft"><span class="dot"></span>OpenXcode</div>
<div class="hright"><div class="fw">openxcode.com</div><div class="badge">{num}</div></div></div>
{main}
<div class="bottom">{bottom}</div>
</body></html>"""


def build_slide_html(s, num):
    if s.get("cta"):
        main = (
            f'<div class="content"><div class="headline" style="font-size:{s.get("hsize",70)}px">'
            f'{s.get("headline","")}</div><div class="line"></div>'
            f'<div class="body">{s.get("body","")}</div></div>'
        )
        bottom = '<div class="pill">Comment <em>BUILD</em> to start.</div>'
    else:
        main = (
            f'<div class="content"><div class="kick">{s.get("kick","")}</div>'
            f'<div class="headline" style="font-size:{s.get("hsize",56)}px">{s.get("headline","")}</div>'
            f'<div class="body">{s.get("body","")}</div></div>'
        )
        bottom = '<div></div><div class="swipe">SWIPE &rarr;</div>'
    return CAROUSEL_PAGE.format(
        accent=ACCENT,
        num=f"{num:02d}",
        hsize=s.get("hsize", 56),
        main=main,
        bottom=bottom,
    )


# Build all HTML first
manifest_images = {"date": date_compact, "images": []}
carousel_dirs = []

for i, day in enumerate(posts, 1):
    # Image
    spec = dict(day.get("image") or {})
    spec.setdefault("date_label", datetime.date.today().strftime("%B %Y"))
    spec.setdefault("source", "OpenXcode · openxcode.com")
    # ensure bars colors
    for bi, bar in enumerate(spec.get("bars") or []):
        bar.setdefault("color", COLORS[bi % len(COLORS)])
        bar.setdefault("width_pct", f"{85 - bi * 15}%")
    html_path = os.path.join(img_dir, f"day-{i:02d}.html")
    png_path = os.path.join(img_dir, f"day-{i:02d}.png")
    render_infographic(spec, html_path)
    manifest_images["images"].append({"id": i, "html": html_path, "png": png_path})
    print(f"Image HTML {i}/{len(posts)} -> {html_path}")

    # Carousel slides
    car_name = f"openxcode-day-{i:02d}"
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

# Render carousels — use batch date folder for output organization
# render.js uses DATE for output path; use each post's date when available
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

# Verify
missing = []
for i, day in enumerate(posts, 1):
    png = os.path.join(img_dir, f"day-{i:02d}.png")
    if not os.path.exists(png):
        missing.append(png)
    day_date = day.get("date") or datetime.date.today().isoformat()
    car_name = f"openxcode-day-{i:02d}"
    pdf_dir = os.path.join(BASE, "carousel-routine", "output", day_date, car_name)
    pdfs = glob.glob(os.path.join(pdf_dir, "*.pdf")) if os.path.isdir(pdf_dir) else []
    if not pdfs:
        missing.append(pdf_dir + "/*.pdf")
    day["_image_png"] = png
    day["_carousel_pdf"] = pdfs[0] if pdfs else None

if missing:
    sys.exit("Missing assets:\n" + "\n".join(missing))

# Persist asset paths back into batch file
data["assetDir"] = img_dir
json.dump(data, open(BATCH, "w"), indent=2)
print(f"Done. Assets ready for {len(posts)} days. Updated {BATCH}")
