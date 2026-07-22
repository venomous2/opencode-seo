"""Response cache for the OpenCode SEO Suite data layer.

Caches DataForSEO responses on disk so repeated identical pulls within the
TTL window do not cost money twice. Used by dfs_client.py; can also be run
directly to inspect or clear the cache:

    python scripts/cache.py stats
    python scripts/cache.py clear [--older-than-days 30]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

from seo_config import SUITE_DIR

CACHE_DIR = SUITE_DIR / "cache"

# Per-command time-to-live in seconds.
TTL = {
    "serp": 6 * 3600,            # SERPs shift quickly
    "volume": 7 * 86400,
    "ideas": 7 * 86400,
    "related": 7 * 86400,
    "ranked": 24 * 3600,
    "competitors": 24 * 3600,
    "intersection": 24 * 3600,
    "backlinks": 7 * 86400,
    "refdomains": 7 * 86400,
    "anchors": 7 * 86400,
    "onpage": 24 * 3600,
    "lighthouse": 24 * 3600,
    "content": 24 * 3600,
    "mentions": 24 * 3600,
    "business": 7 * 86400,
    "whois": 30 * 86400,
    "amazon": 24 * 3600,
    "trends": 7 * 86400,
    "serp-maps": 6 * 3600,
    "serp-news": 6 * 3600,
    "serp-bing": 6 * 3600,
    "serp-youtube": 6 * 3600,
    "autocomplete": 24 * 3600,
    "kd": 7 * 86400,
    "backlinks-history": 24 * 3600,
    "bulk-ranks": 24 * 3600,
    "technologies": 30 * 86400,
}
DEFAULT_TTL = 24 * 3600


def _key(command: str, payload: list[dict[str, Any]]) -> str:
    raw = command + "|" + json.dumps(payload, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def get(command: str, payload: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return a cached response body if present and fresh, else None."""
    path = CACHE_DIR / f"{_key(command, payload)}.json"
    if not path.is_file():
        return None
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    ttl = TTL.get(command, DEFAULT_TTL)
    if time.time() - record.get("created", 0) > ttl:
        return None
    return record.get("body")


def put(command: str, payload: list[dict[str, Any]], body: dict[str, Any]) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        record = {"created": time.time(), "command": command, "body": body}
        (CACHE_DIR / f"{_key(command, payload)}.json").write_text(
            json.dumps(record), encoding="utf-8")
    except OSError:
        pass  # caching is best-effort; never break a live call


def stats() -> dict[str, Any]:
    files = list(CACHE_DIR.glob("*.json")) if CACHE_DIR.is_dir() else []
    now = time.time()
    fresh = 0
    for f in files:
        try:
            record = json.loads(f.read_text(encoding="utf-8"))
            if now - record.get("created", 0) <= TTL.get(record.get("command"), DEFAULT_TTL):
                fresh += 1
        except (json.JSONDecodeError, OSError):
            continue
    size_kb = sum(f.stat().st_size for f in files) // 1024
    return {"entries": len(files), "fresh": fresh, "size_kb": size_kb,
            "dir": str(CACHE_DIR)}


def clear(older_than_days: int = 0) -> int:
    removed = 0
    if not CACHE_DIR.is_dir():
        return 0
    cutoff = time.time() - older_than_days * 86400
    for f in CACHE_DIR.glob("*.json"):
        if older_than_days and f.stat().st_mtime > cutoff:
            continue
        f.unlink(missing_ok=True)
        removed += 1
    return removed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cache", description="Response cache manager")
    parser.add_argument("action", choices=["stats", "clear"])
    parser.add_argument("--older-than-days", type=int, default=0)
    args = parser.parse_args(argv)
    if args.action == "stats":
        print(json.dumps(stats(), indent=2))
    else:
        print(json.dumps({"removed": clear(args.older_than_days)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
