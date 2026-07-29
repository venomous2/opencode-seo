"""PR quality gate for the OpenCode SEO Suite.

Lints the HTML files changed in a pull request, diffs each file's score
against the base branch, annotates findings inline via GitHub workflow
commands, writes a markdown summary (to $GITHUB_STEP_SUMMARY when present,
plus a file for the PR comment), and exits non-zero on regressions.

Fully deterministic and offline: the rule engine runs on the files in the
repo — no DataForSEO calls, no secrets, no API spend.

Usage:
    python scripts/seo_pr_check.py --base origin/main --all-changed
    python scripts/seo_pr_check.py --base origin/main --files a.html b.html
    python scripts/seo_pr_check.py --files a.html --min-score 80 --max-drop 5

Gate defaults: fail on any NEW critical/high finding. --min-score adds a
floor per file; --max-drop caps the score regression vs the base branch.
Markdown is excluded by default — raw .md is not renderable HTML (lint the
built output of your static site generator instead); pass --ext to widen.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

import rule_engine  # noqa: E402
import seo_lint  # noqa: E402

DEFAULT_EXTENSIONS = (".html", ".htm")
MARKER = "<!-- seo-pr-gate -->"
FAIL_SEVERITIES = ("critical", "high")


class GitError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# git plumbing (thin wrappers — the logic lives in compare/gate/summarise)
# ---------------------------------------------------------------------------

def _git(args: list[str]) -> str:
    proc = subprocess.run(["git", *args], capture_output=True, text=True)
    if proc.returncode != 0:
        raise GitError(proc.stderr.strip()[:300])
    return proc.stdout


def git_show(ref: str, path: str) -> str | None:
    """File content at a ref; None when it doesn't exist there."""
    proc = subprocess.run(["git", "show", f"{ref}:{path}"],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return None
    return proc.stdout


def changed_files(base: str, extensions: tuple[str, ...]) -> list[str]:
    out = _git(["diff", "--name-only", "--diff-filter=ACMR",
                f"{base}...HEAD", "--"] + [f"*{e}" for e in extensions])
    return [line.strip() for line in out.splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# Lint + compare
# ---------------------------------------------------------------------------

def lint_text(html_text: str, path: str,
              rules: list[dict[str, Any]]) -> dict[str, Any]:
    page = seo_lint.parse_html(html_text, path)
    outcome = rule_engine.run(
        page, seo_lint.filter_rules(rules, None, local=True))
    outcome["url"] = path
    return outcome


def compare(before: dict[str, Any] | None,
            after: dict[str, Any]) -> dict[str, Any]:
    """Score delta + new/fixed findings between two lint outcomes."""
    after_ids = {f["id"] for f in after["findings"]}
    before_ids = {f["id"] for f in before["findings"]} if before else set()
    new_ids = sorted(after_ids - before_ids)
    fixed_ids = sorted(before_ids - after_ids)
    return {
        "path": after["url"],
        "before_score": before["score"] if before else None,
        "after_score": after["score"],
        "delta": (after["score"] - before["score"]) if before else None,
        "new": [f for f in after["findings"] if f["id"] in new_ids],
        "fixed": fixed_ids,
        "outcome": after,
    }


def gate_failures(rows: list[dict[str, Any]], min_score: int | None,
                  max_drop: int | None,
                  fail_on_new: bool = True) -> list[str]:
    reasons = []
    for row in rows:
        path = row["path"]
        if min_score is not None and row["after_score"] < min_score:
            reasons.append(f"{path} scored {row['after_score']} "
                           f"(below --min-score {min_score})")
        if max_drop is not None and row["delta"] is not None \
                and -row["delta"] > max_drop:
            reasons.append(f"{path} dropped {-row['delta']} points "
                           f"(> --max-drop {max_drop})")
        if fail_on_new:
            bad = [f for f in row["new"]
                   if f["severity"] in FAIL_SEVERITIES]
            if bad:
                ids = ", ".join(f["id"] for f in bad)
                reasons.append(f"{path} introduces new "
                               f"critical/high finding(s): {ids}")
    return reasons


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def summarise(rows: list[dict[str, Any]], failures: list[str],
              min_score: int | None, max_drop: int | None) -> str:
    lines = [MARKER, f"## SEO gate — {len(rows)} file(s) checked, "
                     f"{len(failures)} failure(s)", ""]
    if rows:
        lines.append("| File | Before | After | Δ | New | Fixed |")
        lines.append("|---|---|---|---|---|---|")
        for row in rows:
            before = (str(row["before_score"])
                      if row["before_score"] is not None else "new file")
            delta = ""
            if row["delta"] is not None:
                delta = f"+{row['delta']}" if row["delta"] >= 0 \
                    else str(row["delta"])
            lines.append(f"| `{row['path']}` | {before} "
                         f"| {row['after_score']} | {delta or '—'} "
                         f"| {len(row['new'])} | {len(row['fixed'])} |")
    for row in rows:
        if not row["new"]:
            continue
        lines.append(f"\n### `{row['path']}` — new findings\n")
        for f in row["new"]:
            line = f"- **{f['severity']}** `{f['id']}` — {f['why']}"
            if f["fix"]:
                line += f" *fix: {f['fix']}*"
            lines.append(line)
    conditions = []
    if min_score is not None:
        conditions.append(f"min score {min_score}")
    if max_drop is not None:
        conditions.append(f"max drop {max_drop}")
    conditions.append("fails on new critical/high")
    lines.append(f"\n**Gate:** {' · '.join(conditions)}")
    if failures:
        lines.append("\n**FAIL** — " + "; ".join(failures))
    else:
        lines.append("\n**PASS** — no regressions detected")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="seo_pr_check",
        description="PR quality gate: lint changed HTML files, diff "
                    "against the base branch, fail on regressions")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--all-changed", action="store_true",
                        help="lint every changed file vs --base")
    source.add_argument("--files", nargs="+",
                        help="explicit files (base diff still applied)")
    parser.add_argument("--base", default="HEAD~1",
                        help="git ref to compare against")
    parser.add_argument("--ext", default=",".join(DEFAULT_EXTENSIONS),
                        help="comma-separated extensions (default .html,.htm)")
    parser.add_argument("--min-score", type=int,
                        help="fail if any file scores below this")
    parser.add_argument("--max-drop", type=int,
                        help="fail if any file drops more than N points")
    parser.add_argument("--no-fail-new", action="store_true",
                        help="don't fail on new critical/high findings")
    parser.add_argument("--out", default="seo-pr-summary.md",
                        help="markdown summary for the PR comment")
    args = parser.parse_args(argv)

    extensions = tuple("." + e.lstrip(".")
                       for e in args.ext.split(",") if e.strip())
    try:
        files = changed_files(args.base, extensions) \
            if args.all_changed else sorted(args.files)
    except GitError as exc:
        print(json.dumps({"error": f"git: {exc}"}))
        return 1

    try:
        rules = rule_engine.load_rules()
    except rule_engine.RuleError as exc:
        print(json.dumps({"error": str(exc)}))
        return 1

    rows = []
    for path in files:
        if not path.lower().endswith(extensions):
            continue
        current = git_show("HEAD", path)
        if current is None:
            continue  # deleted in this PR
        before_text = git_show(args.base, path)
        before = lint_text(before_text, path, rules) \
            if before_text is not None else None
        rows.append(compare(before, lint_text(current, path, rules),))

    failures = gate_failures(rows, args.min_score, args.max_drop,
                             fail_on_new=not args.no_fail_new)

    # inline annotations for every current finding on a changed file
    if rows:
        print(seo_lint.render_github([r["outcome"] for r in rows]))

    summary = summarise(rows, failures, args.min_score, args.max_drop)
    Path(args.out).write_text(summary, encoding="utf-8")
    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary:
        with open(step_summary, "a", encoding="utf-8") as fh:
            fh.write(summary)
    print(f"::notice title=SEO gate::{len(rows)} file(s) checked, "
          f"{len(failures)} failure(s) — summary written to {args.out}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
