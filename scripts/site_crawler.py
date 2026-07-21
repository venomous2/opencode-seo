"""Built-in site crawler (v2) for the OpenCode SEO Suite.

A free, polite, same-host crawler for small-to-mid sites. For very large
sites or heavy JS rendering, use `dfs_client.py crawl` (paid) instead.

Usage:
    python scripts/site_crawler.py --url https://example.com [--max-pages 200]
        [--workers 5] [--delay 0.4] [--timeout 15] [--ignore-robots]
        [--no-sitemap-check] [--no-dup-check] [--no-probe] [--pretty]

Output (JSON):
    summary: pages crawled, status distribution, metadata/H1/image stats,
             sitemap cross-check, near-duplicate pairs, soft-404 probe
    pages:   one record per URL with all extracted SEO fields
"""

from __future__ import annotations

import argparse
import json
import re
import secrets
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from collections import deque, namedtuple
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

USER_AGENT = "OpenCodeSEOSuite-Crawler/2.0 (+https://opencode.ai)"

FetchResult = namedtuple("FetchResult", ["status", "content_type", "body", "headers"])


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
        self.number_density = 0.0
        self.links: list[dict[str, str]] = []  # {"href", "anchor"}
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
        self.first_h2_para_words = 0
        self.first_h2_para_text = ""
        self.text_sample = ""
        self.og_title = ""
        self.og_image = ""
        self.twitter_card = ""
        self.mixed_content_count = 0
        self._in_title = False
        self._in_h1 = False
        self._in_h2 = False
        self._in_jsonld = False
        self._jsonld_parts: list[str] = []
        self._current_href: str | None = None
        self._current_anchor: list[str] = []
        self._seen_h2 = False
        self._capture_para = False
        self._para_done = False
        self._para_parts: list[str] = []
        self._text_parts: list[str] = []
        self._skip_depth = 0

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
            if (attr.get("src") or "").startswith("http://"):
                self.mixed_content_count += 1
        elif tag == "meta":
            name = (attr.get("name") or attr.get("property") or "").lower()
            if name == "description":
                self.meta_description = (attr.get("content") or "").strip()
            elif name == "author":
                self.meta_author = (attr.get("content") or "").strip()
            elif name in ("article:published_time", "article:modified_time",
                          "date", "dc.date"):
                self.jsonld_has_dates = True
            elif name == "og:title":
                self.og_title = (attr.get("content") or "").strip()
            elif name == "og:image":
                self.og_image = (attr.get("content") or "").strip()
            elif name == "twitter:card":
                self.twitter_card = (attr.get("content") or "").strip()
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
            if (attr.get("href") or "").startswith("http://"):
                self.mixed_content_count += 1
        elif tag == "a":
            if attr.get("href"):
                self._current_href = attr["href"]
                self._current_anchor = []
            if "author" in (attr.get("rel") or "").lower():
                self.has_rel_author = True
        elif tag == "img":
            self.images_total += 1
            if not (attr.get("alt") or "").strip():
                self.images_missing_alt += 1
            if (attr.get("src") or "").startswith("http://"):
                self.mixed_content_count += 1

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
        elif tag == "a" and self._current_href is not None:
            self.links.append({
                "href": self._current_href,
                "anchor": " ".join(" ".join(self._current_anchor).split()),
            })
            self._current_href = None
            self._current_anchor = []
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
        if self._current_href is not None and self._skip_depth == 0:
            self._current_anchor.append(data)
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
        self.text_sample = text[:5000]
        numbers = len(re.findall(r"\b[\d][\d.,]*%?\b", text))
        self.number_density = round(1000 * numbers / max(self.word_count, 1), 1)


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------

def fetch(url: str, timeout: int) -> FetchResult:
    """GET a URL. Returns FetchResult(status, content_type, body, headers)."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            body = response.read(2_000_000).decode("utf-8", errors="replace")
            headers = {k.lower(): v for k, v in response.headers.items()}
            return FetchResult(response.status, content_type, body, headers)
    except urllib.error.HTTPError as exc:
        return FetchResult(exc.code, "", "", {})
    except (urllib.error.URLError, TimeoutError, OSError):
        return FetchResult(0, "", "", {})


class RateLimiter:
    """Shared per-host politeness gate for concurrent workers."""

    def __init__(self, delay: float) -> None:
        self.delay = delay
        self._lock = threading.Lock()
        self._next = 0.0

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            if now < self._next:
                time.sleep(self._next - now)
            self._next = max(time.monotonic(), self._next + self.delay)


def _record_from_parser(url: str, status: int, parser: PageParser,
                        host: str, headers: dict[str, str]) -> dict[str, Any]:
    internal_out: list[dict[str, str]] = []
    for link in parser.links:
        absolute = urllib.parse.urljoin(url, link["href"])
        link_host = urllib.parse.urlparse(absolute).netloc.lower()
        if link_host == host:
            parser.internal_link_count += 1
            internal_out.append({"url": absolute.split("#")[0],
                                 "anchor": link["anchor"][:120]})
        elif link_host:
            parser.external_link_count += 1
    return {
        "url": url, "status": status,
        "title": parser.title, "title_length": len(parser.title),
        "meta_description": parser.meta_description,
        "meta_description_length": len(parser.meta_description),
        "canonical": parser.canonical,
        "h1": parser.h1, "h1_count": len(parser.h1),
        "h2": parser.h2, "h2_count": parser.h2_count,
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
        "internal_outlinks": internal_out,
        "first_h2_para_words": parser.first_h2_para_words,
        "first_h2_para_text": parser.first_h2_para_text,
        "og_title": parser.og_title,
        "og_image": parser.og_image,
        "twitter_card": parser.twitter_card,
        "mixed_content_count": parser.mixed_content_count,
        "security_hsts": "strict-transport-security" in headers,
        "security_csp": "content-security-policy" in headers,
        "security_xfo": "x-frame-options" in headers,
        "security_xcto": "x-content-type-options" in headers,
        "_shingles": _shingles(parser.text_sample),
    }


def _shingles(text: str, n: int = 5) -> frozenset:
    words = re.findall(r"\w+", text.lower())
    return frozenset(hash(" ".join(words[i:i + n]))
                     for i in range(max(1, len(words) - n + 1)))


def _near_duplicate_pairs(pages: list[dict[str, Any]],
                          threshold: float = 0.9) -> list[dict[str, Any]]:
    valid = [p for p in pages if p.get("_shingles")]
    pairs = []
    for i in range(len(valid)):
        for j in range(i + 1, len(valid)):
            a, b = valid[i]["_shingles"], valid[j]["_shingles"]
            if not a or not b:
                continue
            similarity = len(a & b) / len(a | b)
            if similarity >= threshold:
                pairs.append({"url_a": valid[i]["url"], "url_b": valid[j]["url"],
                              "similarity": round(similarity, 2)})
    return sorted(pairs, key=lambda p: -p["similarity"])


def _fetch_sitemap_urls(base: str, timeout: int,
                        max_sitemaps: int = 10) -> set[str]:
    """Fetch /sitemap.xml (+ one level of sitemap index) and return URLs."""
    result = fetch(f"{base}/sitemap.xml", timeout)
    if result.status != 200:
        return set()
    locs = re.findall(r"<loc>\s*([^<]+?)\s*</loc>", result.body)
    urls: set[str] = set()
    children = [u for u in locs if "sitemap" in u.lower() and u.endswith(".xml")]
    if children:  # sitemap index
        for child in children[:max_sitemaps]:
            child_result = fetch(child, timeout)
            if child_result.status == 200:
                urls.update(re.findall(r"<loc>\s*([^<]+?)\s*</loc>",
                                       child_result.body))
    else:
        urls.update(locs)
    return {u.strip() for u in urls}


def _probe_soft404(start_url: str, timeout: int) -> dict[str, Any]:
    """Request impossible URLs; a 200+HTML means an infinite URL space."""
    token = secrets.token_hex(4)
    parts = urllib.parse.urlparse(start_url)
    base = f"{parts.scheme}://{parts.netloc}"
    targets = [f"{base}/seo-suite-probe-{token}/"]
    if parts.path not in ("", "/"):
        targets.append(f"{base}{parts.path.rstrip('/')}/probe-{token}/")
    hits = 0
    for target in targets:
        result = fetch(target, timeout)
        if result.status == 200 and "html" in result.content_type.lower():
            hits += 1
    return {"trap_detected": hits > 0, "hits": hits, "probe_urls": targets}


def crawl(start_url: str, max_pages: int, delay: float, timeout: int,
          respect_robots: bool, workers: int = 5,
          sitemap_check: bool = True, dup_check: bool = True,
          probe: bool = True) -> dict[str, Any]:
    start_parts = urllib.parse.urlparse(start_url)
    host = start_parts.netloc.lower()
    base = f"{start_parts.scheme}://{host}"

    robots: urllib.robotparser.RobotFileParser | None = None
    if respect_robots:
        robots = urllib.robotparser.RobotFileParser(f"{base}/robots.txt")
        try:
            robots.read()
        except Exception:  # noqa: BLE001 - unreachable robots.txt == allow
            robots = None

    limiter = RateLimiter(delay)
    queue: deque[tuple[str, int]] = deque([(start_url, 0)])
    seen = {start_url}
    pages: list[dict[str, Any]] = []

    def fetch_one(url: str, depth: int) -> dict[str, Any]:
        if robots and not robots.can_fetch(USER_AGENT, url):
            return {"url": url, "status": None, "blocked_by_robots": True,
                    "depth": depth}
        limiter.wait()
        result = fetch(url, timeout)
        record: dict[str, Any] = {"url": url, "status": result.status,
                                  "depth": depth}
        if result.status == 200 and "html" in result.content_type.lower():
            parser = PageParser()
            try:
                parser.feed(result.body)
                parser.finish()
            except Exception:  # noqa: BLE001 - tolerate malformed HTML
                pass
            record.update(_record_from_parser(url, result.status, parser,
                                              host, result.headers))
        return record

    with ThreadPoolExecutor(max_workers=workers) as pool:
        while queue and len(pages) < max_pages:
            batch: list[tuple[str, int]] = []
            while queue and len(batch) < workers \
                    and len(pages) + len(batch) < max_pages:
                batch.append(queue.popleft())
            for record in pool.map(lambda bd: fetch_one(*bd), batch):
                pages.append(record)
                depth = record.get("depth", 0)
                for out in record.get("internal_outlinks", []):
                    nxt = out["url"]
                    if nxt not in seen:
                        seen.add(nxt)
                        queue.append((nxt, depth + 1))

    # --- post-crawl analyses ------------------------------------------------
    ok = [p for p in pages if p.get("status") == 200]
    titles = [p.get("title") for p in ok if p.get("title")]
    duplicate_titles = sorted({t for t in titles if titles.count(t) > 1})
    summary: dict[str, Any] = {
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
        "images_missing_alt": sum(p.get("images_missing_alt", 0) for p in ok),
        "mixed_content_pages": sum(1 for p in ok
                                   if p.get("mixed_content_count") and
                                   p["url"].startswith("https://")),
        "missing_og_title": sum(1 for p in ok if not p.get("og_title")),
        "missing_twitter_card": sum(1 for p in ok if not p.get("twitter_card")),
        "missing_hsts": sum(1 for p in ok if not p.get("security_hsts")),
        "truncated": len(queue) > 0,
    }

    if sitemap_check:
        sitemap_urls = _fetch_sitemap_urls(base, timeout)
        crawled_urls = {p["url"].rstrip("/") for p in pages if p.get("status")}
        sitemap_norm = {u.rstrip("/") for u in sitemap_urls}
        summary["sitemap"] = {
            "urls_in_sitemap": len(sitemap_urls),
            "crawled_not_in_sitemap": sorted(crawled_urls - sitemap_norm)[:50],
            "sitemap_not_crawled": sorted(sitemap_norm - crawled_urls)[:50],
            "non_200_in_sitemap": sorted(
                p["url"] for p in pages
                if p.get("status") and p["status"] != 200
                and p["url"].rstrip("/") in sitemap_norm)[:50],
        }

    if dup_check:
        summary["near_duplicates"] = _near_duplicate_pairs(ok)

    if probe:
        summary["soft404_probe"] = _probe_soft404(start_url, timeout)

    for page in pages:
        page.pop("_shingles", None)

    return {"summary": summary, "pages": pages}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="site_crawler",
                                     description="Built-in site crawler (v2)")
    parser.add_argument("--url", required=True)
    parser.add_argument("--max-pages", type=int, default=200)
    parser.add_argument("--workers", type=int, default=5,
                        help="concurrent fetch workers (default 5)")
    parser.add_argument("--delay", type=float, default=0.4,
                        help="seconds between requests per host (politeness)")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--ignore-robots", action="store_true")
    parser.add_argument("--no-sitemap-check", action="store_true")
    parser.add_argument("--no-dup-check", action="store_true")
    parser.add_argument("--no-probe", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    result = crawl(args.url, args.max_pages, args.delay, args.timeout,
                   respect_robots=not args.ignore_robots,
                   workers=args.workers,
                   sitemap_check=not args.no_sitemap_check,
                   dup_check=not args.no_dup_check,
                   probe=not args.no_probe)
    print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    sys.exit(main())
