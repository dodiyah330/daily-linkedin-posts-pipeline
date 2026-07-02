import os
import re
import urllib.request
import ssl

def ensure_valid_images():
    assets_dir = "./carousel-routine/temp/carousel-branded/assets"
    os.makedirs(assets_dir, exist_ok=True)
    
    # Fallback mappings for general tech/startup themes
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

skill_path = "./skills/branded-carousel/SKILL.md"
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

# Use Linear Purple from the curated premium palette
color = "#5E6AD2"

# Replacements mapping for "Why Most Indian Founders Never Start"
data = {
    "1": (t1, {
        "{{BRAND_COLOR}}": color,
        "{{HEADER_LABEL}}": "STARTUP INERTIA",
        "{{HOOK_PART_1}}": "Why Indian founders",
        "{{HOOK_PART_2}}": "never actually",
        "{{HOOK_EMPHASIS}}": "start",
        "{{SUBTITLE}}": "They have the tech, the market, and the ambition. But 99% get stuck in the exact same loops before writing a line of code."
    }),
    "2": (t2, {
        "{{BRAND_COLOR}}": color,
        "{{PILL_LABEL}}": "THE BARRIER",
        "{{SLIDE_NUM}}": "02",
        "{{EYEBROW}}": "SOCIO-CULTURAL TRAP",
        "{{HEADLINE_PART_1}}": "The fear of",
        "{{HEADLINE_PART_2}}": "imperfect",
        "{{HEADLINE_EMPHASIS}}": "planning",
        "{{SUBHEAD}}": "Our education system values zero error. Entrepreneurship requires embracing constant error.",
        "{{BODY_TEXT}}": "Founders spend months writing business plans and pitch decks instead of building a crude MVP. They seek permission from a market that only gives feedback on execution."
    }),
    "3": (t3, {
        "{{BRAND_COLOR}}": color,
        "{{HEADER_LABEL}}": "THE PRESSURE",
        "{{SLIDE_NUM}}": "03",
        "{{HUGE_STAT}}": "78%",
        "{{CIRCLE_WORD_1}}": "RISK",
        "{{CIRCLE_WORD_2}}": "AVERSION",
        "{{HEADLINE_PART_1}}": "Choosing stability",
        "{{HEADLINE_PART_2}}": "over startup",
        "{{HEADLINE_EMPHASIS}}": "ambition",
        "{{BODY_TEXT}}": "A staggering percentage of prospective Indian founders cite family disapproval and lack of a social safety net as the number one reason they keep their day jobs."
    }),
    "4": (t2, {
        "{{BRAND_COLOR}}": color,
        "{{PILL_LABEL}}": "THE ILLUSION",
        "{{SLIDE_NUM}}": "04",
        "{{EYEBROW}}": "FUNDRAISING MYTH",
        "{{HEADLINE_PART_1}}": "Waiting for venture",
        "{{HEADLINE_PART_2}}": "capital to",
        "{{HEADLINE_EMPHASIS}}": "launch",
        "{{SUBHEAD}}": "Many founders believe they need $100k in funding before they can build anything.",
        "{{BODY_TEXT}}": "They spend 80% of their energy chasing angel investors rather than building traction. In today's landscape, customers are the best source of seed funding."
    }),
    "5": (t3, {
        "{{BRAND_COLOR}}": color,
        "{{HEADER_LABEL}}": "THE RED TAPE",
        "{{SLIDE_NUM}}": "05",
        "{{HUGE_STAT}}": "1",
        "{{CIRCLE_WORD_1}}": "SIMPLE",
        "{{CIRCLE_WORD_2}}": "MVP",
        "{{HEADLINE_PART_1}}": "Legal structure before",
        "{{HEADLINE_PART_2}}": "market demand",
        "{{HEADLINE_EMPHASIS}}": "validation",
        "{{BODY_TEXT}}": "Founders obsess over legal structure, GST registration, and trademarking before they have a single paying customer. Focus on validation first."
    }),
    "6": (t6, {
        "{{BRAND_COLOR}}": color,
        "{{HEADER_LABEL}}": "THE REALITY",
        "{{HUGE_STAT": "100%",
        "{{HEADLINE_PART_1}}": "Ideas are cheap,",
        "{{HEADLINE_PART_2}}": "execution is the only",
        "{{HEADLINE_EMPHASIS}}": "currency",
        "{{SUBHEAD}}": "Hype and startup conferences won't build your product. Action will.",
        "{{BODY_TEXT}}": "Stop attending panels. Stop networking. Close the browser, open your IDE, and ship the first version to 10 potential users today."
    }),
    "7": (t7, {
        "{{BRAND_COLOR}}": color,
        "{{HEADLINE_PART_1}}": "Build in public.",
        "{{HEADLINE_PART_2}}": "Ship fast. Follow for more",
        "{{HEADLINE_EMPHASIS}}": "startup loops",
        "{{SUBHEAD}}": "Don't let analysis paralysis kill your idea. The best time to start was yesterday. The next best time is right now."
    })
}

for slide_num, (template, replacements) in data.items():
    html = template
    for k, v in replacements.items():
        html = html.replace(k, v)
    with open(f"{out_dir}/slide-0{slide_num}.html", "w") as f:
        f.write(html)

print("Generated 7 HTML slides successfully in temp/carousel-branded.")
