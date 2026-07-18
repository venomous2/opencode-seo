"""DataForSEO cost ledger for the OpenCode SEO Suite.

dfs_client.py appends one JSON line per billable API call to
~/.config/opencode/seo-suite/costs.jsonl. This module reports on it:

    python scripts/cost_ledger.py report            # totals by period
    python scripts/cost_ledger.py report --by command
    python scripts/cost_ledger.py tail --limit 10   # recent calls
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from seo_config import SUITE_DIR

LEDGER = SUITE_DIR / "costs.jsonl"

DAY = 86400


def log(command: str, cost: float | None, detail: str = "") -> None:
    """Append a call record. Best-effort: never break the caller."""
    if cost is None:
        return
    try:
        SUITE_DIR.mkdir(parents=True, exist_ok=True)
        record = {"ts": int(time.time()), "command": command,
                  "cost": float(cost), "detail": detail[:200]}
        with LEDGER.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
    except OSError:
        pass


def _records() -> list[dict[str, Any]]:
    if not LEDGER.is_file():
        return []
    out = []
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def report(by: str | None = None) -> dict[str, Any]:
    records = _records()
    now = time.time()
    periods = {"today": DAY, "last_7d": 7 * DAY, "last_30d": 30 * DAY, "all_time": None}
    result: dict[str, Any] = {"ledger": str(LEDGER), "call_count": len(records),
                              "periods": {}}
    for name, window in periods.items():
        subset = records if window is None else [r for r in records if now - r["ts"] <= window]
        result["periods"][name] = {
            "calls": len(subset),
            "cost_usd": round(sum(r["cost"] for r in subset), 4),
        }
    if by == "command":
        per: dict[str, dict[str, Any]] = {}
        for r in records:
            entry = per.setdefault(r["command"], {"calls": 0, "cost_usd": 0.0})
            entry["calls"] += 1
            entry["cost_usd"] = round(entry["cost_usd"] + r["cost"], 4)
        result["by_command"] = dict(sorted(per.items(),
                                           key=lambda kv: kv[1]["cost_usd"],
                                           reverse=True))
    return result


def tail(limit: int) -> list[dict[str, Any]]:
    return _records()[-limit:]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cost_ledger",
                                     description="DataForSEO spend ledger")
    parser.add_argument("action", choices=["report", "tail"])
    parser.add_argument("--by", choices=["command"])
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args(argv)
    if args.action == "report":
        print(json.dumps(report(args.by), indent=2))
    else:
        print(json.dumps(tail(args.limit), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
