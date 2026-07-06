#!/usr/bin/env python3
"""Generate 5 daily automation infographic PNGs from the latest automation_leads batch."""
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
    "1. NEWS → AUTOMATION",
    "2. CASE STUDY",
    "3. QUALIFYING POLL",
    "4. STEAL THIS WORKFLOW",
    "5. DIRECT OFFER",
]
IMAGE_KINDS = [
    "news_automation",
    "case_study",
    "poll_visual",
    "workflow_steps",
    "direct_offer",
]
COLORS = ["#5E6AD2", "#D9785B", "#2563EB", "#059669", "#111111"]


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
        <div class="bar-fill" style="width: {width}; background-color: {bar.get('color', '#5E6AD2')};"></div>
      </div>
    </div>"""
        )

    html = template
    html = html.replace("{{BADGE}}", data.get("badge", "⚡ AI Automation"))
    html = html.replace("{{DATE_LABEL}}", data.get("date_label", ""))
    html = html.replace("{{TITLE_MAIN}}", data.get("title_main", ""))
    html = html.replace("{{TITLE_SPAN}}", data.get("title_span", ""))
    html = html.replace("{{SUBTITLE}}", data.get("subtitle", ""))
    html = html.replace("{{BAR_ROWS}}", "\n".join(bar_rows))
    html = html.replace("{{TAKEAWAY_NUM}}", data.get("takeaway_num", ""))
    html = html.replace("{{TAKEAWAY_TEXT}}", data.get("takeaway_text", ""))
    html = html.replace("{{SOURCE}}", data.get("source", "Hitesh Dodiya · AI Automation"))

    with open(out_html, "w") as f:
        f.write(html)


def generate_infographic_specs(posts_by_label):
    sections_text = ""
    for label, kind in zip(LABELS, IMAGE_KINDS):
        body = posts_by_label.get(label, "")
        sections_text += f"\n--- {label} ({kind}) ---\n{body[:1200]}\n"

    prompt = f"""You create LinkedIn infographic data for an AI automation developer's daily image posts.

For each of the 5 post sections below, output ONE JSON object in an array (exactly 5 objects, same order).

Schema per object:
{{
  "badge": "short emoji label e.g. ⚡ Automation",
  "date_label": "Month Year",
  "title_main": "3-5 word hook (plain English)",
  "title_span": "2-4 word accent phrase",
  "subtitle": "one sentence context, max 120 chars",
  "takeaway_num": "hero stat e.g. 45min → 3min or 14% or 2 slots",
  "takeaway_text": "one line explaining the stat, max 100 chars",
  "source": "Based on: [topic] · Hitesh Dodiya",
  "bars": [
    {{"label": "short label max 40 chars", "value": "display value", "width_pct": "85%", "color": "#hex"}},
    ... 3 or 4 bars
  ]
}}

Rules:
- Pull REAL numbers and tools from each post section (Calendly, HubSpot, DocuSign, Intercom, etc.)
- For poll_visual (section 3): bars = the 4 poll options, values = "Vote A/B/C/D" or short labels, width_pct staggered 90/70/55/40
- For workflow_steps (section 4): bars = Trigger, Step 1, Step 2, Result
- For direct_offer (section 5): bars = 3 services offered + "2 slots left"
- Use colors from this palette rotating: {json.dumps(COLORS)}
- No jargon. No em-dashes.
- width_pct must be a CSS percentage string like "80%"

POST SECTIONS:
{sections_text}

Output ONLY a valid JSON array of 5 objects. No markdown fences."""

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
    print(f"Generating infographic specs via {gemini_model}...")
    with urllib.request.urlopen(req, context=ctx) as res:
        resp = json.loads(res.read().decode("utf-8"))
        raw = resp["candidates"][0]["content"]["parts"][0]["text"]
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    specs = json.loads(raw)
    if not isinstance(specs, list) or len(specs) != 5:
        raise SystemExit(f"Expected 5 infographic specs, got {len(specs) if isinstance(specs, list) else type(specs)}")
    return specs


def main():
    files = sorted(glob.glob(os.path.join(BASE, "automation_leads_*.txt")))
    if not files:
        sys.exit("No automation_leads_*.txt — run generate_automation_leads.py first")

    posts_file = files[-1]
    date_m = re.search(r"automation_leads_(\d{8})\.txt", posts_file)
    date_compact = date_m.group(1) if date_m else datetime.date.today().isoformat().replace("-", "")

    with open(posts_file) as f:
        sections = split_sections(f.read())

    out_dir = os.path.join(BASE, "automation-images", date_compact)
    os.makedirs(out_dir, exist_ok=True)

    try:
        specs = generate_infographic_specs(sections)
    except Exception:
        traceback.print_exc()
        sys.exit("Infographic spec generation failed")

    manifest = {"date": date_compact, "images": []}

    for i, (spec, label) in enumerate(zip(specs, LABELS), 1):
        spec.setdefault("date_label", datetime.date.today().strftime("%B %Y"))
        html_path = os.path.join(out_dir, f"automation-img-{i:02d}.html")
        png_path = os.path.join(out_dir, f"automation-img-{i:02d}.png")
        json_path = os.path.join(out_dir, f"automation-img-{i:02d}.json")
        with open(json_path, "w") as f:
            json.dump(spec, f, indent=2)
        render_infographic_html(spec, html_path)
        manifest["images"].append({
            "id": i,
            "label": label,
            "html": html_path,
            "png": png_path,
            "json": json_path,
        })
        print(f"  HTML {i}/5 -> {html_path}")

    manifest_path = os.path.join(out_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print("Screenshotting PNGs...")
    subprocess.run(["node", os.path.join(BASE, "cap_automation_images.cjs"), manifest_path], check=True)

    for entry in manifest["images"]:
        if not os.path.exists(entry["png"]):
            sys.exit(f"Missing PNG: {entry['png']}")
        print(f"  PNG  {entry['id']}/5 -> {entry['png']}")

    print(f"Done. 5 automation images in {out_dir}")


if __name__ == "__main__":
    main()
