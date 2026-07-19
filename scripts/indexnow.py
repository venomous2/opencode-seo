"""IndexNow submitter for the OpenCode SEO Suite.

Ping Bing, Yandex and other IndexNow-participating engines the moment URLs
are published or updated — no waiting for the next crawl.

Usage:
    python scripts/indexnow.py init --domain example.com
        # generates a key and prints the .txt file you must host
    python scripts/indexnow.py submit --domain example.com --url https://example.com/new-post
    python scripts/indexnow.py submit --domain example.com --file urls.txt
    python scripts/indexnow.py submit --domain example.com --sitemap https://example.com/sitemap.xml

Keys are stored per-domain in
~/.config/opencode/seo-suite/indexnow-keys.json. The key file
(<key>.txt containing just the key) must be reachable at
https://<domain>/<key>.txt or engines reject submissions.
"""

from __future__ import annotations

import argparse
import json
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from seo_config import SUITE_DIR

KEYS_FILE = SUITE_DIR / "indexnow-keys.json"
ENDPOINT = "https://api.indexnow.org/indexnow"


class IndexNowError(RuntimeError):
    pass


def _load_keys() -> dict[str, str]:
    if KEYS_FILE.is_file():
        try:
            return json.loads(KEYS_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def _save_keys(keys: dict[str, str]) -> None:
    SUITE_DIR.mkdir(parents=True, exist_ok=True)
    KEYS_FILE.write_text(json.dumps(keys, indent=2) + "\n", encoding="utf-8")


def init_key(domain: str) -> dict[str, str]:
    keys = _load_keys()
    if domain in keys:
        key = keys[domain]
        rotated = False
    else:
        key = secrets.token_hex(16)  # 32 hex chars, within IndexNow rules
        keys[domain] = key
        _save_keys(keys)
        rotated = True
    return {"domain": domain, "key": key, "new": rotated,
            "key_file_url": f"https://{domain}/{key}.txt"}


def fetch_sitemap_urls(sitemap_url: str, limit: int = 1000) -> list[str]:
    with urllib.request.urlopen(sitemap_url, timeout=30) as response:
        xml = response.read().decode("utf-8", errors="replace")
    import re
    return re.findall(r"<loc>\s*([^<]+?)\s*</loc>", xml)[:limit]


def submit(domain: str, urls: list[str]) -> dict[str, Any]:
    keys = _load_keys()
    key = keys.get(domain)
    if not key:
        raise IndexNowError(
            f"No IndexNow key for {domain}. Run: "
            f"python scripts/indexnow.py init --domain {domain}")
    if not urls:
        raise IndexNowError("No URLs to submit.")
    payload = {
        "host": domain,
        "key": key,
        "keyLocation": f"https://{domain}/{key}.txt",
        "urlList": urls,
    }
    request = urllib.request.Request(
        ENDPOINT, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            status = response.status
    except urllib.error.HTTPError as exc:
        status = exc.code
    accepted = status in (200, 202)
    return {
        "submitted": len(urls), "accepted": accepted, "http_status": status,
        "key_location": payload["keyLocation"],
        "note": ("Accepted — engines will crawl shortly."
                 if accepted else
                 "Rejected — most often the key .txt file is not reachable "
                 "at the keyLocation URL. Verify it in a browser first."),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="indexnow",
                                     description="IndexNow submitter")
    parser.add_argument("action", choices=["init", "submit"])
    parser.add_argument("--domain", required=True)
    parser.add_argument("--url", help="comma-separated URLs (submit)")
    parser.add_argument("--file", help="text file with one URL per line (submit)")
    parser.add_argument("--sitemap", help="sitemap URL to pull URLs from (submit)")
    args = parser.parse_args(argv)

    try:
        if args.action == "init":
            result = init_key(args.domain)
            result["next_step"] = (
                f"Host a plain-text file named {result['key']}.txt containing "
                f"only the key at https://{args.domain}/{result['key']}.txt")
            print(json.dumps(result, indent=2))
            return 0

        urls: list[str] = []
        if args.url:
            urls.extend(u.strip() for u in args.url.split(",") if u.strip())
        if args.file:
            urls.extend(l.strip() for l in
                        Path(args.file).read_text(encoding="utf-8").splitlines()
                        if l.strip().startswith("http"))
        if args.sitemap:
            urls.extend(fetch_sitemap_urls(args.sitemap))
        print(json.dumps(submit(args.domain, urls), indent=2))
        return 0
    except (IndexNowError, urllib.error.URLError, OSError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
