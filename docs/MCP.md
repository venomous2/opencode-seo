# MCP Server (optional)

The suite can expose its DataForSEO layer as a native MCP server, so any
MCP-capable tool (OpenCode itself, other agents, other apps) calls
DataForSEO through the suite — with its credential resolution, response
cache, and cost ledger included.

## Setup

1. Install the MCP package (into your user Python):
   ```bash
   pip install mcp
   ```
2. Register the server in `opencode.json`:
   ```json
   {
     "mcp": {
       "seo-suite": {
         "type": "local",
         "command": ["python", "scripts/mcp_server.py"],
         "enabled": true
       }
     }
   }
   ```
   (Use the installed copy at
   `~/.config/opencode/seo-suite/scripts/mcp_server.py` if you prefer.)
3. Restart OpenCode.

## Tools exposed

| Tool | What it returns |
|---|---|
| `seo_serp` | Live Google SERP for a keyword |
| `seo_search_volume` | Volume + CPC for a keyword list |
| `seo_keyword_ideas` | Keyword ideas from a seed |
| `seo_ranked_keywords` | Keywords a domain ranks for |
| `seo_domain_competitors` | Organic competitors |
| `seo_keyword_gap` | Keywords a competitor ranks for that you don't |
| `seo_backlink_summary` | Backlink profile summary |
| `seo_referring_domains` | Top referring domains |
| `seo_llm_mentions` | LLM/AI citation mentions |
| `seo_onpage` | Instant on-page analysis of a URL |

All calls go through the suite's cache and cost ledger automatically.

## When to use this vs the CLI

The bash CLI (`dfs_client.py`) is what the skills use — simplest and always
available. The MCP server is for when *other* tools or agents need
DataForSEO access without shelling out.
