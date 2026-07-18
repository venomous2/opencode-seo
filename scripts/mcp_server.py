"""MCP server exposing the suite's DataForSEO layer as native tools.

Lets any MCP-capable client call DataForSEO through the suite's client
(with its cache, cost ledger, and credential resolution) instead of wiring
their own integration.

Requires:  pip install mcp
Register in opencode.json:
    "mcp": {
      "seo-suite": {
        "type": "local",
        "command": ["python", "scripts/mcp_server.py"],
        "enabled": true
      }
    }
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

try:
    from mcp.server.fastmcp import FastMCP  # type: ignore
except ImportError:
    print(json.dumps({
        "error": "The 'mcp' package is required: pip install mcp"}))
    sys.exit(1)

import dfs_client  # noqa: E402

mcp = FastMCP("opencode-seo-suite")


def _call(command: str, **kwargs: Any) -> str:
    """Run a dfs_client command through its payload builder."""
    class Args:
        location = kwargs.pop("location", "United States")
        language = kwargs.pop("language", "English")
        limit = kwargs.pop("limit", 50)
        device = kwargs.pop("device", "desktop")
        mode = kwargs.pop("mode", "intersect")
        keyword = kwargs.get("keyword")
        keywords = kwargs.get("keywords")
        target = kwargs.get("target")
        target1 = kwargs.get("target1")
        target2 = kwargs.get("target2")
        url = kwargs.get("url")
    try:
        payload = dfs_client.build_payload(command, Args())
        body = dfs_client.post(dfs_client.ENDPOINTS[command], payload)
        return json.dumps(body.get("tasks", [{}])[0].get("result", []),
                          ensure_ascii=False)
    except Exception as exc:  # noqa: BLE001 - surface as tool error text
        return json.dumps({"error": str(exc)})


@mcp.tool()
def seo_serp(keyword: str, location: str = "United States",
             language: str = "English", limit: int = 20) -> str:
    """Live Google organic SERP for a keyword (top results + features)."""
    return _call("serp", keyword=keyword, location=location,
                 language=language, limit=limit)


@mcp.tool()
def seo_search_volume(keywords: str, location: str = "United States",
                      language: str = "English") -> str:
    """Search volume and CPC for a comma-separated keyword list."""
    return _call("volume", keywords=keywords, location=location,
                 language=language)


@mcp.tool()
def seo_keyword_ideas(keyword: str, limit: int = 50) -> str:
    """Keyword ideas from a seed keyword (DataForSEO Labs)."""
    return _call("ideas", keyword=keyword, limit=limit)


@mcp.tool()
def seo_ranked_keywords(target: str, limit: int = 50) -> str:
    """Keywords a domain ranks for, with positions and volumes."""
    return _call("ranked", target=target, limit=limit)


@mcp.tool()
def seo_domain_competitors(target: str, limit: int = 10) -> str:
    """Organic competitors of a domain."""
    return _call("competitors", target=target, limit=limit)


@mcp.tool()
def seo_keyword_gap(target1: str, target2: str, limit: int = 50) -> str:
    """Keywords target2 ranks for that target1 does not (gap mode)."""
    return _call("intersection", target1=target1, target2=target2,
                 mode="gap", limit=limit)


@mcp.tool()
def seo_backlink_summary(target: str) -> str:
    """Backlink profile summary for a domain or URL."""
    return _call("backlinks", target=target)


@mcp.tool()
def seo_referring_domains(target: str, limit: int = 50) -> str:
    """Top referring domains linking to a target."""
    return _call("refdomains", target=target, limit=limit)


@mcp.tool()
def seo_llm_mentions(keyword: str, limit: int = 50) -> str:
    """LLM/AI citation mentions for a brand or keyword."""
    return _call("mentions", keyword=keyword, limit=limit)


@mcp.tool()
def seo_onpage(url: str) -> str:
    """Instant on-page SEO analysis of a URL."""
    return _call("onpage", url=url)


if __name__ == "__main__":
    mcp.run()
