#!/usr/bin/env python3
"""Generate an on-brand image via Google Gemini image models (uses GEMINI_API_KEY from .env).
Usage: python3 aigen_image.py "<prompt>" <outpath.png> [model]
Default model: gemini-3-pro-image. Falls back to gemini-2.5-flash-image on failure.
Returns nonzero on failure."""
import sys, json, base64, subprocess, urllib.request, os

BASE = os.path.dirname(os.path.abspath(__file__))
KEY = subprocess.check_output("grep '^GEMINI_API_KEY=' " + os.path.join(BASE, ".env") + " | cut -d'=' -f2",
                              shell=True).decode().strip()

BRAND = (" Premium editorial illustration for a LinkedIn carousel. Warm cream background (#F8F7F3). "
         "One muted indigo-purple accent (#5E6AD2). Flat modern vector style, clean geometric shapes, "
         "generous negative space, sophisticated magazine aesthetic. Portrait 4:5 composition. "
         "No text, no words, no letters, no logos, no watermark.")

def _try(prompt, out, model):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt + BRAND}]}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": "application/json", "X-goog-api-key": KEY})
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=150).read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"  {model}: HTTP {e.code} {e.read().decode('utf-8', 'ignore')[:160]}"); return False
    except Exception as e:
        print(f"  {model}: {e}"); return False
    for cand in r.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                open(out, "wb").write(base64.b64decode(inline["data"]))
                print(f"saved {out} ({os.path.getsize(out)} bytes) via {model}")
                return True
    print(f"  {model}: no image in response: {json.dumps(r)[:200]}"); return False

def gen(prompt, out, model="gemini-3-pro-image"):
    if _try(prompt, out, model):
        return True
    if model != "gemini-2.5-flash-image":
        print("  -> falling back to gemini-2.5-flash-image")
        return _try(prompt, out, "gemini-2.5-flash-image")
    return False

if __name__ == "__main__":
    prompt, out = sys.argv[1], sys.argv[2]
    model = sys.argv[3] if len(sys.argv) > 3 else "gemini-3-pro-image"
    sys.exit(0 if gen(prompt, out, model) else 1)
