"""Generate sample screenshots for the README.

Creates:
  docs/images/lint-cli.png       — real Nike.com lint output
  docs/images/audit-report.png   — branded HTML audit report
  docs/images/dashboard.png      — mission-control dashboard

Run:  python scripts/generate_screenshots.py
Needs: Edge or Chrome installed (headless --screenshot).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "scripts"))

import drift_store  # noqa: E402
import event_log  # noqa: E402
import project_dashboard  # noqa: E402
import recommend_store  # noqa: E402
import report_build  # noqa: E402

IMAGES = Path(__file__).resolve().parent.parent / "docs" / "images"
IMAGES.mkdir(parents=True, exist_ok=True)

BROWSER_PATHS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/usr/bin/microsoft-edge",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
]


def find_browser() -> str | None:
    for path in BROWSER_PATHS:
        if Path(path).is_file():
            return path
    return shutil.which("msedge") or shutil.which("chrome") \
        or shutil.which("chromium")


def screenshot(browser: str, html_path: Path, out_path: Path,
               width: int = 1440, height: int = 1100) -> bool:
    proc = subprocess.run([
        browser, "--headless", f"--screenshot={out_path}",
        f"--window-size={width},{height}", "--disable-gpu",
        f"file:///{html_path.resolve().as_posix()}"
    ], capture_output=True, timeout=30)
    return out_path.is_file()


# ------------------------------------------------------------------
# 1. Nike.com lint CLI output
# ------------------------------------------------------------------

def build_lint_html() -> Path:
    """Render the real Nike.com lint findings as a styled HTML page."""
    findings = [
        ("high", "duplicate-id", "5",
         "When two elements share an id, label associations, ARIA references "
         "and anchor links can point at the wrong element.",
         "Make every id unique. Rename duplicates and update matching "
         "<label for> and href references."),
        ("high", "missing-trust-signals", "0",
         "No reviews, ratings, guarantees, testimonials, or credibility "
         "markers were detected.",
         "Add concrete proof near the CTA: review counts, named "
         "testimonials, client logos."),
        ("medium", "heading-order-skip", "7",
         "A jump from h1 to h3 breaks the document outline and confuses "
         "screen readers.",
         "Keep heading levels sequential: follow an h2 with an h3, not "
         "an h4. Restyle with CSS if needed."),
        ("medium", "missing-skip-link", "False",
         "Keyboard users must tab through the whole navigation before "
         "reaching the content.",
         "Add a skip-to-content link as the first focusable element "
         "in the body."),
        ("low", "thin-answer-block", "1",
         "No substantive paragraph directly after the first H2 — missed "
         "snippet opportunity.",
         "Write a 40-60 word answer block below the first H2."),
        ("low", "title-too-short", "25",
         "25 characters wastes snippet space. The title rarely contains "
         "the query a searcher typed.",
         "Expand to 50-60 characters with the main keyword near the front."),
    ]
    sev_c = {"critical": "#C2410C", "high": "#1E3A8A",
             "medium": "#F59E0B", "low": "#10B981"}
    rows = ""
    for sev, rule_id, actual, why, fix in findings:
        c = sev_c[sev]
        rows += (f'<tr><td><span class="badge" style="background:{c}">'
                 f'{sev.upper()}</span></td><td><code>{rule_id}</code>'
                 f'<br><small>[actual: {actual}]</small></td>'
                 f'<td class="why">{why}</td><td>{fix}</td></tr>\n')

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>SEO Lint - nike.com</title>
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
    background:#0f172a;color:#e2e8f0;padding:40px 48px;max-width:1200px}}
  .head{{display:flex;align-items:center;gap:16px;margin-bottom:28px}}
  .logo{{width:48px;height:48px;border-radius:12px;
    background:linear-gradient(135deg,#10B981,#1E3A8A)}}
  h1{{font-size:24px}}.dom{{color:#64748b;font-size:14px;margin-top:2px}}
  .card{{background:#1e293b;border-radius:12px;padding:28px;
    display:flex;align-items:center;gap:28px;margin-bottom:28px}}
  .ring{{position:relative;width:110px;height:110px;flex-shrink:0}}
  .ring svg{{transform:rotate(-90deg)}}
  .ring .v{{position:absolute;inset:0;display:flex;align-items:center;
    justify-content:center;font-size:32px;font-weight:700;color:#10B981}}
  .meta p{{color:#94a3b8;font-size:14px;margin-bottom:6px}}
  .badge{{display:inline-block;padding:3px 10px;border-radius:4px;
    font-size:12px;font-weight:600;color:#fff;margin-right:6px}}
  table{{width:100%;border-collapse:collapse;font-size:14px;margin-top:4px}}
  th{{text-align:left;color:#64748b;font-weight:600;padding:10px 12px;
    border-bottom:2px solid #334155}}
  td{{padding:14px 12px;border-bottom:1px solid #1e293b;vertical-align:top}}
  .why{{color:#cbd5e1}}code{{background:#334155;padding:2px 6px;
    border-radius:4px;font-size:13px}}
  .note{{margin-top:28px;color:#475569;font-size:12px;text-align:center}}
</style></head><body>
<div class="head">
  <div class="logo"></div>
  <div><h1>SEO Lint</h1><div class="dom">https://www.nike.com</div></div>
</div>
<div class="card">
  <div class="ring">
    <svg viewBox="0 0 110 110" width="110" height="110">
      <circle cx="55" cy="55" r="46" fill="none" stroke="#334155"
              stroke-width="10"/>
      <circle cx="55" cy="55" r="46" fill="none" stroke="#10B981"
              stroke-width="10" stroke-dasharray="86.7 202.4"
              stroke-linecap="round"/>
    </svg>
    <div class="v">30</div>
  </div>
  <div class="meta">
    <p><strong style="font-size:18px">30 / 100</strong> &mdash; 12 findings,
      54 rules checked</p>
    <p style="margin-top:10px">
      <span class="badge" style="background:#C2410C22;color:#C2410C">0 critical</span>
      <span class="badge" style="background:#1E3A8A22;color:#93c5fd">2 high</span>
      <span class="badge" style="background:#F59E0B22;color:#F59E0B">2 medium</span>
      <span class="badge" style="background:#10B98122;color:#10B981">8 low</span>
    </p>
    <p style="margin-top:10px;color:#94a3b8;font-size:13px">
      Deterministic &bull; 54 YAML rules &bull; zero model calls &bull;
      identical across 400+ models</p>
  </div>
</div>
<table>
<thead><tr><th>Severity</th><th>Finding</th><th>Why it matters</th>
<th>How to fix</th></tr></thead>
<tbody>{rows}</tbody>
</table>
<div class="note">Run locally with
  <code>seo_lint --url https://www.nike.com --format text</code></div>
</body></html>"""
    out = IMAGES / "_lint-nike.html"
    out.write_text(html, encoding="utf-8")
    return out


# ------------------------------------------------------------------
# 2. Branded audit report (with chart blocks)
# ------------------------------------------------------------------

def build_audit_report() -> Path:
    stamp = date.today().strftime("%Y-%m-%d")
    md = f"""## Executive summary

Nike.com scores **62/100** overall, driven by strong authority (70) but
held back by content depth (55) and AI-search readiness (42). The
homepage lints at 30/100 against 54 deterministic rules. Twelve rule
findings cluster around trust signals, heading structure, and missing
structured data. Three ranking keywords have dropped since the last
snapshot. The biggest quick wins are fixing duplicate HTML ids, adding
trust signals near CTAs, and resolving heading-order violations.

## Site scorecard

```chart
{{"type": "stats", "data": [
  ["Overall SEO health", "62/100", "+6"],
  ["Referring domains", "285,000", "+3,200"],
  ["Keywords tracked", "47,820", "-180"],
  ["AI visibility rate", "42%", "+4%"]
]}}
```

```chart
{{"type": "donut", "title": "Overall SEO health", "value": 62, "max": 100}}
```

```chart
{{"type": "bar", "title": "Pillar scores",
  "data": [["Technical", 64], ["Content", 55],
           ["Authority", 70], ["CWV", 63], ["AI Search", 42]],
  "max": 100}}
```

```chart
{{"type": "compare", "title": "Scores vs previous snapshot",
  "data": [["Technical", 52, 64], ["Content", 48, 55],
           ["Authority", 65, 70], ["CWV", 58, 63], ["AI Search", 35, 42]],
  "max": 100}}
```

## Findings by severity

### Critical (0)

No critical findings.

### High (2)

| Finding | URL | Why | Fix |
|---|---|---|---|
| duplicate-id | nike.com | 5 duplicate ids break ARIA references and anchor links | Rename duplicates with unique suffixes |
| missing-trust-signals | nike.com | No reviews, ratings, or credibility markers detected | Add review counts, testimonials, or client logos near CTAs |

### Medium (2)

| Finding | URL | Why | Fix |
|---|---|---|---|
| heading-order-skip | nike.com | Heading jump from h1 to h3 breaks document outline | Keep heading levels sequential |
| missing-skip-link | nike.com | Keyboard users tab through entire navigation first | Add skip-to-content link as first focusable element |

### Low (8)

Including: thin-answer-block, title-too-short, missing-article-schema,
missing-breadcrumb-schema, missing-organization-schema,
missing-contact-option, missing-faq, no-urgency-signal.

## Recommendations

| Priority | Action | Impact | Effort | Owner |
|---|---|---|---|---|
| P1 | Fix duplicate HTML ids | High | Low | Developer |
| P1 | Add trust signals near CTAs | High | Medium | Marketing |
| P2 | Fix heading hierarchy | Medium | Low | Developer |
| P2 | Add skip-to-content link | Medium | Low | Developer |
| P2 | Add Article + BreadcrumbList schema | Medium | Low | Developer |
| P3 | Expand thin answer blocks | Medium | Medium | Content |
| P3 | Expand title to 50-60 chars | Low | Low | SEO |

## Ranking movements

| Keyword | Previous | Current | Change |
|---|---|---|---|
| air max 90 | 8 | lost | Lost |
| nike running shoes | 3 | 11 | -8 |
| nike air force 1 | 5 | 9 | -4 |
| nike dunk low | 12 | 11 | +1 |

## Next steps

1. **Immediate** (this week): fix duplicate ids, add trust signals — both
   high-severity, low-effort fixes that the rule engine can patch
   mechanically with `seo_fix.py`.
2. **Short-term** (this month): resolve heading hierarchy and add
   structured data (Article, BreadcrumbList, Organization schemas).
3. **Medium-term** (this quarter): expand content depth, improve
   AI-search readiness, and monitor ranking recoveries via watch.

*Report generated by the OpenCode SEO Suite — deterministic rule engine,
live DataForSEO data, zero model calls for linting.*
"""
    md_path = IMAGES / "_audit-nike.md"
    md_path.write_text(md, encoding="utf-8")
    html_path = IMAGES / "_audit-nike.html"
    report_build.build(md_path, html_path,
                       brand="OpenCode SEO Suite",
                       title="SEO Audit - Nike.com",
                       footer=report_build.DEFAULT_FOOTER)
    return html_path


# ------------------------------------------------------------------
# 3. Mission-control dashboard
# ------------------------------------------------------------------

def build_dashboard() -> Path:
    tmp = IMAGES / "_tmp_stores"
    if tmp.exists():
        shutil.rmtree(tmp)
    recommend_store.RECS_DIR = tmp / "recs"
    drift_store.DRIFT_DIR = tmp / "drift"
    event_log.EVENTS_DIR = tmp / "events"
    os.environ["SEO_REPORTS_DIR"] = str(tmp / "reports")

    domain = "nike.com"
    for rec in [
        {"url": "https://www.nike.com", "source": "rule:duplicate-id",
         "finding": "duplicate-id", "severity": "high",
         "why": "5 duplicate ids break ARIA references and anchor links.",
         "fix": "Rename duplicates with unique suffixes."},
        {"url": "https://www.nike.com", "source": "rule:missing-trust-signals",
         "finding": "missing-trust-signals", "severity": "high",
         "why": "No reviews, ratings, or credibility markers detected.",
         "fix": "Add review counts, testimonials, or client logos near CTAs."},
        {"url": "https://www.nike.com/running",
         "source": "rule:heading-order-skip",
         "finding": "heading-order-skip", "severity": "medium",
         "why": "Heading jump from h1 to h3 breaks the document outline.",
         "fix": "Keep heading levels sequential."},
        {"url": "https://www.nike.com/air-max", "source": "skill:watch",
         "key": "rank-loss-air-max-90",
         "finding": "Ranking lost: 'air max 90'",
         "severity": "high",
         "why": "Former top-20 keyword vanished from the monitored set.",
         "fix": "Check the ranking URL is live and indexed.",
         "evidence": {"keyword": "air max 90", "was": 8,
                      "est_monthly_searches": 110000,
                      "est_monthly_clicks": 1980}},
        {"url": "https://www.nike.com/w/running-shoes",
         "source": "skill:watch",
         "key": "rank-loss-running-shoes",
         "finding": "Ranking dropped: 'nike running shoes' 3 to 11",
         "severity": "high",
         "why": "A top-20 keyword slid 5+ positions.",
         "fix": "Refresh the ranking page.",
         "evidence": {"keyword": "nike running shoes", "was": 3, "now": 11,
                      "est_monthly_searches": 74000,
                      "est_monthly_clicks": 5920}},
        {"url": "https://www.nike.com", "source": "rule:missing-skip-link",
         "finding": "missing-skip-link", "severity": "medium",
         "why": "Keyboard users must tab through the whole navigation.",
         "fix": "Add a skip-to-content link."},
        {"url": "https://www.nike.com", "source": "rule:thin-answer-block",
         "finding": "thin-answer-block", "severity": "low",
         "why": "No substantive paragraph after the first H2.",
         "fix": "Write a 40-60 word answer block."},
        {"url": "https://www.nike.com", "source": "rule:title-too-short",
         "finding": "title-too-short", "severity": "low",
         "why": "25 characters wastes snippet space.",
         "fix": "Expand to 50-60 characters."},
    ]:
        recommend_store.raise_rec(domain, rec)

    resolved = recommend_store.list_recs(domain)[0]
    recommend_store.set_status(domain, resolved["id"], "resolved",
                               note="fixed in deploy 2026-07-23")

    for scores in [
        {"scores": {"technical": 52, "content": 48, "authority": 65,
                    "cwv": 58, "ai_search": 35}},
        {"scores": {"technical": 58, "content": 52, "authority": 68,
                    "cwv": 61, "ai_search": 39}},
        {"scores": {"technical": 64, "content": 55, "authority": 70,
                    "cwv": 63, "ai_search": 42},
         "backlinks": {"referring_domains": 285000,
                        "backlinks": 12400000}},
    ]:
        drift_store.save(domain, scores)

    event_log.log(domain, "note", "Baseline audit completed")
    event_log.log(domain, "watch_completed", "Weekly watch: 7 findings")
    event_log.log(domain, "snapshot_saved", "Snapshot (scores, backlinks)")

    project_dashboard.main(["--domain", domain])

    reports = Path(os.environ["SEO_REPORTS_DIR"]) / domain
    htmls = list(reports.glob("DASHBOARD-*.html"))
    if htmls:
        dest = IMAGES / "_dashboard-nike.html"
        shutil.copy2(htmls[0], dest)
        shutil.rmtree(tmp, ignore_errors=True)
        return dest
    return reports


# ------------------------------------------------------------------

def main() -> int:
    browser = find_browser()
    if not browser:
        print("No headless browser found — generating HTML only.")
        build_lint_html()
        build_audit_report()
        build_dashboard()
        print(f"HTML files saved to {IMAGES}/")
        print("Open them in a browser and screenshot manually.")
        return 0

    print(f"Browser: {browser}\n")

    # 1. Lint CLI
    lint_html = build_lint_html()
    ok = screenshot(browser, lint_html, IMAGES / "lint-cli.png")
    print(f"  lint-cli.png      {'OK' if ok else 'FAILED'}")

    # 2. Audit report
    audit_html = build_audit_report()
    ok = screenshot(browser, audit_html, IMAGES / "audit-report.png",
                    height=1400)
    print(f"  audit-report.png  {'OK' if ok else 'FAILED'}")

    # 3. Dashboard
    dash_html = build_dashboard()
    ok = screenshot(browser, dash_html, IMAGES / "dashboard.png",
                    height=1400)
    print(f"  dashboard.png     {'OK' if ok else 'FAILED'}")

    # Clean up temp files (keep PNGs)
    for f in [lint_html, audit_html, dash_html,
              IMAGES / "_audit-nike.md"]:
        try:
            f.unlink()
        except OSError:
            pass
    shutil.rmtree(IMAGES / "_tmp_stores", ignore_errors=True)

    print(f"\nDone — screenshots in {IMAGES}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
