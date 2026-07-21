"""Internal link graph analysis for the OpenCode SEO Suite.

Turns a site_crawler output into link-equity intelligence: orphan pages,
hub pages, depth distribution, and anchor-text quality.

Usage:
    python scripts/site_crawler.py --url https://example.com > crawl.json
    python scripts/link_graph.py --file crawl.json [--format text]
    python scripts/link_graph.py --url https://example.com [--max-pages 200]

Output: summary (orphans, hubs, depth distribution, generic-anchor share),
plus tables for each section. JSON by default, --format text for humans.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter, deque
from pathlib import Path
from typing import Any

GENERIC_ANCHORS = {
    "click here", "here", "read more", "more", "learn more", "link",
    "this", "this page", "find out more", "see more", "view more",
}


def analyse(pages: list[dict[str, Any]], start_url: str) -> dict[str, Any]:
    crawled = {p["url"]: p for p in pages if p.get("status") == 200}
    inlinks: dict[str, list[dict[str, str]]] = {u: [] for u in crawled}
    for page in crawled.values():
        for out in page.get("internal_outlinks", []):
            target = out["url"]
            if target in crawled:
                inlinks[target].append({"from": page["url"],
                                        "anchor": out.get("anchor", "")})

    # BFS depth from the start URL
    start = start_url if start_url in crawled else next(iter(crawled), None)
    depth: dict[str, int] = {}
    if start:
        depth[start] = 0
        queue: deque[str] = deque([start])
        while queue:
            current = queue.popleft()
            for out in crawled[current].get("internal_outlinks", []):
                nxt = out["url"]
                if nxt in crawled and nxt not in depth:
                    depth[nxt] = depth[current] + 1
                    queue.append(nxt)

    orphans = sorted(u for u in crawled if u != start and not inlinks[u])
    hubs = sorted(
        ((len(p.get("internal_outlinks", [])), u) for u, p in crawled.items()),
        reverse=True)
    depth_dist: dict[int, int] = {}
    for d in depth.values():
        depth_dist[d] = depth_dist.get(d, 0) + 1
    unreachable = sorted(set(crawled) - set(depth))

    anchor_counts: Counter[str] = Counter()
    generic_count = 0
    total_anchors = 0
    for page in crawled.values():
        for out in page.get("internal_outlinks", []):
            anchor = (out.get("anchor") or "").strip().lower()
            if not anchor:
                continue
            total_anchors += 1
            anchor_counts[anchor] += 1
            if anchor in GENERIC_ANCHORS:
                generic_count += 1

    most_linked = sorted(((len(v), u) for u, v in inlinks.items()),
                         reverse=True)[:15]

    return {
        "pages_analysed": len(crawled),
        "orphan_pages": orphans,
        "hub_pages": [{"url": u, "outlinks": n} for n, u in hubs[:15] if n > 0],
        "most_linked_pages": [{"url": u, "inlinks": n} for n, u in most_linked if n > 0],
        "depth_distribution": dict(sorted(depth_dist.items())),
        "unreachable_from_homepage": unreachable,
        "anchor_quality": {
            "total_internal_anchors": total_anchors,
            "generic_anchor_count": generic_count,
            "generic_anchor_pct": round(100 * generic_count / max(total_anchors, 1), 1),
            "top_anchors": anchor_counts.most_common(15),
        },
    }


def render_text(result: dict[str, Any]) -> str:
    lines = [f"\nInternal link graph — {result['pages_analysed']} pages"]
    lines.append(f"\nORPHAN PAGES (no internal inlinks): {len(result['orphan_pages'])}")
    for u in result["orphan_pages"][:15]:
        lines.append(f"  - {u}")
    lines.append("\nMOST LINKED PAGES:")
    for row in result["most_linked_pages"][:10]:
        lines.append(f"  {row['inlinks']:>4} inlinks  {row['url']}")
    lines.append("\nHUB PAGES (most outlinks):")
    for row in result["hub_pages"][:10]:
        lines.append(f"  {row['outlinks']:>4} outlinks  {row['url']}")
    lines.append("\nDEPTH DISTRIBUTION (clicks from homepage):")
    for d, n in result["depth_distribution"].items():
        lines.append(f"  depth {d}: {n} pages")
    if result["unreachable_from_homepage"]:
        lines.append(f"  unreachable: {len(result['unreachable_from_homepage'])} pages")
    aq = result["anchor_quality"]
    lines.append(f"\nANCHOR QUALITY: {aq['generic_anchor_pct']}% generic "
                 f"({aq['generic_anchor_count']} of {aq['total_internal_anchors']})")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="link_graph",
                                     description="Internal link graph analysis")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--file", help="crawl JSON from site_crawler.py")
    source.add_argument("--url", help="crawl this site first, then analyse")
    parser.add_argument("--max-pages", type=int, default=200)
    parser.add_argument("--format", choices=["json", "text"], default="json")
    args = parser.parse_args(argv)

    if args.url:
        script = Path(__file__).parent / "site_crawler.py"
        proc = subprocess.run(
            [sys.executable, str(script), "--url", args.url,
             "--max-pages", str(args.max_pages)],
            capture_output=True, text=True, timeout=600)
        if proc.returncode != 0:
            print(json.dumps({"error": f"Crawl failed: {proc.stderr[:300]}"}))
            return 1
        crawl = json.loads(proc.stdout)
        start_url = args.url
    else:
        path = Path(args.file)
        if not path.is_file():
            print(json.dumps({"error": f"File not found: {path}"}))
            return 1
        try:
            crawl = json.loads(path.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            crawl = json.loads(path.read_text(encoding="utf-16"))
        start_url = (crawl.get("summary") or {}).get("start_url", "")

    result = analyse(crawl.get("pages", []), start_url)
    if args.format == "text":
        print(render_text(result))
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    sys.exit(main())
