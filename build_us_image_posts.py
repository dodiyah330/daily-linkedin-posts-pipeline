#!/usr/bin/env python3
"""Build 5 US-focused infographic PNGs from us_image_posts_*.txt."""
import datetime
import glob
import json
import os
import re
import ssl
import subprocess
import sys
import traceback
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

gemini_key = None
with open(".env") as f:
    for line in f:
        if line.startswith("GEMINI_API_KEY="):
            gemini_key = line.strip().split("=", 1)[1]
            break

if not gemini_key:
    sys.exit("Error: GEMINI_API_KEY not found in .env")

LABELS = [
    "1. MON — US NEWS HOOK",
    "2. TUE — US OPS WIN",
    "3. WED — US STACK TIP",
    "4. THU — US WORKFLOW CARD",
    "5. FRI — US OFFER",
]
KINDS = ["us_news", "us_ops", "us_stack", "us_workflow", "us_offer"]
COLORS = ["#1D4ED8", "#DC2626", "#059669", "#7C3AED", "#111111"]


def split_sections(text):
    text = re.sub(r"^={50}\n", "", text.strip())
    chunks = [c.strip() for c in re.split(r"\n={50}\n", text) if c.strip()]
    sections = {}
    i = 0
    while i + 1 < len(chunks):
        if re.match(r"^\d+\.", chunks[i]):
            sections[chunks[i]] = chunks[i + 1]
            i += 2
        else:
            i += 1
    return sections


def render_infographic_html(data, out_html):
    template_path = os.path.join(BASE, "linkedin-infographic-template.html")
    with open(template_path) as f:
        template = f.read()
    bar_rows = []
    for bar in data.get("bars", []):
        width = bar.get("width_pct", bar.get("value", "50%"))
        if not str(width).endswith("%"):
            width = f"{width}%"
        bar_rows.append(
            f"""    <div class="bar-row">
      <div class="bar-info">
        <span class="bar-label">{bar.get('label', '')}</span>
        <span class="bar-value">{bar.get('value', '')}</span>
      </div>
      <div class="bar-track">
        <div class="bar-fill" style="width: {width}; background-color: {bar.get('color', '#1D4ED8')};"></div>
      </div>
    </div>"""
        )
    html = template
    html = html.replace("{{BADGE}}", data.get("badge", "🇺🇸 US SaaS"))
    html = html.replace("{{DATE_LABEL}}", data.get("date_label", ""))
    html = html.replace("{{TITLE_MAIN}}", data.get("title_main", ""))
    html = html.replace("{{TITLE_SPAN}}", data.get("title_span", ""))
    html = html.replace("{{SUBTITLE}}", data.get("subtitle", ""))
    html = html.replace("{{BAR_ROWS}}", "\n".join(bar_rows))
    html = html.replace("{{TAKEAWAY_NUM}}", data.get("takeaway_num", ""))
    html = html.replace("{{TAKEAWAY_TEXT}}", data.get("takeaway_text", ""))
    html = html.replace("{{SOURCE}}", data.get("source", "US SaaS Automation · Hitesh Dodiya"))
    with open(out_html, "w") as f:
        f.write(html)


def generate_specs(sections):
    body = ""
    for label, kind in zip(LABELS, KINDS):
        body += f"\n--- {label} ({kind}) ---\n{sections.get(label, '')[:1000]}\n"

    prompt = f"""Create 5 LinkedIn infographic JSON objects for US SaaS automation audience.
Output a JSON array of exactly 5 objects (same order as sections).

Each object schema:
{{
  "badge": "🇺🇸 US SaaS Ops" or similar US badge,
  "date_label": "Month Year · US Edition",
  "title_main": "3-5 words",
  "title_span": "2-4 word accent",
  "subtitle": "US SaaS context, max 120 chars",
  "takeaway_num": "hero stat",
  "takeaway_text": "max 100 chars",
  "source": "US SaaS Automation · Hitesh Dodiya",
  "bars": [{{"label": "max 40 chars", "value": "display", "width_pct": "80%", "color": "#hex"}}, ... 3-4 bars]
}}

Use US tools (HubSpot, Salesforce, Slack, Stripe, DocuSign). US dollar outcomes where relevant.
Colors: {json.dumps(COLORS)}

SECTIONS:
{body}

Output ONLY valid JSON array."""

    gemini_model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={gemini_key}"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 8000, "responseMimeType": "application/json"},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    print(f"Generating US infographic specs via {gemini_model}...")
    with urllib.request.urlopen(req, context=ctx) as res:
        raw = json.loads(res.read().decode())["candidates"][0]["content"]["parts"][0]["text"].strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    specs = json.loads(raw)
    if len(specs) != 5:
        sys.exit(f"Expected 5 specs, got {len(specs)}")
    return specs


def main():
    files = sorted(glob.glob(os.path.join(BASE, "us_image_posts_*.txt")))
    if not files:
        sys.exit("No us_image_posts_*.txt — run generate_us_image_posts.py first")

    posts_file = files[-1]
    date_m = re.search(r"us_image_posts_(\d{8})\.txt", posts_file)
    date_compact = date_m.group(1) if date_m else datetime.date.today().isoformat().replace("-", "")

    with open(posts_file) as f:
        sections = split_sections(f.read())

    specs = generate_specs(sections)
    out_dir = os.path.join(BASE, "us-images", date_compact)
    os.makedirs(out_dir, exist_ok=True)

    manifest = {"date": date_compact, "stream": "us-image-posts", "images": []}
    for i, spec in enumerate(specs, 1):
        spec.setdefault("date_label", datetime.date.today().strftime("%B %Y · US Edition"))
        html_path = os.path.join(out_dir, f"us-img-{i:02d}.html")
        png_path = os.path.join(out_dir, f"us-img-{i:02d}.png")
        render_infographic_html(spec, html_path)
        manifest["images"].append({"id": i, "html": html_path, "png": png_path})

    manifest_path = os.path.join(out_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    cap_script = os.path.join(BASE, "cap_us_images.cjs")
    subprocess.run(["node", cap_script, manifest_path], check=True)
    print(f"Done. 5 US images in {out_dir}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
