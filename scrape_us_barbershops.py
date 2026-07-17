#!/usr/bin/env python3
"""Scrape qualified US barbershop leads city-wise and export an Excel sheet.

Columns: Name, Shop Name, Website, Location, Email
Qualified = Barber shop + open + real website + valid business email + US location.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
from apify_client import ApifyClient

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "prospects" / "barbershops"
RAW_PATH = OUT_DIR / "raw_places.json"
SHEET_PATH = OUT_DIR / "us_barbershops_qualified.xlsx"
CSV_PATH = OUT_DIR / "us_barbershops_qualified.csv"

CITIES = [
    ("New York, NY, USA", 40),
    ("Los Angeles, CA, USA", 40),
    ("Chicago, IL, USA", 40),
    ("Houston, TX, USA", 40),
    ("Miami, FL, USA", 35),
    ("Atlanta, GA, USA", 35),
    ("Dallas, TX, USA", 35),
    ("Phoenix, AZ, USA", 35),
    ("Philadelphia, PA, USA", 35),
    ("Seattle, WA, USA", 35),
    ("Austin, TX, USA", 30),
    ("Denver, CO, USA", 30),
]

JUNK_EMAIL_DOMAINS = {
    "example.com",
    "domain.com",
    "email.com",
    "sentry.io",
    "wixpress.com",
    "wix.com",
    "squarespace.com",
    "shopify.com",
    "godaddy.com",
    "cloudflare.com",
    "googleapis.com",
    "gstatic.com",
    "schema.org",
    "sentry-next.wixpress.com",
    "jquery.com",
    "yourdomain.com",
    "test.com",
    "mailinator.com",
    "ezoic.com",
    "locmaps.com",
    "vagaro.com",
    "booksy.com",
    "squareup.com",
    "square.site",
    "styleseat.com",
    "fresha.com",
    "schedulicity.com",
    "setmore.com",
    "calendly.com",
    "iboostweb.com",
    "sportclips.com",
    "greatclips.com",
    "supercuts.com",
}

JUNK_EMAIL_DOMAIN_SUFFIXES = (
    "wixpress.com",
    "sentry.io",
    "amazonaws.com",
    "cloudfront.net",
    "googleusercontent.com",
)

CHAIN_NAME_MARKERS = (
    "floyd's 99",
    "floyds 99",
    "sport clips",
    "great clips",
    "supercuts",
    "sports clips",
)

JUNK_EMAIL_LOCAL = {
    "example",
    "email",
    "name",
    "user",
    "username",
    "you",
    "yourname",
    "noreply",
    "no-reply",
    "donotreply",
}

SOCIAL_HOSTS = {
    "instagram.com",
    "facebook.com",
    "fb.com",
    "twitter.com",
    "x.com",
    "tiktok.com",
    "youtube.com",
    "yelp.com",
    "linktr.ee",
    "linktree.com",
    "maps.google.com",
    "goo.gl",
    "booksy.com",
    "vagaro.com",
    "styleseat.com",
    "fresha.com",
    "squareup.com",
    "square.site",
    "getsqr.co",
    "poi.place",
}


def load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    for line in (ROOT / ".env").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip()
    return env


def is_real_website(url: str | None) -> bool:
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        return False
    host = urlparse(url).netloc.lower().removeprefix("www.")
    if not host:
        return False
    return not any(host == s or host.endswith("." + s) for s in SOCIAL_HOSTS)


def clean_emails(emails) -> list[str]:
    if not emails:
        return []
    if isinstance(emails, str):
        emails = [emails]
    out: list[str] = []
    for raw in emails:
        if not raw or not isinstance(raw, str):
            continue
        email = raw.strip().lower().rstrip(".,;")
        if not re.match(r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$", email):
            continue
        local, _, domain = email.partition("@")
        if domain in JUNK_EMAIL_DOMAINS or local in JUNK_EMAIL_LOCAL:
            continue
        if any(domain == s or domain.endswith("." + s) for s in JUNK_EMAIL_DOMAIN_SUFFIXES):
            continue
        if any(domain == d or domain.endswith("." + d) for d in JUNK_EMAIL_DOMAINS):
            continue
        if any(x in email for x in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".avif", ".woff")):
            continue
        if len(local) > 40 and local.replace("-", "").isalnum():
            # Likely hashed tracker addresses
            continue
        # Template / placeholder / designer theme emails
        if domain in {
            "perceny.com",
            "mystore.com",
            "amazon.com",
            "doe.com",
            "indiantypefoundry.com",
            "micahrich.com",
            "samba.com",
            "rfuenzalida.com",
            "emailprovider.com",
            "sentry.wixpress.com",
        }:
            continue
        if local in {"bezos", "john.doe", "jane.doe", "firstname", "lastname", "test"}:
            continue
        if email not in out:
            out.append(email)
    return out


def infer_name(shop_name: str, email: str) -> str:
    """Best-effort contact/owner name from possessive shop titles or email local-part."""
    shop = (shop_name or "").strip()
    # Avoid false possessives like Men's, People's, Children's
    m = re.match(
        r"^([A-Za-z][A-Za-z'’\-\.]+(?:\s+[A-Za-z][A-Za-z'’\-\.]+)?)\s*'s\b",
        shop,
        re.I,
    )
    if m:
        candidate = m.group(1).replace("’", "'").strip()
        if candidate.lower() not in {"men", "women", "people", "children", "kid", "kids"}:
            return candidate

    local = email.split("@", 1)[0]
    if email.endswith(("@gmail.com", "@yahoo.com", "@icloud.com", "@outlook.com", "@hotmail.com", "@aol.com", "@me.com")):
        parts = re.split(r"[._+\-]+", local)
        parts = [p for p in parts if p.isalpha() and len(p) > 1]
        if 1 <= len(parts) <= 3:
            return " ".join(p.capitalize() for p in parts[:2])

    return shop


def is_barber(item: dict) -> bool:
    cats = []
    if item.get("categoryName"):
        cats.append(str(item["categoryName"]))
    cats.extend(str(c) for c in (item.get("categories") or []))
    blob = " | ".join(cats).lower()
    return "barber" in blob


def location_str(item: dict, search_city: str) -> str:
    address = (item.get("address") or "").strip()
    if address:
        return address
    city = (item.get("city") or "").strip()
    state = (item.get("state") or "").strip()
    if city and state:
        return f"{city}, {state}, USA"
    return search_city


def qualify(item: dict, search_city: str) -> dict | None:
    if not is_barber(item):
        return None
    if item.get("permanentlyClosed") or item.get("temporarilyClosed"):
        return None

    website = item.get("website")
    if not is_real_website(website):
        return None

    emails = clean_emails(item.get("emails"))
    if not emails:
        return None

    shop = (item.get("title") or "").strip()
    if not shop:
        return None
    if any(m in shop.lower() for m in CHAIN_NAME_MARKERS):
        return None

    email = emails[0]
    score = item.get("totalScore")
    reviews = item.get("reviewsCount") or 0
    # Prefer established shops; allow unknown scores but drop clearly weak ones.
    if score is not None and score < 3.5 and reviews >= 10:
        return None

    return {
        "Name": infer_name(shop, email),
        "Shop Name": shop,
        "Website": website,
        "Location": location_str(item, search_city),
        "Email": email,
        "City": item.get("city") or search_city.split(",")[0],
        "State": item.get("state") or "",
        "Phone": item.get("phone") or "",
        "Rating": score if score is not None else "",
        "Reviews": reviews,
        "Category": item.get("categoryName") or "",
        "All Emails": "; ".join(emails),
        "Search City": search_city,
        "Place ID": item.get("placeId") or item.get("place_id") or "",
    }


def run_city(client: ApifyClient, city: str, max_places: int) -> tuple[str, list[dict], str | None]:
    run_input = {
        "searchStringsArray": ["barbershop"],
        "locationQuery": city,
        "maxCrawledPlacesPerSearch": max_places,
        "language": "en",
        "countryCode": "us",
        "website": "withWebsite",
        "skipClosedPlaces": True,
        "placeMinimumStars": "three",
        "categoryFilterWords": ["barber shop"],
    }
    try:
        run = client.actor("lukaskrivka/google-maps-with-contact-details").start(
            run_input=run_input,
        )
        run_id = run.id if hasattr(run, "id") else run["id"]
        # Poll until finished
        while True:
            info = client.run(run_id).get()
            status = info.status if hasattr(info, "status") else info["status"]
            if status in {"SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"}:
                break
            time.sleep(8)
        if status != "SUCCEEDED":
            return city, [], f"run {run_id} ended with {status}"
        ds = (
            info.default_dataset_id
            if hasattr(info, "default_dataset_id")
            else info.get("defaultDatasetId")
        )
        items = list(client.dataset(ds).iterate_items())
        for item in items:
            item["_search_city"] = city
        return city, items, None
    except Exception as exc:  # noqa: BLE001
        return city, [], str(exc)


def balance_by_city(rows: list[dict], target: int) -> list[dict]:
    """Take ~even rows per city until target is met."""
    by_city: dict[str, list[dict]] = {}
    for row in rows:
        by_city.setdefault(row["Search City"], []).append(row)

    # Prefer higher-reviewed shops within each city
    for city_rows in by_city.values():
        city_rows.sort(key=lambda r: (r.get("Reviews") or 0, r.get("Rating") or 0), reverse=True)

    selected: list[dict] = []
    seen_emails: set[str] = set()
    seen_shops: set[str] = set()
    cities = list(by_city.keys())
    idx = 0
    while len(selected) < target and any(by_city[c] for c in cities):
        city = cities[idx % len(cities)]
        idx += 1
        bucket = by_city[city]
        if not bucket:
            continue
        row = bucket.pop(0)
        email_key = row["Email"].lower()
        shop_key = row["Shop Name"].strip().lower()
        if email_key in seen_emails or shop_key in seen_shops:
            continue
        seen_emails.add(email_key)
        seen_shops.add(shop_key)
        selected.append(row)
    return selected


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape US barbershop leads")
    parser.add_argument("--target", type=int, default=100, help="Qualified rows to keep")
    parser.add_argument("--workers", type=int, default=4, help="Parallel Apify city runs")
    parser.add_argument(
        "--reuse-raw",
        action="store_true",
        help="Reuse existing raw_places.json instead of scraping",
    )
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    env = load_env()
    token = env.get("APIFY_API_KEY")
    if not token:
        raise SystemExit("APIFY_API_KEY missing in .env")

    if args.reuse_raw and RAW_PATH.exists():
        raw_items = json.loads(RAW_PATH.read_text())
        print(f"Reusing {len(raw_items)} raw places from {RAW_PATH}")
    else:
        client = ApifyClient(token)
        raw_items: list[dict] = []
        print(f"Starting city-wise scrape across {len(CITIES)} cities (workers={args.workers})...")
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {
                pool.submit(run_city, client, city, max_places): city
                for city, max_places in CITIES
            }
            for fut in as_completed(futures):
                city, items, err = fut.result()
                if err:
                    print(f"  ✗ {city}: {err}")
                else:
                    with_email = sum(1 for i in items if clean_emails(i.get("emails")))
                    print(f"  ✓ {city}: {len(items)} places, {with_email} with email")
                    raw_items.extend(items)

        RAW_PATH.write_text(json.dumps(raw_items, indent=2))
        print(f"Saved raw places → {RAW_PATH}")

    qualified: list[dict] = []
    for item in raw_items:
        row = qualify(item, item.get("_search_city") or "")
        if row:
            qualified.append(row)

    # Deduplicate before balancing
    deduped: list[dict] = []
    seen: set[str] = set()
    for row in qualified:
        key = row["Email"].lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)

    print(f"Qualified before balance: {len(deduped)}")
    final_rows = balance_by_city(deduped, args.target)
    print(f"Final selected: {len(final_rows)}")

    export_cols = ["Name", "Shop Name", "Website", "Location", "Email"]
    extra_cols = ["City", "State", "Phone", "Rating", "Reviews", "Category", "Search City"]
    df = pd.DataFrame(final_rows)
    if df.empty:
        raise SystemExit("No qualified rows. Try increasing city limits.")

    sheet_df = df[export_cols + [c for c in extra_cols if c in df.columns]]
    sheet_df.to_excel(SHEET_PATH, index=False)
    sheet_df[export_cols].to_csv(CSV_PATH, index=False)

    by_city = sheet_df.groupby("Search City").size().sort_values(ascending=False)
    print("\nCity breakdown:")
    for city, count in by_city.items():
        print(f"  {city}: {count}")
    print(f"\nSheet: {SHEET_PATH}")
    print(f"CSV:   {CSV_PATH}")


if __name__ == "__main__":
    main()
