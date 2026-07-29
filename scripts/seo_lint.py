"""SEO linter for the OpenCode SEO Suite — "ESLint for SEO".

Deterministic, model-agnostic page checks powered by the rule engine.
Lints a live URL, a local HTML file, or a directory of HTML files, scores
each page 0-100, and can fail your CI when scores drop below a threshold.

Usage:
    python scripts/seo_lint.py --url https://example.com/page
    python scripts/seo_lint.py --file page.html
    python scripts/seo_lint.py --dir ./dist --ext .html
    python scripts/seo_lint.py --url U --min-score 80        # CI gate
    python scripts/seo_lint.py --url U --format text
    python scripts/seo_lint.py --url U --save                # persist findings
    python scripts/seo_lint.py --dir ./dist --format github  # PR annotations

Exit codes: 0 = lint ran and every page passed the gate (if given),
            1 = lint error or a page scored below --min-score.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

import recommend_store  # noqa: E402
import rule_engine  # noqa: E402
from site_crawler import PageParser, fetch  # noqa: E402

SEVERITY_ICON = {"critical": "X", "high": "!", "medium": "*", "low": "-"}


def parse_html(html_text: str, url: str = "") -> dict[str, Any]:
    parser = PageParser()
    try:
        parser.feed(html_text)
        parser.finish()
    except Exception:  # noqa: BLE001 - tolerate malformed HTML
        pass
    # classify links: same-host or relative = internal, foreign = external
    page_host = urllib.parse.urlparse(url).netloc.lower() if url else ""
    for link in parser.links:
        href = link["href"]
        if href.startswith(("http://", "https://")):
            link_host = urllib.parse.urlparse(href).netloc.lower()
            if page_host and link_host == page_host:
                parser.internal_link_count += 1
            else:
                parser.external_link_count += 1
        else:  # relative links are internal by definition
            parser.internal_link_count += 1
    return {
        "url": url,
        "status": 200,
        "title": parser.title,
        "title_length": len(parser.title),
        "meta_description": parser.meta_description,
        "meta_description_length": len(parser.meta_description),
        "canonical": parser.canonical,
        "h1": parser.h1,
        "h1_count": len(parser.h1),
        "h2": parser.h2,
        "h2_count": parser.h2_count,
        "list_count": parser.list_count,
        "time_elements": parser.time_elements,
        "jsonld_has_dates": parser.jsonld_has_dates,
        "meta_author": parser.meta_author,
        "has_rel_author": parser.has_rel_author,
        "number_density": parser.number_density,
        "word_count": parser.word_count,
        "noindex": parser.noindex,
        "images_total": parser.images_total,
        "images_missing_alt": parser.images_missing_alt,
        "schema_blocks": parser.schema_blocks,
        "schema_types": parser.schema_types,
        "has_viewport": parser.has_viewport,
        "html_lang": parser.html_lang,
        "internal_link_count": parser.internal_link_count,
        "external_link_count": parser.external_link_count,
        "first_h2_para_words": parser.first_h2_para_words,
        "first_h2_para_text": parser.first_h2_para_text,
        "og_title": parser.og_title,
        "og_image": parser.og_image,
        "twitter_card": parser.twitter_card,
        "mixed_content_count": parser.mixed_content_count,
        "form_inputs_unlabelled": parser.form_inputs_unlabelled,
        "has_skip_link": parser.has_skip_link,
        "has_main": parser.has_main,
        "has_nav": parser.has_nav,
        "heading_skips": parser.heading_skips,
        "duplicate_ids": parser.duplicate_ids,
        "empty_links": parser.empty_links,
        "empty_buttons": parser.empty_buttons,
        "generic_link_texts": parser.generic_link_texts,
        "tables_total": parser.tables_total,
        "tables_without_th": parser.tables_without_th,
        "iframes_total": parser.iframes_total,
        "iframes_missing_title": parser.iframes_missing_title,
        "positive_tabindex": parser.positive_tabindex,
        "cta_count": parser.cta_count,
        "cta_above_fold": parser.cta_above_fold,
        "cta_texts": parser.cta_texts,
        "primary_cta_generic": parser.primary_cta_generic,
        "form_count": parser.form_count,
        "form_fields_max": parser.form_fields_max,
        "form_has_captcha": parser.form_has_captcha,
        "tel_links": parser.tel_links,
        "trust_signal_count": parser.trust_signal_count,
        "urgency_signal_count": parser.urgency_signal_count,
        "faq_present": parser.faq_present,
        "live_chat": parser.live_chat,
    }


def filter_rules(rules: list[dict[str, Any]], category: str | None,
                 local: bool = False) -> list[dict[str, Any]]:
    """The rule subset a lint run actually evaluates."""
    if category:
        rules = [r for r in rules if r["category"] == category]
    if local:
        # URL-dependent rules (e.g. HTTPS) and header-dependent rules
        # (security headers) are meaningless for local files
        rules = [r for r in rules
                 if r["detect"]["field"] != "url"
                 and not r["detect"]["field"].startswith("security_")]
    return rules


def lint_pages(pages: list[dict[str, Any]], rules: list[dict[str, Any]],
               category: str | None, local: bool = False) -> list[dict[str, Any]]:
    rules = filter_rules(rules, category, local)
    results = []
    for page in pages:
        outcome = rule_engine.run(page, rules)
        outcome["url"] = page.get("url", "")
        results.append(outcome)
    return results


def render_text(results: list[dict[str, Any]]) -> str:
    lines = []
    for result in results:
        lines.append(f"\n{result['url'] or '(inline page)'}  —  "
                     f"score {result['score']}/100  "
                     f"({result['failed']} findings, {result['rules_run']} rules)")
        for f in result["findings"]:
            icon = SEVERITY_ICON[f["severity"]]
            actual = f["evidence"]["actual"]
            actual_txt = f" [actual: {actual!r}]" if actual not in (None, "", []) else ""
            lines.append(f"  {icon} {f['severity']:<8} {f['id']}{actual_txt}")
            lines.append(f"           why: {f['why']}")
            if f["fix"]:
                lines.append(f"           fix: {f['fix']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# GitHub Actions annotations (workflow commands)
# https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions
# ---------------------------------------------------------------------------

def _gh_escape(text: Any) -> str:
    """Escape a workflow-command message body."""
    return str(text).replace("%", "%25").replace("\r", "%0D") \
        .replace("\n", "%0A")


def _gh_escape_prop(text: Any) -> str:
    """Escape a workflow-command property value (file, title)."""
    return _gh_escape(text).replace(":", "%3A").replace(",", "%2C")


def render_github(results: list[dict[str, Any]]) -> str:
    """Findings as ::error/::warning annotations + a per-page ::notice.

    critical/high become errors, medium/low warnings. Findings carry no
    line numbers (the engine works on parsed data, not source positions),
    so annotations attach at file level — which is what PR review shows.
    """
    lines = []
    for result in results:
        path = result["url"] or "(inline page)"
        lines.append(f"::notice file={_gh_escape_prop(path)},"
                     f"title=SEO score {result['score']}/100::"
                     f"{result['failed']} finding(s), "
                     f"{result['rules_run']} rules checked")
        for f in result["findings"]:
            level = "error" if f["severity"] in ("critical", "high") \
                else "warning"
            message = f"{f['severity']}: {f['why']}"
            if f["fix"]:
                message += f" fix: {f['fix']}"
            lines.append(f"::{level} file={_gh_escape_prop(path)},"
                         f"title={_gh_escape_prop(f['id'])}::"
                         f"{_gh_escape(message)}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="seo_lint",
                                     description="Deterministic SEO linter")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--url", help="fetch and lint a live page")
    source.add_argument("--file", help="lint a local HTML file")
    source.add_argument("--dir", help="lint every HTML file in a directory")
    parser.add_argument("--ext", default=".html", help="file extension for --dir")
    parser.add_argument("--category", help="restrict to one rule category")
    parser.add_argument("--render", choices=["auto", "always", "never"],
                        default="never",
                        help="render JS first: auto = detect SPA and render "
                             "if needed, always = force render, never = raw HTML")
    parser.add_argument("--min-score", type=int,
                        help="exit 1 if any page scores below this (CI gate)")
    parser.add_argument("--format", choices=["json", "text", "github"],
                        default="json",
                        help="github = GitHub Actions ::error/::warning "
                             "annotations for PR review")
    parser.add_argument("--save", action="store_true",
                        help="persist findings to the recommendation store "
                             "(raises new/ongoing issues, resolves fixed ones)")
    parser.add_argument("--domain",
                        help="domain for --save (default: URL host, or "
                             "'local' for files)")
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args(argv)

    try:
        rules = rule_engine.load_rules()
    except rule_engine.RuleError as exc:
        print(json.dumps({"error": str(exc)}))
        return 1

    pages: list[dict[str, Any]] = []
    if args.url:
        html_text = None
        render_engine = "raw"
        raw_page = None
        headers: dict[str, str] = {}
        if args.render != "never":
            import spa_detect
            should_render = args.render == "always"
            if args.render == "auto":
                raw_result = fetch(args.url, args.timeout)
                if raw_result.status == 200:
                    verdict = spa_detect.detect(raw_result.body, args.url)
                    should_render = verdict["should_render"]
            if should_render:
                import render_page
                try:
                    html_text, render_engine = render_page.render(
                        args.url, engine="auto")
                    raw_result = fetch(args.url, args.timeout)
                    if raw_result.status == 200:
                        raw_page = parse_html(raw_result.body, args.url)
                        headers = raw_result.headers  # keep real headers
                except Exception:  # noqa: BLE001 - fall back to raw HTML
                    html_text = None
        if html_text is None:
            result = fetch(args.url, args.timeout)
            if result.status != 200 or "html" not in result.content_type.lower():
                print(json.dumps({"error": f"Fetch failed: HTTP {result.status}"}))
                return 1
            html_text = result.body
            headers = result.headers
        page = parse_html(html_text, args.url)
        page["render_engine"] = render_engine
        if raw_page is not None:
            raw_words = max(raw_page.get("word_count") or 0, 1)
            page["raw_word_count"] = raw_page.get("word_count")
            page["js_content_ratio"] = round(
                (page.get("word_count") or 0) / raw_words, 2)
        page["status"] = 200
        page["security_hsts"] = "strict-transport-security" in headers
        page["security_csp"] = "content-security-policy" in headers
        page["security_xfo"] = "x-frame-options" in headers
        page["security_xcto"] = "x-content-type-options" in headers
        pages.append(page)
    elif args.file:
        path = Path(args.file)
        if not path.is_file():
            print(json.dumps({"error": f"File not found: {path}"}))
            return 1
        pages.append(parse_html(path.read_text(encoding="utf-8",
                                               errors="replace"), str(path)))
    else:
        directory = Path(args.dir)
        files = sorted(directory.rglob(f"*{args.ext}"))
        if not files:
            print(json.dumps({"error": f"No *{args.ext} files under {directory}"}))
            return 1
        for path in files:
            pages.append(parse_html(path.read_text(encoding="utf-8",
                                                   errors="replace"), str(path)))

    results = lint_pages(pages, rules, args.category, local=not args.url)

    store_report = None
    if args.save:
        if args.domain:
            domain = args.domain.strip().lower()
        elif args.url:
            domain = urllib.parse.urlparse(args.url).netloc.lower()
        else:
            domain = "local"
        run_rules = filter_rules(rules, args.category, local=not args.url)
        store_report = recommend_store.save_lint_results(domain, results,
                                                         run_rules)

    if args.format == "github":
        print(render_github(results))
        if store_report:
            print(f"::notice title=Recommendation store::"
                  f"{store_report['raised']} saved, "
                  f"{store_report['resolved']} resolved, "
                  f"{store_report['open_total']} open")
    elif args.format == "text":
        print(render_text(results))
        if store_report:
            print(f"\nstore: {store_report['raised']} finding(s) saved, "
                  f"{store_report['resolved']} resolved, "
                  f"{store_report['open_total']} open "
                  f"(domain: {store_report['domain']})")
    else:
        output: dict[str, Any] = {"pages": results}
        if store_report:
            output["store"] = store_report
        print(json.dumps(output, indent=2, ensure_ascii=False))

    if args.min_score is not None:
        failures = [r for r in results if r["score"] < args.min_score]
        if failures:
            if args.format == "text":
                print(f"\nFAIL: {len(failures)} page(s) below "
                      f"--min-score {args.min_score}")
            else:
                print(json.dumps({"gate": "fail",
                                  "below_threshold": [
                                      {"url": r["url"], "score": r["score"]}
                                      for r in failures]}))
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
