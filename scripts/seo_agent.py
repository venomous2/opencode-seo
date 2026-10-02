"""Autonomous SEO agent for the OpenCode SEO Suite.

Closes the loop the deterministic engine already provides:

    scan  -> lint every HTML page in a directory and persist findings with the
             fingerprint lifecycle (NEW / PERSISTING / REGRESSED)
    fix   -> resolve mechanical patches (seo_fix) and apply them to the files
    ship  -> branch, commit and open a review-ready pull request (gh CLI)
    run   -> scan + fix + ship in one pass (the autonomous loop)

Safety defaults: `fix` is a dry-run until --apply, `ship` is a dry-run until
--pr. The agent only ever commits files it patched itself. Every patch comes
from the fix engine's `status: ready` templates (rules/*/fix.patch) - it never
invents copy. Draft patches (title/meta text derived from page content) are
applied but listed separately in the brief so the PR reviewer can rewrite the
wording; pass --mechanical-only to skip them.

Usage:
    python scripts/seo_agent.py scan --dir ./public --domain example.com \\
        --base-url https://example.com
    python scripts/seo_agent.py fix  --dir ./public --domain example.com \\
        --base-url https://example.com --apply
    python scripts/seo_agent.py ship --domain example.com --pr
    python scripts/seo_agent.py run  --dir ./public --domain example.com \\
        --base-url https://example.com --pr

GitHub Actions wrapper: .github/workflows/seo-agent.yml
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

import event_log  # noqa: E402
import recommend_store  # noqa: E402
import rule_engine  # noqa: E402
import seo_fix  # noqa: E402
import seo_lint  # noqa: E402

FOOTER = "Report built by Lee Beirne - https://leebeirne.com"

DEFAULT_EXCLUDES = (
    ".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache",
    ".tox", ".next", ".svelte-kit", ".cache", "vendor",
)

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

BRANCH_PREFIX = "seo-agent"
COMMIT_PREFIX = "fix(seo)"


class AgentError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# Page discovery + URL mapping
# ---------------------------------------------------------------------------

def discover_html(root: Path, excludes: tuple[str, ...] = DEFAULT_EXCLUDES,
                  extra_excludes: tuple[str, ...] = ()) -> list[Path]:
    """Every .html/.htm file under root, minus build/dependency noise."""
    skip = {e.strip().lower().strip("/\\") for e in excludes if e.strip()}
    skip |= {e.strip().lower().strip("/\\") for e in extra_excludes if e.strip()}
    if not root.is_dir():
        raise AgentError(f"--dir is not a directory: {root}")
    found: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in (".html", ".htm"):
            continue
        rel_parts = [p.lower() for p in path.relative_to(root).parts[:-1]]
        if any(part in skip for part in rel_parts):
            continue
        found.append(path)
    return found


def page_url_for(path: Path, root: Path, base_url: str) -> str:
    """Map a repo file to its public URL.

    index.html maps to its directory URL; anything else keeps its filename.
    Without a base URL the file path is used as-is (local-only rules).
    """
    base = (base_url or "").rstrip("/")
    if not base:
        return str(path)
    rel = path.relative_to(root).as_posix()
    if rel.lower().endswith("index.html"):
        rel = rel[: -len("index.html")]
    return f"{base}/{rel}".rstrip("/") or base


# ---------------------------------------------------------------------------
# scan
# ---------------------------------------------------------------------------

def lint_files(paths: list[Path], rules: list[dict[str, Any]],
               root: Path, base_url: str = "") -> list[dict[str, Any]]:
    """Lint repo HTML with the URL-independent rule subset."""
    local_rules = seo_lint.filter_rules(rules, None, local=True)
    results = []
    for path in paths:
        html_text = path.read_text(encoding="utf-8", errors="replace")
        page = seo_lint.parse_html(html_text, page_url_for(path, root, base_url))
        outcome = rule_engine.run(page, local_rules)
        outcome["url"] = page_url_for(path, root, base_url)
        outcome["path"] = str(path)
        outcome["failed_ids"] = sorted(f["id"] for f in outcome["findings"])
        results.append(outcome)
    return results


def classify(domain: str, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Label each live finding NEW / PERSISTING / REGRESSED against memory.

    Runs against the pre-scan state, so the caller must classify before
    `recommend_store.save_lint_results` persists the run.
    """
    prior = recommend_store.replay(domain)
    rows: list[dict[str, Any]] = []
    for result in results:
        url = result.get("url", "")
        for finding in result.get("findings", []):
            rec_id = recommend_store.make_id(domain, url,
                                             f"rule:{finding['id']}",
                                             finding["id"])
            old = prior.get(rec_id)
            if old is None:
                state = "new"
            elif old.get("status") in ("done", "resolved"):
                state = "regressed"
            else:
                state = "persisting"
            rows.append({
                "id": rec_id,
                "url": url,
                "path": result.get("path", ""),
                "rule": finding["id"],
                "severity": finding.get("severity", "medium"),
                "state": state,
                "why": finding.get("why", ""),
                "fix": finding.get("fix", ""),
                "times_raised": (old or {}).get("times_raised", 0) + 1,
            })
    rows.sort(key=lambda r: (SEVERITY_ORDER.get(r["severity"], 9),
                             r["state"] != "regressed",
                             r["rule"]))
    return rows


def scan(domain: str, root: Path, rules: list[dict[str, Any]],
         base_url: str = "", excludes: tuple[str, ...] = (),
         persist: bool = True) -> dict[str, Any]:
    paths = discover_html(root, extra_excludes=excludes)
    results = lint_files(paths, rules, root, base_url)
    classified = classify(domain, results)
    saved = recommend_store.save_lint_results(domain, results, rules) \
        if persist else {"raised": 0, "reopened": 0, "resolved": 0}
    return {
        "domain": domain,
        "pages": [{"path": r["path"], "url": r["url"], "score": r["score"],
                   "failed": len(r["findings"])} for r in results],
        "findings": classified,
        "counts": {
            "pages": len(results),
            "new": sum(1 for f in classified if f["state"] == "new"),
            "persisting": sum(1 for f in classified if f["state"] == "persisting"),
            "regressed": sum(1 for f in classified if f["state"] == "regressed"),
            "total": len(classified),
        },
        "saved": saved,
    }


# ---------------------------------------------------------------------------
# fix
# ---------------------------------------------------------------------------

def collect_fixes(paths: list[Path], rules: list[dict[str, Any]],
                  root: Path, base_url: str, lang: str = "en",
                  only: str | None = None,
                  include_drafts: bool = True) -> list[dict[str, Any]]:
    """Patches per file. Only `status: ready` engine patches are eligible."""
    reports: list[dict[str, Any]] = []
    for path in paths:
        html_text = path.read_text(encoding="utf-8", errors="replace")
        url = page_url_for(path, root, base_url)
        page = seo_lint.parse_html(html_text, url)
        patches = seo_fix.collect_patches(page, rules, base_url, lang,
                                          only=only)
        ready = [p for p in patches if p.get("status") == "ready"]
        if not include_drafts:
            ready = [p for p in ready if not p.get("draft")]
        if not ready:
            continue
        reports.append({"path": path, "url": url, "patches": ready,
                        "drafts": [p for p in ready if p.get("draft")]})
    return reports


def apply_fixes(reports: list[dict[str, Any]],
                rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rewrite each file in place (with .bak) and re-lint to show the delta."""
    local_rules = seo_lint.filter_rules(rules, None, local=True)
    out: list[dict[str, Any]] = []
    for report in reports:
        path: Path = report["path"]
        html_text = path.read_text(encoding="utf-8", errors="replace")
        before = rule_engine.run(seo_lint.parse_html(html_text, report["url"]),
                                 local_rules)
        shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
        new_html, applied = seo_fix.apply_patches(html_text, report["patches"])
        path.write_text(new_html, encoding="utf-8")
        after = rule_engine.run(seo_lint.parse_html(new_html, report["url"]),
                                local_rules)
        out.append({
            "path": str(path),
            "url": report["url"],
            "applied": applied,
            "drafts": [p["rule_id"] for p in report["drafts"]],
            "before_score": before["score"],
            "after_score": after["score"],
            "delta": after["score"] - before["score"],
            "remaining": sorted(f["id"] for f in after["findings"]),
        })
    return out


# ---------------------------------------------------------------------------
# ship
# ---------------------------------------------------------------------------

def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True,
                          text=True)


def ship(domain: str, root: Path, files: list[Path], brief_path: Path | None,
         branch: str | None = None, base_branch: str = "main",
         open_pr: bool = False) -> dict[str, Any]:
    """Branch, commit and (optionally) open a PR for the agent's own edits.

    Dry-run by default: reports the plan and touches nothing. Only the given
    files are ever staged - never `git add -A`.
    """
    rels = sorted({str(f.relative_to(root)).replace("\\", "/")
                   if f.is_absolute() else str(f) for f in files})
    plan = {
        "domain": domain,
        "dry_run": not open_pr,
        "branch": branch or f"{BRANCH_PREFIX}/{date.today().strftime('%Y%m%d')}",
        "base_branch": base_branch,
        "files": rels,
        "commands": [],
    }
    if not rels:
        plan["note"] = "no patched files to ship"
        return plan

    b = plan["branch"]
    plan["commands"] = [
        f"git checkout -b {b}",
        f"git add {' '.join(rels)}",
        f'git commit -m "{COMMIT_PREFIX}: {len(rels)} file(s) from the '
        f'autonomous agent"',
        f"git push -u origin {b}",
        f"gh pr create --base {base_branch} --title "
        f'"{COMMIT_PREFIX}: autonomous SEO fixes" --body-file <brief>',
    ]
    if not open_pr:
        plan["note"] = ("dry-run - pass --pr (or --apply --pr) to execute; "
                        "commands listed above")
        return plan

    proc = _git(["rev-parse", "--is-inside-work-tree"], root)
    if proc.returncode != 0:
        raise AgentError(f"not a git repository: {root}")

    for cmd in (["checkout", "-b", b], ["add", *rels]):
        proc = _git(cmd, root)
        if proc.returncode != 0:
            raise AgentError(f"git {' '.join(cmd)} failed: "
                             f"{proc.stderr.strip()[:300]}")
    message = (f"{COMMIT_PREFIX}: {len(rels)} file(s) from the autonomous "
               f"agent\n\nFindings fixed: "
               + ", ".join(sorted({Path(r).stem for r in rels}))[:200])
    proc = _git(["commit", "-m", message], root)
    if proc.returncode != 0:
        raise AgentError(f"git commit failed: {proc.stderr.strip()[:300]}")
    proc = _git(["push", "-u", "origin", b], root)
    if proc.returncode != 0:
        raise AgentError(f"git push failed: {proc.stderr.strip()[:300]}")

    body_file = brief_path if brief_path and brief_path.is_file() else None
    cmd = ["gh", "pr", "create", "--base", base_branch, "--head", b,
           "--title", f"{COMMIT_PREFIX}: autonomous SEO fixes"]
    if body_file:
        cmd += ["--body-file", str(body_file)]
    else:
        cmd += ["--body", "Mechanical SEO fixes applied by the autonomous "
                          "agent. Review the draft copy before merging."]
    proc = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True)
    if proc.returncode != 0:
        raise AgentError(f"gh pr create failed: {proc.stderr.strip()[:300]}")

    plan["dry_run"] = False
    plan["pr_url"] = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
    plan["committed"] = rels
    event_log.log(domain, "agent_pr",
                  f"Opened PR with {len(rels)} SEO fix(es)",
                  {"branch": b, "files": rels, "pr": plan["pr_url"]})
    return plan


# ---------------------------------------------------------------------------
# brief
# ---------------------------------------------------------------------------

def write_brief(scan_report: dict[str, Any],
                fix_report: list[dict[str, Any]] | None = None,
                ship_plan: dict[str, Any] | None = None,
                out_dir: Path | None = None) -> Path:
    """The agent's weekly brief: state of the site + what it shipped."""
    domain = scan_report["domain"]
    counts = scan_report["counts"]
    reports_root = os.environ.get("SEO_REPORTS_DIR")
    target = out_dir or (Path(reports_root) / domain if reports_root
                         else Path.cwd())
    target.mkdir(parents=True, exist_ok=True)
    stamp = date.today().strftime("%Y-%m-%d")
    path = target / f"SEO-AGENT-{domain}-{stamp}.md"

    findings = scan_report["findings"]
    lines = [
        f"# SEO agent brief - {domain}",
        "",
        f"{stamp} - {counts['pages']} page(s) scanned, "
        f"{counts['total']} open finding(s): {counts['new']} new, "
        f"{counts['persisting']} persisting, {counts['regressed']} regressed.",
        "",
        "## Pages",
        "",
        "| Page | Score | Findings |",
        "|---|---|---|",
    ]
    for page in scan_report["pages"]:
        lines.append(f"| `{page['path']}` | {page['score']} | {page['failed']} |")

    for state, label in (("regressed", "Regressions"),
                         ("new", "New findings"),
                         ("persisting", "Persisting findings")):
        rows = [f for f in findings if f["state"] == state]
        if not rows:
            continue
        lines += ["", f"## {label} ({len(rows)})", ""]
        for f in rows:
            lines.append(f"- **{f['severity']}** `{f['rule']}` on `{f['url']}`"
                         + (f" (raised {f['times_raised']}x)"
                            if f["times_raised"] > 1 else "")
                         + f" - {f['why']}")

    if fix_report:
        lines += ["", f"## Fixes applied ({len(fix_report)} file(s))", "",
                  "| File | Score | Delta | Rules applied |",
                  "|---|---|---|---|"]
        for row in fix_report:
            applied = ", ".join(f"`{r}`" for r in row["applied"]) or "-"
            delta = f"{row['delta']:+d}" if row["delta"] else "0"
            lines.append(f"| `{row['path']}` | {row['before_score']} -> "
                         f"{row['after_score']} | {delta} | {applied} |")
        drafts = sorted({r for row in fix_report for r in row["drafts"]})
        if drafts:
            lines += ["", "### Draft copy to review", ""]
            lines += [f"- `{r}` - wording was derived from page content; "
                      f"rewrite before merge." for r in drafts]

    if ship_plan:
        lines += ["", "## Shipment", ""]
        if ship_plan.get("dry_run"):
            lines.append(f"Dry run. Branch `{ship_plan['branch']}` would "
                         f"contain: "
                         + ", ".join(f"`{f}`" for f in ship_plan["files"]))
        else:
            lines.append(f"Opened PR: {ship_plan.get('pr_url', '(unknown)')} "
                         f"from `{ship_plan['branch']}`.")
            lines.append("")
            lines.append("Merge it to make the fixes live; the next scan "
                         "auto-closes the matching recommendations.")

    top = [f for f in findings if f["state"] != "persisting"]
    lines += ["", "## Next step", ""]
    if top:
        first = top[0]
        lines.append(f"Fix `{first['rule']}` on `{first['url']}` - "
                     f"{first['why'] or 'highest-severity open finding'}")
    elif findings:
        lines.append("No new findings. Keep the current schedule and watch "
                     "the persisting list shrink.")
    else:
        lines.append("Clean scan. Raise coverage next: point the agent at "
                     "more of the site.")
    lines += ["", "---", "", FOOTER, ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _load_rules() -> list[dict[str, Any]]:
    try:
        return rule_engine.load_rules()
    except rule_engine.RuleError as exc:
        raise AgentError(f"rules: {exc}") from exc


def _resolve_paths(args: argparse.Namespace) -> list[Path]:
    root = Path(args.dir).resolve()
    return discover_html(root, extra_excludes=tuple(args.exclude or ()))


def cmd_scan(args: argparse.Namespace) -> int:
    rules = _load_rules()
    root = Path(args.dir).resolve()
    report = scan(args.domain, root, rules, args.base_url,
                  excludes=tuple(args.exclude or ()))
    brief = write_brief(report, out_dir=Path(args.out) if args.out else None)
    report["brief"] = str(brief)
    if args.format == "text":
        c = report["counts"]
        print(f"{args.domain}: {c['pages']} page(s), {c['total']} finding(s) "
              f"({c['new']} new, {c['persisting']} persisting, "
              f"{c['regressed']} regressed)")
        for f in report["findings"]:
            print(f"  [{f['state'].upper()}] {f['severity']} {f['rule']} "
                  f"on {f['url']}")
        print(f"brief: {brief}")
        return 0
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


def cmd_fix(args: argparse.Namespace) -> int:
    rules = _load_rules()
    root = Path(args.dir).resolve()
    paths = _resolve_paths(args)
    reports = collect_fixes(paths, rules, root, args.base_url, args.lang,
                            only=args.only,
                            include_drafts=not args.mechanical_only)
    if not args.apply:
        out = [{"path": str(r["path"]), "url": r["url"],
                "patches": r["patches"]} for r in reports]
        if args.format == "text":
            if not out:
                print("No mechanical fixes available - nothing to patch.")
            for row in out:
                print(f"{row['path']}")
                for p in row["patches"]:
                    draft = " [draft]" if p.get("draft") else ""
                    print(f"  {p['rule_id']}{draft}")
            return 0
        print(json.dumps({"dry_run": True, "files": out}, indent=2,
                         ensure_ascii=False))
        return 0
    applied = apply_fixes(reports, rules)
    if args.format == "text":
        if not applied:
            print("No mechanical fixes available - nothing patched.")
        for row in applied:
            print(f"{row['path']}: {row['before_score']} -> "
                  f"{row['after_score']} ({row['delta']:+d}) "
                  f"applied: {', '.join(row['applied'])}")
        return 0
    print(json.dumps({"applied": applied}, indent=2, ensure_ascii=False))
    return 0


def cmd_ship(args: argparse.Namespace) -> int:
    root = Path(args.dir).resolve()
    if args.files:
        files = [Path(f) for f in args.files]
    else:
        proc = _git(["status", "--porcelain"], root)
        if proc.returncode != 0:
            raise AgentError(f"git status failed: {proc.stderr.strip()[:300]}")
        files = []
        for line in proc.stdout.splitlines():
            entry = line[3:].strip().strip('"')
            if entry.lower().endswith((".html", ".htm")):
                files.append(root / entry)
    plan = ship(args.domain, root, files,
                Path(args.brief) if args.brief else None,
                branch=args.branch, base_branch=args.base_branch,
                open_pr=args.pr)
    if args.format == "text":
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        return 0
    print(json.dumps(plan, indent=2, ensure_ascii=False))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    rules = _load_rules()
    root = Path(args.dir).resolve()
    paths = _resolve_paths(args)

    scan_report = scan(args.domain, root, rules, args.base_url,
                       excludes=tuple(args.exclude or ()))
    reports = collect_fixes(paths, rules, root, args.base_url, args.lang,
                            only=args.only,
                            include_drafts=not args.mechanical_only)
    fix_report = apply_fixes(reports, rules) if (reports and args.apply) \
        else []
    if fix_report:
        # Re-scan after fixes so the brief reflects the post-fix state and
        # the recommendations auto-resolve.
        scan_report = scan(args.domain, root, rules, args.base_url,
                           excludes=tuple(args.exclude or ()))
        scan_report["fixes"] = fix_report

    patched = [Path(row["path"]) for row in fix_report]
    ship_plan = None
    if patched:
        out_dir = Path(args.out) if args.out else None
        brief = write_brief(scan_report, fix_report, out_dir=out_dir)
        ship_plan = ship(args.domain, root, patched, brief,
                         branch=args.branch, base_branch=args.base_branch,
                         open_pr=args.pr)
        scan_report["brief"] = str(brief)
    else:
        scan_report["brief"] = str(write_brief(
            scan_report, out_dir=Path(args.out) if args.out else None))
    scan_report["ship"] = ship_plan
    print(json.dumps(scan_report, indent=2, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="seo_agent",
        description="Autonomous SEO agent: scan, fix, ship")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p: argparse.ArgumentParser, scan_like: bool = True) -> None:
        p.add_argument("--domain", required=True,
                       help="domain key for the recommendation store")
        p.add_argument("--dir", default=".",
                       help="directory of HTML files (default: .)")
        p.add_argument("--base-url", default="",
                       help="public base URL (canonical/schema values)")
        p.add_argument("--exclude", action="append",
                       help="extra directory name to skip (repeatable)")
        p.add_argument("--format", choices=["json", "text"], default="json")
        if scan_like:
            p.add_argument("--out", default="",
                           help="brief output directory (default "
                                "$SEO_REPORTS_DIR/<domain> or cwd)")

    def add_fix_flags(p: argparse.ArgumentParser) -> None:
        p.add_argument("--lang", default="en", help="html lang patch value")
        p.add_argument("--only", help="restrict to one rule id")
        p.add_argument("--mechanical-only", action="store_true",
                       help="skip draft patches (title/meta copy)")
        p.add_argument("--apply", action="store_true",
                       help="rewrite files in place (writes .bak first)")

    p_scan = sub.add_parser("scan", help="lint + classify findings")
    add_common(p_scan)
    p_scan.set_defaults(func=cmd_scan)

    p_fix = sub.add_parser("fix", help="resolve and apply mechanical patches")
    add_common(p_fix, scan_like=False)
    add_fix_flags(p_fix)
    p_fix.set_defaults(func=cmd_fix)

    p_ship = sub.add_parser("ship", help="branch, commit, open a PR")
    p_ship.add_argument("--domain", required=True)
    p_ship.add_argument("--dir", default=".")
    p_ship.add_argument("--files", nargs="+",
                        help="files to ship (default: changed .html)")
    p_ship.add_argument("--brief", help="markdown file for the PR body")
    p_ship.add_argument("--branch", help="branch name")
    p_ship.add_argument("--base-branch", default="main")
    p_ship.add_argument("--pr", action="store_true",
                        help="actually push and open the PR (default dry-run)")
    p_ship.add_argument("--format", choices=["json", "text"], default="json")
    p_ship.set_defaults(func=cmd_ship)

    p_run = sub.add_parser("run", help="scan + fix + ship in one pass")
    add_common(p_run)
    add_fix_flags(p_run)
    p_run.add_argument("--branch", help="branch name for the PR")
    p_run.add_argument("--base-branch", default="main")
    p_run.add_argument("--pr", action="store_true",
                       help="actually push and open the PR (default dry-run)")
    p_run.set_defaults(func=cmd_run)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except AgentError as exc:
        print(json.dumps({"error": str(exc)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())