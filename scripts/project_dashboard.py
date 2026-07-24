"""Project dashboard ("mission control") for the OpenCode SEO Suite.

Aggregates the suite's per-domain stores — the recommendation queue, drift
snapshots, the event timeline and the cost ledger — into one branded,
standalone HTML page rendered by report_build.py. Actions first, charts
second: the page answers "what should I do next?", not "how many charts
can we draw?".

Usage:
    python scripts/project_dashboard.py --domain example.com
    python scripts/project_dashboard.py --domain example.com --out dash.html
    python scripts/project_dashboard.py --domain example.com --limit 15

Output: DASHBOARD-<domain>-<date>.md + .html in $SEO_REPORTS_DIR/<domain>/
when the env var is set, else the current working directory.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

import cost_ledger  # noqa: E402
import drift_store  # noqa: E402
import event_log  # noqa: E402
import recommend_store  # noqa: E402
import report_build  # noqa: E402

# overall health = weighted blend, matching workflow-site-audit's pillars
PILLAR_WEIGHTS = {"technical": 0.30, "content": 0.25, "authority": 0.20,
                  "cwv": 0.15, "ai_search": 0.10}

EVENT_LABELS = {
    "rec_raised": "Finding raised",
    "rec_reopened": "Regression",
    "rec_status": "Status change",
    "lint_saved": "Lint saved",
    "snapshot_saved": "Snapshot",
    "note": "Note",
}


def overall_score(snapshot: dict[str, Any]) -> float | None:
    scores = snapshot.get("scores") or {}
    if not scores:
        return None
    if all(k in scores for k in PILLAR_WEIGHTS):
        return round(sum(scores[k] * w for k, w in PILLAR_WEIGHTS.items()), 1)
    values = [v for v in scores.values() if isinstance(v, (int, float))]
    return round(sum(values) / len(values), 1) if values else None


def _cell(text: Any, limit: int = 0) -> str:
    text = str(text if text is not None else "").replace("|", "\\|")
    text = " ".join(text.split())
    if limit and len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"
    return text or "—"


def _short_url(url: str, limit: int = 48) -> str:
    for prefix in ("https://", "http://"):
        if url.startswith(prefix):
            url = url[len(prefix):]
    return url if len(url) <= limit else url[: limit - 1] + "…"


def _humanise(finding: str) -> str:
    return finding.replace("-", " ").replace("_", " ").capitalize()


def _ts(ts: int | float | None, with_time: bool = False) -> str:
    if not ts:
        return "—"
    fmt = "%d %b %Y %H:%M" if with_time else "%d %b %Y"
    return datetime.fromtimestamp(int(ts)).strftime(fmt)


def _chart(spec: dict[str, Any]) -> str:
    # trailing blank line: report_build's fence parser needs it before the
    # next block or heading
    return "```chart\n" + json.dumps(spec) + "\n```\n"


def build_markdown(domain: str, limit: int = 10
                   ) -> tuple[str, dict[str, Any]]:
    """Assemble the dashboard markdown + the meta dict for the CLI JSON."""
    store = recommend_store.summary(domain)
    actionable = recommend_store.list_recs(domain)
    closed = recommend_store.list_recs(domain, include_closed=True)
    wins = sorted((r for r in closed if r["status"] in ("done", "resolved")),
                  key=lambda r: -r["updated"])[:limit]

    snapshots = drift_store.list_snapshots(domain)
    latest = drift_store.load(domain, snapshots[-1]) if snapshots else None
    previous = drift_store.load(domain, snapshots[-2]) \
        if len(snapshots) >= 2 else None
    health = overall_score(latest) if latest else None
    prev_health = overall_score(previous) if previous else None
    health_delta = round(health - prev_health, 1) \
        if health is not None and prev_health is not None else None

    spend = cost_ledger.report()["periods"]["last_30d"]["cost_usd"]
    recent_events = event_log.events(domain, limit=15)

    md: list[str] = []
    md.append(f"*Generated {date.today().strftime('%d %B %Y')} — action "
              "queue first, charts second.*\n")

    # -- health -------------------------------------------------------------
    md.append("## Health\n")
    if health is not None:
        delta_txt = ""
        if health_delta is not None:
            sign = "+" if health_delta >= 0 else "−"
            delta_txt = f" — {sign}{abs(health_delta):g} vs previous snapshot"
        md.append(f"Overall SEO health: **{health:g}/100**{delta_txt}, "
                  f"from {len(snapshots)} drift snapshot(s).\n")
        md.append(_chart({"type": "donut", "title": "Overall SEO health",
                          "value": health, "max": 100}))
        scores = latest.get("scores") or {}
        if scores:
            md.append(_chart({
                "type": "bar", "title": "Pillar scores (latest snapshot)",
                "data": [[k.replace("_", " ").title(), v]
                         for k, v in scores.items()], "max": 100}))
        if previous is not None:
            for spec in drift_store.build_chart_specs(previous, latest):
                md.append(_chart(spec))
                break  # the pillar compare chart only — keep the page lean
        if len(snapshots) >= 3:
            trend = []
            for ts in snapshots[-12:]:
                score = overall_score(drift_store.load(domain, ts))
                if score is not None:
                    trend.append([_ts(ts), score])
            if len(trend) >= 2:
                md.append(_chart({"type": "line",
                                  "title": "Health trend (last snapshots)",
                                  "data": trend, "max": 100}))
    else:
        md.append("No drift snapshots yet — health tracking starts when the "
                  "first audit saves one (`drift_store.py save`).\n")

    # -- needs attention ------------------------------------------------------
    md.append("\n## Needs attention\n")
    by_sev = store["actionable_by_severity"]
    md.append(_chart({"type": "stats", "data": [
        ["Actionable recommendations", str(store["actionable"])],
        ["Critical open", str(by_sev["critical"])],
        ["Auto-fixable open", str(store["auto_fixable_open"])],
        ["Fixed / resolved", str(len(wins))],
        ["API spend (30 days)", f"${spend:.2f}"],
    ]}))

    # -- top actions ----------------------------------------------------------
    md.append("\n## Top actions\n")
    if actionable:
        md.append("*Ordered by priority score (impact x confidence, with "
                  "auto-fixable and persistence nudges).*\n")
        md.append("| Priority | Severity | Action | Why | Status | Fixable |")
        md.append("|---|---|---|---|---|---|")
        for rec in actionable[:limit]:
            action = _humanise(rec["finding"])
            if rec["url"]:
                action += f" — {_short_url(rec['url'])}"
            est = (rec.get("evidence") or {}).get("est_monthly_clicks")
            if isinstance(est, (int, float)) and est > 0:
                action += f" *(~{est:g} clicks/mo at stake)*"
            fixable = "✓ auto" if rec["auto_fixable"] else "manual"
            md.append("| {pri} | {sev} | {act} | {why} | {status} | {fix} |"
                      .format(pri=rec.get("priority", "—"),
                              sev=rec["severity"], act=_cell(action, 80),
                              why=_cell(rec["why"], 100),
                              status=rec["status"], fix=fixable))
        remaining = store["actionable"] - min(limit, len(actionable))
        if remaining > 0:
            md.append(f"\n*…and {remaining} more in the queue "
                      f"(`recommend_store.py list --domain {domain}`).*")
    else:
        md.append("The queue is empty. Populate it with "
                  f"`python scripts/seo_lint.py --url <page> --save "
                  f"--domain {domain}` or a full site audit.")

    # -- recent wins ------------------------------------------------------------
    if wins:
        md.append("\n## Recent wins\n")
        md.append("| Fixed | How | When |")
        md.append("|---|---|---|")
        for rec in wins:
            how = "auto-resolved (re-lint passed)" \
                if rec["status"] == "resolved" else "marked done"
            md.append(f"| {_cell(_humanise(rec['finding']), 60)} | {how} "
                      f"| {_ts(rec['updated'])} |")

    # -- activity -----------------------------------------------------------------
    if recent_events:
        md.append("\n## Recent activity\n")
        md.append("| When | Event | Detail |")
        md.append("|---|---|---|")
        for event in reversed(recent_events):
            label = EVENT_LABELS.get(event.get("type", ""),
                                     event.get("type", "event"))
            md.append(f"| {_ts(event.get('ts'), with_time=True)} | {label} "
                      f"| {_cell(event.get('summary', ''), 90)} |")

    md.append("")
    meta = {
        "domain": domain,
        "actionable": store["actionable"],
        "critical_open": by_sev["critical"],
        "auto_fixable_open": store["auto_fixable_open"],
        "wins": len(wins),
        "health": health,
        "health_delta": health_delta,
        "snapshots": len(snapshots),
    }
    return "\n".join(md), meta


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="project_dashboard",
        description="Mission-control HTML dashboard for a domain")
    parser.add_argument("--domain", required=True)
    parser.add_argument("--out", help="output .html path")
    parser.add_argument("--limit", type=int, default=10,
                        help="rows shown in the action / wins tables")
    args = parser.parse_args(argv)

    domain = args.domain.strip().lower()
    markdown, meta = build_markdown(domain, limit=args.limit)

    reports_root = os.environ.get("SEO_REPORTS_DIR")
    out_dir = Path(reports_root) / domain if reports_root else Path.cwd()
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = date.today().strftime("%Y-%m-%d")
    md_path = out_dir / f"DASHBOARD-{domain}-{stamp}.md"
    md_path.write_text(markdown, encoding="utf-8")
    html_path = Path(args.out) if args.out else md_path.with_suffix(".html")
    report_build.build(md_path, html_path, brand="Lee Beirne",
                       title=f"Project Dashboard — {domain}",
                       footer=report_build.DEFAULT_FOOTER)

    print(json.dumps({**meta,
                      "markdown": str(md_path.resolve()),
                      "html": str(html_path.resolve())},
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
