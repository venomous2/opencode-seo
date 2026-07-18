"""Built-in mini site crawler for the OpenCode SEO Suite.

A free, polite, same-host crawler for small sites (default up to 200 pages).
Use this when a full DataForSEO On-Page crawl would be overkill. For large
sites or JS-heavy rendering, use `dfs_client.py crawl` instead.

Usage:
    python scripts/site_crawler.py --url https://example.com [--max-pages 200]
        [--delay 0.5] [--timeout 15] [--ignore-robots] [--pretty]

Output (JSON):
    summary: pages crawled, status distribution, counts of missing/duplicate
             titles, missing meta descriptions, missing H1s, noindex pages
    pages:   one record per URL with the extracted SEO fields
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from collections import deque
from html.parser import HTMLParser
from typing import Any

USER_AGENT = "OpenCodeSEOSuite-Crawler/1.0 (+https://opencode.ai)"


class PageParser(HTMLParser):
    """Extracts the SEO fields we care about from an HTML page."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.meta_description = ""
        self.meta_author = ""
        self.canonical = ""
        self.h1: list[str] = []
        self.h2: list[str] = []
        self.h2_count = 0
        self.list_count = 0
        self.time_elements = 0
        self.jsonld_has_dates = False
        self.has_rel_author = False
        self.number_density = 0
        self.links: list[str] = []
        self.internal_link_count = 0
        self.external_link_count = 0
        self.images_total = 0
        self.images_missing_alt = 0
        self.schema_blocks = 0
        self.schema_types: list[str] = []
        self.has_viewport = False
        self.html_lang = ""
        self.noindex = False
        self.word_count = 0
        self.first_h2_para_words = 0  # answer-block heuristic
        self.first_h2_para_text = ""  # truncated raw text (for fix drafts)
        self._in_title = False
        self._in_h1 = False
        self._in_h2 = False
        self._in_jsonld = False
        self._jsonld_parts: list[str] = []
        self._seen_h2 = False
        self._capture_para = False
        self._para_done = False
        self._para_parts: list[str] = []
        self._text_parts: list[str] = []
        self._skip_depth = 0  # inside script/style

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        if tag == "html" and attr.get("lang"):
            self.html_lang = attr["lang"].strip()
        if tag == "title":
            self._in_title = True
        elif tag == "h1":
            self._in_h1 = True
        elif tag == "h2":
            self._in_h2 = True
            self._seen_h2 = True
            self.h2_count += 1
        elif tag in ("ul", "ol"):
            self.list_count += 1
        elif tag == "time":
            self.time_elements += 1
        elif tag == "p" and self._seen_h2 and not self._para_done:
            self._capture_para = True
        elif tag in ("script", "style", "noscript"):
            self._skip_depth += 1
            if tag == "script" and (attr.get("type") or "").lower() == "application/ld+json":
                self._in_jsonld = True
                self._jsonld_parts = []
        elif tag == "meta":
            name = (attr.get("name") or attr.get("property") or "").lower()
            if name == "description":
                self.meta_description = (attr.get("content") or "").strip()
            elif name == "author":
                self.meta_author = (attr.get("content") or "").strip()
            elif name in ("article:published_time", "article:modified_time",
                          "date", "dc.date"):
                self.jsonld_has_dates = True
            elif name == "viewport":
                self.has_viewport = True
            elif name == "robots" and "noindex" in (attr.get("content") or "").lower():
                self.noindex = True
        elif tag == "link":
            rel = (attr.get("rel") or "").lower()
            if rel == "canonical" and attr.get("href"):
                self.canonical = attr["href"].strip()
            if "author" in rel:
                self.has_rel_author = True
        elif tag == "a":
            if attr.get("href"):
                self.links.append(attr["href"])
            if "author" in (attr.get("rel") or "").lower():
                self.has_rel_author = True
        elif tag == "img":
            self.images_total += 1
            if not (attr.get("alt") or "").strip():
                self.images_missing_alt += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        elif tag == "h1":
            self._in_h1 = False
        elif tag == "h2":
            self._in_h2 = False
        elif tag == "p" and self._capture_para:
            self._capture_para = False
            self._para_done = True
        elif tag in ("script", "style", "noscript") and self._skip_depth:
            self._skip_depth -= 1
            if tag == "script" and self._in_jsonld:
                self._in_jsonld = False
                self.schema_blocks += 1
                raw = "".join(self._jsonld_parts)
                if "datePublished" in raw or "dateModified" in raw:
                    self.jsonld_has_dates = True
                self._extract_schema_types(raw)

    def _extract_schema_types(self, raw: str) -> None:
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return
        for match in re.findall(r'"@type"\s*:\s*(?:"([^"]+)"|\[([^\]]+)\])',
                                json.dumps(data)):
            if match[0]:
                self.schema_types.append(match[0])
            elif match[1]:
                self.schema_types.extend(
                    t.strip().strip('"') for t in match[1].split(","))

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
        if self._in_h1:
            self.h1.append(data.strip())
        if self._in_h2:
            self.h2.append(data.strip())
        if self._in_jsonld:
            self._jsonld_parts.append(data)
        if self._capture_para:
            self._para_parts.append(data)
        if self._skip_depth == 0:
            self._text_parts.append(data)

    def finish(self) -> None:
        text = " ".join(self._text_parts)
        self.word_count = len(re.findall(r"\w+", text))
        self.title = " ".join(self.title.split())
        self.h1 = [" ".join(h.split()) for h in self.h1 if h.strip()]
        self.h2 = [" ".join(h.split()) for h in self.h2 if h.strip()]
        para_text = " ".join(" ".join(self._para_parts).split())
        self.first_h2_para_words = len(re.findall(r"\w+", para_text))
        self.first_h2_para_text = para_text[:400]
        # factual-density proxy: tokens containing digits or % per 1k words
        numbers = len(re.findall(r"\b[\d][\d.,]*%?\b", text))
        self.number_density = round(1000 * numbers / max(self.word_count, 1), 1)


def fetch(url: str, timeout: int) -> tuple[int, str, str]:
    """Return (status_code, content_type, html_text)."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            body = response.read(2_000_000).decode("utf-8", errors="replace")
            return response.status, content_type, body
    except urllib.error.HTTPError as exc:
        return exc.code, "", ""
    except (urllib.error.URLError, TimeoutError, OSError):
        return 0, "", ""


def normalise(base: str, href: str) -> str | None:
    """Resolve href against base; keep same-host http(s) URLs only."""
    absolute = urllib.parse.urljoin(base, href)
    parts = urllib.parse.urlparse(absolute)
    if parts.scheme not in ("http", "https"):
        return None
    # strip fragment and common tracking params
    cleaned = parts._replace(fragment="")
    return urllib.parse.urlunparse(cleaned)


def crawl(start_url: str, max_pages: int, delay: float, timeout: int,
          respect_robots: bool) -> dict[str, Any]:
    start_parts = urllib.parse.urlparse(start_url)
    host = start_parts.netloc.lower()

    robots: urllib.robotparser.RobotFileParser | None = None
    if respect_robots:
        robots = urllib.robotparser.RobotFileParser(
            f"{start_parts.scheme}://{host}/robots.txt")
        try:
            robots.read()
        except Exception:  # noqa: BLE001 - unreachable robots.txt == allow
            robots = None

    queue: deque[str] = deque([start_url])
    seen = {start_url}
    pages: list[dict[str, Any]] = []

    while queue and len(pages) < max_pages:
        url = queue.popleft()
        if robots and not robots.can_fetch(USER_AGENT, url):
            pages.append({"url": url, "status": None, "blocked_by_robots": True})
            continue

        status, content_type, html = fetch(url, timeout)
        record: dict[str, Any] = {"url": url, "status": status}
        if status == 200 and "html" in content_type.lower():
            parser = PageParser()
            try:
                parser.feed(html)
                parser.finish()
            except Exception:  # noqa: BLE001 - tolerate malformed HTML
                pass
            for href in parser.links:
                absolute = urllib.parse.urljoin(url, href)
                link_host = urllib.parse.urlparse(absolute).netloc.lower()
                if link_host == host:
                    parser.internal_link_count += 1
                elif link_host:
                    parser.external_link_count += 1
            record.update({
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
            })
            for href in parser.links:
                nxt = normalise(url, href)
                if not nxt:
                    continue
                if urllib.parse.urlparse(nxt).netloc.lower() != host:
                    continue
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        pages.append(record)
        if delay:
            time.sleep(delay)

    # --- summary ---------------------------------------------------------
    ok = [p for p in pages if p.get("status") == 200]
    titles = [p.get("title") for p in ok if p.get("title")]
    duplicate_titles = sorted({t for t in titles if titles.count(t) > 1})
    summary = {
        "start_url": start_url,
        "pages_crawled": len(pages),
        "urls_discovered": len(seen),
        "status_distribution": {str(s): sum(1 for p in pages if p.get("status") == s)
                                for s in {p.get("status") for p in pages}},
        "missing_title": sum(1 for p in ok if not p.get("title")),
        "duplicate_titles": duplicate_titles,
        "missing_meta_description": sum(1 for p in ok if not p.get("meta_description")),
        "missing_h1": sum(1 for p in ok if p.get("h1_count") == 0),
        "multiple_h1": sum(1 for p in ok if (p.get("h1_count") or 0) > 1),
        "noindex_pages": sum(1 for p in ok if p.get("noindex")),
        "truncated": len(queue) > 0,
    }
    return {"summary": summary, "pages": pages}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="site_crawler",
                                     description="Built-in polite mini crawler")
    parser.add_argument("--url", required=True)
    parser.add_argument("--max-pages", type=int, default=200)
    parser.add_argument("--delay", type=float, default=0.5,
                        help="seconds between requests (politeness)")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--ignore-robots", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    result = crawl(args.url, args.max_pages, args.delay, args.timeout,
                   respect_robots=not args.ignore_robots)
    print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
