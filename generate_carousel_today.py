import os
import re
import urllib.request
import ssl
import json

def ensure_valid_images():
    assets_dir = "./carousel-routine/temp/carousel-branded/assets"
    os.makedirs(assets_dir, exist_ok=True)
    
    # Fallback mappings for onboarding/conversion themes
    fallbacks = {
        "hero-ui.png": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=1080&q=80",
        "interface.png": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=1080&q=80"
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
            print(f"Asset '{filename}' is missing or invalid. Downloading fallback from {url}...")
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

# Run asset verification first
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

# Linear Purple Color
color = "#5E6AD2"

# Load dynamic carousel data if exists
json_data = {}
if os.path.exists("./carousel_data.json"):
    try:
        with open("./carousel_data.json") as f:
            json_data = json.load(f)
            print("Loaded dynamic carousel slide data from carousel_data.json")
    except Exception as e:
        print(f"Error loading carousel_data.json: {e}")

def get_slide_val(slide_num, key, fallback):
    slide_obj = json_data.get(str(slide_num), json_data.get(slide_num, {}))
    return slide_obj.get(key, fallback)

data = {
    "1": (t1, {
        "{{BRAND_COLOR}}": color,
        "{{HEADER_LABEL}}": get_slide_val("1", "HEADER_LABEL", "PRODUCT CONVERSION"),
        "{{HOOK_PART_1}}": get_slide_val("1", "HOOK_PART_1", "5x MRR in seven days"),
        "{{HOOK_PART_2}}": get_slide_val("1", "HOOK_PART_2", "with two simple"),
        "{{HOOK_EMPHASIS}}": get_slide_val("1", "HOOK_EMPHASIS", "changes"),
        "{{SUBTITLE}}": get_slide_val("1", "SUBTITLE", "A founder was stuck at $60 MRR for months. In one week, they changed only their onboarding and paywall. Revenue jumped to $300 MRR.")
    }),
    "2": (t2, {
        "{{BRAND_COLOR}}": color,
        "{{PILL_LABEL}}": get_slide_val("2", "PILL_LABEL", "THE BOTTLENECK"),
        "{{SLIDE_NUM}}": "02",
        "{{EYEBROW}}": get_slide_val("2", "EYEBROW", "CONVERSION FUNNEL"),
        "{{HEADLINE_PART_1}}": get_slide_val("2", "HEADLINE_PART_1", "Optimizing the user"),
        "{{HEADLINE_PART_2}}": get_slide_val("2", "HEADLINE_PART_2", "journey in under three"),
        "{{HEADLINE_EMPHASIS}}": get_slide_val("2", "HEADLINE_EMPHASIS", "days"),
        "{{SUBHEAD}}": get_slide_val("2", "SUBHEAD", "A developer spent months building features while ignoring the onboarding flow."),
        "{{BODY_TEXT}}": get_slide_val("2", "BODY_TEXT", "They had thousands of downloads but only a single paying user. The bottleneck wasn't utility — it was friction.")
    }),
    "3": (t3, {
        "{{BRAND_COLOR}}": color,
        "{{HEADER_LABEL}}": get_slide_val("3", "HEADER_LABEL", "THE LEAK"),
        "{{SLIDE_NUM}}": "03",
        "{{HUGE_STAT}}": get_slide_val("3", "HUGE_STAT", "90%"),
        "{{CIRCLE_WORD_1}}": get_slide_val("3", "CIRCLE_WORD_1", "USERS"),
        "{{CIRCLE_WORD_2}}": get_slide_val("3", "CIRCLE_WORD_2", "LOST"),
        "{{HEADLINE_PART_1}}": get_slide_val("3", "HEADLINE_PART_1", "Traditional onboarding was"),
        "{{HEADLINE_PART_2}}": get_slide_val("3", "HEADLINE_PART_2", "leaking users at every"),
        "{{HEADLINE_EMPHASIS}}": get_slide_val("3", "HEADLINE_EMPHASIS", "step"),
        "{{BODY_TEXT}}": get_slide_val("3", "BODY_TEXT", "Requiring sign-ups and credit cards before showing any value caused ninety percent of users to close the app immediately.")
    }),
    "4": (t2, {
        "{{BRAND_COLOR}}": color,
        "{{PILL_LABEL}}": get_slide_val("4", "PILL_LABEL", "THE SHIFT"),
        "{{SLIDE_NUM}}": "04",
        "{{EYEBROW}}": get_slide_val("4", "EYEBROW", "EMOTIONAL VALUE"),
        "{{HEADLINE_PART_1}}": get_slide_val("4", "HEADLINE_PART_1", "Showing immediate utility"),
        "{{HEADLINE_PART_2}}": get_slide_val("4", "HEADLINE_PART_2", "before presenting the"),
        "{{HEADLINE_EMPHASIS}}": get_slide_val("4", "HEADLINE_EMPHASIS", "paywall"),
        "{{SUBHEAD}}": get_slide_val("4", "SUBHEAD", "They moved the sign-up prompt to after the first action."),
        "{{BODY_TEXT}}": get_slide_val("4", "BODY_TEXT", "Users got to try the tool's core feature first. The paywall was only shown when they wanted to save their work.")
    }),
    "5": (t3, {
        "{{BRAND_COLOR}}": color,
        "{{HEADER_LABEL}}": get_slide_val("5", "HEADER_LABEL", "THE PAYOFF"),
        "{{SLIDE_NUM}}": "05",
        "{{HUGE_STAT}}": get_slide_val("5", "HUGE_STAT", "5x"),
        "{{CIRCLE_WORD_1}}": get_slide_val("5", "CIRCLE_WORD_1", "MRR"),
        "{{CIRCLE_WORD_2}}": get_slide_val("5", "CIRCLE_WORD_2", "JUMP"),
        "{{HEADLINE_PART_1}}": get_slide_val("5", "HEADLINE_PART_1", "Revenue jumped to three"),
        "{{HEADLINE_PART_2}}": get_slide_val("5", "HEADLINE_PART_2", "hundred dollars in"),
        "{{HEADLINE_EMPHASIS}}": get_slide_val("5", "HEADLINE_EMPHASIS", "seven days"),
        "{{BODY_TEXT}}": get_slide_val("5", "BODY_TEXT", "The conversion rate rose from under one percent to five percent, converting passive sign-ups into recurring buyers.")
    }),
    "6": (t6, {
        "{{BRAND_COLOR}}": color,
        "{{HEADER_LABEL}}": get_slide_val("6", "HEADER_LABEL", "THE LESSON"),
        "{{HUGE_STAT}}": get_slide_val("6", "HUGE_STAT", "80%"),
        "{{HEADLINE_PART_1}}": get_slide_val("6", "HEADLINE_PART_1", "Conversion is won at"),
        "{{HEADLINE_PART_2}}": get_slide_val("6", "HEADLINE_PART_2", "the first few minutes of"),
        "{{HEADLINE_EMPHASIS}}": get_slide_val("6", "HEADLINE_EMPHASIS", "interaction"),
        "{{SUBHEAD}}": get_slide_val("6", "SUBHEAD", "Simplify the entry. Delay the payment."),
        "{{BODY_TEXT}}": get_slide_val("6", "BODY_TEXT", "A product that is easy to try is easy to buy. Stop building features and start removing onboarding friction.")
    }),
    "7": (t7, {
        "{{BRAND_COLOR}}": color,
        "{{HEADLINE_PART_1}}": get_slide_val("7", "HEADLINE_PART_1", "Fix your onboarding."),
        "{{HEADLINE_PART_2}}": get_slide_val("7", "HEADLINE_PART_2", "Multiply your"),
        "{{HEADLINE_EMPHASIS}}": get_slide_val("7", "HEADLINE_EMPHASIS", "conversions"),
        "{{SUBHEAD}}": get_slide_val("7", "SUBHEAD", "Complexity won't save a product if users get stuck at the front door. Focus on user flow first.")
    })
}

for slide_num, (template, replacements) in data.items():
    html = template
    for k, v in replacements.items():
        html = html.replace(k, v)
    # Correct template 3 & 5 replacement bugs if any (e.g. circle word 2)
    html = html.replace("{{CIRCLE_WORD_2}}", replacements.get("{{CIRCLE_WORD_2}}", "LOST" if slide_num=="3" else "JUMP"))
    with open(f"{out_dir}/slide-0{slide_num}.html", "w") as f:
        f.write(html)

print("Generated 7 HTML slides successfully in temp/carousel-branded.")
