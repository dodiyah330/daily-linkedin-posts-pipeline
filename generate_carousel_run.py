import os
import re
import urllib.request
import ssl

def ensure_valid_images():
    assets_dir = "./carousel-routine/temp/carousel-branded/assets"
    os.makedirs(assets_dir, exist_ok=True)
    
    fallbacks = {
        "hero-ui.png": "https://images.unsplash.com/photo-1540575467063-178a50c2df87?auto=format&fit=crop&w=1080&q=80",
        "interface.png": "https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=1080&q=80"
    }
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    for filename, url in fallbacks.items():
        file_path = os.path.join(assets_dir, filename)
        is_valid = False
        
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            if size > 10000:
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        header = f.read(100)
                        if not ("<html" in header.lower() or "<!doctype" in header.lower()):
                            is_valid = True
                except Exception:
                    is_valid = True
                    
        if not is_valid:
            print(f"Asset '{filename}' is missing or invalid. Downloading fallback...")
            try:
                req = urllib.request.Request(
                    url, 
                    headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
                )
                with urllib.request.urlopen(req, context=ctx) as response:
                    with open(file_path, "wb") as f:
                        f.write(response.read())
                print(f"Successfully downloaded fallback for '{filename}'.")
            except Exception as e:
                print(f"Error downloading fallback for {filename}: {e}")

# Verify assets
ensure_valid_images()

skill_path = "/Users/prithal/.gemini/config/skills/branded-carousel/SKILL.md"
with open(skill_path, "r") as f:
    content = f.read()

# Extract templates
t1 = re.search(r"TEMPLATE 1.*?```html(.*?)```", content, re.DOTALL).group(1)
t2 = re.search(r"TEMPLATE 2 & 4.*?```html(.*?)```", content, re.DOTALL).group(1)
t3 = re.search(r"TEMPLATE 3 & 5.*?```html(.*?)```", content, re.DOTALL).group(1)
t6 = re.search(r"TEMPLATE 6.*?```html(.*?)```", content, re.DOTALL).group(1)
t7 = re.search(r"TEMPLATE 7.*?```html(.*?)```", content, re.DOTALL).group(1)

out_dir = "./carousel-routine/temp/carousel-branded"
os.makedirs(out_dir, exist_ok=True)

# Notion Red Color
color = "#E16259"

# Replacements mapping for "The Single-Client Freelance Trap"
data = {
    "1": (t1, {
        "{{BRAND_COLOR}}": color,
        "{{HEADER_LABEL}}": "FREELANCE RISK",
        "{{HOOK_PART_1}}": "From $120k to $0",
        "{{HOOK_PART_2}}": "in less than",
        "{{HOOK_EMPHASIS}}": "6 weeks",
        "{{SUBTITLE}}": "Leaving a stable job for freelance is the ultimate dream. Until your single client cancels your contract overnight."
    }),
    "2": (t2, {
        "{{BRAND_COLOR}}": color,
        "{{PILL_LABEL}}": "THE TRAP",
        "{{SLIDE_NUM}}": "02",
        "{{EYEBROW}}": "THE SINGLE CLIENT ILLUSION",
        "{{HEADLINE_PART_1}}": "Freelancing is a job",
        "{{HEADLINE_PART_2}}": "with only one",
        "{{HEADLINE_EMPHASIS}}": "boss",
        "{{SUBHEAD}}": "Having one client is not a business. It is a job without a safety net.",
        "{{BODY_TEXT}}": "If 100% of your revenue comes from a single company, you have all the risk of employment with none of the legal benefits."
    }),
    "3": (t3, {
        "{{BRAND_COLOR}}": color,
        "{{HEADER_LABEL}}": "THE DANGER",
        "{{SLIDE_NUM}}": "03",
        "{{HUGE_STAT}}": "1",
        "{{CIRCLE_WORD_1}}": "CLIENT",
        "{{CIRCLE_WORD_2}}": "LIMIT",
        "{{HEADLINE_PART_1}}": "The single client",
        "{{HEADLINE_PART_2}}": "trap is a timing",
        "{{HEADLINE_EMPHASIS}}": "bomb",
        "{{BODY_TEXT}}": "When they cut budget, you are the first line item to go. You have zero warning and zero leverage."
    }),
    "4": (t2, {
        "{{BRAND_COLOR}}": color,
        "{{PILL_LABEL}}": "THE SOLUTION",
        "{{SLIDE_NUM}}": "04",
        "{{EYEBROW}}": "DIVERSIFICATION",
        "{{HEADLINE_PART_1}}": "Never allow one",
        "{{HEADLINE_PART_2}}": "client to exceed",
        "{{HEADLINE_EMPHASIS}}": "50%",
        "{{SUBHEAD}}": "Cap your single-client exposure early.",
        "{{BODY_TEXT}}": "Even if they want to pay you full-time, keep at least 2 other small clients. It keeps your pipeline active and protects your sanity."
    }),
    "5": (t3, {
        "{{BRAND_COLOR}}": color,
        "{{HEADER_LABEL}}": "THE SHIFT",
        "{{SLIDE_NUM}}": "05",
        "{{HUGE_STAT}}": "3",
        "{{CIRCLE_WORD_1}}": "CLIENTS",
        "{{CIRCLE_WORD_2}}": "MINIMUM",
        "{{HEADLINE_PART_1}}": "Structure your pipeline",
        "{{HEADLINE_PART_2}}": "for absolute",
        "{{HEADLINE_EMPHASIS}}": "safety",
        "{{BODY_TEXT}}": "Having three clients means if one leaves, you lose 33% of your income — not 100%. It gives you breathing room to find the next one."
    }),
    "6": (t6, {
        "{{BRAND_COLOR}}": color,
        "{{HEADER_LABEL}}": "THE REALITY",
        "{{HUGE_STAT}}": "0%",
        "{{HEADLINE_PART_1}}": "Promises do not pay",
        "{{HEADLINE_PART_2}}": "your bills or",
        "{{HEADLINE_EMPHASIS}}": "rent",
        "{{SUBHEAD}}": "Always require a 30-day notice or retainer.",
        "{{BODY_TEXT}}": "If a client cannot commit to a notice period, charge them a premium. Never sell your stability cheap."
    }),
    "7": (t7, {
        "{{BRAND_COLOR}}": color,
        "{{HEADLINE_PART_1}}": "Build a pipeline.",
        "{{HEADLINE_PART_2}}": "Protect your",
        "{{HEADLINE_EMPHASIS}}": "business",
        "{{SUBHEAD}}": "Never let one decision maker control 100% of your income. Diversify before you quit your job."
    })
}

for slide_num, (template, replacements) in data.items():
    html = template
    for k, v in replacements.items():
        html = html.replace(k, v)
    with open(f"{out_dir}/slide-0{slide_num}.html", "w") as f:
        f.write(html)

print("Generated 7 HTML slides successfully in temp/carousel-branded.")
