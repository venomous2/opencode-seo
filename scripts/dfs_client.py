"""DataForSEO API client CLI - the mandatory live-data backbone of the suite.

Every skill that needs live SERP, keyword, backlink, on-page, or competitive
data calls this script via bash and consumes the JSON it prints.

Usage:
    python scripts/dfs_client.py <command> [options]

Instant commands (single live call):
    serp           Google organic SERP for a keyword
    volume         Search volume + CPC for a keyword list
    ideas          Keyword ideas from a seed keyword (Labs)
    related        Related keywords (Labs)
    ranked         Keywords a domain/URL ranks for (Labs)
    competitors    Competing domains in organic search (Labs)
    intersection   Keyword intersection/gap between two domains (Labs)
    backlinks      Backlink profile summary for a target
    refdomains     Referring domains for a target
    anchors        Anchor text distribution for a target
    onpage         Instant on-page analysis of a URL
    lighthouse     Lighthouse audit of a URL via DataForSEO
    content        Content analysis: topic/brand mentions across the web
    mentions       LLM/AI citation mentions for a brand or keyword
    business       Google Business Profile info for a business
    whois          WHOIS overview for a domain
    amazon         Amazon product SERP for a keyword (Merchant)
    trends         Google Trends interest over time for keywords

Site crawl commands (task-based On-Page API):
    crawl          Full flow: start crawl, wait, return pages + summary
    crawl-start    Start a crawl, print the task id (for huge crawls)
    crawl-status   Check whether a task id has finished
    crawl-pages    Pull crawled pages for a finished task id

Global options:
    --location  "United States" (default) or any DataForSEO location_name
    --language  "English" (default) or any language_name
    --limit     Max items to return where supported (default 100)
    --sandbox   Use the DataForSEO sandbox (free fake data, for testing)
    --no-cache  Bypass the response cache for this call
    --pretty    Pretty-print the JSON response

Responses are cached on disk (see cache.py) and billed calls are logged to
the cost ledger (see cost_ledger.py). All endpoints live in the ENDPOINTS
table so they can be adjusted in one place.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import time
import urllib.error
import urllib.request
from typing import Any

try:
    from seo_config import ConfigError, dataforseo_credentials
    import cache as response_cache
    import cost_ledger
except ImportError:  # running from another cwd
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
    from seo_config import ConfigError, dataforseo_credentials
    import cache as response_cache
    import cost_ledger

BASE_URL = "https://api.dataforseo.com"
SANDBOX_URL = "https://sandbox.dataforseo.com"

ENDPOINTS = {
    "serp": "/v3/serp/google/organic/live/advanced",
    "volume": "/v3/keywords_data/google_ads/search_volume/live",
    "ideas": "/v3/dataforseo_labs/google/keyword_ideas/live",
    "related": "/v3/dataforseo_labs/google/related_keywords/live",
    "ranked": "/v3/dataforseo_labs/google/ranked_keywords/live",
    "competitors": "/v3/dataforseo_labs/google/competitors_domain/live",
    "intersection": "/v3/dataforseo_labs/google/domain_intersection/live",
    "backlinks": "/v3/backlinks/summary/live",
    "refdomains": "/v3/backlinks/referring_domains/live",
    "anchors": "/v3/backlinks/anchors/live",
    "onpage": "/v3/on_page/instant_pages",
    "lighthouse": "/v3/on_page/lighthouse/live/json",
    "content": "/v3/content_analysis/search/live",
    "mentions": "/v3/ai_optimization/llm_mentions/search/live",
    "business": "/v3/business_data/google/my_business_info/live",
    "whois": "/v3/domain_analytics/whois/overview/live",
    "amazon": "/v3/merchant/amazon/products/live",
    "trends": "/v3/keywords_data/google_trends/explore/live",
}

CRAWL_ENDPOINTS = {
    "task_post": "/v3/on_page/task_post",
    "tasks_ready": "/v3/on_page/tasks_ready",
    "pages": "/v3/on_page/pages",
    "summary": "/v3/on_page/summary/{task_id}",
}

CRAWL_COMMANDS = ("crawl", "crawl-start", "crawl-status", "crawl-pages")


class DfsError(RuntimeError):
    pass


def _auth_header(login: str, password: str) -> str:
    token = base64.b64encode(f"{login}:{password}".encode()).decode()
    return f"Basic {token}"


def post(path: str, payload: list[dict[str, Any]], *, sandbox: bool = False,
         retries: int = 2, timeout: int = 120) -> dict[str, Any]:
    """POST a task array to DataForSEO and return the decoded JSON body."""
    login, password = dataforseo_credentials()
    base = SANDBOX_URL if sandbox else BASE_URL
    request = urllib.request.Request(
        base + path,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": _auth_header(login, password),
            "Content-Type": "application/json",
        },
        method="POST",
    )
    return _execute(request, path, retries, timeout)


def get(path: str, *, sandbox: bool = False, timeout: int = 60) -> dict[str, Any]:
    """GET an authenticated DataForSEO resource (used by crawl helpers)."""
    login, password = dataforseo_credentials()
    base = SANDBOX_URL if sandbox else BASE_URL
    request = urllib.request.Request(
        base + path,
        headers={"Authorization": _auth_header(login, password)},
        method="GET",
    )
    return _execute(request, path, retries=1, timeout=timeout)


def _execute(request: urllib.request.Request, path: str,
             retries: int, timeout: int) -> dict[str, Any]:
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = json.loads(response.read().decode())
                break
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:500]
            if exc.code in (429, 500, 502, 503) and attempt < retries:
                time.sleep(2 * (attempt + 1))
                continue
            raise DfsError(f"HTTP {exc.code} from {path}: {detail}") from exc
        except urllib.error.URLError as exc:
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
                continue
            raise DfsError(f"Network error calling {path}: {exc}") from exc
    if body.get("status_code") not in (20000, None):
        raise DfsError(f"DataForSEO error {body.get('status_code')}: "
                       f"{body.get('status_message')}")
    return body


def tasks(body: dict[str, Any]) -> list[dict[str, Any]]:
    return body.get("tasks") or []


def first_result(body: dict[str, Any]) -> dict[str, Any]:
    for task in tasks(body):
        if task.get("status_code") not in (20000, None):
            raise DfsError(f"Task error {task.get('status_code')}: "
                           f"{task.get('status_message')}")
        results = task.get("result") or []
        if results:
            return results[0]
    return {}


def items(body: dict[str, Any]) -> list[dict[str, Any]]:
    result = first_result(body)
    return result.get("items") or []


# --------------------------------------------------------------------------
# Instant (single-call) commands
# --------------------------------------------------------------------------

def build_payload(command: str, args: argparse.Namespace) -> list[dict[str, Any]]:
    loc, lang, limit = args.location, args.language, args.limit
    if command == "serp":
        return [{
            "keyword": args.keyword, "location_name": loc, "language_name": lang,
            "device": args.device, "os": "windows" if args.device == "desktop" else "android",
            "depth": limit, "calculate_rectangles": False,
        }]
    if command == "volume":
        keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
        return [{"keywords": keywords, "location_name": loc, "language_name": lang}]
    if command == "ideas":
        return [{"keywords": [args.keyword], "location_name": loc,
                 "language_name": lang, "limit": limit}]
    if command == "related":
        return [{"keyword": args.keyword, "location_name": loc,
                 "language_name": lang, "limit": limit}]
    if command == "ranked":
        return [{"target": args.target, "location_name": loc,
                 "language_name": lang, "limit": limit,
                 "order_by": ["keyword_data.keyword_info.search_volume,desc"]}]
    if command == "competitors":
        return [{"target": args.target, "location_name": loc,
                 "language_name": lang, "limit": limit}]
    if command == "intersection":
        return [{"target1": args.target1, "target2": args.target2,
                 "location_name": loc, "language_name": lang, "limit": limit,
                 "intersections": args.mode == "intersect"}]
    if command == "backlinks":
        return [{"target": args.target, "internal_list_limit": 10,
                 "backlinks_status_type": "live"}]
    if command == "refdomains":
        return [{"target": args.target, "limit": limit,
                 "order_by": ["rank,desc"]}]
    if command == "anchors":
        return [{"target": args.target, "limit": limit,
                 "order_by": ["backlinks,desc"]}]
    if command == "onpage":
        return [{"url": args.url, "enable_javascript": True,
                 "load_resources": True,
                 "checks_threshold": {"canonical": 1}}]
    if command == "lighthouse":
        return [{"url": args.url, "for_mobile": args.device != "desktop",
                 "location_name": loc, "language_name": lang}]
    if command == "content":
        return [{"keyword": args.keyword, "search_mode": "as_is", "limit": limit}]
    if command == "mentions":
        return [{"target": args.keyword, "limit": limit}]
    if command == "business":
        return [{"keyword": args.keyword, "location_name": loc,
                 "language_name": lang}]
    if command == "whois":
        return [{"target": args.target, "limit": limit}]
    if command == "amazon":
        return [{"keyword": args.keyword, "location_name": loc,
                 "language_name": lang, "depth": limit}]
    if command == "trends":
        keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
        task: dict[str, Any] = {"keywords": keywords, "location_name": loc,
                                "language_name": lang, "type": "web"}
        if args.date_from:
            task["date_from"] = args.date_from
        if args.date_to:
            task["date_to"] = args.date_to
        return [task]
    raise DfsError(f"Unknown command: {command}")


def run_instant(command: str, args: argparse.Namespace) -> dict[str, Any]:
    payload = build_payload(command, args)
    body = None
    if not args.no_cache and not args.sandbox:
        body = response_cache.get(command, payload)
        cache_hit = body is not None
    else:
        cache_hit = False
    if body is None:
        body = post(ENDPOINTS[command], payload, sandbox=args.sandbox)
        if not args.sandbox:
            response_cache.put(command, payload, body)
            cost_ledger.log(command, body.get("cost"),
                            detail=(args.keyword or args.target or args.url or "")[:120])
    return {
        "command": command,
        "cached": cache_hit,
        "cost": body.get("cost"),
        "tasks_count": body.get("tasks_count"),
        "tasks_error": body.get("tasks_error"),
        "time": body.get("time"),
        "result": [t.get("result") for t in tasks(body)],
    }


# --------------------------------------------------------------------------
# Site crawl commands (task-based On-Page API)
# --------------------------------------------------------------------------

def crawl_start(args: argparse.Namespace) -> str:
    """Submit a crawl task and return its task id."""
    payload = [{
        "target": args.target,
        "max_crawl_pages": args.max_pages,
        "load_resources": False,
        "enable_javascript": args.javascript,
        "store_sitemap": True,
        "crawl_sitemap_only": False,
    }]
    body = post(CRAWL_ENDPOINTS["task_post"], payload, sandbox=args.sandbox)
    cost_ledger.log("crawl-start", body.get("cost"),
                    detail=f"{args.target} ({args.max_pages} pages)")
    for task in tasks(body):
        if task.get("id"):
            return task["id"]
    raise DfsError(f"No task id returned: {json.dumps(body)[:400]}")


def crawl_ready(task_id: str, sandbox: bool = False) -> bool:
    """True when the crawl task appears in the ready list."""
    body = get(CRAWL_ENDPOINTS["tasks_ready"], sandbox=sandbox)
    for task in tasks(body):
        if task.get("id") == task_id:
            return True
    return False


def crawl_pages(task_id: str, args: argparse.Namespace) -> dict[str, Any]:
    payload = [{"id": task_id, "limit": args.limit}]
    body = post(CRAWL_ENDPOINTS["pages"], payload, sandbox=args.sandbox)
    return {
        "command": "crawl-pages",
        "cost": body.get("cost"),
        "result": [t.get("result") for t in tasks(body)],
    }


def crawl_summary(task_id: str, sandbox: bool = False) -> dict[str, Any]:
    return get(CRAWL_ENDPOINTS["summary"].format(task_id=task_id), sandbox=sandbox)


def run_crawl(args: argparse.Namespace) -> dict[str, Any]:
    """Full flow: start, poll until ready, pull summary + pages."""
    task_id = crawl_start(args)
    deadline = time.time() + args.wait * 60
    status = "in_progress"
    while time.time() < deadline:
        if crawl_ready(task_id, sandbox=args.sandbox):
            status = "ready"
            break
        time.sleep(15)
    output: dict[str, Any] = {"command": "crawl", "task_id": task_id,
                              "status": status}
    if status == "ready":
        output["summary"] = crawl_summary(task_id, sandbox=args.sandbox)
        output["pages"] = crawl_pages(task_id, args)["result"]
    else:
        output["hint"] = (f"Still crawling after {args.wait}m. Poll later with: "
                          f"python scripts/dfs_client.py crawl-status --task-id {task_id}")
    return output


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dfs_client",
                                     description="DataForSEO client CLI")
    parser.add_argument("command", choices=sorted(ENDPOINTS) + list(CRAWL_COMMANDS))
    parser.add_argument("--keyword", help="keyword / brand / business name")
    parser.add_argument("--keywords", help="comma-separated keyword list (volume, trends)")
    parser.add_argument("--date-from", help="YYYY-MM-DD (trends)")
    parser.add_argument("--date-to", help="YYYY-MM-DD (trends)")
    parser.add_argument("--target", help="domain or URL target")
    parser.add_argument("--target1", help="first domain (intersection)")
    parser.add_argument("--target2", help="second domain (intersection)")
    parser.add_argument("--mode", choices=["intersect", "gap"], default="intersect",
                        help="intersection mode: shared keywords or gap")
    parser.add_argument("--url", help="full URL (onpage, lighthouse)")
    parser.add_argument("--device", choices=["desktop", "mobile"], default="desktop")
    parser.add_argument("--location", default="United States")
    parser.add_argument("--language", default="English")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--max-pages", type=int, default=500,
                        help="max pages for crawl commands")
    parser.add_argument("--javascript", action="store_true",
                        help="render JS during crawl (slower, costs more)")
    parser.add_argument("--wait", type=int, default=10,
                        help="minutes to wait for a crawl to finish (crawl)")
    parser.add_argument("--task-id", help="task id (crawl-status, crawl-pages)")
    parser.add_argument("--sandbox", action="store_true")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.command == "crawl":
            output = run_crawl(args)
        elif args.command == "crawl-start":
            output = {"command": "crawl-start", "task_id": crawl_start(args)}
        elif args.command == "crawl-status":
            if not args.task_id:
                raise DfsError("crawl-status needs --task-id")
            output = {"command": "crawl-status", "task_id": args.task_id,
                      "ready": crawl_ready(args.task_id, sandbox=args.sandbox)}
        elif args.command == "crawl-pages":
            if not args.task_id:
                raise DfsError("crawl-pages needs --task-id")
            output = crawl_pages(args.task_id, args)
        else:
            output = run_instant(args.command, args)
    except (ConfigError, DfsError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1

    print(json.dumps(output, indent=2 if args.pretty else None, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
