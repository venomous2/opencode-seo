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


def lint_pages(pages: list[dict[str, Any]], rules: list[dict[str, Any]],
               category: str | None, local: bool = False) -> list[dict[str, Any]]:
    if category:
        rules = [r for r in rules if r["category"] == category]
    if local:
        # URL-dependent rules (e.g. HTTPS) and header-dependent rules
        # (security headers) are meaningless for local files
        rules = [r for r in rules
                 if r["detect"]["field"] != "url"
                 and not r["detect"]["field"].startswith("security_")]
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="seo_lint",
                                     description="Deterministic SEO linter")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--url", help="fetch and lint a live page")
    source.add_argument("--file", help="lint a local HTML file")
    source.add_argument("--dir", help="lint every HTML file in a directory")
    parser.add_argument("--ext", default=".html", help="file extension for --dir")
    parser.add_argument("--category", help="restrict to one rule category")
    parser.add_argument("--min-score", type=int,
                        help="exit 1 if any page scores below this (CI gate)")
    parser.add_argument("--format", choices=["json", "text"], default="json")
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args(argv)

    try:
        rules = rule_engine.load_rules()
    except rule_engine.RuleError as exc:
        print(json.dumps({"error": str(exc)}))
        return 1

    pages: list[dict[str, Any]] = []
    if args.url:
        result = fetch(args.url, args.timeout)
        if result.status != 200 or "html" not in result.content_type.lower():
            print(json.dumps({"error": f"Fetch failed: HTTP {result.status}"}))
            return 1
        page = parse_html(result.body, args.url)
        page["status"] = result.status
        page["security_hsts"] = "strict-transport-security" in result.headers
        page["security_csp"] = "content-security-policy" in result.headers
        page["security_xfo"] = "x-frame-options" in result.headers
        page["security_xcto"] = "x-content-type-options" in result.headers
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

    if args.format == "text":
        print(render_text(results))
    else:
        print(json.dumps({"pages": results}, indent=2, ensure_ascii=False))

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
