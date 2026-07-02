import os
import re

def main():
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

    # Use Claude Salmon/Bronze color
    color = "#D9785B"

    data = {
        "1": (t1, {
            "{{BRAND_COLOR}}": color,
            "{{HEADER_LABEL}}": "MODEL LAUNCH",
            "{{HOOK_PART_1}}": "Anthropic's new model",
            "{{HOOK_PART_2}}": "has one",
            "{{HOOK_EMPHASIS}}": "catch",
            "{{SUBTITLE}}": "Claude Fable 5 is Anthropic's most capable model, but it includes safety routing."
        }),
        "2": (t2, {
            "{{BRAND_COLOR}}": color,
            "{{PILL_LABEL}}": "THE LAUNCH",
            "{{SLIDE_NUM}}": "02",
            "{{EYEBROW}}": "CLAUDE FABLE 5",
            "{{HEADLINE_PART_1}}": "Anthropic introduces its",
            "{{HEADLINE_PART_2}}": "first Mythos class",
            "{{HEADLINE_EMPHASIS}}": "model",
            "{{SUBHEAD}}": "Built for long-horizon agentic tasks.",
            "{{BODY_TEXT}}": "It is Anthropic's most capable model, designed for multi-day autonomous sessions."
        }),
        "3": (t3, {
            "{{BRAND_COLOR}}": color,
            "{{HEADER_LABEL}}": "THE SPECS",
            "{{SLIDE_NUM}}": "03",
            "{{HUGE_STAT}}": "128k",
            "{{CIRCLE_WORD_1}}": "OUTPUT",
            "{{CIRCLE_WORD_2}}": "TOKENS",
            "{{HEADLINE_PART_1}}": "A massive window for",
            "{{HEADLINE_PART_2}}": "large codebase",
            "{{HEADLINE_EMPHASIS}}": "migrations",
            "{{BODY_TEXT}}": "The 1 million token context allows developers to run codebase migrations in one go."
        }),
        "4": (t2, {
            "{{BRAND_COLOR}}": color,
            "{{PILL_LABEL}}": "AGENTIC WORKFLOWS",
            "{{SLIDE_NUM}}": "04",
            "{{EYEBROW}}": "AGENT INFRASTRUCTURE",
            "{{HEADLINE_PART_1}}": "Designed to run complex",
            "{{HEADLINE_PART_2}}": "autonomous multi-agent",
            "{{HEADLINE_EMPHASIS}}": "squads",
            "{{SUBHEAD}}": "Sub-agents collaborate, plan, and verify tasks.",
            "{{BODY_TEXT}}": "This helps teams deploy agents that work for days without looping or losing state."
        }),
        "5": (t3, {
            "{{BRAND_COLOR}}": color,
            "{{HEADER_LABEL}}": "THE SAFEGUARDS",
            "{{SLIDE_NUM}}": "05",
            "{{HUGE_STAT}}": "4.8",
            "{{CIRCLE_WORD_1}}": "OPUS",
            "{{CIRCLE_WORD_2}}": "FALLBACK",
            "{{HEADLINE_PART_1}}": "Automatic routing for",
            "{{HEADLINE_PART_2}}": "sensitive security",
            "{{HEADLINE_EMPHASIS}}": "requests",
            "{{BODY_TEXT}}": "High-risk queries automatically fall back to the safety-vetted Opus 4.8 model."
        }),
        "6": (t6, {
            "{{BRAND_COLOR}}": color,
            "{{HEADER_LABEL}}": "PROJECT GLASSWING",
            "{{HUGE_STAT}}": "150+",
            "{{HEADLINE_PART_1}}": "Vetted partners get",
            "{{HEADLINE_PART_2}}": "unrestricted access to",
            "{{HEADLINE_EMPHASIS}}": "Mythos 5",
            "{{SUBHEAD}}": "Securing critical software infrastructure.",
            "{{BODY_TEXT}}": "Defenders use the unrestricted Mythos 5 to scan for critical software flaws."
        }),
        "7": (t7, {
            "{{BRAND_COLOR}}": color,
            "{{HEADLINE_PART_1}}": "Understand the model limits.",
            "{{HEADLINE_PART_2}}": "Build safer agent",
            "{{HEADLINE_EMPHASIS}}": "networks",
            "{{SUBHEAD}}": "Fable 5 shifts AI to long-running systems. Follow for daily framework updates."
        })
    }

    for slide_num, (template, replacements) in data.items():
        html = template
        for k, v in replacements.items():
            html = html.replace(k, v)
        # Ensure images use relative assets/ path
        # In slide 4, replace template 2's assets/interface.png with assets/hero-ui.png or similar
        # Actually slide 4 in template 2 has <img src="assets/interface.png" class="top-image" onerror="this.style.display='none'"/>
        # Let's verify and keep it as assets/interface.png since we copied interface image there
        with open(f"{out_dir}/slide-0{slide_num}.html", "w") as f:
            f.write(html)

    print("Generated 7 HTML slides successfully in temp/carousel-branded.")

if __name__ == "__main__":
    main()
