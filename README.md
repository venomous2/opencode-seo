# OpenCode SEO Suite

A native [OpenCode](https://opencode.ai) SEO skill pack: **82 skills, 4 specialist agents, 8 slash commands, and a deterministic rule engine** covering technical SEO, content strategy, AI search optimization (GEO/AEO), competitive research, local SEO, and e-commerce — with **DataForSEO as the mandatory live-data backbone** and optional Google API enrichment (Search Console, GA4, PageSpeed, CrUX).

**Built by Lee Beirne.** Inspired by [`AgriciDaniel/claude-seo`](https://github.com/AgriciDaniel/claude-seo) — an original re-implementation for OpenCode, modified and extended by Lee Beirne (DataForSEO-mandatory data layer, three-layer architecture, project memory). All skill content is original; credit for the underlying concept goes to Agrici Daniel.

## Why this suite

- **Live data, not guesses.** Every volume, ranking, and backlink number comes from the DataForSEO API. Skills refuse to fabricate metrics.
- **A deterministic core.** 26 SEO checks as YAML rules with embedded tests, evaluated in pure Python — zero model calls, so results are identical across all 400+ OpenCode models. Lint any page, gate your CI with `--min-score`.
- **Three layers.** Atomic skills for focused tasks → workflow skills that chain them for end-to-end jobs → project memory (`seo-project.yml` or per-client profiles) that keeps outputs consistent.
- **AI-search first.** Ten skills for AI Overviews, AI Mode, ChatGPT, Perplexity, Gemini, and LLM citation readiness — evidence-based, no hype.
- **Optional Google tier.** Add a Google API key / service account for real CrUX field data, Search Console queries, and GA4 organic traffic when you have them.
- **British English by default.** All analysis, recommendations, and reports are written in British English unless you ask for another variant.
- **Monitoring built in.** Drift snapshots, a DataForSEO cost ledger, and response caching turn one-off audits into a repeatable system.
- **Client-ready output.** White-label HTML reports with charts, an executive one-pager, and before/after comparisons — one command away from any markdown report.

## Install

**Windows (PowerShell):**
```powershell
git clone https://github.com/venomous2/opencode-seo.git
powershell -ExecutionPolicy Bypass -File opencode-seo-suite\install.ps1
```

**macOS / Linux:**
```bash
git clone https://github.com/venomous2/opencode-seo.git
bash opencode-seo-suite/install.sh
```

Then **restart OpenCode** and set up DataForSEO credentials (the installer offers to do this):
```bash
python scripts/seo_config.py status   # verify the data layer
```

Full guide: [INSTALL.md](INSTALL.md) · Credentials: [docs/DATAFORSEO-SETUP.md](docs/DATAFORSEO-SETUP.md) · Google tiers: [docs/GOOGLE-APIS.md](docs/GOOGLE-APIS.md)

## Quick start

```
/site-audit https://example.com        # full audit, 4 parallel specialist agents
/keyword-research best espresso beans  # live volumes, ideas, clusters
/new-post "pour over vs french press"  # research → publish-ready brief
/serp-analysis "crm for freelancers"   # who ranks and why
/keyword-gap example.com               # keywords competitors rank for, you don't
/citation-check https://example.com/guide  # AI citation readiness
/content-refresh example.com           # triage decaying content at scale
/schema article                        # generate JSON-LD
```

Or just talk naturally — "audit my site", "why don't I rank for X", "optimize this page for AI Overviews" — the `seo-suite` orchestrator routes you to the right skill.

## The skill map (81 skills)

| Collection | Skills |
|---|---|
| **Orchestration** | `seo-suite` (router), `workflow-site-audit`, `workflow-new-content`, `workflow-ecommerce-launch`, `workflow-content-refresh`, `workflow-migration`, `workflow-quarterly-review` |
| **Foundation** | `site-audit`, `technical-seo`, `on-page-seo`, `metadata-optimizer`, `heading-optimizer`, `internal-linking`, `external-linking`, `canonical-review`, `robots-advisor`, `sitemap-builder` |
| **Content Strategy** | `keyword-research`, `search-intent-analysis`, `topic-clustering`, `topical-authority-planner`, `content-calendar`, `pillar-page-designer`, `supporting-content-planner`, `content-brief`, `faq-generator`, `entity-extraction` |
| **Content Optimization** | `content-review`, `content-refresh`, `thin-content-detector`, `duplicate-content-review`, `readability-analysis`, `semantic-seo`, `nlp-optimization`, `eeat-review`, `fact-verification`, `content-gap-analysis` |
| **Technical SEO** | `schema-generator`, `schema-validator`, `core-web-vitals`, `javascript-seo`, `crawl-budget`, `redirect-analysis`, `url-structure-review`, `image-seo`, `mobile-seo`, `international-seo` |
| **Crawl & Logs** | `crawl-analyzer`, `log-file-analysis` |
| **AI Search** | `ai-overviews-optimization`, `ai-mode-optimization`, `chatgpt-citation-optimizer`, `perplexity-optimization`, `gemini-optimization`, `llm-citation-readiness`, `answer-engine-optimization`, `retrieval-optimization`, `knowledge-graph-enhancement`, `entity-seo` |
| **Competitive** | `competitor-audit`, `serp-analysis`, `keyword-gap`, `backlink-opportunity-planner`, `content-opportunity-finder`, `topical-coverage-comparison` |
| **Local & Commerce** | `local-seo`, `gbp-advisor`, `ecommerce-seo`, `product-page-optimizer`, `category-page-optimizer` |
| **Growth & PR** | `digital-pr-planner`, `programmatic-seo`, `news-seo`, `video-seo`, `parasite-seo-check` |
| **Monitoring** | `seo-drift` |
| **Automation** | `seo-report-writer`, `seo-project-planner`, `seo-task-generator`, `seo-checklist-generator`, `seo-roadmap-builder` |

## Project memory

Run once per project to give every workflow consistent context (audience,
brand voice, competitors, goals):

```bash
python scripts/project_memory.py --init              # seo-project.yml
python scripts/project_memory.py --client acme --init  # clients/acme.yml
```

Freelancers and agencies can keep one profile per client under `clients/`
and load it with `--client <name>`.

## The data layer

| Script | What it does |
|---|---|
| `dfs_client.py` | DataForSEO CLI — 17 instant commands + full site crawl (`crawl`) |
| `google_client.py` | Optional Google tiers: PSI, CrUX, GSC, GA4 |
| `seo_config.py` | Credential resolution + `status` report |
| `cache.py` | Response cache (per-endpoint TTLs) — avoids paying twice |
| `cost_ledger.py` | DataForSEO spend ledger — totals by period and command |
| `drift_store.py` | Timestamped SEO snapshots per domain + diff/compare |
| `site_crawler.py` | Free built-in mini crawler (< 200 pages, robots-aware) |
| `log_analyzer.py` | Server-log bot/crawl analysis |
| `report_build.py` | Markdown → branded standalone HTML reports |
| `schema_gen.py` | JSON-LD generator (18 schema.org types) |
| `project_memory.py` | `seo-project.yml` + client profiles |
| `mcp_server.py` | Optional MCP server exposing DataForSEO as native tools |
| `setup_wizard.py` | Interactive first-time setup |
| `rule_engine.py` | Deterministic rule engine (26 YAML rules) — zero model calls |
| `seo_lint.py` | "ESLint for SEO": lint URL/file/dir, `--min-score` CI gate |

Plus `rules/` — 26 SEO checks as structured YAML (metadata, headings,
indexability, content, images, schema, mobile, international, links), each
with embedded tests. See [docs/RULE-ENGINE.md](docs/RULE-ENGINE.md).

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  You (chat / slash commands)                        │
└──────────────┬──────────────────────────────────────┘
               ▼
│  seo-suite orchestrator  ── routes to ──┐
               ▼                          ▼
│  Workflow skills (4)            Atomic skills (66)
│  chain skills + dispatch        one focused job each
│  specialist agents (4)                │
               └────────────┬───────────┘
                            ▼
│  Data layer (scripts/)                         │
│  ├── dfs_client.py     DataForSEO (mandatory)  │
│  ├── google_client.py  Google APIs (optional)  │
│  ├── seo_config.py     credential resolution   │
│  ├── schema_gen.py     JSON-LD generator       │
│  └── project_memory.py seo-project.yml loader  │
└────────────────────────────────────────────────┘
```

Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Requirements

- OpenCode (latest)
- Python 3.10+
- DataForSEO account ([register](https://app.dataforseo.com/register)) — pay-as-you-go, a few cents per typical query
- Optional: Google API key / service account for the enrichment tier

## License

MIT — see [LICENSE](LICENSE).
