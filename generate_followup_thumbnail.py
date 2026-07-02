import os
import re

skill_path = "./skills/branded-carousel/SKILL.md"
with open(skill_path, "r") as f:
    content = f.read()

# Extract Template 1
t1 = re.search(r"TEMPLATE 1.*?```html(.*?)```", content, re.DOTALL).group(1)

out_dir = "./carousel-routine/temp/carousel-branded"
os.makedirs(out_dir, exist_ok=True)

color = "#5E6AD2"  # Linear Purple

# Follow-up cover content
replacements = {
    "{{BRAND_COLOR}}": color,
    "{{HEADER_LABEL}}": "STARTUP INERTIA",
    "{{HOOK_PART_1}}": "How Indian founders",
    "{{HOOK_PART_2}}": "can actually",
    "{{HOOK_EMPHASIS}}": "start",
    "{{SUBTITLE}}": "3 rules to break the analysis paralysis loop, launch your crude MVP, and secure your first paying customer in 7 days."
}

html = t1
for k, v in replacements.items():
    html = html.replace(k, v)

# Save as slide-followup.html
with open(f"{out_dir}/slide-followup.html", "w") as f:
    f.write(html)

print("Generated follow-up HTML cover slide.")
