"""Visual internal link graph renderer for the OpenCode SEO Suite.

Turns crawl data into a client-facing radial link-graph: homepage at the
centre, pages arranged in depth rings (clicks from home), node size =
inlinks, colours by page role. Pure SVG — no JavaScript — so it prints
cleanly to PDF.

Usage:
    python scripts/link_graph_render.py --file crawl.json [-o graph.html]
    python scripts/link_graph_render.py --url https://example.com [-o graph.html]
    python scripts/link_graph_render.py --file crawl.json --pdf

Then (optional): python scripts/report_pdf.py <graph>.html for the PDF.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import urllib.parse
from collections import deque
from datetime import date
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

import report_build  # noqa: E402
import report_pdf  # noqa: E402
from link_graph import analyse  # noqa: E402

W, H = 1100, 1100
CX, CY = W / 2, H / 2
RING_START = 150
RING_STEP = 130

COLOURS = {
    "home": report_build.PURPLE,
    "normal": report_build.TEAL,
    "hub": report_build.YELLOW,
    "orphan": report_build.PINK,
    "unreachable": "#94a3b8",
}


def _short(url: str, length: int = 28) -> str:
    path = urllib.parse.urlparse(url).path or "/"
    return path if len(path) <= length else path[: length - 1] + "…"


def layout(crawl: dict[str, Any]) -> dict[str, Any]:
    """Assign each page a position, colour, and size on the radial graph."""
    pages = {p["url"]: p for p in crawl.get("pages", []) if p.get("status") == 200}
    start = (crawl.get("summary") or {}).get("start_url") or next(iter(pages), "")
    if start not in pages:
        start = next(iter(pages), "")

    # BFS: depth + parent per page
    depth: dict[str, int] = {start: 0} if start else {}
    parent: dict[str, str] = {}
    queue: deque[str] = deque([start]) if start else deque()
    while queue:
        current = queue.popleft()
        for out in pages[current].get("internal_outlinks", []):
            nxt = out["url"]
            if nxt in pages and nxt not in depth:
                depth[nxt] = depth[current] + 1
                parent[nxt] = current
                queue.append(nxt)

    # inlink / outlink counts
    inlinks: dict[str, int] = {u: 0 for u in pages}
    for page in pages.values():
        for out in page.get("internal_outlinks", []):
            if out["url"] in inlinks:
                inlinks[out["url"]] += 1

    # group children per parent, assign angles: depth-1 even spread,
    # children clustered inside their parent's sector
    children: dict[str, list[str]] = {}
    for node in depth:
        if node != start:
            children.setdefault(parent.get(node, start), []).append(node)
    for kids in children.values():
        kids.sort(key=lambda u: -inlinks[u])

    angle: dict[str, float] = {}
    if start:
        angle[start] = 0.0
    sectors = children.get(start, [])
    step = 2 * math.pi / max(len(sectors), 1)

    def assign(node: str, centre: float, span: float, ring_depth: int) -> None:
        angle[node] = centre
        kids = children.get(node, [])
        if not kids:
            return
        child_span = span / max(len(kids), 1)
        for i, kid in enumerate(kids):
            assign(kid, centre - span / 2 + child_span * (i + 0.5),
                   child_span, ring_depth + 1)

    for i, node in enumerate(sectors):
        assign(node, step * i, step * 0.9, 1)

    nodes = []
    for url, d in depth.items():
        radius = RING_START + RING_STEP * d if d > 0 else 0
        a = angle.get(url, 0.0)
        x = CX + radius * math.cos(a)
        y = CY + radius * math.sin(a)
        count = inlinks[url]
        size = 5 + min(14, math.sqrt(count) * 2.2)
        out_count = len(pages[url].get("internal_outlinks", []))
        if url == start:
            colour, role = COLOURS["home"], "home"
        elif not count:
            colour, role = COLOURS["orphan"], "orphan"
        elif out_count >= 25:
            colour, role = COLOURS["hub"], "hub"
        else:
            colour, role = COLOURS["normal"], "normal"
        nodes.append({"url": url, "x": x, "y": y, "size": size,
                      "colour": colour, "role": role, "depth": d,
                      "inlinks": count, "outlinks": out_count})

    # unreachable pages: grey arc at the outer edge
    unreachable = sorted(set(pages) - set(depth))
    for i, url in enumerate(unreachable):
        a = 2 * math.pi * i / max(len(unreachable), 1)
        radius = RING_START + RING_STEP * (max(depth.values(), default=1) + 1)
        nodes.append({"url": url, "x": CX + radius * math.cos(a),
                      "y": CY + radius * math.sin(a), "size": 4,
                      "colour": COLOURS["unreachable"], "role": "unreachable",
                      "depth": -1, "inlinks": inlinks[url],
                      "outlinks": len(pages[url].get("internal_outlinks", []))})

    edges = []
    node_xy = {n["url"]: (n["x"], n["y"]) for n in nodes}
    for url in depth:
        for out in pages[url].get("internal_outlinks", []):
            if out["url"] in node_xy:
                edges.append({"x1": node_xy[url][0], "y1": node_xy[url][1],
                              "x2": node_xy[out["url"]][0],
                              "y2": node_xy[out["url"]][1],
                              "tree": parent.get(out["url"]) == url})
    return {"nodes": nodes, "edges": edges, "start": start}


def render_svg(graph: dict[str, Any], max_labels: int = 16) -> str:
    nodes, edges = graph["nodes"], graph["edges"]
    parts = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" '
             'aria-label="Internal link graph">']
    parts.append(f'<rect width="{W}" height="{H}" fill="#f8fafc" rx="12"/>')
    max_depth = max((n["depth"] for n in nodes if n["depth"] > 0), default=0)
    for d in range(1, max_depth + 1):
        r = RING_START + RING_STEP * d
        parts.append(f'<circle cx="{CX}" cy="{CY}" r="{r}" fill="none" '
                     f'stroke="#e2e8f0" stroke-dasharray="3 5"/>')
    for e in edges:
        opacity = "0.30" if e["tree"] else "0.05"
        parts.append(f'<line x1="{e["x1"]:.0f}" y1="{e["y1"]:.0f}" '
                     f'x2="{e["x2"]:.0f}" y2="{e["y2"]:.0f}" '
                     f'stroke="{report_build.MUTED}" stroke-opacity="{opacity}" '
                     f'stroke-width="1"/>')
    top = sorted(nodes, key=lambda n: -n["inlinks"])[:max_labels]
    label_urls = {n["url"] for n in top}
    for n in nodes:
        parts.append(f'<circle cx="{n["x"]:.0f}" cy="{n["y"]:.0f}" r="{n["size"]:.0f}" '
                     f'fill="{n["colour"]}" stroke="#fff" stroke-width="1.5">'
                     f'<title>{n["url"]} — {n["inlinks"]} inlinks, '
                     f'{n["outlinks"]} outlinks</title></circle>')
        if n["url"] in label_urls and n["depth"] >= 0:
            parts.append(f'<text x="{n["x"] + n["size"] + 3:.0f}" y="{n["y"] + 3:.0f}" '
                         f'font-size="11" fill="{report_build.INK}">'
                         f'{_short(n["url"])}</text>')
    parts.append("</svg>")
    return "".join(parts)


def render_html(crawl: dict[str, Any], analysis: dict[str, Any],
                graph: dict[str, Any]) -> str:
    summary = crawl.get("summary") or {}
    domain = urllib.parse.urlparse(graph["start"]).netloc or graph["start"]
    orphan_n = len(analysis["orphan_pages"])
    hub_n = len(analysis["hub_pages"])
    unreachable_n = len(analysis["unreachable_from_homepage"])
    aq = analysis["anchor_quality"]

    legend = "".join(
        f'<span class="legend-item"><span class="sw" style="background:{c}"></span>{lbl}</span>'
        for lbl, c in [("Homepage", COLOURS["home"]), ("Page", COLOURS["normal"]),
                       ("Hub (25+ outlinks)", COLOURS["hub"]),
                       ("Orphan (no inlinks)", COLOURS["orphan"]),
                       ("Unreachable", COLOURS["unreachable"])])
    stats_block = (
        "```chart\n" + json.dumps({"type": "stats", "data": [
            ["Pages analysed", str(analysis["pages_analysed"])],
            ["Orphan pages", str(orphan_n)],
            ["Unreachable", str(unreachable_n)],
            ["Generic anchors", f"{aq['generic_anchor_pct']}%"],
        ]}) + "\n```")

    top_linked = "\n".join(
        f"| {r['inlinks']} | {r['url']} |" for r in analysis["most_linked_pages"][:10])
    orphans = "\n".join(f"- {u}" for u in analysis["orphan_pages"][:15]) \
        or "- None — every page has internal inlinks."
    depth_rows = "\n".join(f"| {d} | {n} |"
                           for d, n in analysis["depth_distribution"].items())

    body_md = f"""## Internal link graph

%%LEGEND_HTML%%

%%LINKGRAPH_SVG%%

{stats_block}

| Inlinks | Page |
|---|---|
{top_linked}

## Depth distribution (clicks from homepage)

| Depth | Pages |
|---|---|
{depth_rows}

## Orphan pages

{orphans}

> Node size = number of internal inlinks. Rings = clicks from the homepage.
> Faint lines = internal links; brighter lines = primary link paths.
> Crawl of {summary.get('pages_crawled', '?')} pages from {graph['start']}.
"""
    body, toc = report_build.md_to_html(body_md)
    # raw HTML must bypass markdown escaping — swap placeholders afterwards
    body = body.replace("<p>%%LINKGRAPH_SVG%%</p>", render_svg(graph))
    body = body.replace("%%LINKGRAPH_SVG%%", render_svg(graph))
    body = body.replace("<p>%%LEGEND_HTML%%</p>",
                        f'<div class="legend">{legend}</div>')
    body = body.replace("%%LEGEND_HTML%%",
                        f'<div class="legend">{legend}</div>')
    return report_build.SHELL.format(
        title=f"Internal link graph — {domain}",
        brand="Lee Beirne",
        report_date=date.today().strftime("%d %B %Y"),
        teal=report_build.TEAL, purple=report_build.PURPLE,
        pink=report_build.PINK, yellow=report_build.YELLOW,
        ink=report_build.INK, muted=report_build.MUTED,
        toc="", body=body,
        footer=report_build._linkify(report_build.DEFAULT_FOOTER),
        body_class="")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="link_graph_render",
                                     description="Visual internal link graph renderer")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--file", help="crawl JSON from site_crawler.py")
    source.add_argument("--url", help="crawl this site first, then render")
    parser.add_argument("-o", "--output", help="output .html path")
    parser.add_argument("--max-pages", type=int, default=200)
    parser.add_argument("--pdf", action="store_true",
                        help="also write the PDF (needs headless browser)")
    args = parser.parse_args(argv)

    if args.url:
        script = Path(__file__).parent / "site_crawler.py"
        proc = subprocess.run(
            [sys.executable, str(script), "--url", args.url,
             "--max-pages", str(args.max_pages)],
            capture_output=True, text=True, timeout=900)
        if proc.returncode != 0:
            print(json.dumps({"error": f"Crawl failed: {proc.stderr[:300]}"}))
            return 1
        crawl = json.loads(proc.stdout)
    else:
        path = Path(args.file)
        if not path.is_file():
            print(json.dumps({"error": f"File not found: {path}"}))
            return 1
        try:
            crawl = json.loads(path.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            crawl = json.loads(path.read_text(encoding="utf-16"))

    graph = layout(crawl)
    analysis = analyse(crawl.get("pages", []), graph["start"])
    html_text = render_html(crawl, analysis, graph)

    if args.output:
        out_path = Path(args.output)
    else:
        domain = (urllib.parse.urlparse(graph["start"]).netloc or "site")
        out_path = Path(f"LINK-GRAPH-{domain}-{date.today().isoformat()}.html")
    out_path.write_text(html_text, encoding="utf-8")
    outputs: dict[str, str] = {"html": str(out_path.resolve())}

    if args.pdf:
        browser = report_pdf.find_browser()
        if browser:
            pdf_path = report_pdf.html_to_pdf(
                out_path, out_path.with_suffix(".pdf"), browser)
            outputs["pdf"] = str(pdf_path.resolve())
        else:
            outputs["pdf"] = "skipped (no headless browser found)"

    print(json.dumps(outputs, indent=2))
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    sys.exit(main())
