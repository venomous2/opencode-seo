"""Watch — scheduled monitoring for the OpenCode SEO Suite.

One command runs a monitoring bundle for a domain: lint key pages into the
recommendation store, pull fresh rankings/backlinks into a drift snapshot,
diff them against the previous snapshot (ranking losses and recoveries
become recommendations automatically), track competitor keyword growth,
and optionally re-check AI visibility. Everything lands in the local
stores — the seo-briefing skill and project_dashboard.py surface it.

Profiles:
    daily    lint + rankings            (cheap, fast)
    weekly   + backlinks, competitors,  (the full bundle)
             ai_visibility (only with --brand and --prompts)

Usage:
    python scripts/watch.py --domain example.com --profile weekly \
        --pages https://example.com/,https://example.com/pricing \
        --competitors rival1.com,rival2.com --brand "Example" \
        --prompts "best espresso grinder,grinder buying guide"
    python scripts/watch.py --domain example.com --dry-run
    python scripts/watch.py schedule --domain example.com --profile weekly

Pages, competitors and brand fall back to seo-project.yml when the flags
are omitted. Scheduling is delegated to the OS — `schedule` prints the
exact Task Scheduler / cron lines; nothing daemons in the background.
Every DataForSEO call is billed: the summary reports the run's cost and
the cache means re-runs within TTL are free.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

import cost_ledger  # noqa: E402
import drift_store  # noqa: E402
import event_log  # noqa: E402
import project_memory  # noqa: E402
import recommend_store  # noqa: E402
import rule_engine  # noqa: E402
import seo_lint  # noqa: E402
from site_crawler import fetch  # noqa: E402

SCRIPTS_DIR = Path(__file__).resolve().parent

PROFILES = {
    "daily": ("lint", "rankings"),
    "weekly": ("lint", "rankings", "backlinks", "competitors",
               "ai_visibility"),
}

RANK_LOSS_CAP = 10          # max ranking-loss recommendations per run
COMPETITOR_GAIN_MIN = 3     # new rankings before a competitor rec is raised


class WatchError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# External calls (isolated so tests can stub them)
# ---------------------------------------------------------------------------

def _dfs(args: list[str], sandbox: bool = False, timeout: int = 180) -> dict:
    cmd = [sys.executable, str(SCRIPTS_DIR / "dfs_client.py"), *args]
    if sandbox:
        cmd.append("--sandbox")
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          timeout=timeout)
    if proc.returncode != 0:
        detail = (proc.stdout or proc.stderr).strip()[:300]
        raise WatchError(f"dfs_client {' '.join(args[:1])} failed: {detail}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise WatchError(f"dfs_client returned non-JSON: {exc}") from exc


def _ai_visibility(domain: str, brand: str, prompts: str, location: str,
                   language: str, sandbox: bool = False) -> dict:
    cmd = [sys.executable, str(SCRIPTS_DIR / "ai_visibility.py"), "check",
           "--domain", domain, "--brand", brand, "--prompts", prompts,
           "--location", location, "--language", language]
    if sandbox:
        cmd.append("--sandbox")
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        detail = (proc.stdout or proc.stderr).strip()[:300]
        raise WatchError(f"ai_visibility failed: {detail}")
    return json.loads(proc.stdout)


# ---------------------------------------------------------------------------
# Response extraction (tolerant of Labs / simple shapes)
# ---------------------------------------------------------------------------

def rank_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalise a `ranked` response into [{keyword, position, url}]."""
    items = []
    for result in payload.get("result") or []:
        for item in (result or {}).get("items") or []:
            keyword = item.get("keyword") \
                or (item.get("keyword_data") or {}).get("keyword")
            element = item.get("ranked_serp_element") or {}
            serp_item = element.get("serp_item") or {}
            position = item.get("position") or item.get("rank_group") \
                or serp_item.get("rank_group")
            url = item.get("url") or serp_item.get("url") \
                or element.get("check_url") or ""
            if keyword and isinstance(position, (int, float)):
                items.append({"keyword": keyword,
                              "position": int(position), "url": url})
    return items


def backlink_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Pull referring-domain/backlink counts out of a backlinks response."""
    candidates = []
    for result in payload.get("result") or []:
        if isinstance(result, dict):
            candidates.append(result)
            candidates.extend(i for i in result.get("items") or []
                              if isinstance(i, dict))
    for cand in candidates:
        refs = cand.get("referring_domains") or cand.get("refdomains")
        links = cand.get("backlinks") or cand.get("backlinks_count") \
            or cand.get("total_count")
        if isinstance(refs, (int, float)) or isinstance(links, (int, float)):
            out = {}
            if isinstance(refs, (int, float)):
                out["referring_domains"] = int(refs)
            if isinstance(links, (int, float)):
                out["backlinks"] = int(links)
            return out
    return {}


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48]


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_lint(domain: str, pages: list[str],
               rules: list[dict[str, Any]], timeout: int = 20) -> dict:
    """Lint key pages straight into the recommendation store."""
    parsed = []
    errors = []
    for url in pages:
        result = fetch(url, timeout)
        if result.status != 200:
            errors.append({"url": url, "error": f"HTTP {result.status}"})
            continue
        parsed.append(seo_lint.parse_html(result.body, url))
    outcomes = seo_lint.lint_pages(parsed, rules, None)
    store = recommend_store.save_lint_results(domain, outcomes, rules)
    return {"pages_linted": len(parsed), "errors": errors or None,
            "raised": store["raised"], "reopened": store["reopened"],
            "resolved": store["resolved"], "open_total": store["open_total"]}


def check_rankings(domain: str, location: str, language: str, limit: int,
                   sandbox: bool = False) -> tuple[dict, list[dict[str, Any]]]:
    """Diff fresh rankings against the previous snapshot.

    Significant losses (was in the top 20, now gone or down 5+) become
    recommendations; recoveries resolve earlier loss recommendations.
    Returns (summary, items) so the caller can snapshot the items.
    """
    payload = _dfs(["ranked", "--target", domain, "--limit", str(limit),
                    "--location", location, "--language", language], sandbox)
    items = rank_items(payload)
    new_map = {i["keyword"]: i for i in items}

    snapshots = drift_store.list_snapshots(domain)
    old_map = {}
    if snapshots:
        previous = drift_store.load(domain, snapshots[-1])
        old_map = {r["keyword"]: r for r in previous.get("rankings") or []}

    losses = []
    for keyword, old in old_map.items():
        was = old.get("position", 999)
        if was > 20:
            continue
        current = new_map.get(keyword)
        if current is None:
            losses.append({"keyword": keyword, "was": was, "now": None,
                           "severity": "high" if was <= 10 else "medium"})
        elif current["position"] - was >= 5:
            drop = current["position"] - was
            losses.append({"keyword": keyword, "was": was,
                           "now": current["position"],
                           "severity": "high" if drop >= 10 else "medium"})
    order = {"high": 0, "medium": 1}
    losses.sort(key=lambda l: (order[l["severity"]], l["was"]))
    for loss in losses[:RANK_LOSS_CAP]:
        if loss["now"] is None:
            finding = f"Ranking lost: '{loss['keyword']}' (was {loss['was']})"
            why = ("The page no longer ranks in the monitored set for a "
                   "former top-20 keyword — traffic on that term is at zero.")
            fix = ("Check the ranking URL is still live and indexed; "
                   "compare the current SERP to see what replaced you.")
        else:
            finding = (f"Ranking dropped: '{loss['keyword']}' "
                       f"{loss['was']} → {loss['now']}")
            why = ("A top-20 keyword slid 5+ positions — usually lost clicks "
                   "before it leaves page one entirely.")
            fix = ("Refresh the ranking page: search intent may have "
                   "shifted, or a competitor improved their coverage.")
        recommend_store.raise_rec(domain, {
            "url": (old_map[loss["keyword"]].get("url") or ""),
            "source": "skill:watch",
            "key": f"rank-loss-{_slug(loss['keyword'])}",
            "category": "rankings",
            "severity": loss["severity"],
            "confidence": "high",
            "finding": finding,
            "why": why,
            "fix": fix,
            "evidence": {"keyword": loss["keyword"], "was": loss["was"],
                         "now": loss["now"]},
        })

    recovered = 0
    for rec in recommend_store.list_recs(domain):
        if rec["source"] != "skill:watch" \
                or not rec["key"].startswith("rank-loss-"):
            continue
        evidence = rec.get("evidence") or {}
        keyword, was = evidence.get("keyword"), evidence.get("was")
        current = new_map.get(keyword or "")
        if keyword and current and isinstance(was, int) \
                and current["position"] <= was:
            recommend_store.set_status(domain, rec["id"], "resolved",
                                       note="ranking recovered")
            recovered += 1

    gained = [kw for kw in new_map if kw not in old_map]
    return ({"tracked": len(items), "previous_tracked": len(old_map),
             "losses_raised": min(len(losses), RANK_LOSS_CAP),
             "recovered": recovered, "new_keywords": len(gained),
             "cached": payload.get("cached")}, items)


def check_backlinks(domain: str, sandbox: bool = False) -> dict:
    payload = _dfs(["backlinks", "--target", domain], sandbox)
    return backlink_summary(payload)


def check_competitors(domain: str, competitors: list[str], location: str,
                      language: str, limit: int,
                      sandbox: bool = False) -> dict:
    """Snapshot each competitor's rankings; flag notable growth."""
    reports = []
    for comp in competitors[:3]:
        payload = _dfs(["ranked", "--target", comp, "--limit", str(limit),
                        "--location", location, "--language", language],
                       sandbox)
        items = rank_items(payload)
        store_key = f"competitor-{comp}"
        previous_keys = set()
        snapshots = drift_store.list_snapshots(store_key)
        if snapshots:
            previous = drift_store.load(store_key, snapshots[-1])
            previous_keys = {r["keyword"]
                             for r in previous.get("rankings") or []}
        drift_store.save(store_key, {"rankings": items})
        gained = [i["keyword"] for i in items
                  if i["keyword"] not in previous_keys]
        raised = False
        if previous_keys and len(gained) >= COMPETITOR_GAIN_MIN:
            recommend_store.raise_rec(domain, {
                "url": f"https://{comp}",
                "source": "skill:watch",
                "key": f"competitor-growth-{_slug(comp)}",
                "category": "competitive",
                "severity": "medium",
                "confidence": "high",
                "finding": f"Competitor {comp} gained {len(gained)} "
                           "new rankings",
                "why": ("They are publishing or optimising — each new "
                        "ranking is a query where you may now be invisible."),
                "fix": ("Review their newest ranking pages; decide which "
                        "queries warrant a competing page from you."),
                "evidence": {"competitor": comp,
                             "gained": len(gained),
                             "examples": gained[:10]},
            })
            raised = True
        reports.append({"competitor": comp, "tracked": len(items),
                        "new_keywords": len(gained), "rec_raised": raised})
    return {"competitors": reports}


def check_ai(domain: str, brand: str, prompts: str, location: str,
             language: str, sandbox: bool = False) -> dict:
    snap = _ai_visibility(domain, brand, prompts, location, language,
                          sandbox)
    return {"llm_mentions": snap.get("llm_mentions"),
            "llm_answers": snap.get("llm_answers"),
            "visibility_rate": snap.get("visibility_rate"),
            "aio_mentioned": snap.get("aio_mentioned")}


# ---------------------------------------------------------------------------
# Run + schedule
# ---------------------------------------------------------------------------

def run(domain: str, profile: str, pages: list[str],
        competitors: list[str], brand: str, prompts: str | None,
        location: str, language: str, limit: int,
        sandbox: bool = False) -> dict[str, Any]:
    started = time.time()
    cost_before = cost_ledger.report()["periods"]["all_time"]["cost_usd"]
    summary: dict[str, Any] = {"domain": domain, "profile": profile,
                               "checks": {}, "errors": {}}

    checks = PROFILES[profile]
    snapshot: dict[str, Any] = {}

    if "lint" in checks and pages:
        try:
            rules = rule_engine.load_rules()
            summary["checks"]["lint"] = check_lint(domain, pages, rules)
        except Exception as exc:  # noqa: BLE001 - record, never abort run
            summary["errors"]["lint"] = str(exc)[:200]

    if "rankings" in checks:
        try:
            result, items = check_rankings(domain, location, language,
                                           limit, sandbox)
            summary["checks"]["rankings"] = result
            snapshot["rankings"] = items
        except WatchError as exc:
            summary["errors"]["rankings"] = str(exc)

    if "backlinks" in checks:
        try:
            links = check_backlinks(domain, sandbox)
            if links:
                snapshot["backlinks"] = links
                summary["checks"]["backlinks"] = links
            else:
                summary["errors"]["backlinks"] = "shape not recognised"
        except WatchError as exc:
            summary["errors"]["backlinks"] = str(exc)

    if "competitors" in checks and competitors:
        try:
            summary["checks"]["competitors"] = check_competitors(
                domain, competitors, location, language, limit, sandbox)
        except WatchError as exc:
            summary["errors"]["competitors"] = str(exc)

    if "ai_visibility" in checks:
        if brand and prompts:
            try:
                ai = check_ai(domain, brand, prompts, location, language,
                              sandbox)
                summary["checks"]["ai_visibility"] = ai
                snapshot["mentions"] = {
                    "ai_mentions": ai.get("llm_mentions") or 0}
            except WatchError as exc:
                summary["errors"]["ai_visibility"] = str(exc)
        else:
            summary["checks"]["ai_visibility"] = \
                "skipped (needs --brand and --prompts)"

    if snapshot:
        drift_store.save(domain, snapshot)
        summary["snapshot_saved"] = sorted(snapshot)

    event_log.log(domain, "watch_completed",
                  f"Watch ({profile}): {len(summary['checks'])} check(s), "
                  f"{len(summary['errors'])} error(s)",
                  {"profile": profile,
                   "checks": sorted(summary["checks"]),
                   "errors": sorted(summary["errors"])})

    cost_after = cost_ledger.report()["periods"]["all_time"]["cost_usd"]
    summary["cost_usd"] = round(cost_after - cost_before, 4)
    summary["duration_s"] = round(time.time() - started, 1)
    return summary


def schedule_lines(domain: str, profile: str) -> dict[str, str]:
    python = sys.executable
    script = SCRIPTS_DIR / "watch.py"
    run_line = f'"{python}" "{script}" --domain {domain} --profile {profile}'
    when = "Mondays 07:00" if profile == "weekly" else "daily 07:00"
    return {
        "windows_schtasks":
            f'schtasks /Create /SC {"WEEKLY /D MON" if profile == "weekly" else "DAILY"} '
            f'/ST 07:00 /TN "OpenCode SEO watch - {domain}" /TR "{run_line}"',
        "cron":
            f'0 7 * * {"1" if profile == "weekly" else "*"} {run_line} '
            f'>> "{SCRIPTS_DIR.parent / "watch.log"}" 2>&1',
        "note": f"Runs {when}. Adjust --profile or the time to taste; the "
                "OS does the scheduling, nothing daemons in the background.",
    }


def _memory_fallbacks() -> dict[str, Any]:
    path = project_memory.find_project_file()
    if not path:
        return {}
    try:
        return project_memory.load(path)
    except Exception:  # noqa: BLE001 - memory is optional enrichment
        return {}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="watch", description="Scheduled monitoring bundle for a domain")
    parser.add_argument("action", nargs="?", default="run",
                        choices=["run", "schedule"])
    parser.add_argument("--domain", required=True)
    parser.add_argument("--profile", choices=sorted(PROFILES),
                        default="weekly")
    parser.add_argument("--pages", help="comma-separated URLs to lint")
    parser.add_argument("--competitors", help="comma-separated domains")
    parser.add_argument("--brand", help="brand name for AI visibility checks")
    parser.add_argument("--prompts", help="comma-separated AI prompts")
    parser.add_argument("--location", default="United States")
    parser.add_argument("--language", default="English")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--sandbox", action="store_true")
    parser.add_argument("--dry-run", action="store_true",
                        help="list what would run, call nothing")
    args = parser.parse_args(argv)

    domain = args.domain.strip().lower()
    if args.action == "schedule":
        print(json.dumps(schedule_lines(domain, args.profile), indent=2))
        return 0

    memory = _memory_fallbacks()
    pages = ([p.strip() for p in args.pages.split(",") if p.strip()]
             if args.pages else [f"https://{domain}"])
    competitors = ([c.strip() for c in args.competitors.split(",")
                    if c.strip()] if args.competitors
                   else list(memory.get("competitors") or []))
    brand = args.brand or (memory.get("site") or {}).get("name", "")

    if args.dry_run:
        print(json.dumps({
            "domain": domain, "profile": args.profile,
            "checks": PROFILES[args.profile], "pages": pages,
            "competitors": competitors,
            "brand": brand or None,
            "prompts": args.prompts or None,
            "note": "dry run - nothing was called or saved"},
            indent=2, ensure_ascii=False))
        return 0

    summary = run(domain, args.profile, pages, competitors, brand,
                  args.prompts, args.location, args.language, args.limit,
                  args.sandbox)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if not summary["errors"] else 1


if __name__ == "__main__":
    sys.exit(main())
