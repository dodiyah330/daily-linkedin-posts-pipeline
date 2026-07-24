#!/usr/bin/env python3
"""Build July remaining-days schedule: 2 posts/day (WordPress + AI) at 12:00 AM / 12:30 AM, with images + hashtags."""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent
OUT_DIR = BASE / "post-assets" / "july-wp-ai"
OUT_DIR.mkdir(parents=True, exist_ok=True)

WP_HASHTAGS = "#WordPress #WooCommerce #Elementor #WebDevelopment #WebsiteDesign #PHP #eCommerce #Freelancer"
AI_HASHTAGS = "#AI #ArtificialIntelligence #Automation #MachineLearning #ChatGPT #AIAgents #Productivity #Tech"

WP_TOPICS = [
    ("Stop stacking plugins", "More WordPress plugins is not more capability. It is more risk.\n\nEvery extra plugin is another update path, another conflict, another support ticket. The sites that stay calm are the ones with a short, intentional stack and clear ownership of what each piece does.\n\nAudit your plugin list this week. If you cannot explain why a plugin exists, remove it."),
    ("WooCommerce checkout friction", "Your WooCommerce store does not lose sales at the product page. It loses them at checkout.\n\nToo many fields. Surprise shipping. Weak trust signals. Guests forced into accounts. Fix those and revenue often moves before ads do.\n\nWhat is the one checkout step your buyers complain about most?"),
    ("Elementor without bloat", "Elementor is powerful. Uncontrolled Elementor is a performance tax.\n\nReuse global styles. Limit nested sections. Compress media. Turn off widgets you never use. A clean Elementor build can look premium without feeling sluggish.\n\nPretty pages that bounce are not a design win."),
    ("Security is a product feature", "WordPress security is not an afterthought for 'later'.\n\nUpdates, least-privilege users, hardened login, backups you can actually restore. Clients do not celebrate security until something breaks. Then it is the only thing that matters.\n\nWhen did you last test a full restore, not just a backup export?"),
    ("Content architecture beats theme hopping", "Switching WordPress themes will not fix unclear offers.\n\nMap pages to buyer questions. Make the next step obvious. Keep forms short. Theme changes are expensive distractions when the message is still fuzzy.\n\nClarity converts. Themes decorate."),
    ("Custom fields with purpose", "Custom post types and ACF fields are useful when they match real workflows.\n\nIf editors still dump everything into the page builder, your data model failed. Build fields editors actually fill, then render them cleanly on the front end.\n\nStructure is what makes WordPress scale past one marketer."),
    ("Maintenance is the product", "A WordPress launch is not the finish line.\n\nUpdates, monitoring, uptime checks, form tests, and content QA keep sites earning. Most 'mysterious' breakage is skipped maintenance catching up.\n\nIf nobody owns monthly care, the site is already decaying."),
]

AI_TOPICS = [
    ("Judgment stays human", "AI can draft. It cannot own the call.\n\nThe teams winning with AI treat models like fast juniors: useful drafts, mandatory review, clear ownership. Confidence without checking is how bad answers become company policy.\n\nWhere do you still require a human sign-off?"),
    ("Agents need guardrails", "AI agents that can click, send, and edit files are powerful and dangerous.\n\nGive them narrow scopes, audit logs, and approval gates for anything customer-facing. Speed is worthless if one bad action creates cleanup for a week.\n\nWhat is the first task you would never let an agent do alone?"),
    ("Prompting is a skill, not magic", "Better prompts are clearer briefs.\n\nRole, context, constraints, examples, output format. That is the whole game. Vague asks produce vague work, with or without AI.\n\nWrite the brief you would give a sharp contractor. Then hand it to the model."),
    ("Automate the boring layer", "The best AI ROI is usually boring.\n\nClassify tickets. Summarize calls. Enrich leads. Draft first replies. Route work. Leave strategy and taste to people.\n\nWhich boring weekly task would free the most hours if it disappeared?"),
    ("Data quality beats model hype", "A stronger model will not save dirty CRM fields.\n\nIf names, stages, and notes are inconsistent, every AI summary inherits the mess. Clean inputs first. Then automation looks smart.\n\nYour model is only as good as your last form field."),
    ("Local vs cloud AI tradeoffs", "Cloud AI is convenient. Local AI is private and controllable.\n\nSensitive docs, regulated industries, and internal IP often belong behind your own walls. Public chat is fine for non-sensitive drafting.\n\nWhat data should never leave your environment?"),
    ("Ship one AI win this month", "Do not build an AI roadmap of twenty ideas.\n\nPick one painful workflow. Instrument it. Ship a thin automation. Show a before/after in hours saved. Momentum beats strategy decks.\n\nWhat is the one AI win you will finish this month?"),
]


def font(size: int):
    for name in ("arial.ttf", "C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/segoeui.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    return ImageFont.load_default()


def make_image(path: Path, kind: str, title: str, subtitle: str) -> None:
    W, H = 1200, 1500
    if kind == "wordpress":
        top, mid, accent = (15, 23, 42), (30, 58, 138), (56, 189, 248)
        badge = "WORDPRESS"
    else:
        top, mid, accent = (17, 24, 39), (88, 28, 135), (216, 180, 254)
        badge = "AI"

    img = Image.new("RGB", (W, H), top)
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        r = int(top[0] + (mid[0] - top[0]) * t)
        g = int(top[1] + (mid[1] - top[1]) * t)
        b = int(top[2] + (mid[2] - top[2]) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    draw.rounded_rectangle([70, 120, W - 70, 420], radius=32, fill=(15, 23, 42), outline=accent, width=4)
    draw.rounded_rectangle([110, 170, 420, 250], radius=18, fill=accent)
    draw.text((140, 188), badge, fill=(15, 23, 42), font=font(36))

    # wrap title
    title_font = font(58)
    words = title.upper().split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=title_font) < W - 180:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    y = 520
    for line in lines[:4]:
        draw.text((90, y), line, fill=(248, 250, 252), font=title_font)
        y += 72

    sub_font = font(36)
    y += 30
    for line in subtitle.split("\n")[:4]:
        draw.text((90, y), line, fill=(203, 213, 225), font=sub_font)
        y += 52

    draw.rounded_rectangle([90, 1280, 620, 1360], radius=20, fill=accent)
    tag = "#WordPress" if kind == "wordpress" else "#AI"
    draw.text((130, 1302), f"{tag}  ·  LinkedIn", fill=(15, 23, 42), font=font(30))
    img.save(path, "PNG")


def build() -> Path:
    today = date(2026, 7, 23)
    start = today + timedelta(days=1)  # Jul 24
    end = date(2026, 7, 31)
    posts = []
    pid = 1
    day_i = 0
    d = start
    while d <= end:
        wp_title, wp_body = WP_TOPICS[day_i % len(WP_TOPICS)]
        ai_title, ai_body = AI_TOPICS[day_i % len(AI_TOPICS)]
        date_str = d.strftime("%m/%d/%Y")

        wp_img = OUT_DIR / f"wp-{d.isoformat()}.png"
        ai_img = OUT_DIR / f"ai-{d.isoformat()}.png"
        make_image(wp_img, "wordpress", wp_title, "Practical WordPress advice\nfor real client sites.")
        make_image(ai_img, "ai", ai_title, "Practical AI advice\nfor real workflows.")

        posts.append(
            {
                "id": pid,
                "type": "infographic",
                "date": date_str,
                "time": "12:00 AM",
                "stream": "wordpress",
                "title": wp_title,
                "caption": f"{wp_body}\n\nFollow me for practical WordPress builds.\n\n{WP_HASHTAGS}",
                "assetPath": str(wp_img.resolve()),
            }
        )
        pid += 1
        posts.append(
            {
                "id": pid,
                "type": "infographic",
                "date": date_str,
                "time": "12:30 AM",
                "stream": "ai",
                "title": ai_title,
                "caption": f"{ai_body}\n\nFollow me for practical AI workflows.\n\n{AI_HASHTAGS}",
                "assetPath": str(ai_img.resolve()),
            }
        )
        pid += 1
        day_i += 1
        d += timedelta(days=1)

    schedule = {
        "posts": posts,
        "meta": {
            "month": "2026-07",
            "note": "Remaining July days: 2 posts/day (WordPress 12:00 AM, AI 12:30 AM), image + hashtags",
        },
    }
    out = BASE / "schedule_july_wp_ai.json"
    out.write_text(json.dumps(schedule, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out} with {len(posts)} posts")
    print(f"Images in {OUT_DIR}")
    return out


if __name__ == "__main__":
    build()
