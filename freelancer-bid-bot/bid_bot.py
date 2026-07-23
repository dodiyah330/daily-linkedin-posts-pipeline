#!/usr/bin/env python3
"""
Freelancer.com AI bid bot.

- Polls for recently posted projects
- Generates proposal text with Google Gemini (free tier) or OpenRouter
- Bids at the midpoint of the project's budget range (configurable)
- dry_run=true by default (no live bids until you flip it)

Requires in repo-root .env:
  FLN_OAUTH_TOKEN=...
  GEMINI_API_KEY=...   (preferred)
  # or OPENROUTER_API_KEY=... as fallback
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
STATE_PATH = ROOT / "bid_state.json"
CONFIG_PATH = ROOT / "config.json"
ENV_PATH = REPO_ROOT / ".env"


def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text())


def save_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n")


def today_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def utc_now_ts() -> int:
    return int(time.time())


def get_session(oauth_token: str, url: str | None):
    from freelancersdk.session import Session

    kwargs = {"oauth_token": oauth_token}
    if url:
        kwargs["url"] = url
    return Session(**kwargs)


def get_self_user_id(session) -> int:
    from freelancersdk.resources.users import get_self_user_id

    return int(get_self_user_id(session))


def search_recent_projects(session, query: str, from_time: int, limit: int = 50):
    from freelancersdk.resources.projects.helpers import (
        create_get_projects_project_details_object,
        create_search_projects_filter,
    )
    from freelancersdk.resources.projects.projects import search_projects
    from freelancersdk.resources.projects.exceptions import ProjectsNotFoundException

    search_filter = create_search_projects_filter(
        sort_field="time_updated",
        or_search_query=True,
        from_time=from_time,
    )
    project_details = create_get_projects_project_details_object(
        full_description=True,
        jobs=True,
        upgrades=True,
    )
    try:
        result = search_projects(
            session,
            query=query,
            search_filter=search_filter,
            project_details=project_details,
            limit=limit,
            offset=0,
            active_only=True,
        )
    except ProjectsNotFoundException:
        return []

    if isinstance(result, dict):
        return result.get("projects") or result.get("result", {}).get("projects") or []
    return result or []


def project_budget_min(project: dict) -> float | None:
    """Native currency minimum (eligibility + bid pricing input)."""
    budget = project.get("budget") or {}
    minimum = budget.get("minimum")
    if minimum is None:
        return None
    try:
        return float(minimum)
    except (TypeError, ValueError):
        return None


def project_budget_max(project: dict) -> float | None:
    """Native currency maximum; falls back to minimum when absent."""
    budget = project.get("budget") or {}
    maximum = budget.get("maximum")
    if maximum is None:
        return project_budget_min(project)
    try:
        return float(maximum)
    except (TypeError, ValueError):
        return project_budget_min(project)


def project_bid_amount(project: dict, config: dict | None = None) -> float | None:
    """
    Bid amount in the project's native currency.

    bid_amount_strategy:
      - mid (default): midpoint of min/max budget
      - min: project minimum
      - max: project maximum
    """
    low = project_budget_min(project)
    if low is None:
        return None
    high = project_budget_max(project)
    if high is None:
        high = low
    if high < low:
        high = low

    strategy = ((config or {}).get("bid_amount_strategy") or "mid").lower()
    if strategy == "min":
        amount = low
    elif strategy == "max":
        amount = high
    else:
        amount = (low + high) / 2.0

    # Keep money-like precision; avoid long floats.
    return round(amount, 2)


def project_budget_min_usd(project: dict) -> float | None:
    """Minimum budget converted to USD for filter comparisons."""
    amount = project_budget_min(project)
    if amount is None:
        return None
    currency = project.get("currency") or {}
    rate = currency.get("exchange_rate")
    code = (currency.get("code") or "USD").upper()
    try:
        rate_f = float(rate) if rate is not None else 1.0
    except (TypeError, ValueError):
        rate_f = 1.0
    if code != "USD" and rate_f > 0:
        return amount * rate_f
    return amount


def project_budget_max_usd(project: dict) -> float | None:
    budget = project.get("budget") or {}
    maximum = budget.get("maximum")
    if maximum is None:
        return project_budget_min_usd(project)
    try:
        amount = float(maximum)
    except (TypeError, ValueError):
        return project_budget_min_usd(project)
    currency = project.get("currency") or {}
    rate = currency.get("exchange_rate")
    code = (currency.get("code") or "USD").upper()
    try:
        rate_f = float(rate) if rate is not None else 1.0
    except (TypeError, ValueError):
        rate_f = 1.0
    if code != "USD" and rate_f > 0:
        return amount * rate_f
    return amount


def project_is_hourly(project: dict) -> bool:
    # type: 0 fixed, 1 hourly (Freelancer API convention)
    ptype = project.get("type")
    if isinstance(ptype, str):
        return ptype.lower() in {"hourly", "1"}
    return ptype == 1


def project_age_minutes(project: dict) -> float | None:
    submitted = project.get("time_submitted") or project.get("submitdate")
    if not submitted:
        return None
    try:
        return max(0.0, (utc_now_ts() - int(submitted)) / 60.0)
    except (TypeError, ValueError):
        return None


def text_blob(project: dict) -> str:
    jobs = project.get("jobs") or []
    job_names = ", ".join(
        j.get("name", "") for j in jobs if isinstance(j, dict) and j.get("name")
    )
    parts = [
        project.get("title") or "",
        project.get("description") or project.get("preview_description") or "",
        job_names,
    ]
    return "\n".join(parts).lower()


def project_job_names(project: dict) -> list[str]:
    jobs = project.get("jobs") or []
    names = []
    for job in jobs:
        if isinstance(job, dict) and job.get("name"):
            names.append(str(job["name"]).lower())
    return names


# Map profile skills / search terms -> match aliases found in title/desc/jobs.
SKILL_ALIASES: dict[str, list[str]] = {
    "html": ["html", "html5"],
    "php": ["php"],
    "website design": ["website design", "web design", "ui design"],
    "graphic design": ["graphic design", "branding design"],
    "wordpress": ["wordpress", "wp plugin", "wp theme", "elementor"],
    "ecommerce": ["ecommerce", "e-commerce", "woocommerce", "shopify"],
    "woocommerce": ["woocommerce", "woo commerce"],
    "seo": ["seo", "search engine optimization"],
    "wordpress design": ["wordpress design", "wp design", "elementor"],
    "website development": ["website development", "web development", "web app", "website"],
    "javascript": ["javascript", "vanilla js", "js"],
    "logo design": ["logo design", "logo"],
    "branding": ["branding", "brand identity"],
    "shopify": ["shopify"],
    "shopify development": ["shopify development", "shopify store", "shopify theme", "liquid"],
    "shopify templates": ["shopify template", "shopify theme"],
    "api": ["rest api", "graphql", "apis", "api"],
    "api integration": ["api integration", "integrate api", "third-party api"],
    "api development": ["api development", "build api", "rest api"],
    "frontend development": ["frontend", "front-end", "front end"],
    "prototyping": ["prototyping", "prototype", "wireframe"],
    "automation": ["automation", "automate", "workflow automation"],
    "process automation": ["process automation", "workflow automation", "business automation"],
    "make.com": ["make.com", "integromat", "make.com scenario"],
    "zapier": ["zapier"],
    "n8n": ["n8n"],
    "photoshop": ["photoshop", "adobe photoshop", "psd"],
    "testing / qa": ["testing", "qa", "quality assurance"],
    "advertising": ["advertising", "ads", "facebook ads", "google ads"],
    "inventory management": ["inventory management", "inventory system"],
    "mysql": ["mysql", "mariadb"],
    "landing pages": ["landing page", "landing pages", "squeeze page"],
    "node.js": ["node.js", "nodejs", "node js", "express.js", "express"],
    "social media marketing": ["social media marketing", "smm"],
    "instagram": ["instagram api", "instagram bot", "instagram integration"],
    "instagram api": ["instagram api", "instagram graph api"],
    "wireframes": ["wireframe", "wireframes"],
    "json": ["json", "json api"],
    "full stack development": ["full stack", "fullstack", "full-stack"],
    "backend development": ["backend", "back-end", "server-side"],
    "figma": ["figma"],
    "figma ai": ["figma ai", "figma"],
    "elementor": ["elementor"],
    "openai": ["openai", "chatgpt", "gpt-4", "gpt-3"],
    "ai chatbot development": ["chatbot", "ai chatbot", "gpt chatbot"],
    "chatbot integration": ["chatbot integration", "chatbot", "live chat bot"],
    "ai agents": ["ai agent", "ai agents", "autonomous agent", "llm agent"],
}


def normalize_skill_key(skill: str) -> str:
    return skill.strip().lower()


def alias_in_text(text: str, alias: str) -> bool:
    a = alias.strip().lower()
    if not a:
        return False
    # Multi-word / dotted aliases: substring is fine
    if " " in a or "." in a or "-" in a:
        return a in text
    return re.search(rf"(?<![a-z0-9]){re.escape(a)}(?![a-z0-9])", text) is not None


def matched_skills(project: dict, config: dict) -> list[str]:
    blob = text_blob(project)
    job_names = project_job_names(project)
    job_blob = " | ".join(job_names)

    skill_keys = config.get("match_skills") or config.get("skills_for_ai") or []
    hits: list[str] = []
    for skill in skill_keys:
        key = normalize_skill_key(skill)
        aliases = SKILL_ALIASES.get(key, [key])
        for alias in aliases:
            if alias_in_text(blob, alias) or alias_in_text(job_blob, alias):
                hits.append(skill)
                break
    seen: set[str] = set()
    out: list[str] = []
    for h in hits:
        hk = h.lower()
        if hk not in seen:
            seen.add(hk)
            out.append(h)
    return out


def core_skill_hits(matched: list[str], config: dict) -> list[str]:
    core = [normalize_skill_key(s) for s in (config.get("core_skills") or [])]
    if not core:
        return matched
    return [s for s in matched if normalize_skill_key(s) in core]


def should_skip(project: dict, config: dict, state: dict) -> str | None:
    pid = str(project.get("id"))
    if not pid or pid == "None":
        return "missing project id"
    if pid in state.get("bid_project_ids", {}):
        return "already bid"
    if project.get("status") not in (None, "active", "open", 1, "1"):
        # Some payloads omit status when active_only=True
        status = project.get("status")
        if status not in (None, "active", "open", 1, "1"):
            return f"status={status}"

    age = project_age_minutes(project)
    max_age = float(config.get("max_project_age_minutes", 30))
    if age is not None and age > max_age:
        return f"too old ({age:.1f}m > {max_age}m)"

    if config.get("skip_hourly") and project_is_hourly(project):
        return "hourly project"

    upgrades = project.get("upgrades") or {}
    if config.get("skip_sealed") and upgrades.get("sealed"):
        return "sealed"
    if config.get("skip_nda") and upgrades.get("NDA"):
        return "NDA"
    if config.get("skip_recruiter", True) and upgrades.get("recruiter"):
        return "recruiter/preferred-only"

    amount = project_budget_min(project)
    amount_usd = project_budget_min_usd(project)
    if amount is None or amount_usd is None:
        return "no minimum budget"
    min_b = float(config.get("min_budget", 0))
    max_b = float(config.get("max_budget", 1e12))
    if amount_usd < min_b or amount_usd > max_b:
        code = ((project.get("currency") or {}).get("code") or "USD")
        return f"budget {amount} {code} (~${amount_usd:.0f}) outside [${min_b}, ${max_b}]"

    blob = text_blob(project)
    title_jobs = " ".join(
        [
            (project.get("title") or "").lower(),
            " ".join(project_job_names(project)),
        ]
    )
    # Social/media excludes: only title + job names (descriptions often mention TikTok casually).
    social_excludes = {
        "influencer",
        "instagram reel",
        "tiktok",
        "youtube short",
        "video editing",
        "voice over",
        "transcription",
    }
    for kw in config.get("exclude_keywords") or []:
        k = kw.lower()
        target = title_jobs if k in social_excludes else blob
        if alias_in_text(target, k) or (k in target and " " in k):
            return f"exclude keyword: {kw}"

    matched = matched_skills(project, config)
    min_hits = int(config.get("min_skill_hits", 2))
    min_core = int(config.get("min_core_skill_hits", 1))
    core_hits = core_skill_hits(matched, config)

    if len(core_hits) < min_core:
        return f"weak skill fit (core={core_hits or 'none'}; matched={matched or 'none'})"
    if len(matched) < min_hits:
        return f"weak skill fit (matched={matched}; need {min_hits})"

    # Stash for logging
    project["_matched_skills"] = matched
    project["_core_skills"] = core_hits
    return None


def load_portfolio_projects(config: dict) -> list[dict]:
    path = ROOT / (config.get("portfolio_projects_file") or "portfolio_projects.json")
    if path.exists():
        data = load_json(path, [])
        if isinstance(data, list):
            return [p for p in data if isinstance(p, dict)]
    return list(config.get("portfolio_projects") or [])


def infer_portfolio_categories(project: dict, config: dict) -> list[str]:
    blob = text_blob(project)
    matched = [normalize_skill_key(s) for s in (project.get("_matched_skills") or matched_skills(project, config))]
    cats: list[str] = []

    def add(cat: str):
        if cat not in cats:
            cats.append(cat)

    checks = [
        ("figma", ["figma", "logo design", "branding", "graphic design", "wireframes", "prototyping", "website design"]),
        ("shopify", ["shopify", "shopify development", "shopify templates"]),
        ("elementor", ["elementor", "wordpress design"]),
        ("wordpress", ["wordpress", "woocommerce", "website development"]),
        ("react_laravel", ["javascript", "node.js", "full stack development", "backend development", "api", "api development", "api integration", "php"]),
        ("automation", ["automation", "process automation", "make.com", "zapier", "n8n", "openai", "ai chatbot development", "chatbot integration", "ai agents", "instagram api"]),
    ]
    for cat, keys in checks:
        if any(k in matched for k in keys) or any(alias_in_text(blob, k) for k in keys):
            add(cat)

    if any(alias_in_text(blob, k) for k in ["figma", "ui/ux", "logo", "brand identity", "wireframe"]):
        add("figma")
    if alias_in_text(blob, "shopify"):
        add("shopify")
    if alias_in_text(blob, "elementor"):
        add("elementor")
    if alias_in_text(blob, "wordpress") or alias_in_text(blob, "woocommerce"):
        add("wordpress")
    if any(alias_in_text(blob, k) for k in ["laravel", "react", "next.js", "nodejs", "node.js"]):
        add("react_laravel")
    if any(alias_in_text(blob, k) for k in ["n8n", "zapier", "make.com", "automation", "chatbot", "openai"]):
        add("automation")

    if not cats:
        cats = ["wordpress", "shopify", "figma"]
    return cats


def select_portfolio_links(project: dict, config: dict) -> list[dict]:
    """Pick 1-2 relevant portfolio items (prefer items with URLs)."""
    projects = load_portfolio_projects(config)
    if not projects:
        url = (config.get("portfolio_url") or "").strip()
        return [{"title": "Freelancer profile", "url": url}] if url else []

    cats = infer_portfolio_categories(project, config)
    limit = int(config.get("portfolio_links_per_bid", 2))
    picked: list[dict] = []
    seen_urls: set[str] = set()

    def consider(item: dict):
        url = (item.get("url") or "").strip()
        title = (item.get("title") or "").strip()
        key = url or title.lower()
        if not key or key in seen_urls:
            return
        if not url:
            return
        seen_urls.add(key)
        picked.append({"title": title or url, "url": url, "category": item.get("category")})

    for cat in cats:
        for item in projects:
            if item.get("category") == cat:
                consider(item)
            if len(picked) >= limit:
                return picked[:limit]

    if len(picked) < limit:
        for item in projects:
            consider(item)
            if len(picked) >= limit:
                break

    if not picked:
        url = (config.get("portfolio_url") or "").strip()
        if url:
            picked.append({"title": "Freelancer profile", "url": url})
    return picked[:limit]


def format_portfolio_block(links: list[dict], config: dict) -> str:
    label = (config.get("portfolio_label") or "Relevant portfolio projects:").strip()
    if not links:
        url = (config.get("portfolio_url") or "").strip()
        return f"{label} {url}" if url else label
    lines = [label]
    for item in links:
        title = item.get("title") or "Project"
        url = item.get("url") or ""
        lines.append(f"- {title}: {url}" if url else f"- {title}")
    return "\n".join(lines)


def validate_proposal(text: str, config: dict, project: dict | None = None, portfolio_links: list[dict] | None = None) -> str | None:
    """Return a reason string if the proposal is incomplete/invalid, else None."""
    cleaned = (text or "").strip()
    if not cleaned:
        return "empty proposal"

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned).strip()

    min_chars = int(config.get("min_proposal_chars", 400))
    max_chars = int(config.get("max_proposal_chars", 1500))
    min_words = int(config.get("min_proposal_words", 90))

    if len(cleaned) < min_chars:
        return f"too short ({len(cleaned)} chars < {min_chars})"
    if len(cleaned) > max_chars:
        return f"too long ({len(cleaned)} chars > {max_chars})"

    words = re.findall(r"[A-Za-z0-9']+", cleaned)
    if len(words) < min_words:
        return f"too few words ({len(words)} < {min_words})"

    if not re.search(r'[.!?]"?\s*$', cleaned):
        return "does not end with complete sentence punctuation"
    if re.search(r"\b[A-Za-z]{1,2}$", cleaned):
        return "looks truncated mid-word"
    if re.search(
        r"\b(ensuring|including|implementing|providing|focusing|creating|building|using|with|and|the|to|for|of|a|an)\s+[a-z]{1,3}$",
        cleaned,
        re.I,
    ):
        return "looks truncated mid-phrase"

    if "?" not in cleaned:
        return "missing closing question to client"

    first_line = cleaned.splitlines()[0].strip().lower()
    weak_openers = (
        "hi there", "hi,", "hi!", "hello", "hello,", "hello!",
        "dear client", "dear hiring", "good day", "greetings",
        "i am writing", "i'm writing", "my name is",
    )
    if any(first_line.startswith(w) for w in weak_openers):
        return f"weak opening hook: {first_line[:40]!r}"

    links = portfolio_links or []
    required_urls = [(l.get("url") or "").strip() for l in links if (l.get("url") or "").strip()]
    fallback = (config.get("portfolio_url") or "").strip()
    if not required_urls and fallback:
        required_urls = [fallback]
    if not required_urls:
        return "portfolio links missing"
    if not any(u.lower() in cleaned.lower() for u in required_urls):
        return "missing portfolio link"

    if project:
        title = (project.get("title") or "").lower()
        stop = {
            "and", "the", "for", "with", "from", "needed", "need", "expert", "looking",
            "project", "website", "web", "app", "build", "design", "developer", "development",
            "a", "an", "to", "of", "in", "on", "or", "&", "-", "/",
        }
        stop.update({
            "site", "page", "pages", "new", "old", "full", "stack", "based", "using",
            "second", "hand", "first", "best", "simple", "basic", "quick", "small",
            "large", "complete", "professional", "modern", "custom", "create",
            "creation", "make", "type", "style",
        })
        title_terms = [t for t in re.findall(r"[a-z0-9]{4,}", title) if t not in stop][:6]
        if len(title_terms) >= 1:
            hits = sum(1 for t in title_terms if t in cleaned.lower())
            if hits < 1:
                skill_terms = [
                    normalize_skill_key(s).split()[0]
                    for s in (project.get("_core_skills") or project.get("_matched_skills") or [])
                ]
                if not any(st and st in cleaned.lower() for st in skill_terms):
                    return f"not specific enough to project title terms {title_terms}"

    if len(cleaned.splitlines()) == 1 and len(words) < 40:
        return "single short line"

    return None


def ensure_portfolio_link(text: str, config: dict, portfolio_links: list[dict] | None = None) -> str:
    """Guarantee selected portfolio URLs appear in every bid."""
    links = portfolio_links or []
    block = format_portfolio_block(links, config)
    urls = [(l.get("url") or "").strip() for l in links if (l.get("url") or "").strip()]
    if not urls:
        url = (config.get("portfolio_url") or "").strip()
        if url:
            urls = [url]
            block = format_portfolio_block([{"title": "Freelancer profile", "url": url}], config)
    if not urls:
        return text
    if any(u.lower() in text.lower() for u in urls):
        return text
    body = text.rstrip()
    m = re.search(r"^(?P<head>.*?)(?P<q>\n*[^\n]*\?\s*)$", body, re.S)
    if m:
        return f"{m.group('head').rstrip()}\n\n{block}\n\n{m.group('q').strip()}"
    return f"{body}\n\n{block}"


SYSTEM_PROMPT = (
    "You write elite Freelancer.com proposals: specific hooks, concrete plans, "
    "and always include the provided portfolio URLs exactly. "
    "Never open with Hi/Hello. Always end with a question mark."
)


def build_proposal_prompt(project: dict, config: dict, *, shorter: bool = False) -> tuple[str, list[dict], int]:
    title = project.get("title") or ""
    description = project.get("description") or project.get("preview_description") or ""
    amount = project_budget_min(project)
    skills = ", ".join(config.get("skills_for_ai") or [])
    name = config.get("your_name") or "there"
    pitch = config.get("your_pitch") or ""
    days = int(config.get("default_delivery_days", 7))
    max_chars = int(config.get("max_proposal_chars", 1500))
    portfolio_links = select_portfolio_links(project, config)
    portfolio_block = format_portfolio_block(portfolio_links, config)
    portfolio_notes = config.get("portfolio_notes") or ""

    desc_lines = [ln.strip() for ln in description.splitlines() if ln.strip()]
    key_reqs = "; ".join(desc_lines[:4])[:500]

    length_rule = (
        "110-150 words, keep under 1300 characters"
        if shorter
        else "140-220 words, keep under 1500 characters"
    )
    bid_amount = project_bid_amount(project, config) or amount
    budget_high = project_budget_max(project) or amount

    prompt = f"""Write a Freelancer.com bid proposal for THIS exact project.

Structure (mandatory):
1) HOOK (first line): a sharp, project-specific opening that references a concrete detail from the brief. Do NOT start with Hi/Hello/Dear/My name is.
2) FIT: 2-4 sentences proving you understand the scope, naming exact tools/features from the brief.
3) PLAN: 1-2 concrete next steps you would take in the first 24-48 hours.
4) PORTFOLIO: include these exact links (do not invent others):
{portfolio_block}
5) CLOSE: one short question to the client.

Rules:
- {length_rule}
- Be highly specific to the project title and requirements below
- Quote or paraphrase at least one concrete requirement (feature, stack, deliverable)
- Mention at least one portfolio project by name when natural
- Sound human and confident, not salesy
- Do not invent fake client names or fake case studies
- Do not mention AI/bot
- Do not discuss price
- Plain text only
- Finish the FULL proposal — never stop mid-sentence
{f"- Portfolio context: {portfolio_notes}" if portfolio_notes else ""}

Freelancer profile:
Name: {name}
Skills: {skills}
Pitch: {pitch}
Delivery: {days} days
Bid amount context (do not quote unless natural): {bid_amount} (budget range {amount}-{budget_high})

Project title: {title}
Key requirements excerpt: {key_reqs}

Full project description:
{description[:3500]}
"""
    return prompt, portfolio_links, max_chars


def _clean_proposal_text(text: str) -> str:
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text).strip()
    return text


def _finalize_proposal_text(
    text: str,
    config: dict,
    portfolio_links: list[dict],
    max_chars: int,
    finish_reason: str | None,
) -> tuple[str, str | None]:
    text = ensure_portfolio_link(text, config, portfolio_links)

    if len(text) > max_chars:
        reserve = "\n\n" + format_portfolio_block(portfolio_links, config) + "\n\nCan we align on scope priorities first?"
        clipped = text[: max(0, max_chars - len(reserve))].rsplit(" ", 1)[0] + reserve
        text = ensure_portfolio_link(clipped, config, portfolio_links)

    if finish_reason in {"length", "max_tokens", "MAX_TOKENS"}:
        return text, "model hit token limit (truncated)"
    return text, None


def call_gemini(prompt: str, config: dict, api_key: str, *, shorter: bool = False) -> tuple[str, str | None]:
    model = config.get("gemini_model") or "gemini-2.5-flash"
    max_tokens = int(config.get("proposal_max_tokens", 1400))
    temperature = 0.55 if shorter else 0.65
    # Disable thinking so free-tier output tokens aren't burned on internals.
    thinking_budget = int(config.get("gemini_thinking_budget", 0))
    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
            "thinkingConfig": {"thinkingBudget": thinking_budget},
        },
    }
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as res:
        data = json.loads(res.read().decode("utf-8"))

    cand = (data.get("candidates") or [{}])[0]
    finish_reason = cand.get("finishReason")
    parts = ((cand.get("content") or {}).get("parts")) or []
    # Ignore thought parts if any slip through
    text = _clean_proposal_text(
        "".join(p.get("text") or "" for p in parts if not p.get("thought"))
    )
    return text, finish_reason


def call_openrouter(prompt: str, config: dict, api_key: str, *, shorter: bool = False) -> tuple[str, str | None]:
    model = config.get("openrouter_model") or "google/gemini-2.5-flash"
    payload = {
        "model": model,
        "max_tokens": int(config.get("proposal_max_tokens", 1400)),
        "temperature": 0.55 if shorter else 0.65,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    }
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost",
            "X-Title": "freelancer-bid-bot",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as res:
        data = json.loads(res.read().decode("utf-8"))

    choice = data["choices"][0]
    finish_reason = choice.get("finish_reason") or choice.get("native_finish_reason")
    text = _clean_proposal_text((choice.get("message") or {}).get("content") or "")
    return text, finish_reason


def generate_proposal_once(
    project: dict,
    config: dict,
    ai: dict,
    *,
    shorter: bool = False,
) -> tuple[str, str | None]:
    prompt, portfolio_links, max_chars = build_proposal_prompt(project, config, shorter=shorter)
    provider = ai.get("provider") or "gemini"
    api_key = ai.get("api_key") or ""

    if provider == "gemini":
        text, finish_reason = call_gemini(prompt, config, api_key, shorter=shorter)
    else:
        text, finish_reason = call_openrouter(prompt, config, api_key, shorter=shorter)

    project["_portfolio_links"] = portfolio_links
    return _finalize_proposal_text(text, config, portfolio_links, max_chars, finish_reason)


def generate_proposal(project: dict, config: dict, ai: dict) -> str:
    """Generate a proposal and retry until validation passes or attempts exhausted."""
    if not (config.get("portfolio_url") or "").strip() and not load_portfolio_projects(config):
        raise RuntimeError("Set portfolio_url or portfolio_projects.json")

    attempts = int(config.get("proposal_retries", 3))
    last_reason = "unknown"
    last_text = ""

    for i in range(1, attempts + 1):
        text, gen_reason = generate_proposal_once(
            project,
            config,
            ai,
            shorter=(i > 1),
        )
        last_text = text
        links = project.get("_portfolio_links") or select_portfolio_links(project, config)
        reason = gen_reason or validate_proposal(text, config, project, links)
        if reason is None:
            if i > 1:
                print(f"  proposal ok on attempt {i}")
            return text
        last_reason = reason
        print(f"  proposal rejected (attempt {i}/{attempts}): {reason}")

    raise RuntimeError(f"incomplete proposal after {attempts} attempts: {last_reason}; last={last_text[:120]!r}")


def place_bid(session, project_id: int, bidder_id: int, description: str, amount: float, period: int, milestone_percentage: int):
    from freelancersdk.resources.projects import place_project_bid
    from freelancersdk.exceptions import BidNotPlacedException

    try:
        return place_project_bid(
            session,
            project_id=project_id,
            bidder_id=bidder_id,
            description=description,
            amount=amount,
            period=period,
            milestone_percentage=milestone_percentage,
        )
    except BidNotPlacedException as e:
        raise RuntimeError(f"Bid failed: {getattr(e, 'message', e)} ({getattr(e, 'error_code', '')})") from e


def record_bid(state: dict, project: dict, amount: float, dry_run: bool) -> None:
    pid = str(project["id"])
    state.setdefault("bid_project_ids", {})[pid] = {
        "title": project.get("title"),
        "amount": amount,
        "dry_run": dry_run,
        "at": datetime.now(timezone.utc).isoformat(),
    }
    day = today_key()
    counts = state.setdefault("daily_counts", {})
    counts[day] = int(counts.get(day, 0)) + 1
    save_json(STATE_PATH, state)


def record_skip(state: dict, project: dict, reason: str) -> None:
    """Remember a project we cannot/should not bid on again (does not count toward daily limit)."""
    pid = str(project["id"])
    state.setdefault("bid_project_ids", {})[pid] = {
        "title": project.get("title"),
        "skipped": True,
        "reason": reason,
        "at": datetime.now(timezone.utc).isoformat(),
    }
    save_json(STATE_PATH, state)


def daily_count(state: dict) -> int:
    return int(state.get("daily_counts", {}).get(today_key(), 0))


def wait_for_bid_slot(state: dict, config: dict) -> None:
    """Pace live bids so Freelancer doesn't reject with BID_TOO_EARLY."""
    min_gap = int(config.get("min_seconds_between_bids", 120))
    last = state.get("last_live_bid_at")
    if not last:
        return
    try:
        last_ts = datetime.fromisoformat(last).timestamp()
    except ValueError:
        return
    elapsed = time.time() - last_ts
    remaining = min_gap - elapsed
    if remaining > 0:
        print(f"  pacing: waiting {remaining:.0f}s before next live bid")
        time.sleep(remaining)


def mark_live_bid_time(state: dict) -> None:
    state["last_live_bid_at"] = datetime.now(timezone.utc).isoformat()
    save_json(STATE_PATH, state)


def project_submitted_ts(project: dict) -> int:
    submitted = project.get("time_submitted") or project.get("submitdate") or 0
    try:
        return int(submitted)
    except (TypeError, ValueError):
        return 0


def collect_eligible_projects(
    session,
    config: dict,
    state: dict,
    *,
    log_skips: bool = True,
) -> list[dict]:
    """Search all queries, filter, and return eligible projects newest-first."""
    max_age_min = float(config.get("max_project_age_minutes", 30))
    from_time = utc_now_ts() - int(max_age_min * 60)
    queries = config.get("search_queries") or ["python"]
    seen: set[str] = set()
    eligible: list[dict] = []

    for query in queries:
        try:
            projects = search_recent_projects(session, query, from_time=from_time)
        except Exception as e:
            print(f"[search error] query={query!r}: {e}")
            continue

        print(f"[search] query={query!r} found={len(projects)}")
        for project in projects:
            pid = str(project.get("id"))
            if not pid or pid in seen:
                continue
            seen.add(pid)

            reason = should_skip(project, config, state)
            if reason:
                if log_skips:
                    print(f"  skip #{pid}: {reason}")
                continue
            eligible.append(project)

    eligible.sort(key=project_submitted_ts, reverse=True)
    return eligible


def log_match(project: dict, config: dict) -> float:
    """Print match line and return bid amount."""
    pid = str(project.get("id"))
    amount = project_bid_amount(project, config)
    assert amount is not None
    budget_low = project_budget_min(project)
    budget_high = project_budget_max(project)
    title = project.get("title") or ""
    age = project_age_minutes(project)
    age_s = f"{age:.1f}m" if age is not None else "?"
    skills = ",".join(project.get("_core_skills") or project.get("_matched_skills") or [])
    range_s = (
        f"{budget_low:.2f}-{budget_high:.2f}"
        if budget_low is not None and budget_high is not None
        else "?"
    )
    print(
        f"  match #{pid} [{age_s}] bid={amount:.2f} "
        f"(budget {range_s}) skills=[{skills}] — {title[:80]}"
    )
    return amount


def try_place_live_bid(
    session,
    bidder_id: int,
    project: dict,
    proposal: str,
    amount: float,
    config: dict,
    state: dict,
) -> bool:
    """Place a live bid with retries. Returns True if placed successfully."""
    pid = str(project.get("id"))
    for attempt in range(1, 4):
        try:
            place_bid(
                session,
                project_id=int(pid),
                bidder_id=bidder_id,
                description=proposal,
                amount=amount,
                period=int(config.get("default_delivery_days", 7)),
                milestone_percentage=int(config.get("milestone_percentage", 100)),
            )
            print(f"  BID PLACED #{pid} amount={amount} chars={len(proposal)}")
            record_bid(state, project, amount, dry_run=False)
            mark_live_bid_time(state)
            return True
        except Exception as e:
            err = str(e)
            print(f"  bid error #{pid}: {err}")
            if "DUPLICATE_BID" in err or "already bid" in err.lower():
                record_bid(state, project, amount, dry_run=False)
                print(f"  marked #{pid} as already bid")
                return False
            if "UNLISTED_NOT_PREFERRED" in err or "Preferred Freelancer" in err:
                record_skip(state, project, "preferred_only")
                print(f"  marked #{pid} as preferred-only (skip forever)")
                return False
            if "SKILLS_REQUIREMENT_NOT_MET" in err or "required skills" in err.lower():
                record_skip(state, project, "skills_requirement_not_met")
                print(f"  marked #{pid} as missing required Freelancer skills")
                return False
            if "PROJECT_NOT_ACTIVE" in err or "not in an active state" in err.lower():
                record_skip(state, project, "project_not_active")
                print(f"  marked #{pid} as inactive/closed")
                return False
            if "BID_TOO_EARLY" in err or "bidding too fast" in err.lower():
                cooldown = int(config.get("bid_too_early_cooldown_seconds", 180))
                print(f"  rate limited — cooling down {cooldown}s (will retry later)")
                mark_live_bid_time(state)
                time.sleep(cooldown)
                return False
            if "Connection" in err or "ConnectionReset" in err or "timed out" in err.lower():
                if attempt < 3:
                    wait = 5 * attempt
                    print(f"  network error — retrying in {wait}s (attempt {attempt}/3)")
                    time.sleep(wait)
                    continue
                print(f"  network error — giving up on #{pid} for now")
                return False
            return False
    return False


def process_once(session, bidder_id: int, config: dict, state: dict, ai: dict) -> int:
    """
    Live flow: wait for pacing → refresh search → bid the newest eligible job.
    Dry-run: process eligible jobs newest-first without pacing.
    """
    daily_limit = int(config.get("daily_bid_limit", 20))
    placed = 0
    dry_run = bool(config.get("dry_run", True))

    if dry_run:
        eligible = collect_eligible_projects(session, config, state, log_skips=True)
        for project in eligible:
            if daily_count(state) >= daily_limit:
                print(f"[limit] daily_bid_limit reached ({daily_limit})")
                break
            pid = str(project.get("id"))
            amount = log_match(project, config)
            try:
                proposal = generate_proposal(project, config, ai)
            except Exception as e:
                print(f"  AI/validation error #{pid}: {e}")
                continue
            bad = validate_proposal(proposal, config, project, project.get("_portfolio_links"))
            if bad:
                print(f"  skip bid #{pid}: proposal failed final check ({bad})")
                continue
            print(
                f"  DRY RUN bid #{pid} amount={amount} "
                f"days={config.get('default_delivery_days', 7)} chars={len(proposal)}"
            )
            print("  --- proposal ---")
            print(proposal)
            print("  ---------------")
            record_bid(state, project, amount, dry_run=True)
            placed += 1
        return placed

    # LIVE: after each pace window, re-scan and always take the newest job.
    max_bids_this_cycle = int(config.get("max_bids_per_cycle", 5))
    soft_skip: set[str] = set()  # AI/validation failures this cycle — try next newest
    while placed < max_bids_this_cycle:
        if daily_count(state) >= daily_limit:
            print(f"[limit] daily_bid_limit reached ({daily_limit})")
            break

        wait_for_bid_slot(state, config)

        print("[refresh] picking most recently posted eligible job after pacing")
        eligible = [
            p
            for p in collect_eligible_projects(session, config, state, log_skips=True)
            if str(p.get("id")) not in soft_skip
        ]
        if not eligible:
            print("[refresh] no eligible projects right now")
            break

        project = eligible[0]
        pid = str(project.get("id"))
        amount = log_match(project, config)
        age = project_age_minutes(project)
        print(f"  selected newest #{pid} (age={age:.1f}m)" if age is not None else f"  selected newest #{pid}")

        try:
            proposal = generate_proposal(project, config, ai)
        except Exception as e:
            print(f"  AI/validation error #{pid}: {e}")
            soft_skip.add(pid)
            continue

        bad = validate_proposal(proposal, config, project, project.get("_portfolio_links"))
        if bad:
            print(f"  skip bid #{pid}: proposal failed final check ({bad})")
            soft_skip.add(pid)
            continue

        if try_place_live_bid(session, bidder_id, project, proposal, amount, config, state):
            placed += 1
        else:
            # Permanent skip already recorded, or transient failure — don't hammer same id.
            soft_skip.add(pid)
        # Whether placed or skipped, loop again (pace → newest).

    return placed


def main() -> int:
    parser = argparse.ArgumentParser(description="Freelancer.com AI bid bot")
    parser.add_argument("--once", action="store_true", help="Run a single poll cycle and exit")
    parser.add_argument("--live", action="store_true", help="Override config dry_run and place real bids")
    parser.add_argument("--dry-run", action="store_true", help="Force dry run even if config says live")
    parser.add_argument(
        "--reset-dry-run-state",
        action="store_true",
        help="Clear previous dry-run project IDs from bid_state.json before running",
    )
    args = parser.parse_args()

    env = load_env(ENV_PATH)
    # Also allow process env to override
    for k, v in os.environ.items():
        if k.startswith("FLN_") or k.startswith("OPENROUTER_") or k.startswith("GEMINI_"):
            env[k] = v

    oauth = env.get("FLN_OAUTH_TOKEN")
    gemini_key = env.get("GEMINI_API_KEY")
    openrouter_key = env.get("OPENROUTER_API_KEY")
    if not oauth:
        print("Missing FLN_OAUTH_TOKEN in .env (get it from https://developers.freelancer.com/)")
        return 1
    if gemini_key:
        ai = {"provider": "gemini", "api_key": gemini_key}
    elif openrouter_key:
        ai = {"provider": "openrouter", "api_key": openrouter_key}
    else:
        print("Missing GEMINI_API_KEY (preferred) or OPENROUTER_API_KEY in .env")
        return 1

    config = load_json(CONFIG_PATH, {})
    if args.live:
        config["dry_run"] = False
    if args.dry_run:
        config["dry_run"] = True

    state = load_json(STATE_PATH, {"bid_project_ids": {}, "daily_counts": {}})
    if args.reset_dry_run_state:
        kept = {
            pid: meta
            for pid, meta in state.get("bid_project_ids", {}).items()
            if not (isinstance(meta, dict) and meta.get("dry_run"))
        }
        removed = len(state.get("bid_project_ids", {})) - len(kept)
        state["bid_project_ids"] = kept
        # Reset today's dry-run inflated daily count when clearing dry runs
        if removed:
            state.setdefault("daily_counts", {})[today_key()] = len(
                [
                    m
                    for m in kept.values()
                    if isinstance(m, dict) and str(m.get("at", "")).startswith(today_key())
                ]
            )
            save_json(STATE_PATH, state)
            print(f"Cleared {removed} dry-run state entries")

    session = get_session(oauth, env.get("FLN_URL"))
    bidder_id = get_self_user_id(session)

    mode = "DRY RUN" if config.get("dry_run", True) else "LIVE"
    model_name = (
        (config.get("gemini_model") or "gemini-2.5-flash")
        if ai["provider"] == "gemini"
        else (config.get("openrouter_model") or "google/gemini-2.5-flash")
    )
    print(f"Freelancer bid bot started ({mode})")
    print(f"ai={ai['provider']}:{model_name}")
    print(f"user_id={bidder_id} max_age={config.get('max_project_age_minutes')}m "
          f"daily_limit={config.get('daily_bid_limit')} queries={config.get('search_queries')}")

    while True:
        try:
            placed = process_once(session, bidder_id, config, state, ai)
            print(f"[cycle] placed_or_queued={placed} daily={daily_count(state)}")
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            print(f"[http error] {e.code}: {body[:500]}")
        except Exception as e:
            print(f"[cycle error] {e}")

        if args.once:
            break
        time.sleep(int(config.get("poll_interval_seconds", 60)))

    return 0


if __name__ == "__main__":
    sys.exit(main())
