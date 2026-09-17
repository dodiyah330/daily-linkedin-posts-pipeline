#!/usr/bin/env python3
"""Check / exchange Facebook Page tokens for BookWellNow posting.

  python3 facebook_page_auth.py              # validate FACEBOOK_PAGE_ACCESS_TOKEN
  python3 facebook_page_auth.py pages        # list pages on a user token
  python3 facebook_page_auth.py exchange     # short-lived user token → long-lived Page token

Development-mode apps can post to Pages you admin without App Review.
"""
from __future__ import annotations

import os
import sys

from facebook_graph import (
    BASE,
    exchange_long_lived_user_token,
    graph_request,
    list_managed_pages,
    load_dotenv,
    page_identity,
)

os.chdir(BASE)
load_dotenv()

PAGE_HINTS = ("bookwellnow", "book well now", "book-well-now")


def token_from_env() -> str:
    for key in (
        "FACEBOOK_PAGE_ACCESS_TOKEN",
        "FACEBOOK_USER_ACCESS_TOKEN",
        "FACEBOOK_ACCESS_TOKEN",
    ):
        value = os.environ.get(key, "").strip()
        if value:
            return value
    sys.exit(
        "No Facebook token in .env. Add FACEBOOK_PAGE_ACCESS_TOKEN "
        "(see docs/API_KEYS.md § Facebook)."
    )


def is_bookwellnow(page: dict) -> bool:
    blob = f"{page.get('name', '')} {page.get('id', '')} {page.get('link', '')}".lower()
    return any(h in blob for h in PAGE_HINTS)


def cmd_check() -> None:
    token = token_from_env()
    ident = page_identity(token)
    print("Token is valid.")
    print(f"  id:        {ident.get('id')}")
    print(f"  name:      {ident.get('name')}")
    print(f"  link:      {ident.get('link')}")
    if ident.get("fan_count") is not None:
        print(f"  followers: {ident.get('fan_count')}")
    name = str(ident.get("name") or "")
    if "bookwellnow" not in name.lower().replace(" ", ""):
        print(
            "\nThis token is not the BookWellNow page. If this is a USER token, run:\n"
            "  python3 facebook_page_auth.py pages"
        )
    else:
        print("\nThis looks like the BookWellNow Page token. Ready to schedule.")
        print("Put this in .env if missing:")
        print(f"  FACEBOOK_PAGE_ID={ident.get('id')}")


def cmd_pages() -> None:
    token = os.environ.get("FACEBOOK_USER_ACCESS_TOKEN", "").strip() or token_from_env()
    pages = list_managed_pages(token)
    if not pages:
        sys.exit(
            "No Pages returned. The token needs pages_show_list, and you must be "
            "a Page admin. In Graph API Explorer, grant pages_show_list, "
            "pages_manage_posts, pages_read_engagement, then GET /me/accounts."
        )
    print(f"{len(pages)} Page(s):")
    match = None
    for page in pages:
        mark = ""
        if is_bookwellnow(page):
            mark = "  ← BookWellNow"
            match = page
        print(f"  {page.get('id')}  {page.get('name')}{mark}")
    if match:
        print("\nAdd these to .env (do not commit):")
        print(f"  FACEBOOK_PAGE_ID={match.get('id')}")
        print(f"  FACEBOOK_PAGE_ACCESS_TOKEN={match.get('access_token')}")
    else:
        print("\nNo Page name matched BookWellNow. Copy the correct page token from above.")


def cmd_exchange() -> None:
    app_id = os.environ.get("FACEBOOK_APP_ID", "").strip()
    app_secret = os.environ.get("FACEBOOK_APP_SECRET", "").strip()
    short = (
        os.environ.get("FACEBOOK_USER_ACCESS_TOKEN", "").strip()
        or os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN", "").strip()
    )
    if not (app_id and app_secret and short):
        sys.exit(
            "exchange needs FACEBOOK_APP_ID, FACEBOOK_APP_SECRET, and "
            "FACEBOOK_USER_ACCESS_TOKEN (short-lived user token from Graph API Explorer)."
        )
    exchanged = exchange_long_lived_user_token(short, app_id, app_secret)
    long_user = exchanged.get("access_token")
    if not long_user:
        sys.exit(f"exchange failed: {exchanged}")
    expires = exchanged.get("expires_in")
    print(f"Long-lived USER token ok (expires_in={expires} seconds). Fetching pages…")
    pages = list_managed_pages(long_user)
    match = next((p for p in pages if is_bookwellnow(p)), pages[0] if pages else None)
    if not match:
        sys.exit("No managed Pages on this user token.")
    debug = graph_request(
        "GET",
        "/debug_token",
        {"input_token": match["access_token"], "access_token": f"{app_id}|{app_secret}"},
    )
    info = (debug.get("data") or {})
    print(f"Page: {match.get('name')} ({match.get('id')})")
    print(f"  token type: {info.get('type')}  expires_at={info.get('expires_at') or 'never'}")
    print("\nAdd these to .env (do not commit):")
    print(f"  FACEBOOK_PAGE_ID={match.get('id')}")
    print(f"  FACEBOOK_PAGE_ACCESS_TOKEN={match.get('access_token')}")


def main() -> None:
    cmd = (sys.argv[1] if len(sys.argv) > 1 else "check").lower()
    if cmd in {"check", "whoami"}:
        cmd_check()
    elif cmd in {"pages", "list"}:
        cmd_pages()
    elif cmd in {"exchange", "longlived"}:
        cmd_exchange()
    else:
        sys.exit("Usage: python3 facebook_page_auth.py [check|pages|exchange]")


if __name__ == "__main__":
    main()
