"""Built-in site crawler (v2) for the OpenCode SEO Suite.

A free, polite, same-host crawler for small-to-mid sites. For very large
sites or heavy JS rendering, use `dfs_client.py crawl` (paid) instead.

Usage:
    python scripts/site_crawler.py --url https://example.com [--max-pages 200]
        [--workers 5] [--delay 0.4] [--timeout 15] [--ignore-robots]
        [--no-sitemap-check] [--no-dup-check] [--no-probe] [--pretty]
    python scripts/site_crawler.py --url https://www.example.com \
        --canonical-variants --pretty

Output (JSON):
    summary: pages crawled, status distribution, metadata/H1/image stats,
              sitemap cross-check, near-duplicate pairs, soft-404 probe
    pages:   one record per URL with all extracted SEO fields

Redirect tracing uses no-follow requests. Unlike a normal content fetch, it
preserves the original status, every Location header, final URL and hop count
so a 301 -> 200 chain is never reported as a source URL returning 200.
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
from typing import Any, Callable

USER_AGENT = "OpenCodeSEOSuite-Crawler/2.0 (+https://opencode.ai)"

GENERIC_ANCHOR_TEXTS = {
    "click here", "here", "read more", "more", "learn more", "link",
    "this", "this page", "find out more", "see more", "view more",
}

CTA_PHRASES = {
    "get started", "sign up", "signup", "register", "buy now", "buy",
    "shop", "order", "book", "book a demo", "book a consultation",
    "book a call", "demo", "request a demo", "get a quote", "get quote",
    "quote", "contact us", "contact", "call us", "call now", "phone",
    "download", "subscribe", "join", "try", "start free", "free trial",
    "add to cart", "add to basket", "checkout", "enquire", "enquiry",
    "apply", "claim", "get my", "schedule", "reserve", "submit", "send",
}

GENERIC_CTA_TEXTS = {"submit", "click here", "go", "send", "ok", "more",
                     "learn more"}

TRUST_KEYWORDS = (
    "guarantee", "money-back", "money back", "refund", "warranty",
    "testimonial", "testimonials", "reviews", "reviewed", "rated",
    "stars", "trusted by", "as seen", "certified", "accredited",
    "award", "secure checkout", "ssl secure", "verified", "trustpilot",
    "feefo", "google reviews", "years of experience", "years in business",
)

URGENCY_KEYWORDS = (
    "limited time", "limited offer", "ends soon", "offer ends", "% off",
    "sale ends", "last chance", "countdown", "today only", "expires",
    "only a few left", "selling fast",
)

LIVE_CHAT_MARKERS = (
    "intercom", "drift", "zendesk", "tidio", "livechat", "crisp",
    "live-chat", "live_chat", "chat-widget", "olark",
)

# Keep the original four positional fields for existing callers/tests. The
# fifth field records urllib's final URL after it has followed redirects.
FetchResult = namedtuple("FetchResult",
                         ["status", "content_type", "body", "headers", "final_url"],
                         defaults=[""])
REDIRECT_STATUSES = {301, 302, 303, 307, 308}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Expose redirect responses to the tracer instead of following them."""

    def redirect_request(self, req: Any, fp: Any, code: int, msg: str,
                         headers: Any, newurl: str) -> None:
        return None


_NO_REDIRECT_OPENER = urllib.request.build_opener(_NoRedirect())


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
        # --- accessibility fields ---
        self.form_inputs_unlabelled = 0
        self.has_skip_link = False
        self.has_main = False
        self.has_nav = False
        self.heading_skips = 0
        self.duplicate_ids = 0
        self.empty_links = 0
        self.empty_buttons = 0
        self.generic_link_texts = 0
        self.tables_total = 0
        self.tables_without_th = 0
        self.iframes_total = 0
        self.iframes_missing_title = 0
        self.positive_tabindex = 0
        # --- CRO fields ---
        self.cta_count = 0
        self.cta_above_fold = 0
        self.cta_texts: list[str] = []
        self.primary_cta_generic = False
        self.form_count = 0
        self.form_fields_max = 0
        self.form_has_captcha = False
        self.tel_links = 0
        self.trust_signal_count = 0
        self.urgency_signal_count = 0
        self.faq_present = False
        self.live_chat = False
        self._doc_position = 0
        self._cta_positions: list[int] = []
        self._element_index = 0
        self._body_index = 0
        self._form_depth = 0
        self._form_fields = 0
        self._label_targets: set[str] = set()
        self._label_depth = 0
        self._pending_inputs: list[dict[str, Any]] = []
        self._ids: list[str] = []
        self._last_heading_level = 0
        self._link_aria = False
        self._link_img_alt = False
        self._table_has_th = False
        self._in_button = False
        self._button_text: list[str] = []
        self._button_aria = False
        self._button_img_alt = False
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
        self._element_index += 1
        attr = dict(attrs)
        marker_blob = " ".join([
            (attr.get("id") or ""), (attr.get("class") or ""),
            (attr.get("src") or "")]).lower()
        if any(m in marker_blob for m in LIVE_CHAT_MARKERS):
            self.live_chat = True
        if attr.get("id"):
            self._ids.append(attr["id"])
        tabindex = attr.get("tabindex") or ""
        if tabindex.lstrip("-").isdigit() and int(tabindex) > 0:
            self.positive_tabindex += 1
        if tag == "html" and attr.get("lang"):
            self.html_lang = attr["lang"].strip()
        if tag == "body":
            self._body_index = self._element_index
        if tag == "title":
            self._in_title = True
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag[1])
            if self._last_heading_level and level > self._last_heading_level + 1:
                self.heading_skips += 1
            self._last_heading_level = level
            if tag == "h1":
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
        elif tag == "label":
            self._label_depth += 1
            if attr.get("for"):
                self._label_targets.add(attr["for"].strip())
        elif tag == "form":
            self.form_count += 1
            self._form_depth += 1
            self._form_fields = 0
        elif tag in ("input", "select", "textarea"):
            if self._form_depth:
                self._form_fields += 1
            input_type = (attr.get("type") or "text").lower()
            if tag != "input" or input_type not in (
                    "hidden", "submit", "button", "reset"):
                self._pending_inputs.append({
                    "aria": (attr.get("aria-label") or "").strip(),
                    "labelledby": (attr.get("aria-labelledby") or "").strip(),
                    "title": (attr.get("title") or "").strip(),
                    "id": (attr.get("id") or "").strip(),
                    "wrapped": self._label_depth > 0,
                })
        elif tag in ("script", "style", "noscript"):
            self._skip_depth += 1
            if tag == "script" and (attr.get("type") or "").lower() == "application/ld+json":
                self._in_jsonld = True
                self._jsonld_parts = []
            src = (attr.get("src") or "").lower()
            if any(m in src for m in ("recaptcha", "hcaptcha", "turnstile")):
                self.form_has_captcha = True
            if src.startswith("http://"):
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
        elif tag in ("main",) or (attr.get("role") or "").lower() == "main":
            self.has_main = True
        elif tag in ("nav",) or (attr.get("role") or "").lower() == "navigation":
            self.has_nav = True
        elif tag == "a":
            if attr.get("href"):
                self._current_href = attr["href"]
                self._current_anchor = []
                self._link_aria = bool((attr.get("aria-label") or "").strip())
                self._link_img_alt = False
            if "author" in (attr.get("rel") or "").lower():
                self.has_rel_author = True
        elif tag == "button":
            self._in_button = True
            self._button_text = []
            self._button_aria = bool((attr.get("aria-label") or "").strip())
            self._button_img_alt = False
        elif tag == "table":
            self.tables_total += 1
            self._table_has_th = False
        elif tag == "th":
            self._table_has_th = True
        elif tag == "iframe":
            self.iframes_total += 1
            if not (attr.get("title") or "").strip():
                self.iframes_missing_title += 1
        elif tag == "img":
            self.images_total += 1
            has_alt = bool((attr.get("alt") or "").strip())
            if not has_alt:
                self.images_missing_alt += 1
            if self._current_href is not None and has_alt:
                self._link_img_alt = True
            if self._in_button and has_alt:
                self._button_img_alt = True
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
            anchor_text = " ".join(" ".join(self._current_anchor).split())
            self.links.append({
                "href": self._current_href,
                "anchor": anchor_text,
            })
            if self._current_href.startswith("#") and "skip" in anchor_text.lower():
                self.has_skip_link = True
            if self._current_href.lower().startswith("tel:"):
                self.tel_links += 1
            if not anchor_text and not self._link_aria and not self._link_img_alt:
                self.empty_links += 1
            if anchor_text.lower() in GENERIC_ANCHOR_TEXTS:
                self.generic_link_texts += 1
            lowered = anchor_text.lower()
            if any(p in lowered for p in CTA_PHRASES):
                self.cta_count += 1
                self.cta_texts.append(anchor_text[:60])
                self._cta_positions.append(self._element_index)
                if len(self.cta_texts) == 1 and lowered in GENERIC_CTA_TEXTS:
                    self.primary_cta_generic = True
            self._current_href = None
            self._current_anchor = []
        elif tag == "form":
            self._form_depth = max(0, self._form_depth - 1)
            self.form_fields_max = max(self.form_fields_max, self._form_fields)
            self._form_fields = 0
        elif tag == "button" and self._in_button:
            button_text = " ".join(" ".join(self._button_text).split())
            if not button_text and not self._button_aria and not self._button_img_alt:
                self.empty_buttons += 1
            lowered_b = button_text.lower()
            if any(p in lowered_b for p in CTA_PHRASES):
                self.cta_count += 1
                self.cta_texts.append(button_text[:60])
                self._cta_positions.append(self._element_index)
                if len(self.cta_texts) == 1 and lowered_b in GENERIC_CTA_TEXTS:
                    self.primary_cta_generic = True
            self._in_button = False
        elif tag == "button" and self._in_button:
            button_text = " ".join(" ".join(self._button_text).split())
            if not button_text and not self._button_aria and not self._button_img_alt:
                self.empty_buttons += 1
            self._in_button = False
        elif tag == "label":
            self._label_depth = max(0, self._label_depth - 1)
        elif tag == "table":
            if not self._table_has_th:
                self.tables_without_th += 1
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
        self._doc_position += len(data)
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
        if self._in_button and self._skip_depth == 0:
            self._button_text.append(data)
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
        # CRO: above-fold CTAs (first ~40% of BODY elements — the fold
        # proxy, measured from <body> so head markup doesn't skew it)
        body_start = self._body_index
        body_span = max(self._element_index - body_start, 1)
        self.cta_above_fold = sum(
            1 for pos in self._cta_positions
            if (pos - body_start) / body_span < 0.40)
        lowered_text = text.lower()
        self.trust_signal_count = sum(lowered_text.count(k)
                                      for k in TRUST_KEYWORDS)
        self.urgency_signal_count = sum(lowered_text.count(k)
                                        for k in URGENCY_KEYWORDS)
        self.faq_present = ("faqpage" in [t.lower() for t in self.schema_types]
                            or any("faq" in h.lower() or "frequently asked" in h.lower()
                                   for h in self.h2))
        self.live_chat = (self.live_chat
                          or any(m in lowered_text for m in LIVE_CHAT_MARKERS))
        # resolve pending form inputs now that all <label for> targets are known
        for field in self._pending_inputs:
            labelled = (field["aria"] or field["labelledby"] or field["title"]
                        or field["wrapped"]
                        or (field["id"] and field["id"] in self._label_targets))
            if not labelled:
                self.form_inputs_unlabelled += 1
        seen: set[str] = set()
        for element_id in self._ids:
            if element_id in seen:
                self.duplicate_ids += 1
            seen.add(element_id)


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------

def fetch(url: str, timeout: int) -> FetchResult:
    """GET content, following redirects, while preserving the final URL.

    Use ``trace_redirects`` for canonicalisation or redirect-chain claims;
    this helper intentionally follows redirects so the crawler can parse the
    final page content.
    """
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            body = response.read(2_000_000).decode("utf-8", errors="replace")
            headers = {k.lower(): v for k, v in response.headers.items()}
            return FetchResult(response.status, content_type, body, headers,
                               response.geturl())
    except urllib.error.HTTPError as exc:
        return FetchResult(exc.code, "", "", {}, url)
    except (urllib.error.URLError, TimeoutError, OSError):
        return FetchResult(0, "", "", {}, url)


def _request_no_follow(url: str, timeout: int) -> tuple[int, dict[str, str]]:
    """Return one response without following a Location header."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with _NO_REDIRECT_OPENER.open(request, timeout=timeout) as response:
            return response.status, {k.lower(): v for k, v in response.headers.items()}
    except urllib.error.HTTPError as exc:
        headers = {k.lower(): v for k, v in exc.headers.items()} if exc.headers else {}
        return exc.code, headers
    except (urllib.error.URLError, TimeoutError, OSError):
        return 0, {}


def trace_redirects(url: str, timeout: int = 20, max_hops: int = 10,
                    requester: Callable[[str, int], tuple[int, dict[str, str]]] | None = None
                    ) -> dict[str, Any]:
    """Trace redirects without losing the initial response evidence.

    ``requester`` is injectable for offline tests. The returned chain holds
    one entry per request, including the final non-redirect response.
    """
    requester = requester or _request_no_follow
    requested_url = url
    current_url = url
    seen = {url}
    chain: list[dict[str, Any]] = []
    loop = False
    broken_location = False

    for _ in range(max_hops + 1):
        status, headers = requester(current_url, timeout)
        location = headers.get("location", "")
        resolved_location = urllib.parse.urljoin(current_url, location) if location else ""
        chain.append({"url": current_url, "status": status,
                      "location": location or None,
                      "resolved_location": resolved_location or None})

        if status not in REDIRECT_STATUSES:
            break
        if not location:
            broken_location = True
            break
        if resolved_location in seen:
            loop = True
            break
        seen.add(resolved_location)
        current_url = resolved_location
    else:
        # The trace exhausted its hop limit while still redirecting.
        loop = True

    final = chain[-1] if chain else {"url": requested_url, "status": 0}
    redirect_count = sum(1 for hop in chain if hop["status"] in REDIRECT_STATUSES)
    if broken_location:
        verdict = "broken_location"
    elif loop:
        verdict = "loop_or_limit"
    elif final["status"] == 0:
        verdict = "request_failed"
    elif final["status"] != 200:
        verdict = "non_200_final"
    elif redirect_count > 1:
        verdict = "redirect_chain"
    else:
        verdict = "ok"
    return {
        "requested_url": requested_url,
        "initial_status": chain[0]["status"] if chain else 0,
        "final_url": final["url"],
        "final_status": final["status"],
        "redirect_count": redirect_count,
        "chain": chain,
        "loop": loop,
        "broken_location": broken_location,
        "verdict": verdict,
    }


def _normal_url(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    path = parts.path or "/"
    return urllib.parse.urlunsplit((parts.scheme.lower(), parts.netloc.lower(),
                                    path, parts.query, ""))


def canonical_variant_audit(canonical_url: str, timeout: int = 20,
                            max_hops: int = 10,
                            requester: Callable[[str, int], tuple[int, dict[str, str]]] | None = None
                            ) -> dict[str, Any]:
    """Trace http/https and www/non-www home/path variants against a canonical."""
    parsed = urllib.parse.urlsplit(canonical_url)
    bare_host = parsed.netloc.lower().removeprefix("www.")
    path = parsed.path or "/"
    suffix = ("?" + parsed.query) if parsed.query else ""
    variants = [
        f"http://{bare_host}{path}{suffix}",
        f"http://www.{bare_host}{path}{suffix}",
        f"https://{bare_host}{path}{suffix}",
        f"https://www.{bare_host}{path}{suffix}",
    ]
    expected = _normal_url(canonical_url)
    results = []
    for variant in dict.fromkeys(variants):
        trace = trace_redirects(variant, timeout, max_hops, requester)
        same_as_canonical = _normal_url(variant) == expected
        final_matches = _normal_url(trace["final_url"]) == expected
        if trace["loop"] or trace["broken_location"]:
            canonical_verdict = trace["verdict"]
        elif trace["final_status"] != 200:
            canonical_verdict = "non_200_final"
        elif not same_as_canonical and trace["initial_status"] not in REDIRECT_STATUSES:
            canonical_verdict = "variant_direct_200"
        elif not final_matches:
            canonical_verdict = "wrong_final_url"
        elif same_as_canonical and trace["redirect_count"] == 0:
            canonical_verdict = "canonical_200"
        elif trace["redirect_count"] > 1:
            canonical_verdict = "redirect_chain"
        else:
            canonical_verdict = "redirect_ok"
        trace["canonical_verdict"] = canonical_verdict
        trace["final_matches_canonical"] = final_matches
        results.append(trace)

    failures = {"loop_or_limit", "broken_location", "non_200_final",
                "wrong_final_url", "variant_direct_200", "request_failed"}
    chains = sum(1 for result in results
                 if result["canonical_verdict"] == "redirect_chain")
    return {
        "canonical_url": expected,
        "variants": results,
        "overall_verdict": "failure" if any(
            result["canonical_verdict"] in failures for result in results
        ) else "needs_chain_cleanup" if chains else "healthy",
        "redirect_chains": chains,
    }


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
        record: dict[str, Any] = {
            "url": url,
            "requested_url": url,
            "final_url": result.final_url or url,
            "status": result.status,
            "depth": depth,
        }
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
    parser.add_argument("--trace-redirects", action="store_true",
                        help="trace this URL without following redirect evidence")
    parser.add_argument("--canonical-variants", action="store_true",
                        help="trace http/https and www/non-www variants against --url")
    parser.add_argument("--max-redirects", type=int, default=10,
                        help="redirect hop cap for trace modes (default 10)")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    if args.canonical_variants:
        result = canonical_variant_audit(args.url, args.timeout,
                                         args.max_redirects)
        print(json.dumps(result, indent=2 if args.pretty else None,
                         ensure_ascii=False))
        return 0
    if args.trace_redirects:
        result = trace_redirects(args.url, args.timeout, args.max_redirects)
        print(json.dumps(result, indent=2 if args.pretty else None,
                         ensure_ascii=False))
        return 0

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
