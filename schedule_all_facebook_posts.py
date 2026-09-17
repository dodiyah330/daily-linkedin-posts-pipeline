#!/usr/bin/env python3
"""Schedule BookWellNow Facebook Page posts via the Graph API.

Mirrors schedule_all_posts.cjs, but uses the official Page API instead of
browser automation. Each item is a multi-photo album (LinkedIn carousel slides).

Usage:
  python3 facebook_page_auth.py
  DRY_RUN=1 python3 schedule_all_facebook_posts.py
  python3 schedule_all_facebook_posts.py

Env:
  SCHEDULE_FILE     default schedule_bookwellnow_facebook.json
  START_POST_ID     resume from this id
  POST_NOW=1        publish immediately
  DRY_RUN=1         print actions, do not call Graph
  LIST_SCHEDULED=1  print unpublished/scheduled posts and exit
  FACEBOOK_PAGE_ID  optional; auto-detected from the page token
  FACEBOOK_PAGE_ACCESS_TOKEN  required (long-lived Page token)
"""
from __future__ import annotations

import datetime
import json
import os
import sys
import tempfile
import time
import traceback

from facebook_graph import (
    BASE,
    bump_facebook_slot,
    load_dotenv,
    page_identity,
    prepare_upload_image,
    graph_request,
    ist_zone,
    schedule_datetime,
    to_unix,
)

os.chdir(BASE)
load_dotenv()

SCHEDULE_FILE = os.environ.get("SCHEDULE_FILE", "schedule_bookwellnow_facebook.json")
START_POST_ID = int(os.environ.get("START_POST_ID", "1"))
POST_NOW = os.environ.get("POST_NOW", "0") == "1"
DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"
LIST_SCHEDULED = os.environ.get("LIST_SCHEDULED", "0") == "1"
DELETE_SCHEDULED = os.environ.get("DELETE_SCHEDULED", "0") == "1"
LOG_PATH = os.path.join(BASE, "bookwellnow-facebook-run-log.json")
DELAY_S = float(os.environ.get("FACEBOOK_POST_DELAY_S", "2.5"))


def load_log() -> list:
    if not os.path.exists(LOG_PATH):
        return []
    try:
        return json.load(open(LOG_PATH))
    except Exception:
        return []


def save_log(entries: list) -> None:
    json.dump(entries[-80:], open(LOG_PATH, "w"), indent=2)


def require_token() -> str:
    token = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN", "").strip()
    if not token:
        sys.exit(
            "FACEBOOK_PAGE_ACCESS_TOKEN missing in .env — "
            "run python3 facebook_page_auth.py after creating a Page token "
            "(see docs/API_KEYS.md § Facebook)."
        )
    return token


def resolve_page(token: str) -> dict:
    ident = page_identity(token)
    env_id = os.environ.get("FACEBOOK_PAGE_ID", "").strip()
    page_id = env_id or ident.get("id")
    if not page_id:
        sys.exit("Could not resolve Facebook Page ID from token")
    if env_id and ident.get("id") and env_id != str(ident["id"]):
        print(
            f"Warning: FACEBOOK_PAGE_ID={env_id} but token is for "
            f"{ident.get('name')} ({ident.get('id')}). Using token page."
        )
        page_id = ident["id"]
    ident["id"] = str(page_id)
    return ident


def list_scheduled(token: str, page_id: str) -> list:
    data = graph_request(
        "GET",
        f"/{page_id}/scheduled_posts",
        {"fields": "id,message,created_time,scheduled_publish_time,is_published,status_type", "limit": "100"},
        token=token,
    )
    return list(data.get("data") or [])


def print_scheduled(token: str, page_id: str) -> None:
    rows = list_scheduled(token, page_id)
    print(f"{len(rows)} scheduled/unpublished posts on page {page_id}")
    for row in rows:
        when = row.get("scheduled_publish_time") or row.get("created_time")
        msg = (row.get("message") or "").splitlines()[0][:80]
        print(f"  {row.get('id')}  {when}  {msg}")


def delete_scheduled(token: str, page_id: str) -> int:
    rows = list_scheduled(token, page_id)
    if not rows:
        print("No scheduled posts to delete")
        return 0
    deleted = 0
    for row in rows:
        pid = row.get("id")
        if not pid:
            continue
        try:
            graph_request("DELETE", f"/{pid}", token=token)
            print(f"  deleted {pid}")
            deleted += 1
            time.sleep(0.4)
        except Exception as e:
            print(f"  FAIL delete {pid}: {e}")
    print(f"Deleted {deleted}/{len(rows)} scheduled posts")
    return deleted


def upload_photos(token: str, page_id: str, paths: list[str], scheduled: bool, tmp: str) -> list[str]:
    ids = []
    for src in paths:
        prepared = prepare_upload_image(src, tmp)
        fields = {"published": "false"}
        if scheduled:
            fields["temporary"] = "true"
        resp = graph_request(
            "POST",
            f"/{page_id}/photos",
            fields,
            files={"source": prepared},
            token=token,
        )
        pid = resp.get("id")
        if not pid:
            raise RuntimeError(f"photo upload returned no id: {resp}")
        ids.append(str(pid))
        print(f"    uploaded photo {os.path.basename(src)} -> {pid}")
    return ids


def publish_post(
    token: str,
    page_id: str,
    caption: str,
    photo_ids: list[str],
    unix_ts: int | None,
) -> dict:
    fields: dict[str, object] = {"message": caption}
    for i, pid in enumerate(photo_ids):
        fields[f"attached_media[{i}]"] = json.dumps({"media_fbid": pid})
    if unix_ts is None:
        fields["published"] = "true"
    else:
        fields["published"] = "false"
        fields["scheduled_publish_time"] = str(unix_ts)
        fields["unpublished_content_type"] = "SCHEDULED"
    return graph_request("POST", f"/{page_id}/feed", fields, token=token)


def already_posted(log: list, post: dict) -> bool:
    key = f"{post.get('date')}|{post.get('time')}|{post.get('label')}"
    for row in log:
        if row.get("key") == key and row.get("ok"):
            return True
    return False


def main() -> None:
    token = require_token()
    page = resolve_page(token)
    page_id = page["id"]
    tz = ist_zone()
    print(f"Page: {page.get('name')} ({page_id})  now={datetime.datetime.now(tz=tz).isoformat()}")

    if LIST_SCHEDULED:
        print_scheduled(token, page_id)
        return

    if DELETE_SCHEDULED:
        delete_scheduled(token, page_id)
        if os.environ.get("SCHEDULE_AFTER_DELETE", "1") != "1":
            return

    if not os.path.exists(SCHEDULE_FILE):
        sys.exit(f"No {SCHEDULE_FILE} — run python3 prepare_bookwellnow_facebook_schedule.py")

    payload = json.load(open(SCHEDULE_FILE))
    posts = payload.get("posts") or []
    if not posts:
        sys.exit(f"{SCHEDULE_FILE} has no posts")

    log = load_log()
    run = {
        "started": datetime.datetime.now(tz=tz).isoformat(),
        "mode": "now" if POST_NOW else "scheduled",
        "dryRun": DRY_RUN,
        "file": os.path.basename(SCHEDULE_FILE),
        "pageId": page_id,
        "pageName": page.get("name"),
        "results": [],
    }

    selected = [p for p in posts if int(p.get("id") or 0) >= START_POST_ID]
    print(f"{len(selected)} posts from id {START_POST_ID} ({'DRY RUN' if DRY_RUN else 'LIVE'})")

    tmp = tempfile.mkdtemp(prefix="fb-bookwellnow-")
    ok = fail = skip = 0

    for post in selected:
        label = post.get("label") or f"#{post.get('id')}"
        paths = [p for p in (post.get("assetPaths") or []) if p and os.path.exists(p)]
        if not paths and post.get("assetPath") and os.path.exists(post["assetPath"]):
            paths = [post["assetPath"]]
        caption = (post.get("caption") or "").strip()
        if not caption:
            print(f"  SKIP {label}: empty caption")
            skip += 1
            continue
        if not paths:
            print(f"  SKIP {label}: no images")
            skip += 1
            continue
        if already_posted(log, post) and not POST_NOW:
            print(f"  SKIP {label}: already logged as posted")
            skip += 1
            continue

        unix_ts = None
        when_label = "NOW"
        if not POST_NOW:
            try:
                slot = bump_facebook_slot(schedule_datetime(post["date"], post["time"]))
            except Exception as e:
                print(f"  SKIP {label}: {e}")
                skip += 1
                continue
            unix_ts = to_unix(slot)
            when_label = slot.strftime("%Y-%m-%d %I:%M %p %Z")

        print(f"  #{post['id']:02d} {when_label}  {len(paths)} imgs  {label}")
        if DRY_RUN:
            ok += 1
            run["results"].append({"id": post["id"], "label": label, "dryRun": True, "when": when_label})
            continue

        try:
            photo_ids = upload_photos(token, page_id, paths, scheduled=unix_ts is not None, tmp=tmp)
            resp = publish_post(token, page_id, caption, photo_ids, unix_ts)
            post_id = resp.get("id")
            print(f"    Graph post id={post_id}")
            row = {
                "ok": True,
                "id": post["id"],
                "label": label,
                "graphId": post_id,
                "when": when_label,
                "key": f"{post.get('date')}|{post.get('time')}|{post.get('label')}",
                "photoIds": photo_ids,
            }
            ok += 1
            run["results"].append(row)
            log.append({**row, "date": datetime.date.today().isoformat()})
            save_log(log)
        except Exception as e:
            fail += 1
            print(f"    FAIL: {e}")
            traceback.print_exc()
            run["results"].append({"ok": False, "id": post["id"], "label": label, "error": str(e)})
            log.append(
                {
                    "ok": False,
                    "id": post["id"],
                    "label": label,
                    "error": str(e),
                    "date": datetime.date.today().isoformat(),
                }
            )
            save_log(log)
        time.sleep(DELAY_S)

    run["finished"] = datetime.datetime.now(tz=tz).isoformat()
    run["ok"] = ok
    run["fail"] = fail
    run["skip"] = skip
    log.append({"run": run})
    save_log(log)
    print(f"Done. ok={ok} fail={fail} skip={skip}. Log: {LOG_PATH}")
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
