#!/usr/bin/env python3
"""Canonical BookWellNow URLs with channel UTMs.

utm_source is exactly "facebook post" or "linkedin post" so Analytics can split them.
"""
from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

SITE = "https://bookwellnow.com/"
DOCS = "https://bookwellnow.com/docs/getting-started/installing/"
WPORG = "https://wordpress.org/plugins/bookwellnow-appointment-booking/"

UTM_SOURCE = {
    "facebook": "facebook post",
    "linkedin": "linkedin post",
}


def site_url(channel: str) -> str:
    return with_utm(SITE, channel)


def docs_url(channel: str) -> str:
    return with_utm(DOCS, channel)


def wporg_url(channel: str) -> str:
    return with_utm(WPORG, channel)


def with_utm(url: str, channel: str) -> str:
    source = UTM_SOURCE.get(channel, channel)
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["utm_source"] = source
    path = parsed.path or "/"
    return urlunparse(
        (parsed.scheme or "https", parsed.netloc, path, parsed.params, urlencode(query), parsed.fragment)
    )


def inject_utm_in_text(text: str, channel: str) -> str:
    """Rewrite every bookwellnow.com / wordpress.org plugin URL to carry utm_source."""

    def repl(match: re.Match) -> str:
        url = match.group(0).rstrip(").,")
        return with_utm(url, channel)

    text = re.sub(r"https?://(?:www\.)?bookwellnow\.com[^\s)\]>]*", repl, text or "")
    text = re.sub(
        r"https?://(?:www\.)?wordpress\.org/plugins/bookwellnow-appointment-booking/?[^\s)\]>]*",
        repl,
        text,
    )
    return text


def ensure_tracked_footer(text: str, channel: str, hiring: bool = False) -> str:
    t = inject_utm_in_text((text or "").strip(), channel)
    if hiring:
        return t
    if "bookwellnow.com" not in t.lower():
        t = (t + f"\n\nStart free: {site_url(channel)}").strip()
    elif "utm_source=" not in t.lower():
        t = inject_utm_in_text(t, channel)
    return t
