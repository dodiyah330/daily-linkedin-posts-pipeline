#!/usr/bin/env python3
"""Generate 7 daily automation infographic PNGs (one IMAGE post per day, Mon–Sun)."""
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

gemini_key = openrouter_key = None
with open(".env") as f:
    for line in f:
        if line.startswith("GEMINI_API_KEY="):
            gemini_key = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
        elif line.startswith("OPENROUTER_API_KEY="):
            openrouter_key = line.strip().split("=", 1)[1].strip().strip('"').strip("'")

if not gemini_key and not openrouter_key:
    sys.exit("Error: need GEMINI_API_KEY or OPENROUTER_API_KEY in .env")

# Only IMAGE slots (odd numbered in the 14-post week)
IMAGE_LABELS = [
    "1. MON IMAGE — NEWS → AUTOMATION",
    "3. TUE IMAGE — CASE STUDY",
    "5. WED IMAGE — QUALIFYING POLL",
    "7. THU IMAGE — WORKFLOW CARD",
    "9. FRI IMAGE — DIRECT OFFER",
    "11. SAT IMAGE — PAIN → AUTOMATION",
    "13. SUN IMAGE — MINI WIN",
]
IMAGE_KINDS = [
    "news_automation",
    "case_study",
    "poll_visual",
    "workflow_steps",
    "direct_offer",
    "pain_automation",
    "mini_win",
]
COLORS = ["#5E6AD2", "#D9785B", "#2563EB", "#059669", "#111111", "#7C3AED", "#DC2626"]


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


def llm_json(prompt, max_tokens=10000):
    gemini_model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
    openrouter_model = os.environ.get("OPENROUTER_MODEL", "google/gemini-2.5-flash")
    errors = []
    if gemini_key:
        try:
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{gemini_model}:generateContent?key={gemini_key}"
            )
            payload = {
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {
                    "maxOutputTokens": max_tokens,
                    "responseMimeType": "application/json",
                },
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            print(f"Generating infographic specs via Gemini {gemini_model}...")
            with urllib.request.urlopen(req, context=ctx) as res:
                resp = json.loads(res.read().decode("utf-8"))
                raw = resp["candidates"][0]["content"]["parts"][0]["text"]
            return raw
        except Exception as e:
            errors.append(str(e))
            print(f"Gemini failed ({e}); trying OpenRouter...")
    if openrouter_key:
        url = "https://openrouter.ai/api/v1/chat/completions"
        payload = {
            "model": openrouter_model,
            "messages": [{"role": "user", "content": prompt + "\n\nReturn ONLY valid JSON."}],
            "max_tokens": max_tokens,
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {openrouter_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://openxcode.com",
                "X-Title": "automation-images",
            },
            method="POST",
        )
        print(f"Generating infographic specs via OpenRouter {openrouter_model}...")
        with urllib.request.urlopen(req, context=ctx) as res:
            resp = json.loads(res.read().decode("utf-8"))
            return resp["choices"][0]["message"]["content"]
    raise RuntimeError(" | ".join(errors) or "no LLM key")


def fallback_spec(label, body, kind, color):
    """Deterministic infographic spec from caption text (no LLM required)."""
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    hook = lines[0][:60] if lines else label.split("—")[-1].strip()
    # crude number hunt
    nums = re.findall(r"\b\d+%|\b\d+\s*(?:hrs?|hours?|min|mins?|days?|slots?)\b|\b\d+\b", body, re.I)
    hero = nums[0] if nums else "AUTO"
    words = re.findall(r"[A-Za-z][A-Za-z0-9+./-]{2,}", body)
    tools = []
    for w in words:
        if w[0].isupper() or w.lower() in {
            "hubspot", "slack", "stripe", "notion", "calendly", "intercom",
            "zapier", "make", "docusign", "salesforce", "postgres",
        }:
            if w not in tools and len(tools) < 4:
                tools.append(w)
    while len(tools) < 3:
        tools.append(["Trigger", "AI step", "SaaS action", "Result"][len(tools)])

    if kind == "poll_visual":
        opts = re.findall(r"[☐□]\s*(.+)", body) or tools[:4]
        bars = [
            {"label": o[:40], "value": f"Opt {chr(65+i)}", "width_pct": f"{90 - i*15}%", "color": color}
            for i, o in enumerate(opts[:4])
        ]
    elif kind in ("workflow_steps", "pain_automation"):
        labels_w = ["Trigger", "Step 1", "Step 2", "Result"]
        bars = [
            {"label": labels_w[i], "value": tools[i][:20] if i < len(tools) else labels_w[i],
             "width_pct": f"{90 - i*12}%", "color": color}
            for i in range(4)
        ]
    elif kind == "direct_offer":
        bars = [
            {"label": tools[0][:40], "value": "Build", "width_pct": "90%", "color": color},
            {"label": tools[1][:40], "value": "Wire", "width_pct": "75%", "color": color},
            {"label": tools[2][:40], "value": "Ship", "width_pct": "60%", "color": color},
            {"label": "2 slots left", "value": "Open", "width_pct": "45%", "color": color},
        ]
    else:
        bars = [
            {"label": tools[i][:40], "value": nums[i] if i < len(nums) else f"{85 - i*15}%",
             "width_pct": f"{85 - i*15}%", "color": color}
            for i in range(min(4, max(3, len(tools))))
        ]

    title_words = hook.split()
    return {
        "badge": "⚡ Automation",
        "date_label": datetime.date.today().strftime("%B %Y"),
        "title_main": " ".join(title_words[:4]) or "Automation win",
        "title_span": " ".join(title_words[4:7]) or "that ships",
        "subtitle": (lines[1] if len(lines) > 1 else hook)[:120],
        "takeaway_num": str(hero)[:24],
        "takeaway_text": (lines[-2] if len(lines) > 2 else "Comment AUTO for a free audit")[:100],
        "source": f"Based on: {kind.replace('_', ' ')} · Hitesh Dodiya",
        "bars": bars,
    }


def generate_infographic_specs(posts_by_label):
    """Prefer LLM specs; fall back to deterministic specs on JSON failure."""
    specs = []
    for i, (label, kind) in enumerate(zip(IMAGE_LABELS, IMAGE_KINDS), 1):
        body = posts_by_label.get(label, "")[:1500]
        color = COLORS[(i - 1) % len(COLORS)]
        print(f"  Spec {i}/7 ({kind})...")
        try:
            prompt = f"""Create ONE LinkedIn infographic JSON object.

Return ONLY a single JSON object. Escape all strings. Do not use arrows like → (use "to" instead).

Schema:
{{"badge":"⚡ Automation","date_label":"{datetime.date.today().strftime('%B %Y')}","title_main":"3-5 words","title_span":"2-4 words","subtitle":"max 120 chars","takeaway_num":"stat text","takeaway_text":"max 100 chars","source":"Based on: topic · Hitesh Dodiya","bars":[{{"label":"x","value":"y","width_pct":"85%","color":"{color}"}}]}}

Kind: {kind}
Caption:
{body}
"""
            raw = llm_json(prompt, max_tokens=2000).strip()
            if raw.startswith("```"):
                raw = re.sub(r"^```(?:json)?\n?", "", raw)
                raw = re.sub(r"\n?```$", "", raw)
            raw = raw.replace("→", " to ").replace("–", "-").replace("—", "-")
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                m = re.search(r"\{[\s\S]*\}", raw)
                obj = json.loads(m.group(0)) if m else None
            if isinstance(obj, dict) and "specs" in obj:
                obj = obj["specs"][0]
            if isinstance(obj, list):
                obj = obj[0]
            if not isinstance(obj, dict) or "title_main" not in obj:
                raise ValueError("missing title_main")
            specs.append(obj)
            print("    LLM OK")
        except Exception as e:
            print(f"    LLM failed ({e}); using fallback")
            specs.append(fallback_spec(label, body, kind, color))
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

    # Require image labels (fallback: use first 7 numbered sections if old format)
    missing = [l for l in IMAGE_LABELS if l not in sections]
    if missing:
        print(f"Warning: missing image labels {missing} — check generate_automation_leads.py output")

    out_dir = os.path.join(BASE, "automation-images", date_compact)
    os.makedirs(out_dir, exist_ok=True)

    try:
        specs = generate_infographic_specs(sections)
    except Exception:
        traceback.print_exc()
        sys.exit("Infographic spec generation failed")

    manifest = {"date": date_compact, "images": []}

    for i, (spec, label) in enumerate(zip(specs, IMAGE_LABELS), 1):
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
        print(f"  HTML {i}/7 -> {html_path}")

    manifest_path = os.path.join(out_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print("Screenshotting PNGs...")
    subprocess.run(["node", os.path.join(BASE, "cap_automation_images.cjs"), manifest_path], check=True)

    for entry in manifest["images"]:
        if not os.path.exists(entry["png"]):
            sys.exit(f"Missing PNG: {entry['png']}")
        print(f"  PNG  {entry['id']}/7 -> {entry['png']}")

    print(f"Done. 7 automation images in {out_dir}")


if __name__ == "__main__":
    main()
