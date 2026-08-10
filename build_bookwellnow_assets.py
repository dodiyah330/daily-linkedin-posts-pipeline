#!/usr/bin/env python3
"""
Build BookWellNow assets from bookwellnow_batch_*.json:
  - denser infographic PNGs (4 bars + checklist)
  - denser carousels (body + bullets per slide)
Supports 4 posts/day: image_am, carousel_am, image_pm, carousel_pm
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

ACCENT = "#5700B4"
COLORS = ["#5700B4", "#7C3AED", "#C084FC", "#4C1D95", "#111111"]
SOURCE = "BookWellNow · bookwellnow.com"
SITE = "bookwellnow.com"

files = sorted(glob.glob("bookwellnow_batch_*.json"))
if os.environ.get("BOOKWELLNOW_BATCH"):
    BATCH = os.environ["BOOKWELLNOW_BATCH"]
    if not os.path.exists(BATCH):
        sys.exit(f"BOOKWELLNOW_BATCH not found: {BATCH}")
elif not files:
    sys.exit("No bookwellnow_batch_*.json — run generate_bookwellnow_batch.py first")
else:
    BATCH = files[-1]

data = json.load(open(BATCH))
posts = data["posts"]
date_compact = datetime.date.today().isoformat().replace("-", "")
img_dir = os.path.join(BASE, "bookwellnow-images", date_compact)
os.makedirs(img_dir, exist_ok=True)


def esc(s):
    return html_lib.escape(str(s or ""))


INFOGRAPHIC_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BookWellNow Infographic</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800;900&family=Instrument+Serif:ital@1&display=swap');
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Plus Jakarta Sans', sans-serif; background: #FAF8FF; width: 1080px; height: 1080px; overflow: hidden; }}
  .card {{ width: 1080px; height: 1080px; background: #FAF8FF; padding: 48px 56px 40px; display: flex; flex-direction: column; gap: 16px; }}
  .top-bar {{ display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; }}
  .badge {{ background: {accent}; color: #fff; font-size: 13px; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; padding: 7px 16px; border-radius: 4px; }}
  .date-label {{ font-size: 15px; color: #6B6B6B; font-style: italic; font-family: 'Instrument Serif', Georgia, serif; }}
  .title {{ font-size: 52px; font-weight: 900; color: #111; line-height: 1.08; letter-spacing: -1.6px; margin-bottom: 8px; }}
  .title span {{ color: {accent}; font-style: italic; font-family: 'Instrument Serif', Georgia, serif; font-weight: 400; }}
  .subtitle {{ font-size: 18px; color: #444; line-height: 1.35; max-width: 960px; }}
  .content-area {{ flex: 1; display: flex; flex-direction: column; justify-content: space-between; gap: 14px; min-height: 0; }}
  .bars {{ display: flex; flex-direction: column; gap: 12px; }}
  .bar-row {{ display: flex; flex-direction: column; gap: 6px; }}
  .bar-info {{ display: flex; justify-content: space-between; align-items: center; font-size: 17px; font-weight: 700; color: #111; }}
  .bar-value {{ font-size: 20px; font-weight: 900; }}
  .bar-track {{ width: 100%; height: 22px; background: #EDE7F6; border-radius: 6px; overflow: hidden; }}
  .bar-fill {{ height: 100%; border-radius: 6px; }}
  .checklist {{ background: #fff; border: 1px solid #E8E0F5; border-radius: 14px; padding: 16px 20px; display: grid; grid-template-columns: 1fr 1fr; gap: 12px 18px; }}
  .check-item {{ display: flex; align-items: flex-start; gap: 10px; font-size: 16px; font-weight: 600; color: #222; line-height: 1.3; }}
  .check {{ width: 22px; height: 22px; border-radius: 6px; background: {accent}; color: #fff; font-size: 13px; font-weight: 800; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }}
  .takeaway-box {{ background: #111; color: #fff; border-radius: 14px; padding: 16px 22px; display: flex; align-items: baseline; gap: 14px; flex-shrink: 0; }}
  .takeaway-num {{ font-family: 'Instrument Serif', Georgia, serif; font-style: italic; font-size: 34px; color: {accent}; white-space: nowrap; }}
  .takeaway-text {{ font-size: 19px; font-weight: 600; line-height: 1.3; }}
  .footer {{ display: flex; justify-content: space-between; align-items: flex-end; border-top: 1px solid #E8E0F5; padding-top: 14px; flex-shrink: 0; }}
  .source {{ font-size: 12px; color: #9B8E7E; font-family: monospace; }}
  .brand {{ font-size: 16px; font-weight: 800; color: {accent}; }}
</style>
</head>
<body>
<div class="card">
  <div class="top-bar"><div class="badge">{badge}</div><div class="date-label">{date_label}</div></div>
  <div><div class="title">{title_main} <span>{title_span}</span></div><div class="subtitle">{subtitle}</div></div>
  <div class="content-area">
    <div class="bars">{bar_rows}</div>
    <div class="checklist">{bullet_rows}</div>
  </div>
  <div class="takeaway-box"><div class="takeaway-num">{takeaway_num}</div><div class="takeaway-text">{takeaway_text}</div></div>
  <div class="footer"><div class="source">{source}</div><div class="brand">Follow BookWellNow</div></div>
</div>
</body>
</html>"""


def render_infographic(spec, out_html):
    bar_rows = []
    for bar in (spec.get("bars") or [])[:4]:
        width = bar.get("width_pct", "70%")
        if not str(width).endswith("%"):
            width = f"{width}%"
        color = bar.get("color", ACCENT)
        bar_rows.append(
            f"""<div class="bar-row"><div class="bar-info"><span class="bar-label">{esc(bar.get('label',''))}</span>
            <span class="bar-value">{esc(bar.get('value',''))}</span></div>
            <div class="bar-track"><div class="bar-fill" style="width:{width};background-color:{color};"></div></div></div>"""
        )
    bullets = (spec.get("bullets") or [])[:4]
    while len(bullets) < 4:
        bullets.append("Unlimited staff, services, bookings")
    bullet_rows = "".join(
        f'<div class="check-item"><div class="check">{i}</div><div>{esc(b)}</div></div>'
        for i, b in enumerate(bullets, 1)
    )
    html = INFOGRAPHIC_PAGE.format(
        accent=ACCENT,
        badge=esc(spec.get("badge", "BookWellNow")),
        date_label=esc(spec.get("date_label", datetime.date.today().strftime("%B %Y"))),
        title_main=esc(spec.get("title_main", "Take bookings")),
        title_span=esc(spec.get("title_span", "online")),
        subtitle=esc(spec.get("subtitle", "")),
        bar_rows="\n".join(bar_rows),
        bullet_rows=bullet_rows,
        takeaway_num=esc(spec.get("takeaway_num", "")),
        takeaway_text=esc(spec.get("takeaway_text", "")),
        source=esc(spec.get("source", SOURCE)),
    )
    with open(out_html, "w") as f:
        f.write(html)


CAROUSEL_PAGE = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080"/>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800;900&family=Instrument+Serif:ital@1&display=swap" rel="stylesheet"/>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{width:1080px;height:1080px;overflow:hidden;background:#FAF8FF;color:#111;font-family:'Plus Jakarta Sans',sans-serif;position:relative}}
.header{{position:absolute;top:48px;left:64px;right:64px;display:flex;justify-content:space-between;align-items:center;z-index:10}}
.hleft{{display:flex;align-items:center;gap:12px;font-size:14px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:#111}}
.dot{{width:14px;height:14px;border-radius:50%;background:{accent}}}
.hright{{display:flex;align-items:center;gap:15px}}
.meta{{font-family:'Instrument Serif',serif;font-style:italic;font-size:22px;color:#999}}
.badge{{width:46px;height:46px;background:{accent};border-radius:50%;display:flex;justify-content:center;align-items:center;color:#fff;font-weight:800;font-size:17px}}
.content{{position:absolute;top:150px;left:64px;right:64px;bottom:120px;z-index:5;display:flex;flex-direction:column}}
.kick{{font-size:16px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:{accent};margin-bottom:12px}}
.headline{{font-size:{hsize}px;font-weight:900;letter-spacing:-2px;line-height:1.08;max-width:940px;flex-shrink:0}}
.headline em{{font-family:'Instrument Serif',serif;font-style:italic;color:{accent};font-weight:400;letter-spacing:0;padding-left:4px}}
.body{{font-size:22px;font-weight:500;color:#333;line-height:1.35;margin-top:14px;max-width:900px;flex-shrink:0}}
.bullets{{margin-top:14px;display:flex;flex-direction:column;gap:8px;flex:0 0 auto;justify-content:flex-start}}
.bullet{{display:flex;gap:12px;align-items:center;background:#fff;border:1px solid #E8E0F5;border-radius:12px;padding:12px 16px;min-height:0}}
.bnum{{width:28px;height:28px;border-radius:8px;background:{accent};color:#fff;font-size:14px;font-weight:800;display:flex;align-items:center;justify-content:center;flex-shrink:0}}
.btext{{font-size:22px;font-weight:600;color:#1a1a1a;line-height:1.25}}
.line{{width:64px;height:5px;background:{accent};margin-top:20px}}
.bottom{{position:absolute;bottom:48px;left:64px;right:64px;display:flex;justify-content:space-between;align-items:center;z-index:5}}
.swipe{{font-size:14px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:#111}}
.site{{font-size:14px;font-weight:700;color:#666}}
.pill{{background:#111;color:#fff;padding:18px 36px;border-radius:50px;font-size:20px;font-weight:800}}
.pill em{{font-family:'Instrument Serif',serif;font-style:italic;color:{accent};font-weight:400;margin-left:6px}}
</style></head><body>
<div class="header"><div class="hleft"><span class="dot"></span>BookWellNow</div>
<div class="hright"><div class="meta">{site}</div><div class="badge">{num}</div></div></div>
{main}
<div class="bottom">{bottom}</div>
</body></html>"""


def bullets_html(bullets):
    items = []
    for i, b in enumerate((bullets or [])[:4], 1):
        items.append(f'<div class="bullet"><div class="bnum">{i}</div><div class="btext">{esc(b)}</div></div>')
    return f'<div class="bullets">{"".join(items)}</div>' if items else ""


def build_slide_html(s, num):
    bullets = s.get("bullets") or []
    hsize = s.get("hsize") or (58 if s.get("cta") else 48)
    headline = str(s.get("headline", ""))
    body = esc(s.get("body", ""))
    if s.get("cta"):
        main = (
            f'<div class="content"><div class="headline" style="font-size:{hsize}px">{headline}</div>'
            f'<div class="line"></div><div class="body">{body}</div>{bullets_html(bullets)}</div>'
        )
        bottom = f'<div class="site">{SITE}</div><div class="pill">Comment <em>BOOK</em> to start.</div>'
    else:
        main = (
            f'<div class="content"><div class="kick">{esc(s.get("kick",""))}</div>'
            f'<div class="headline" style="font-size:{hsize}px">{headline}</div>'
            f'<div class="body">{body}</div>{bullets_html(bullets)}</div>'
        )
        bottom = f'<div class="site">{SITE}</div><div class="swipe">SWIPE &rarr;</div>'
    return CAROUSEL_PAGE.format(accent=ACCENT, site=SITE, num=f"{num:02d}", hsize=hsize, main=main, bottom=bottom)


def day_image_specs(day):
    """Return list of (slot_key, image_spec) for a day."""
    specs = []
    if day.get("image_am") or day.get("image"):
        specs.append(("am", day.get("image_am") or day.get("image")))
    if day.get("image_pm"):
        specs.append(("pm", day.get("image_pm")))
    return specs


def day_carousel_specs(day):
    specs = []
    if day.get("carousel_am") or day.get("carousel"):
        specs.append(("am", day.get("carousel_am") or day.get("carousel")))
    if day.get("carousel_pm"):
        specs.append(("pm", day.get("carousel_pm")))
    return specs


manifest_images = {"date": date_compact, "images": []}
carousel_jobs = []  # (car_name, day_date, day_ref_key)

img_counter = 0
for i, day in enumerate(posts, 1):
    day_date = day.get("date") or datetime.date.today().isoformat()
    for slot, spec in day_image_specs(day):
        img_counter += 1
        spec = dict(spec or {})
        spec.setdefault("date_label", datetime.date.today().strftime("%B %Y"))
        spec.setdefault("source", SOURCE)
        spec.setdefault("badge", "BookWellNow")
        for bi, bar in enumerate(spec.get("bars") or []):
            bar.setdefault("color", COLORS[bi % len(COLORS)])
            bar.setdefault("width_pct", f"{90 - bi * 12}%")
        html_path = os.path.join(img_dir, f"day-{i:02d}-{slot}.html")
        png_path = os.path.join(img_dir, f"day-{i:02d}-{slot}.png")
        # also write legacy day-NN.png for first image
        render_infographic(spec, html_path)
        if slot == "am":
            legacy = os.path.join(img_dir, f"day-{i:02d}.html")
            render_infographic(spec, legacy)
            manifest_images["images"].append({"id": f"{i}-legacy", "html": legacy, "png": os.path.join(img_dir, f"day-{i:02d}.png")})
        manifest_images["images"].append({"id": f"{i}-{slot}", "html": html_path, "png": png_path})
        day[f"_image_png_{slot}"] = png_path
        if slot == "am":
            day["_image_png"] = os.path.join(img_dir, f"day-{i:02d}.png")
        print(f"Image HTML day{i}/{slot} -> {html_path}")

    for slot, car in day_carousel_specs(day):
        car_name = f"bookwellnow-day-{i:02d}-{slot}" if slot != "am" else f"bookwellnow-day-{i:02d}"
        if slot == "pm":
            car_name = f"bookwellnow-day-{i:02d}-pm"
        temp_dir = os.path.join(BASE, "carousel-routine", "temp", car_name)
        os.makedirs(temp_dir, exist_ok=True)
        for f in os.listdir(temp_dir):
            if f.startswith("slide-") and f.endswith(".html"):
                os.remove(os.path.join(temp_dir, f))
        slides = (car or {}).get("slides") or []
        for si, s in enumerate(slides[:6], 1):
            open(os.path.join(temp_dir, f"slide-{si:02d}.html"), "w").write(build_slide_html(s, si))
        carousel_jobs.append((car_name, day_date, i, slot))
        print(f"Carousel HTML {car_name} -> {temp_dir}")

manifest_path = os.path.join(img_dir, "manifest.json")
json.dump(manifest_images, open(manifest_path, "w"), indent=2)

print("Screenshotting image PNGs...")
subprocess.run(["node", os.path.join(BASE, "cap_automation_images.cjs"), manifest_path], check=True)

print("Rendering carousels (PNG + PDF)...")
for car_name, day_date, day_i, slot in carousel_jobs:
    print(f"  Carousel {car_name} @ {day_date}")
    subprocess.run(["node", "render.js", day_date, car_name], cwd=os.path.join(BASE, "carousel-routine"), check=True)
    subprocess.run(["node", "render-pdf.js", day_date, car_name], cwd=os.path.join(BASE, "carousel-routine"), check=True)
    pdf_dir = os.path.join(BASE, "carousel-routine", "output", day_date, car_name)
    pdfs = glob.glob(os.path.join(pdf_dir, "*.pdf")) if os.path.isdir(pdf_dir) else []
    day = posts[day_i - 1]
    if pdfs:
        day[f"_carousel_pdf_{slot}"] = pdfs[0]
        if slot == "am":
            day["_carousel_pdf"] = pdfs[0]

missing = []
for i, day in enumerate(posts, 1):
    for slot, _ in day_image_specs(day):
        png = day.get(f"_image_png_{slot}") or (day.get("_image_png") if slot == "am" else None)
        if slot == "am":
            png = os.path.join(img_dir, f"day-{i:02d}-am.png")
            if not os.path.exists(png):
                png = os.path.join(img_dir, f"day-{i:02d}.png")
            day["_image_png_am"] = png if os.path.exists(png) else None
            day["_image_png"] = day["_image_png_am"]
        else:
            png = os.path.join(img_dir, f"day-{i:02d}-pm.png")
            day["_image_png_pm"] = png if os.path.exists(png) else None
        if not day.get(f"_image_png_{slot}") or not os.path.exists(day[f"_image_png_{slot}"]):
            # refresh from expected path
            expected = os.path.join(img_dir, f"day-{i:02d}-{slot}.png")
            if os.path.exists(expected):
                day[f"_image_png_{slot}"] = expected
            else:
                missing.append(expected)
    for slot, _ in day_carousel_specs(day):
        if not day.get(f"_carousel_pdf_{slot}"):
            car_name = f"bookwellnow-day-{i:02d}" if slot == "am" else f"bookwellnow-day-{i:02d}-pm"
            day_date = day.get("date") or datetime.date.today().isoformat()
            pdf_dir = os.path.join(BASE, "carousel-routine", "output", day_date, car_name)
            pdfs = glob.glob(os.path.join(pdf_dir, "*.pdf")) if os.path.isdir(pdf_dir) else []
            if pdfs:
                day[f"_carousel_pdf_{slot}"] = pdfs[0]
                if slot == "am":
                    day["_carousel_pdf"] = pdfs[0]
            else:
                missing.append(pdf_dir + "/*.pdf")

if missing:
    sys.exit("Missing assets:\n" + "\n".join(missing))

data["assetDir"] = img_dir
json.dump(data, open(BATCH, "w"), indent=2)
print(f"Done. Assets ready for {len(posts)} days × up to 4 posts. Updated {BATCH}")
