"""SPA detection for the OpenCode SEO Suite.

Decides whether a URL needs JavaScript rendering before analysis, so
audits only pay the render cost when it matters. Pure stdlib heuristics —
zero model calls, zero dependencies.

Usage:
    python scripts/spa_detect.py --url https://example.com [--pretty]
    python scripts/spa_detect.py --file page.html

Signals scored:
  +3  empty app shell (<div id="root">/<div id="app"> with little inside)
  +2  framework markers (__NEXT_DATA__, data-reactroot, ng-, data-v-, __NUXT__)
  +2  low visible text relative to document size
  +1  suspiciously few internal links for a full page
  +1  script-heavy document with almost no text

Verdicts: >=4 "spa" (render required), 2-3 "maybe" (render if available),
<2 "static" (raw HTML is fine).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from site_crawler import PageParser, fetch  # noqa: E402

FRAMEWORK_MARKERS = (
    "__NEXT_DATA__", "_next/", "data-reactroot", "data-react-helmet",
    "ng-app", "ng-version", "data-v-", "__NUXT__", "_nuxt/", "__VUE__",
    "data-astro", "webpackJsonp", "gatsby", "sveltekit", "__sveltekit",
)

SHELL_IDS = ('<div id="root"', '<div id="app"', '<div id="__next"',
             '<div id="__nuxt"', '<div id="svelte"')


def detect(html: str, url: str = "") -> dict[str, Any]:
    signals: list[dict[str, Any]] = []
    score = 0

    # app-shell: a known root container that is (nearly) empty inside
    for marker in SHELL_IDS:
        idx = html.find(marker)
        if idx != -1:
            close_idx = html.find("</div>", idx)
            if close_idx != -1:
                inner = html[idx:close_idx]
                inner_words = len(re.findall(r"\w+", inner))
                if inner_words < 10:
                    signals.append({"signal": "app_shell", "points": 3,
                                    "evidence": f"{marker}... with "
                                                f"{inner_words} words inside"})
                    score += 3
            break

    # framework markers
    found = [m for m in FRAMEWORK_MARKERS if m in html]
    if found:
        points = min(2, len(found))
        signals.append({"signal": "framework_markers", "points": points,
                        "evidence": ", ".join(found[:4])})
        score += points

    # text-to-markup ratio
    parser = PageParser()
    try:
        parser.feed(html)
        parser.finish()
    except Exception:  # noqa: BLE001
        pass
    words = parser.word_count
    size_kb = len(html) / 1024
    if words < 150 and size_kb > 10:
        signals.append({"signal": "low_text_ratio", "points": 2,
                        "evidence": f"{words} words in {size_kb:.0f} KB of markup"})
        score += 2

    # link poverty on an otherwise document-sized page
    internalish = [l for l in parser.links if l["href"].startswith(("/", "."))]
    if len(parser.links) < 5 and size_kb > 10:
        signals.append({"signal": "few_links", "points": 1,
                        "evidence": f"only {len(parser.links)} links"})
        score += 1

    # script-heavy
    script_count = len(re.findall(r"<script", html, re.IGNORECASE))
    if script_count > 10 and words < 100:
        signals.append({"signal": "script_heavy", "points": 1,
                        "evidence": f"{script_count} scripts, {words} words"})
        score += 1

    verdict = "spa" if score >= 4 else ("maybe" if score >= 2 else "static")
    return {
        "url": url,
        "verdict": verdict,
        "score": score,
        "should_render": score >= 2,
        "signals": signals,
        "stats": {"visible_words": words, "document_kb": round(size_kb, 1),
                  "links": len(parser.links), "scripts": script_count},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="spa_detect",
                                     description="SPA detection heuristics")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--url")
    source.add_argument("--file")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args(argv)

    if args.url:
        result = fetch(args.url, args.timeout)
        if result.status != 200:
            print(json.dumps({"error": f"Fetch failed: HTTP {result.status}"}))
            return 1
        html, url = result.body, args.url
    else:
        path = Path(args.file)
        if not path.is_file():
            print(json.dumps({"error": f"File not found: {path}"}))
            return 1
        html, url = path.read_text(encoding="utf-8", errors="replace"), str(path)

    print(json.dumps(detect(html, url),
                     indent=2 if args.pretty else None, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    sys.exit(main())
