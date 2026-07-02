#!/usr/bin/env python3
"""Free-first carousel image sourcer with web fallback.

Cascade order (stops at first success):
  1. source og:image  - if --source-url given (brand-story carousels). Free, real, on-brand.
  2. Pollinations      - free AI generation (works on non-shared IPs; saturated on shared sandbox IPs).
  3. Gemini AI-gen     - on-brand AI image via GEMINI_API_KEY (~4c/image; needs billing enabled).
  4. Openverse stock   - web photo fallback (ALLOW_STOCK=1, default on). Quality varies — last resort.

Prints the source that worked, or 'NONE' (caller should fall back to clean typography, never junk).
Usage:
  python3 fetch_carousel_image.py --prompt "<ai prompt>" --query "<search terms>" --out a.png [--source-url URL]
"""
import sys, os, json, base64, subprocess, urllib.request, urllib.parse, argparse

BASE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "Mozilla/5.0 (FounderWing pipeline)"}

def _valid(path, minbytes=10000):
    if not (os.path.exists(path) and os.path.getsize(path) > minbytes):
        return False
    with open(path, "rb") as f:
        sig = f.read(8)
    return sig[:3] == b"\xff\xd8\xff" or sig[:8] == b"\x89PNG\r\n\x1a\n"

def via_source_og(url, out):
    try:
        node = (f'const p=require("{BASE}/carousel-routine/node_modules/puppeteer");(async()=>{{'
                f'const b=await p.launch({{headless:"shell",args:["--no-sandbox","--disable-setuid-sandbox"]}});'
                f'const g=await b.newPage();await g.goto("{url}",{{waitUntil:"networkidle2",timeout:40000}});'
                f'const o=await g.evaluate(()=>{{const m=document.querySelector(\'meta[property="og:image"]\')'
                f'||document.querySelector(\'meta[name="twitter:image"]\');return m?m.content:""}});'
                f'console.log(o);await b.close()}})()')
        og = subprocess.check_output(["node", "-e", node], timeout=75, stderr=subprocess.DEVNULL).decode().strip()
        if og:
            data = urllib.request.urlopen(urllib.request.Request(og, headers=UA), timeout=30).read()
            open(out, "wb").write(data)
            return _valid(out)
    except Exception as e:
        print("  source-og:", str(e)[:80], file=sys.stderr)
    return False

def via_pollinations(prompt, out):
    try:
        u = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt) + "?width=1024&height=1280&nologo=true&model=flux"
        data = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=120).read()
        if data[:3] == b"\xff\xd8\xff" or data[:8] == b"\x89PNG\r\n\x1a\n":
            open(out, "wb").write(data)
            return _valid(out)
    except Exception as e:
        print("  pollinations:", str(e)[:80], file=sys.stderr)
    return False

def via_gemini(prompt, out):
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("aigen", os.path.join(BASE, "aigen_image.py"))
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        return bool(m.gen(prompt, out)) and _valid(out)
    except Exception as e:
        print("  gemini:", str(e)[:80], file=sys.stderr)
    return False

def via_openverse(query, out):
    try:
        u = ("https://api.openverse.org/v1/images/?q=" + urllib.parse.quote(query)
             + "&page_size=12&mature=false&category=photograph")
        d = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=25).read())
        for r in d.get("results", []):
            if r.get("url") and (r.get("width") or 0) >= 700:
                try:
                    img = urllib.request.urlopen(urllib.request.Request(r["url"], headers=UA), timeout=30).read()
                    open(out, "wb").write(img)
                    if _valid(out):
                        return True
                except Exception:
                    continue
    except Exception as e:
        print("  openverse:", str(e)[:80], file=sys.stderr)
    return False

def fetch(prompt, query, out, source_url=None):
    if source_url and via_source_og(source_url, out):
        return "source-og"
    if via_pollinations(prompt, out):
        return "pollinations"
    if via_gemini(prompt, out):
        return "gemini"
    if os.environ.get("ALLOW_STOCK", "1") == "1" and via_openverse(query, out):
        return "openverse-stock"
    return None

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--query", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--source-url", default=None)
    a = ap.parse_args()
    res = fetch(a.prompt, a.query or a.prompt, a.out, a.source_url)
    print(res or "NONE")
    sys.exit(0 if res else 2)
