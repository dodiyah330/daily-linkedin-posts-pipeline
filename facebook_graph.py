#!/usr/bin/env python3
"""Shared Facebook Graph API helpers for BookWellNow page posting."""
from __future__ import annotations

import datetime
import json
import os
import ssl
import uuid
from io import BytesIO
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

BASE = os.path.dirname(os.path.abspath(__file__))


def graph_version() -> str:
    return os.environ.get("FACEBOOK_GRAPH_VERSION", "v26.0")


def graph_base() -> str:
    return f"https://graph.facebook.com/{graph_version()}"


def timezone_name() -> str:
    return os.environ.get("FACEBOOK_TIMEZONE", "Asia/Kolkata")


def ist_zone() -> ZoneInfo:
    return ZoneInfo(timezone_name())


IST = ZoneInfo("Asia/Kolkata")


def load_dotenv(path: str | None = None) -> dict[str, str]:
    env: dict[str, str] = {}
    env_path = path or os.path.join(BASE, ".env")
    if not os.path.exists(env_path):
        return env
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip().strip('"').strip("'")
    for key, value in env.items():
        os.environ.setdefault(key, value)
    return env


def graph_error_body(exc: HTTPError) -> str:
    try:
        raw = exc.read().decode("utf-8", errors="replace")
    except Exception:
        return str(exc)
    try:
        data = json.loads(raw)
        err = data.get("error") or data
        parts = [
            str(err.get("message") or raw),
            f"type={err.get('type')}" if err.get("type") else "",
            f"code={err.get('code')}" if err.get("code") is not None else "",
            f"subcode={err.get('error_subcode')}" if err.get("error_subcode") is not None else "",
        ]
        return " ".join(p for p in parts if p)
    except Exception:
        return raw[:800]


def ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    try:
        import certifi

        ctx.load_verify_locations(certifi.where())
    except Exception:
        pass
    if os.environ.get("FACEBOOK_SSL_INSECURE", "1") == "1":
        # macOS python.org builds often lack a CA bundle; same fallback as the LLM scripts.
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


def graph_request(
    method: str,
    path: str,
    params: dict[str, Any] | None = None,
    files: dict[str, str] | None = None,
    token: str | None = None,
    timeout: int = 120,
) -> dict[str, Any]:
    params = dict(params or {})
    if token:
        params.setdefault("access_token", token)
    url = path if path.startswith("http") else f"{graph_base()}{path}"
    ctx = ssl_context()
    try:
        if files:
            body, content_type = encode_multipart(params, files)
            req = Request(url, data=body, method=method.upper())
            req.add_header("Content-Type", content_type)
        elif method.upper() == "GET":
            qs = urlencode({k: v for k, v in params.items() if v is not None})
            req = Request(f"{url}?{qs}" if qs else url, method="GET")
        else:
            data = urlencode({k: str(v) for k, v in params.items() if v is not None}).encode()
            req = Request(url, data=data, method=method.upper())
            req.add_header("Content-Type", "application/x-www-form-urlencoded")
        with urlopen(req, context=ctx, timeout=timeout) as res:
            raw = res.read().decode()
            return json.loads(raw) if raw else {}
    except HTTPError as e:
        raise RuntimeError(f"Graph {method.upper()} {path}: {graph_error_body(e)}") from e


def encode_multipart(fields: dict[str, Any], files: dict[str, str]) -> tuple[bytes, str]:
    boundary = "----FacebookFormBoundary" + uuid.uuid4().hex
    buf = BytesIO()
    for key, value in fields.items():
        if value is None:
            continue
        buf.write(f"--{boundary}\r\n".encode())
        buf.write(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode())
        buf.write(str(value).encode() + b"\r\n")
    for key, filepath in files.items():
        filename = os.path.basename(filepath)
        ext = os.path.splitext(filename)[1].lower()
        mime = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }.get(ext, "application/octet-stream")
        buf.write(f"--{boundary}\r\n".encode())
        buf.write(
            f'Content-Disposition: form-data; name="{key}"; filename="{filename}"\r\n'.encode()
        )
        buf.write(f"Content-Type: {mime}\r\n\r\n".encode())
        with open(filepath, "rb") as f:
            buf.write(f.read())
        buf.write(b"\r\n")
    buf.write(f"--{boundary}--\r\n".encode())
    return buf.getvalue(), f"multipart/form-data; boundary={boundary}"


def parse_clock(time_str: str) -> tuple[int, int]:
    text = (time_str or "").strip().upper()
    hour_s, rest = text.split(":", 1)
    minute_s, ap = rest.split()
    hour, minute = int(hour_s), int(minute_s)
    if ap == "PM" and hour != 12:
        hour += 12
    if ap == "AM" and hour == 12:
        hour = 0
    return hour, minute


def schedule_datetime(date_str: str, time_str: str) -> datetime.datetime:
    """Parse MM/DD/YYYY + '10:00 AM' as FACEBOOK_TIMEZONE (default IST)."""
    month, day, year = [int(p) for p in date_str.split("/")]
    hour, minute = parse_clock(time_str)
    return datetime.datetime(year, month, day, hour, minute, tzinfo=ist_zone())


def to_unix(dt: datetime.datetime) -> int:
    return int(dt.timestamp())


def bump_facebook_slot(dt: datetime.datetime, now: datetime.datetime | None = None) -> datetime.datetime:
    """Graph API requires scheduled_publish_time 10 minutes to 75 days from now."""
    now = now or datetime.datetime.now(tz=ist_zone())
    earliest = now + datetime.timedelta(minutes=12)
    latest = now + datetime.timedelta(days=75)
    if dt < earliest:
        cursor = earliest.replace(second=0, microsecond=0)
        if cursor.minute not in (0, 15, 30, 45):
            extra = 15 - (cursor.minute % 15)
            cursor += datetime.timedelta(minutes=extra)
        return cursor
    if dt > latest:
        raise ValueError(f"slot {dt.isoformat()} is more than 75 days out")
    return dt


def page_identity(token: str) -> dict[str, Any]:
    try:
        return graph_request("GET", "/me", {"fields": "id,name,link,fan_count"}, token=token)
    except RuntimeError:
        return graph_request("GET", "/me", {"fields": "id,name,link"}, token=token)


def list_managed_pages(user_token: str) -> list[dict[str, Any]]:
    data = graph_request(
        "GET",
        "/me/accounts",
        {"fields": "id,name,access_token,tasks,link", "limit": "100"},
        token=user_token,
    )
    return list(data.get("data") or [])


def exchange_long_lived_user_token(short_token: str, app_id: str, app_secret: str) -> dict[str, Any]:
    return graph_request(
        "GET",
        "/oauth/access_token",
        {
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": short_token,
        },
    )


def prepare_upload_image(src: str, dest_dir: str) -> str:
    """Copy or JPEG-compress a slide so Facebook gets a <1MB raster."""
    os.makedirs(dest_dir, exist_ok=True)
    ext = os.path.splitext(src)[1].lower()
    size = os.path.getsize(src)
    if ext in {".jpg", ".jpeg"} and size <= 1_000_000:
        return src
    if ext == ".png" and size <= 900_000:
        return src
    try:
        from PIL import Image
    except ImportError:
        return src
    im = Image.open(src)
    if im.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", im.size, (255, 255, 255))
        if im.mode == "P":
            im = im.convert("RGBA")
        bg.paste(im, mask=im.split()[-1] if im.mode == "RGBA" else None)
        im = bg
    else:
        im = im.convert("RGB")
    out = os.path.join(dest_dir, os.path.splitext(os.path.basename(src))[0] + ".jpg")
    im.save(out, "JPEG", quality=88, optimize=True)
    return out
