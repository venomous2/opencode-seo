"""Event log for the OpenCode SEO Suite — the project timeline.

Everything the suite does for a domain appends one JSON line here, so the
dashboard and briefing can answer "what happened?" chronologically and
change-impact analysis can later join actions to drift diffs.

Storage: ~/.config/opencode/seo-suite/events/<domain>.jsonl

Event shape:
    {"ts": 1721..., "type": "rec_raised", "summary": "human line",
     "data": {...}}                     # data optional

Types emitted by the data layer:
    rec_raised, rec_reopened, rec_status   (recommend_store)
    lint_saved                             (seo_lint --save)
    snapshot_saved                         (drift_store)
    note                                   (manual, via this CLI)

Usage:
    python scripts/event_log.py log --domain example.com --type note \
        --summary "Published espresso grinder guide"
    python scripts/event_log.py list --domain example.com [--limit 20]
        [--since TS] [--type rec_status]
    python scripts/event_log.py domains
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

from seo_config import SUITE_DIR

EVENTS_DIR = SUITE_DIR / "events"


def _path(domain: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9.-]", "_", domain.strip().lower())
    return EVENTS_DIR / f"{safe}.jsonl"


def log(domain: str, type: str, summary: str,
        data: dict[str, Any] | None = None) -> None:
    """Append an event. Best-effort: never break the caller."""
    try:
        EVENTS_DIR.mkdir(parents=True, exist_ok=True)
        event: dict[str, Any] = {"ts": int(time.time()), "type": type,
                                 "summary": summary[:300]}
        if data:
            event["data"] = data
        with _path(domain).open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    except OSError:
        pass


def events(domain: str, limit: int | None = None, since: int | None = None,
           type: str | None = None) -> list[dict[str, Any]]:
    path = _path(domain)
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if since is not None and int(event.get("ts", 0)) < since:
            continue
        if type is not None and event.get("type") != type:
            continue
        out.append(event)
    if limit is not None:
        out = out[-limit:]
    return out


def domains() -> list[str]:
    if not EVENTS_DIR.is_dir():
        return []
    return sorted(p.stem for p in EVENTS_DIR.glob("*.jsonl"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="event_log",
                                     description="Per-domain event timeline")
    parser.add_argument("action", choices=["log", "list", "domains"])
    parser.add_argument("--domain")
    parser.add_argument("--type", help="event type (log) or filter (list)")
    parser.add_argument("--summary", help="human-readable line (log)")
    parser.add_argument("--data", help="optional JSON object (log)")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--since", type=int, help="unix timestamp (list)")
    args = parser.parse_args(argv)

    if args.action == "domains":
        print(json.dumps({"domains": domains()}, indent=2))
        return 0
    if not args.domain:
        print(json.dumps({"error": "--domain is required"}))
        return 1
    domain = args.domain.strip().lower()

    if args.action == "log":
        if not args.type or not args.summary:
            print(json.dumps({"error": "log needs --type and --summary"}))
            return 1
        data = None
        if args.data:
            try:
                data = json.loads(args.data)
            except json.JSONDecodeError as exc:
                print(json.dumps({"error": f"--data: {exc}"}))
                return 1
        log(domain, args.type, args.summary, data)
        print(json.dumps({"logged": True, "domain": domain}))
        return 0
    # list
    print(json.dumps({"domain": domain,
                      "events": events(domain, limit=args.limit,
                                       since=args.since, type=args.type)},
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
