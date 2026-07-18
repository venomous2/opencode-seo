"""Drift monitoring store for the OpenCode SEO Suite.

Saves timestamped SEO snapshots per domain and diffs any two of them, so
skills can answer "what changed since last month?" with evidence.

Usage:
    python scripts/drift_store.py save --domain example.com --file snapshot.json
    python scripts/drift_store.py save --domain example.com          # reads stdin
    python scripts/drift_store.py list --domain example.com
    python scripts/drift_store.py latest --domain example.com
    python scripts/drift_store.py compare --domain example.com [--from TS] [--to TS]
    python scripts/drift_store.py chart --domain example.com [--from TS] [--to TS]

`chart` prints fenced ```chart blocks (before/after specs) ready to paste
into a report that report_build.py renders as graphs.

Snapshot JSON shape (all sections optional — save what you have):
    {
      "scores":   {"technical": 74, "content": 81, ...},       # 0-100 pillars
      "rankings": [{"keyword": "...", "position": 5, "url": "..."}],
      "backlinks": {"referring_domains": 120, "backlinks": 3400},
      "mentions":  {"ai_mentions": 12},
      "notes":    "anything worth remembering"
    }

Storage: ~/.config/opencode/seo-suite/drift/<domain>/<unix-ts>.json
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

DRIFT_DIR = SUITE_DIR / "drift"


def _domain_dir(domain: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9.-]", "_", domain.strip().lower())
    return DRIFT_DIR / safe


def save(domain: str, snapshot: dict[str, Any]) -> Path:
    directory = _domain_dir(domain)
    directory.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    path = directory / f"{ts}.json"
    # avoid same-second collisions overwriting a previous snapshot
    while path.exists():
        ts += 1
        path = directory / f"{ts}.json"
    snapshot = dict(snapshot)
    snapshot["_saved_at"] = ts
    path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False),
                    encoding="utf-8")
    return path


def list_snapshots(domain: str) -> list[int]:
    directory = _domain_dir(domain)
    if not directory.is_dir():
        return []
    return sorted(int(p.stem) for p in directory.glob("*.json")
                  if p.stem.isdigit())


def load(domain: str, ts: int) -> dict[str, Any]:
    path = _domain_dir(domain) / f"{ts}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def compare(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    """Diff two snapshots into a human-actionable change report."""
    diff: dict[str, Any] = {
        "from": old.get("_saved_at"), "to": new.get("_saved_at"),
    }

    # --- scores ---------------------------------------------------------
    score_changes = {}
    for pillar in set((old.get("scores") or {}) | (new.get("scores") or {})):
        before = (old.get("scores") or {}).get(pillar)
        after = (new.get("scores") or {}).get(pillar)
        if before is not None and after is not None and after != before:
            score_changes[pillar] = {"from": before, "to": after,
                                     "delta": after - before}
    if score_changes:
        diff["score_changes"] = score_changes

    # --- rankings -------------------------------------------------------
    old_rank = {r["keyword"]: r for r in old.get("rankings") or []}
    new_rank = {r["keyword"]: r for r in new.get("rankings") or []}
    if old_rank or new_rank:
        gained = sorted(set(new_rank) - set(old_rank))
        lost = sorted(set(old_rank) - set(new_rank))
        moved = []
        for kw in set(old_rank) & set(new_rank):
            before, after = old_rank[kw]["position"], new_rank[kw]["position"]
            if before != after:
                moved.append({"keyword": kw, "from": before, "to": after,
                              "delta": before - after,  # + = moved up
                              "url": new_rank[kw].get("url")})
        moved.sort(key=lambda m: m["delta"], reverse=True)
        diff["rankings"] = {
            "gained": gained, "lost": lost,
            "moved_up": [m for m in moved if m["delta"] > 0],
            "moved_down": [m for m in moved if m["delta"] < 0],
        }

    # --- simple numeric sections ---------------------------------------
    for section in ("backlinks", "mentions"):
        changes = {}
        for key in set((old.get(section) or {}) | (new.get(section) or {})):
            before = (old.get(section) or {}).get(key)
            after = (new.get(section) or {}).get(key)
            if isinstance(before, (int, float)) and isinstance(after, (int, float)) and after != before:
                changes[key] = {"from": before, "to": after, "delta": after - before}
        if changes:
            diff[section] = changes

    return diff


def build_chart_specs(old: dict[str, Any], new: dict[str, Any]) -> list[dict[str, Any]]:
    """Turn two snapshots into before/after chart specs for report_build."""
    specs: list[dict[str, Any]] = []

    # pillar scores -> compare chart
    score_rows = []
    for pillar in (new.get("scores") or {}):
        before = (old.get("scores") or {}).get(pillar)
        after = (new.get("scores") or {}).get(pillar)
        if isinstance(before, (int, float)) and isinstance(after, (int, float)):
            score_rows.append([pillar.replace("_", " ").title(), before, after])
    if score_rows:
        specs.append({"type": "compare",
                      "title": "Scores vs previous snapshot",
                      "data": score_rows, "max": 100})

    # backlinks / mentions -> compare chart
    metric_rows = []
    for section in ("backlinks", "mentions"):
        for key in (new.get(section) or {}):
            before = (old.get(section) or {}).get(key)
            after = (new.get(section) or {}).get(key)
            if isinstance(before, (int, float)) and isinstance(after, (int, float)):
                metric_rows.append([key.replace("_", " ").title(), before, after])
    if metric_rows:
        specs.append({"type": "compare",
                      "title": "Authority & mentions vs previous",
                      "data": metric_rows})

    # ranking movement -> stats cards
    old_rank = {r["keyword"]: r for r in old.get("rankings") or []}
    new_rank = {r["keyword"]: r for r in new.get("rankings") or []}
    if old_rank or new_rank:
        gained = len(set(new_rank) - set(old_rank))
        lost = len(set(old_rank) - set(new_rank))
        up = down = 0
        for kw in set(old_rank) & set(new_rank):
            delta = old_rank[kw]["position"] - new_rank[kw]["position"]
            if delta > 0:
                up += 1
            elif delta < 0:
                down += 1
        specs.append({"type": "stats", "data": [
            ["Keywords gained", str(gained)],
            ["Keywords lost", str(lost)],
            ["Moved up", str(up)],
            ["Moved down", str(down)],
        ]})
    return specs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="drift_store",
                                     description="Drift monitoring store")
    parser.add_argument("action", choices=["save", "list", "latest", "compare", "chart"])
    parser.add_argument("--domain", required=True)
    parser.add_argument("--file", help="snapshot JSON file (save); omit to read stdin")
    parser.add_argument("--from", dest="from_ts", type=int,
                        help="older snapshot ts (compare; default: oldest)")
    parser.add_argument("--to", dest="to_ts", type=int,
                        help="newer snapshot ts (compare; default: newest)")
    args = parser.parse_args(argv)

    try:
        if args.action == "save":
            raw = Path(args.file).read_text(encoding="utf-8") if args.file \
                else sys.stdin.read()
            snapshot = json.loads(raw)
            path = save(args.domain, snapshot)
            print(json.dumps({"saved": str(path)}))
            return 0

        snapshots = list_snapshots(args.domain)
        if args.action == "list":
            print(json.dumps({"domain": args.domain, "snapshots": snapshots}))
            return 0
        if not snapshots:
            print(json.dumps({"error": f"No snapshots for {args.domain}. "
                                       "Save one first with drift_store.py save."}))
            return 1

        if args.action == "latest":
            print(json.dumps(load(args.domain, snapshots[-1]),
                             indent=2, ensure_ascii=False))
            return 0

        # compare / chart
        from_ts = args.from_ts or (snapshots[-2] if len(snapshots) >= 2
                                   else snapshots[0])
        to_ts = args.to_ts or snapshots[-1]
        if from_ts not in snapshots or to_ts not in snapshots:
            raise ValueError(f"Unknown snapshot ts. Available: {snapshots}")
        old, new = load(args.domain, from_ts), load(args.domain, to_ts)
        if args.action == "compare":
            print(json.dumps(compare(old, new), indent=2, ensure_ascii=False))
        else:  # chart
            specs = build_chart_specs(old, new)
            if not specs:
                print(json.dumps({"error": "Snapshots have no comparable "
                                           "scores, metrics, or rankings"}))
                return 1
            for spec in specs:
                print("```chart")
                print(json.dumps(spec, ensure_ascii=False))
                print("```\n")
        return 0
    except (ValueError, json.JSONDecodeError, OSError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
