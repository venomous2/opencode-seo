"""Fix engine for the OpenCode SEO Suite.

Turns lint findings into concrete patches. Rules that carry a `fix.patch`
spec (see docs/RULE-ENGINE.md) get their templates resolved against the
page's real data; everything else stays guidance-only. Mechanical only —
it never invents content: patches needing human input are emitted as drafts
with TODO markers.

Usage:
    python scripts/seo_fix.py --url https://example.com/page
    python scripts/seo_fix.py --file page.html --dry-run
    python scripts/seo_fix.py --file page.html --base-url https://example.com/page --apply
    python scripts/seo_fix.py --file page.html --only missing-canonical --apply

Modes: --dry-run (default) prints patches; --apply rewrites the local HTML
file (a .bak backup is written first) and re-lints to show the new score.
"""

from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import shutil
import sys
import urllib.parse
from datetime import date
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

import rule_engine  # noqa: E402
import seo_lint  # noqa: E402
from site_crawler import fetch  # noqa: E402


class FixError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# Derived placeholder values
# ---------------------------------------------------------------------------

def build_breadcrumb_json(url: str) -> dict[str, Any]:
    parts = urllib.parse.urlparse(url)
    base = f"{parts.scheme}://{parts.netloc}"
    segments = [s for s in parts.path.split("/") if s]
    items = [{"@type": "ListItem", "position": 1, "name": "Home", "item": base}]
    for i, segment in enumerate(segments, start=2):
        name = segment.replace("-", " ").replace("_", " ").strip().title() or "Page"
        items.append({
            "@type": "ListItem", "position": i, "name": name,
            "item": base + "/" + "/".join(segments[:i - 1]),
        })
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": items}


def make_meta_draft(page: dict[str, Any]) -> str:
    text = (page.get("first_h2_para_text") or "").strip()
    if len(text) < 50:
        text = (page.get("title") or "").strip()
    if not text:
        return ""
    if len(text) > 155:
        text = text[:155].rsplit(" ", 1)[0].rstrip(".,;:")
    return text


def derive_values(page: dict[str, Any], base_url: str, lang: str) -> dict[str, str]:
    url = page.get("url") or ""
    if not url.startswith(("http://", "https://")):
        url = base_url
    domain = urllib.parse.urlparse(url).netloc if url else ""
    h1_first = (page.get("h1") or [""])[0]
    title_draft = (h1_first + (f" | {domain}" if domain else "")).strip(" |")
    return {
        "url": url,
        "domain": domain,
        # schema patches may legitimately use the draft title that the
        # missing-title patch is about to add
        "title": (page.get("title") or "").strip() or title_draft,
        "h1_first": h1_first,
        "title_draft": title_draft,
        "meta_draft": make_meta_draft(page),
        "breadcrumb_json": json.dumps(build_breadcrumb_json(url), indent=2) if url else "",
        "date": date.today().isoformat(),
        "lang": lang,
    }


# ---------------------------------------------------------------------------
# Template resolution
# ---------------------------------------------------------------------------

def resolve_patch(rule: dict[str, Any], values: dict[str, str]) -> dict[str, Any]:
    """Resolve one rule's patch template. Returns a patch record."""
    patch = rule["fix"]["patch"]
    requires = patch.get("requires") or []
    missing = [key for key in requires if not values.get(key)]
    record: dict[str, Any] = {
        "rule_id": rule["id"],
        "severity": rule["severity"],
        "type": patch.get("type"),
        "target": patch.get("target"),
        "draft": bool(patch.get("draft")),
    }
    if missing:
        record.update(status="skipped",
                      reason=f"missing required values: {', '.join(missing)} "
                             f"(pass --base-url for local files)")
        return record

    escape_html = patch.get("type") in ("meta", "link", "title")
    content = patch["template"]
    for key, value in values.items():
        replacement = (html_lib.escape(value, quote=True) if escape_html
                       else value)
        content = content.replace("{{" + key + "}}", replacement)
    leftovers = re.findall(r"\{\{[^}]+\}\}", content)
    if leftovers:
        record.update(status="skipped",
                      reason=f"unresolved placeholders: {', '.join(leftovers)}")
        return record
    record.update(status="ready", content=content.strip())
    return record


def collect_patches(page: dict[str, Any], rules: list[dict[str, Any]],
                    base_url: str, lang: str,
                    only: str | None = None) -> list[dict[str, Any]]:
    patchable = [r for r in rules
                 if isinstance(r.get("fix"), dict) and r["fix"].get("patch")]
    if only:
        patchable = [r for r in patchable if r["id"] == only]
    fired = rule_engine.run(page, patchable)
    values = derive_values(page, base_url, lang)
    return [resolve_patch(rule, values)
            for rule in patchable
            if any(f["id"] == rule["id"] for f in fired["findings"])]


# ---------------------------------------------------------------------------
# Applying patches to a local HTML file
# ---------------------------------------------------------------------------

def apply_patches(html_text: str, patches: list[dict[str, Any]]) -> tuple[str, list[str]]:
    applied = []
    for patch in patches:
        if patch["status"] != "ready":
            continue
        content = patch["content"]
        ptype = patch["type"]
        if ptype == "title":
            if re.search(r"<title>.*?</title>", html_text, re.IGNORECASE | re.DOTALL):
                html_text = re.sub(r"<title>.*?</title>", content,
                                   html_text, count=1,
                                   flags=re.IGNORECASE | re.DOTALL)
            elif re.search(r"<head[^>]*>", html_text, re.IGNORECASE):
                html_text = re.sub(r"(<head[^>]*>)", r"\1\n  " + content,
                                   html_text, count=1, flags=re.IGNORECASE)
            else:
                html_text = content + "\n" + html_text
        elif patch["target"] == "head":
            if re.search(r"</head>", html_text, re.IGNORECASE):
                html_text = re.sub(r"</head>", "  " + content.replace("\n", "\n  ") + "\n</head>",
                                   html_text, count=1, flags=re.IGNORECASE)
            else:
                html_text += "\n" + content + "\n"
        elif patch["target"] == "html_tag":
            attr = content  # e.g. lang="en"
            match = re.search(r"<html\b([^>]*)>", html_text, re.IGNORECASE)
            if match and attr.split("=")[0] not in match.group(1):
                html_text = (html_text[:match.start()] + "<html"
                             + match.group(1) + " " + attr + ">"
                             + html_text[match.end():])
            else:
                continue
        applied.append(patch["rule_id"])
    return html_text, applied


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="seo_fix",
                                     description="Mechanical fix engine")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--url", help="fetch a live page and patch its HTML")
    source.add_argument("--file", help="local HTML file to patch")
    parser.add_argument("--base-url", default="",
                        help="production URL for local files (canonical/schema)")
    parser.add_argument("--lang", default="en", help="language for html lang patch")
    parser.add_argument("--only", help="apply only this rule id")
    parser.add_argument("--apply", action="store_true",
                        help="rewrite --file in place (writes .bak first)")
    parser.add_argument("--dry-run", action="store_true",
                        help="print patches without changing anything (default)")
    parser.add_argument("--format", choices=["json", "text"], default="json")
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args(argv)

    try:
        rules = rule_engine.load_rules()
    except rule_engine.RuleError as exc:
        print(json.dumps({"error": str(exc)}))
        return 1

    # --- load the page -----------------------------------------------------
    if args.url:
        status, content_type, html_text = fetch(args.url, args.timeout)
        if status != 200 or "html" not in content_type.lower():
            print(json.dumps({"error": f"Fetch failed: HTTP {status}"}))
            return 1
        page = seo_lint.parse_html(html_text, args.url)
    else:
        path = Path(args.file)
        if not path.is_file():
            print(json.dumps({"error": f"File not found: {path}"}))
            return 1
        html_text = path.read_text(encoding="utf-8", errors="replace")
        page = seo_lint.parse_html(html_text, args.base_url)

    patches = collect_patches(page, rules, args.base_url, args.lang,
                              only=args.only)

    if args.apply:
        if not args.file:
            print(json.dumps({"error": "--apply only works with --file "
                                       "(fetch the page and save it first)"}))
            return 1
        ready = [p for p in patches if p["status"] == "ready"]
        if not ready:
            print(json.dumps({"applied": [], "note": "no ready patches",
                              "patches": patches}, indent=2))
            return 0
        shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
        new_html, applied = apply_patches(html_text, ready)
        path.write_text(new_html, encoding="utf-8")
        # re-lint to prove improvement
        new_page = seo_lint.parse_html(new_html, args.base_url)
        outcome = rule_engine.run(new_page, rules)
        print(json.dumps({
            "applied": applied,
            "backup": str(path.with_suffix(path.suffix + ".bak")),
            "drafts_to_complete": [p["rule_id"] for p in ready if p["draft"]],
            "new_score": outcome["score"],
            "remaining_findings": outcome["failed"],
        }, indent=2))
        return 0

    # dry-run output
    if args.format == "text":
        if not patches:
            print("No patchable findings — nothing to fix mechanically.")
        for p in patches:
            marker = "READY " if p["status"] == "ready" else "SKIP  "
            draft = " [draft - complete the TODOs]" if p.get("draft") else ""
            print(f"{marker} {p['rule_id']} ({p['severity']}){draft}")
            if p["status"] == "ready":
                print("  " + p["content"].replace("\n", "\n  "))
            else:
                print(f"  reason: {p['reason']}")
        return 0
    print(json.dumps({"patches": patches}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
