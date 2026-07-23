"""JavaScript page renderer for the OpenCode SEO Suite.

Renders JS-heavy pages into final DOM HTML using the headless browser
already installed on the machine (Edge on Windows, Chrome/Chromium
elsewhere) — Chromium's --dump-dom with a virtual-time budget gives a
deterministic wait without any new dependencies. Falls back to DataForSEO's
JS-enabled on-page fetch when no local browser is available.

Usage:
    python scripts/render_page.py --url https://example.com [-o out.html]
    python scripts/render_page.py --url https://example.com --wait 10000
    python scripts/render_page.py --url https://example.com --engine dfs
    python scripts/render_page.py --url https://example.com --diff

--diff compares the raw fetched page against the rendered DOM (words,
links, schema, title) — the "what does Google see that curl doesn't"
metric.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

import dfs_client  # noqa: E402
import report_pdf  # noqa: E402
import seo_lint  # noqa: E402
from site_crawler import fetch  # noqa: E402

DEFAULT_WAIT_MS = 8000


class RenderError(RuntimeError):
    pass


def render_with_browser(url: str, wait_ms: int, timeout: int = 90) -> str:
    browser = report_pdf.find_browser()
    if not browser:
        raise RenderError("no local browser found")
    command = [
        browser, "--headless", "--disable-gpu", "--no-first-run",
        "--disable-extensions", "--mute-audio",
        f"--virtual-time-budget={wait_ms}",
        "--dump-dom", url,
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True,
                                timeout=timeout, encoding="utf-8",
                                errors="replace")
    except subprocess.TimeoutExpired as exc:
        raise RenderError(f"render timed out after {timeout}s") from exc
    html = result.stdout or ""
    if len(html) < 200:
        raise RenderError(f"browser returned too little content "
                          f"({len(html)} bytes): {result.stderr[:200]}")
    return html


def render_with_dfs(url: str) -> str:
    payload = [{"url": url, "enable_javascript": True, "load_resources": True}]
    body = dfs_client.post("/v3/on_page/content_parsing/live", payload)
    result = dfs_client.first_result(body)
    html = (result.get("content") or "") if result else ""
    if not html:
        items = (result.get("items") or [{}])
        html = items[0].get("content", "") if items else ""
    if not html:
        raise RenderError("DataForSEO returned no rendered content")
    return html


def render(url: str, wait_ms: int = DEFAULT_WAIT_MS,
           engine: str = "auto") -> tuple[str, str]:
    """Return (html, engine_used). engine: auto | browser | dfs."""
    if engine in ("auto", "browser"):
        try:
            return render_with_browser(url, wait_ms), "browser"
        except RenderError:
            if engine == "browser":
                raise
    return render_with_dfs(url), "dataforseo"


def diff(raw_html: str, rendered_html: str, url: str) -> dict[str, Any]:
    """Compare raw vs rendered extraction — the JS content gap."""
    raw = seo_lint.parse_html(raw_html, url)
    rendered = seo_lint.parse_html(rendered_html, url)

    def delta(field: str) -> dict[str, Any]:
        before, after = raw.get(field), rendered.get(field)
        return {"raw": before, "rendered": after,
                "delta": (after - before) if isinstance(before, (int, float))
                          and isinstance(after, (int, float)) else None}

    raw_words = max(raw.get("word_count") or 0, 1)
    ratio = round((rendered.get("word_count") or 0) / raw_words, 2)
    raw_types = set(raw.get("schema_types") or [])
    rendered_types = set(rendered.get("schema_types") or [])
    return {
        "word_count": delta("word_count"),
        "internal_link_count": delta("internal_link_count"),
        "images_total": delta("images_total"),
        "schema_blocks": delta("schema_blocks"),
        "title_changed": raw.get("title") != rendered.get("title"),
        "schema_only_in_render": sorted(rendered_types - raw_types),
        "js_content_ratio": ratio,
        "verdict": ("significant JS-dependent content — raw-HTML analysis "
                    "would miss it" if ratio >= 1.5 else
                    "raw HTML is substantially complete"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="render_page",
                                     description="JS page renderer (zero-dependency)")
    parser.add_argument("--url", required=True)
    parser.add_argument("-o", "--output", help="write rendered HTML to file")
    parser.add_argument("--wait", type=int, default=DEFAULT_WAIT_MS,
                        help="virtual-time budget in ms (default 8000)")
    parser.add_argument("--engine", choices=["auto", "browser", "dfs"],
                        default="auto")
    parser.add_argument("--diff", action="store_true",
                        help="also compute the raw-vs-rendered diff")
    args = parser.parse_args(argv)

    try:
        html, engine = render(args.url, args.wait, args.engine)
    except (RenderError, dfs_client.DfsError, dfs_client.ConfigError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1

    out: dict[str, Any] = {"url": args.url, "engine": engine,
                           "bytes": len(html)}
    if args.output:
        Path(args.output).write_text(html, encoding="utf-8")
        out["html_path"] = args.output
    else:
        out["html"] = html[:500]

    if args.diff:
        raw = fetch(args.url, 20)
        out["diff"] = diff(raw.body, html, args.url)

    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    sys.exit(main())
