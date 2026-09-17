#!/usr/bin/env python3
"""
Build BookWellNow carousel PDFs from bookwellnow_batch_*.json
or bookwellnow_facebook_batch_*.json (3 posts/day).

2 or 3 posts/day, 4 slides each. Layouts rotate so carousels do not look identical:
  hook_stat, list, cards, split, cta
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
ACCENT2 = "#7C3AED"
ACCENT3 = "#C084FC"
INK = "#111111"
CREAM = "#FAF8FF"
SITE = "bookwellnow.com"

files = sorted(glob.glob("bookwellnow_batch_*.json"))
fb_files = sorted(glob.glob("bookwellnow_facebook_batch_*.json"))
if os.environ.get("BOOKWELLNOW_BATCH"):
    BATCH = os.environ["BOOKWELLNOW_BATCH"]
    if not os.path.exists(BATCH):
        sys.exit(f"BOOKWELLNOW_BATCH not found: {BATCH}")
elif os.environ.get("BOOKWELLNOW_FACEBOOK") == "1" and fb_files:
    BATCH = fb_files[-1]
elif not files:
    sys.exit("No bookwellnow_batch_*.json — run generate_bookwellnow_batch.py first")
else:
    BATCH = files[-1]

ASSET_PREFIX = os.environ.get("BOOKWELLNOW_ASSET_PREFIX")
if not ASSET_PREFIX:
    ASSET_PREFIX = "bookwellnow-fb" if "facebook" in os.path.basename(BATCH) else "bookwellnow"

data = json.load(open(BATCH))
posts = data["posts"]
date_compact = datetime.date.today().isoformat().replace("-", "")
img_dir = os.path.join(BASE, "bookwellnow-images", date_compact)
os.makedirs(img_dir, exist_ok=True)


def esc(s):
    return html_lib.escape(str(s or ""))


def rich(s):
    t = esc(s)
    return t.replace("&lt;em&gt;", "<em>").replace("&lt;/em&gt;", "</em>")


FONTS = (
    "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800;900"
    "&family=Instrument+Serif:ital@1&display=swap"
)

BASE_CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{width:1080px;height:1080px;overflow:hidden;font-family:'Plus Jakarta Sans',sans-serif;position:relative}
em{font-family:'Instrument Serif',serif;font-style:italic;font-weight:400;letter-spacing:0}
.header{position:absolute;top:44px;left:56px;right:56px;display:flex;justify-content:space-between;align-items:center;z-index:10}
.hleft{display:flex;align-items:center;gap:12px;font-size:14px;font-weight:800;letter-spacing:2.2px;text-transform:uppercase}
.dot{width:14px;height:14px;border-radius:50%;background:#5700B4;flex-shrink:0}
.badge{width:48px;height:48px;border-radius:50%;display:flex;justify-content:center;align-items:center;font-weight:800;font-size:17px}
.bottom{position:absolute;bottom:36px;left:56px;right:56px;display:flex;justify-content:space-between;align-items:center;z-index:10}
.swipe{font-size:13px;font-weight:800;letter-spacing:1.6px;text-transform:uppercase;min-width:110px;text-align:right}
.site{font-size:13px;font-weight:700;min-width:140px}
"""


def dots_html(num, total, light=True):
    on = "#fff" if not light else ACCENT
    off = "rgba(255,255,255,.28)" if not light else "#D9D0F0"
    bits = []
    for i in range(1, max(total, 1) + 1):
        w = 28 if i == num else 10
        c = on if i == num else off
        bits.append(
            f'<i style="display:inline-block;width:{w}px;height:10px;border-radius:99px;background:{c};margin:0 4px"></i>'
        )
    return f'<div class="dots">{"".join(bits)}</div>'


def wrap(body_css, inner, num, light=True, total=4):
    ink = "#111" if light else "#fff"
    muted = "#666" if light else "rgba(255,255,255,0.72)"
    badge_bg = ACCENT if light else "#fff"
    badge_fg = "#fff" if light else ACCENT
    bg = CREAM if light else ACCENT
    dots = dots_html(num, total, light=light)
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080"/>
<link href="{FONTS}" rel="stylesheet"/>
<style>
{BASE_CSS}
body{{background:{bg};color:{ink}}}
.hleft{{color:{ink}}}
.badge{{background:{badge_bg};color:{badge_fg}}}
.swipe{{color:{ink}}}
.site{{color:{muted}}}
.dots{{display:flex;align-items:center;justify-content:center}}
{body_css}
</style></head><body>
<div class="header"><div class="hleft"><span class="dot"></span>BookWellNow</div>
<div class="badge">{num:02d}</div></div>
{inner}
<div class="bottom"><div class="site">{SITE}</div>{dots}<div class="swipe">SWIPE {num}/{total}</div></div>
</body></html>"""


def bullets_block(items, dark=False):
    bg = "rgba(255,255,255,0.12)" if dark else "#fff"
    bd = "rgba(255,255,255,0.18)" if dark else "#E8E0F5"
    fg = "#fff" if dark else "#1a1a1a"
    rows = []
    for i, b in enumerate(items[:4], 1):
        rows.append(
            f'<div class="li"><div class="n">{i}</div><div class="t">{esc(b)}</div></div>'
        )
    return f"""<style>
.lis{{display:flex;flex-direction:column;gap:12px;margin-top:22px}}
.li{{display:flex;gap:14px;align-items:center;background:{bg};border:1px solid {bd};border-radius:16px;padding:16px 18px}}
.n{{width:34px;height:34px;border-radius:10px;background:{ACCENT if not dark else '#fff'};color:{'#fff' if not dark else ACCENT};font-size:15px;font-weight:800;display:flex;align-items:center;justify-content:center;flex-shrink:0}}
.t{{font-size:22px;font-weight:650;color:{fg};line-height:1.25}}
</style><div class="lis">{''.join(rows)}</div>"""


def layout_hook_stat(s, num, total=4):
    headline = rich(s.get("headline", "Take <em>bookings</em> online"))
    raw_stat = str(s.get("stat") or "").strip()
    if len(raw_stat) > 8:
        raw_stat = raw_stat.split()[0][:8]
    stat = esc(raw_stat)
    label = esc(s.get("stat_label") or "")
    stat_size = 132 if len(raw_stat) <= 4 else (96 if len(raw_stat) <= 6 else 68)
    kick = esc(s.get("kick") or "BOOKING")
    body = esc(s.get("body") or "")
    bullets = s.get("bullets") or []
    stat_html = ""
    if stat:
        stat_html = f"""<div class="statrow">
          <div class="stat">{stat}</div>
          <div class="statlab">{label}</div>
        </div>"""
    pills = "".join(f'<div class="pill">{esc(b)}</div>' for b in bullets[:3])
    css = f"""
.content{{position:absolute;top:124px;left:56px;right:56px;bottom:100px;display:flex;flex-direction:column}}
.rail{{position:absolute;left:0;top:0;bottom:0;width:18px;background:#C084FC}}
.kick{{display:inline-block;align-self:flex-start;font-size:14px;font-weight:800;letter-spacing:3px;text-transform:uppercase;color:{ACCENT};background:#fff;padding:8px 14px;border-radius:999px;margin-bottom:18px}}
.headline{{font-size:64px;font-weight:900;letter-spacing:-2.4px;line-height:1.02;color:#fff;max-width:960px}}
.headline em{{color:#FDE68A}}
.statrow{{display:flex;align-items:flex-end;gap:22px;margin-top:28px;padding:22px 26px;background:rgba(0,0,0,.18);border-radius:24px;border:1px solid rgba(255,255,255,.14);width:fit-content;max-width:100%}}
.stat{{font-size:{stat_size}px;font-weight:900;letter-spacing:-6px;line-height:.85;color:#FDE68A}}
.statlab{{font-family:'Instrument Serif',serif;font-style:italic;font-size:26px;color:#E9D5FF;padding-bottom:10px;max-width:420px;line-height:1.25}}
.body{{font-size:24px;font-weight:500;color:rgba(255,255,255,.92);line-height:1.38;margin-top:22px;max-width:920px}}
.pills{{display:flex;flex-wrap:wrap;gap:10px;margin-top:auto}}
.pill{{background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.22);color:#fff;font-size:16px;font-weight:700;padding:12px 16px;border-radius:999px}}
.bottom{{color:#fff}}
.site,.swipe{{color:#fff}}
.header .hleft{{color:#fff}}
.dot{{background:#fff}}
.badge{{background:#fff;color:{ACCENT}}}
.deco{{position:absolute;right:-120px;bottom:-140px;width:520px;height:520px;border-radius:50%;background:rgba(255,255,255,.08);pointer-events:none}}
.deco2{{position:absolute;right:80px;top:180px;width:220px;height:220px;border-radius:50%;border:18px solid rgba(255,255,255,.1);pointer-events:none}}
"""
    inner = f"""<div class="rail"></div><div class="deco"></div><div class="deco2"></div>
<div class="content">
  <div class="kick">{kick}</div>
  <div class="headline">{headline}</div>
  {stat_html}
  <div class="body">{body}</div>
  <div class="pills">{pills}</div>
</div>"""
    return wrap(css, inner, num, light=False, total=total)


def layout_list(s, num, total=4):
    headline = rich(s.get("headline", "Fix these <em>mistakes</em>"))
    kick = esc(s.get("kick") or "CHECKLIST")
    body = esc(s.get("body") or "")
    items = s.get("bullets") or []
    rows = []
    colors = [ACCENT, ACCENT2, "#6D28D9", "#4C1D95"]
    for i, b in enumerate(items[:4], 1):
        rows.append(
            f"""<div class="row">
              <div class="num" style="color:{colors[(i-1)%4]}">{i:02d}</div>
              <div class="txt">{esc(b)}</div>
            </div>"""
        )
    css = """
.content{position:absolute;top:124px;left:56px;right:56px;bottom:100px;display:flex;flex-direction:column}
.kick{display:inline-block;align-self:flex-start;font-size:14px;font-weight:800;letter-spacing:3px;text-transform:uppercase;color:#fff;background:#5700B4;padding:8px 14px;border-radius:999px;margin-bottom:14px}
.headline{font-size:50px;font-weight:900;letter-spacing:-2px;line-height:1.06;max-width:960px}
.headline em{color:#5700B4}
.body{font-size:22px;font-weight:500;color:#333;line-height:1.35;margin:14px 0 18px;max-width:900px}
.rows{display:flex;flex-direction:column;gap:12px;margin-top:auto}
.row{display:flex;align-items:center;gap:18px;background:#fff;border:1px solid #E8E0F5;border-radius:18px;padding:18px 22px;box-shadow:0 10px 24px rgba(87,0,180,.06)}
.num{font-size:40px;font-weight:900;letter-spacing:-2px;line-height:1;min-width:74px}
.txt{font-size:23px;font-weight:700;color:#111;line-height:1.28}
"""
    inner = f"""<div class="content">
  <div class="kick">{kick}</div>
  <div class="headline">{headline}</div>
  <div class="body">{body}</div>
  <div class="rows">{''.join(rows)}</div>
</div>"""
    return wrap(css, inner, num, light=True, total=total)


def layout_cards(s, num, total=4):
    headline = rich(s.get("headline", "What you <em>get</em>"))
    kick = esc(s.get("kick") or "FEATURES")
    body = esc(s.get("body") or "")
    cards = s.get("cards") or []
    bullets = s.get("bullets") or []
    while len(cards) < 4:
        idx = len(cards)
        cards.append({
            "title": bullets[idx] if idx < len(bullets) else f"Point {idx+1}",
            "body": "",
        })
    fills = ["#5700B4", "#6D28D9", "#111111", "#4C1D95"]
    cells = []
    for i, c in enumerate(cards[:4]):
        title = esc(c.get("title", ""))
        desc = esc(c.get("body", "") or (bullets[i] if i < len(bullets) and c.get("title") != bullets[i] else ""))
        cells.append(
            f"""<div class="card" style="background:{fills[i]}">
              <div class="cn">{i+1:02d}</div>
              <div class="ct">{title}</div>
              <div class="cd">{desc}</div>
            </div>"""
        )
    css = """
.content{position:absolute;top:118px;left:56px;right:56px;bottom:100px;display:flex;flex-direction:column}
.kick{display:inline-block;align-self:flex-start;font-size:14px;font-weight:800;letter-spacing:3px;text-transform:uppercase;color:#fff;background:#5700B4;padding:8px 14px;border-radius:999px;margin-bottom:12px}
.headline{font-size:46px;font-weight:900;letter-spacing:-1.8px;line-height:1.08}
.headline em{color:#5700B4}
.body{font-size:20px;font-weight:500;color:#333;margin:10px 0 16px}
.grid{display:grid;grid-template-columns:1fr 1fr;grid-template-rows:1fr 1fr;gap:16px;flex:1;min-height:0}
.card{border-radius:22px;padding:22px 24px;color:#fff;display:flex;flex-direction:column;justify-content:flex-end;position:relative;overflow:hidden}
.cn{font-size:64px;font-weight:900;opacity:.18;position:absolute;top:8px;right:16px;letter-spacing:-3px}
.ct{font-size:22px;font-weight:800;line-height:1.2;margin-bottom:8px;position:relative;overflow-wrap:break-word}
.cd{font-size:16px;font-weight:500;opacity:.9;line-height:1.3;position:relative;overflow-wrap:break-word}
"""
    inner = f"""<div class="content">
  <div class="kick">{kick}</div>
  <div class="headline">{headline}</div>
  <div class="body">{body}</div>
  <div class="grid">{''.join(cells)}</div>
</div>"""
    return wrap(css, inner, num, light=True, total=total)


def layout_split(s, num, total=4):
    headline = rich(s.get("headline", "Before vs <em>after</em>"))
    kick = esc(s.get("kick") or "COMPARE")
    body = esc(s.get("body") or "")
    left_title = esc(s.get("left_title") or "BEFORE")
    right_title = esc(s.get("right_title") or "AFTER")
    left_items = s.get("left_items") or (s.get("bullets") or ["Phone tag", "No-shows", "Double books"])[:3]
    right_items = s.get("right_items") or ["24/7 booking", "Reminders", "Self-serve reschedule"]
    left_lis = "".join(f"<div class='it'>✕ {esc(x)}</div>" for x in left_items[:3])
    right_lis = "".join(f"<div class='it'>✓ {esc(x)}</div>" for x in right_items[:3])
    css = """
.content{position:absolute;top:118px;left:56px;right:56px;bottom:100px;display:flex;flex-direction:column}
.kick{display:inline-block;align-self:flex-start;font-size:14px;font-weight:800;letter-spacing:3px;text-transform:uppercase;color:#fff;background:#5700B4;padding:8px 14px;border-radius:999px;margin-bottom:12px}
.headline{font-size:46px;font-weight:900;letter-spacing:-1.8px;line-height:1.08}
.headline em{color:#5700B4}
.body{font-size:20px;font-weight:500;color:#333;margin:10px 0 16px}
.split{display:grid;grid-template-columns:1fr 1fr;gap:16px;flex:1;min-height:0}
.panel{border-radius:24px;padding:28px 28px 24px;display:flex;flex-direction:column}
.panel.left{background:#1A1028;color:#fff}
.panel.right{background:#5700B4;color:#fff}
.pt{font-size:14px;font-weight:800;letter-spacing:2.4px;opacity:.75;margin-bottom:18px}
.ph{font-family:'Instrument Serif',serif;font-style:italic;font-size:34px;margin-bottom:18px}
.it{font-size:22px;font-weight:700;line-height:1.35;padding:12px 0;border-top:1px solid rgba(255,255,255,.16)}
"""
    inner = f"""<div class="content">
  <div class="kick">{kick}</div>
  <div class="headline">{headline}</div>
  <div class="body">{body}</div>
  <div class="split">
    <div class="panel left"><div class="pt">{left_title}</div><div class="ph">The old way</div>{left_lis}</div>
    <div class="panel right"><div class="pt">{right_title}</div><div class="ph">With BookWellNow</div>{right_lis}</div>
  </div>
</div>"""
    return wrap(css, inner, num, light=True, total=total)


def layout_cta(s, num, total=4):
    headline = rich(s.get("headline") or "Ready to take <em>bookings</em>?")
    body = esc(s.get("body") or "Comment BOOK for the free plugin and a setup checklist.")
    bullets = s.get("bullets") or ["Free core", "Expert install", SITE]
    lis = "".join(f"<div class='tb'>{esc(b)}</div>" for b in bullets[:3])
    dots = dots_html(num, total, light=False)
    css = f"""
.top{{position:absolute;top:0;left:0;right:0;height:58%;background:{ACCENT};color:#fff}}
.deco{{position:absolute;right:-80px;top:-80px;width:340px;height:340px;border-radius:50%;background:rgba(255,255,255,.08)}}
.content{{position:absolute;top:132px;left:56px;right:56px}}
.kick{{display:inline-block;font-size:14px;font-weight:800;letter-spacing:3px;text-transform:uppercase;color:{ACCENT};background:#FDE68A;padding:8px 14px;border-radius:999px;margin-bottom:16px}}
.headline{{font-size:60px;font-weight:900;letter-spacing:-2.4px;line-height:1.04;color:#fff}}
.headline em{{color:#FDE68A}}
.body{{font-size:24px;font-weight:500;color:rgba(255,255,255,.92);margin-top:18px;max-width:860px;line-height:1.35}}
.bot{{position:absolute;top:58%;left:0;right:0;bottom:0;background:#111;color:#fff}}
.trust{{position:absolute;top:32px;left:56px;right:56px;display:flex;gap:12px;flex-wrap:wrap}}
.tb{{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.14);padding:12px 16px;border-radius:999px;font-size:16px;font-weight:700}}
.pill{{position:absolute;bottom:88px;right:56px;background:{ACCENT};color:#fff;padding:18px 34px;border-radius:50px;font-size:22px;font-weight:800}}
.pill em{{color:#FDE68A}}
.footer{{position:absolute;bottom:36px;left:56px;right:56px;display:flex;justify-content:space-between;align-items:center}}
.site{{color:rgba(255,255,255,.6);font-size:13px;font-weight:700;min-width:140px}}
.swipe{{color:#fff;font-size:13px;font-weight:800;letter-spacing:1.6px;min-width:110px;text-align:right}}
.header .hleft{{color:#fff}}
.dot{{background:#fff}}
.badge{{background:#fff;color:{ACCENT}}}
"""
    inner = f"""<div class="top"><div class="deco"></div>
  <div class="content">
    <div class="kick">NEXT STEP</div>
    <div class="headline">{headline}</div>
    <div class="body">{body}</div>
  </div>
</div>
<div class="bot">
  <div class="trust">{lis}</div>
  <div class="pill">Comment <em>BOOK</em> to start</div>
  <div class="footer"><div class="site">{SITE}</div>{dots}<div class="swipe">SWIPE {num}/{total}</div></div>
</div>"""
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080"/>
<link href="{FONTS}" rel="stylesheet"/>
<style>
{BASE_CSS}
body{{background:#111;color:#fff}}
{css}
</style></head><body>
<div class="header"><div class="hleft"><span class="dot"></span>BookWellNow</div>
<div class="badge">{num:02d}</div></div>
{inner}
</body></html>"""


LAYOUTS = {
    "hook_stat": layout_hook_stat,
    "list": layout_list,
    "cards": layout_cards,
    "split": layout_split,
    "cta": layout_cta,
}


def build_slide_html(s, num, total=4):
    layout = (s or {}).get("layout") or ("cta" if s.get("cta") else "list")
    fn = LAYOUTS.get(layout) or layout_list
    return fn(s, num, total)


def day_carousels(day):
    """Return list of (slot_letter, carousel_spec)."""
    if day.get("carousels"):
        return [(chr(ord("a") + i), c) for i, c in enumerate(day["carousels"][:3])]
    specs = []
    # legacy 2-slot image+carousel days
    if day.get("carousel_am") or day.get("carousel"):
        specs.append(("a", day.get("carousel_am") or day.get("carousel")))
    if day.get("carousel_mid"):
        specs.append(("b", day.get("carousel_mid")))
    if day.get("carousel_pm"):
        specs.append(("c" if day.get("carousel_mid") else "b", day.get("carousel_pm")))
    return specs


carousel_jobs = []
for i, day in enumerate(posts, 1):
    day_date = day.get("date") or datetime.date.today().isoformat()
    for slot, car in day_carousels(day):
        car_name = f"{ASSET_PREFIX}-day-{i:02d}-{slot}"
        temp_dir = os.path.join(BASE, "carousel-routine", "temp", car_name)
        os.makedirs(temp_dir, exist_ok=True)
        for f in os.listdir(temp_dir):
            if f.startswith("slide-") and f.endswith(".html"):
                os.remove(os.path.join(temp_dir, f))
        slides = (car or {}).get("slides") or []
        slides = slides[:4]
        if slides:
            s0 = slides[0]
            if s0.get("layout") == "hook_stat" and not str(s0.get("stat") or "").strip():
                s0["stat"] = car.get("stat") or "24/7"
                s0["stat_label"] = s0.get("stat_label") or car.get("stat_label") or "online booking"
        if not slides:
            print(f"  SKIP empty carousel {car_name}")
            continue
        for si, s in enumerate(slides, 1):
            open(os.path.join(temp_dir, f"slide-{si:02d}.html"), "w").write(build_slide_html(s, si, len(slides)))
        carousel_jobs.append((car_name, day_date, i, slot))
        print(f"Carousel HTML {car_name} ({len(slides)} slides) -> {temp_dir}")

if not carousel_jobs:
    sys.exit("No carousels to render")

def pngs_to_pdf(pngs, out_pdf):
    """Stitch slide PNGs into a multi-page PDF without launching Chrome."""
    try:
        from PIL import Image
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "pillow", "-q"], check=True)
        from PIL import Image
    images = [Image.open(p).convert("RGB") for p in pngs]
    images[0].save(out_pdf, save_all=True, append_images=images[1:], resolution=72.0)
    return os.path.getsize(out_pdf)


print(f"Rendering {len(carousel_jobs)} carousels (PNG + PDF)...")
for car_name, day_date, day_i, slot in carousel_jobs:
    print(f"  Carousel {car_name} @ {day_date}")
    subprocess.run(["node", "render.js", day_date, car_name], cwd=os.path.join(BASE, "carousel-routine"), check=True)
    pdf_dir = os.path.join(BASE, "carousel-routine", "output", day_date, car_name)
    pngs = sorted(glob.glob(os.path.join(pdf_dir, "slide-*.png"))) if os.path.isdir(pdf_dir) else []
    if not pngs:
        sys.exit(f"No PNGs for {car_name}")
    day = posts[day_i - 1]
    day.setdefault("_carousel_pngs", {})
    day["_carousel_pngs"][slot] = pngs
    pdf_path = os.path.join(pdf_dir, f"carousel-{day_date.replace('-', '')}.pdf")
    try:
        size = pngs_to_pdf(pngs, pdf_path)
        print(f"    PDF {size // 1024} KB -> {pdf_path}")
    except Exception as e:
        print(f"    Pillow PDF failed ({e}), trying render-pdf.js")
        subprocess.run(["node", "render-pdf.js", day_date, car_name], cwd=os.path.join(BASE, "carousel-routine"), check=True)
        pdfs = glob.glob(os.path.join(pdf_dir, "*.pdf"))
        pdf_path = pdfs[0] if pdfs else None
    if pdf_path and os.path.exists(pdf_path):
        day.setdefault("_carousel_pdfs", {})
        day["_carousel_pdfs"][slot] = pdf_path
        day[f"_carousel_pdf_{slot}"] = pdf_path
        if slot == "a":
            day["_carousel_pdf"] = pdf_path

missing = []
for i, day in enumerate(posts, 1):
    for slot, _ in day_carousels(day):
        if not day.get(f"_carousel_pdf_{slot}"):
            car_name = f"{ASSET_PREFIX}-day-{i:02d}-{slot}"
            day_date = day.get("date") or datetime.date.today().isoformat()
            pdf_dir = os.path.join(BASE, "carousel-routine", "output", day_date, car_name)
            pdfs = glob.glob(os.path.join(pdf_dir, "*.pdf")) if os.path.isdir(pdf_dir) else []
            if pdfs:
                day[f"_carousel_pdf_{slot}"] = pdfs[0]
            else:
                missing.append(pdf_dir + "/*.pdf")

if missing:
    sys.exit("Missing assets:\n" + "\n".join(missing))

data["assetDir"] = img_dir
json.dump(data, open(BATCH, "w"), indent=2)
print(f"Done. {len(carousel_jobs)} carousel PDFs ready. Updated {BATCH}")
