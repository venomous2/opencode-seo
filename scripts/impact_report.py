"""Change-impact analysis for the OpenCode SEO Suite.

Joins completed recommendations (done/resolved) to the drift snapshots
taken before and after each completion, and reports what moved — keyword
positions for ranking fixes, URL-level movement for page fixes, pillar
score deltas for context.

The verdict language is deliberately cautious: SEO has too many
confounders (algorithm updates, seasonality, competitors) to claim credit,
so every verdict is an *association*, never a causal claim.

Usage:
    python scripts/impact_report.py --domain example.com [--days 90]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

import drift_store  # noqa: E402
import recommend_store  # noqa: E402

DISCLAIMER = ("association, not causation - snapshots bracket the "
              "completion date, but rankings also move for reasons "
              "unrelated to your fix")


def _nearest(snapshots: list[int], ts: int, before: bool) -> int | None:
    candidates = [s for s in snapshots if s <= ts] if before \
        else [s for s in snapshots if s > ts]
    return (max(candidates) if before else min(candidates)) \
        if candidates else None


def _url_positions(snapshot: dict[str, Any], url: str) -> list[int]:
    return [r["position"] for r in snapshot.get("rankings") or []
            if r.get("url") == url]


def assess(rec: dict[str, Any], before: dict[str, Any] | None,
           after: dict[str, Any] | None) -> dict[str, Any]:
    """Verdict for one completed recommendation."""
    if before is None:
        return {"verdict": "insufficient_data",
                "detail": "no snapshot before completion — nothing to "
                          "compare against"}
    if after is None:
        return {"verdict": "insufficient_data",
                "detail": "no snapshot since completion — run watch or an "
                          "audit to measure impact"}

    evidence = rec.get("evidence") or {}
    keyword = evidence.get("keyword")
    if keyword:
        after_rank = {r["keyword"]: r for r in after.get("rankings") or []}
        was_lost = evidence.get("now") is None
        entry = after_rank.get(keyword)
        if entry is None:
            verdict = "no_change" if was_lost else "worse"
            detail = f"'{keyword}' still absent from the monitored set" \
                if was_lost else f"'{keyword}' has since vanished"
        else:
            reference = evidence.get("now") or evidence.get("was") or 999
            if entry["position"] < reference:
                verdict = "improved"
                detail = (f"'{keyword}' now at {entry['position']} "
                          f"(was {evidence.get('now', evidence.get('was'))})")
            elif entry["position"] > reference:
                verdict = "worse"
                detail = (f"'{keyword}' slid further to "
                          f"{entry['position']}")
            else:
                verdict = "no_change"
                detail = f"'{keyword}' unchanged at {entry['position']}"
        return {"verdict": verdict, "detail": detail}

    url = rec.get("url", "")
    if url:
        before_pos = _url_positions(before, url)
        after_pos = _url_positions(after, url)
        if not before_pos and not after_pos:
            return {"verdict": "insufficient_data",
                    "detail": "URL has no tracked rankings in either "
                              "snapshot"}
        before_avg = sum(before_pos) / len(before_pos) if before_pos else 999
        after_avg = sum(after_pos) / len(after_pos) if after_pos else 999
        delta = round(before_avg - after_avg, 1)  # + = improved
        verdict = "improved" if delta >= 1 else "worse" if delta <= -1 \
            else "no_change"
        return {"verdict": verdict,
                "detail": f"URL average position {before_avg:g} → "
                          f"{after_avg:g} across "
                          f"{max(len(before_pos), len(after_pos))} keyword(s)"}

    return {"verdict": "insufficient_data",
            "detail": "no keyword or URL evidence to assess"}


def report(domain: str, days: int = 90) -> dict[str, Any]:
    cutoff = int(time.time()) - days * 86400
    closed = [r for r in recommend_store.list_recs(domain,
                                                   include_closed=True,
                                                   sort="severity")
              if r["status"] in ("done", "resolved")
              and r.get("updated", 0) >= cutoff]
    snapshots = drift_store.list_snapshots(domain)
    items = []
    counts = {"improved": 0, "no_change": 0, "worse": 0,
              "insufficient_data": 0}
    for rec in closed:
        completed = rec["updated"]
        before_ts = _nearest(snapshots, completed, before=True)
        after_ts = _nearest(snapshots, completed, before=False)
        before = drift_store.load(domain, before_ts) if before_ts else None
        after = drift_store.load(domain, after_ts) if after_ts else None
        outcome = assess(rec, before, after)
        counts[outcome["verdict"]] += 1
        items.append({
            "id": rec["id"], "finding": rec["finding"],
            "source": rec["source"], "status": rec["status"],
            "completed": completed, **outcome,
        })
    order = {"improved": 0, "worse": 1, "no_change": 2,
             "insufficient_data": 3}
    items.sort(key=lambda i: (order[i["verdict"]], -i["completed"]))
    return {
        "domain": domain,
        "window_days": days,
        "evaluated": len(items),
        "counts": counts,
        "items": items,
        "note": DISCLAIMER,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="impact_report",
        description="What happened after completed recommendations "
                    "(association, not causation)")
    parser.add_argument("--domain", required=True)
    parser.add_argument("--days", type=int, default=90)
    args = parser.parse_args(argv)
    print(json.dumps(report(args.domain.strip().lower(), args.days),
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
