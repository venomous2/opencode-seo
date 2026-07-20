# OpenCode SEO Suite

[![CI](https://github.com/venomous2/opencode-seo/actions/workflows/ci.yml/badge.svg)](https://github.com/venomous2/opencode-seo/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-71%20passing-brightgreen)](tests)
[![Rules](https://img.shields.io/badge/rules-26%20self--testing-00E0BA)](rules)

**An AI-native SEO platform for OpenCode.** Ask "why has my traffic dropped?", "what should we publish next?", "how do we improve AI visibility?" — and get evidence-backed answers, fixes, and client-ready reports, powered by live [DataForSEO](https://dataforseo.com) data and a deterministic rule engine that works identically across all [OpenRouter.ai](https://openrouter.ai/) models.

Under the bonnet: 82 skills, 4 specialist agents, 8 slash commands, 26 self-testing rules, a fix engine, and a citation scorer — covering technical SEO, content strategy, AI search (GEO/AEO), competitive research, local SEO, and e-commerce. Google APIs (Search Console, GA4, PageSpeed, CrUX) are optional enrichment tiers.

Inspired by [`AgriciDaniel/claude-seo`](https://github.com/AgriciDaniel/claude-seo) — an original re-implementation for OpenCode, modified and extended by Lee Beirne (DataForSEO-mandatory data layer, three-layer architecture, project memory). All skill content is original; credit for the underlying concept goes to Agrici Daniel.

## Contents

- [Why this suite](#why-this-suite)
- [Who it's for](#who-its-for)
- [How it compares](#how-it-compares)
- [Install](#install)
- [Quick start](#quick-start)
- [Sample output](#sample-output)
- [The skill map](#the-skill-map-82-skills)
- [Project memory](#project-memory)
- [The data layer](#the-data-layer)
- [Architecture](#architecture)
- [FAQ](#faq)
- [Requirements](#requirements)
- [License](#license)

## Why this suite

- **Live data, not guesses.** Every volume, ranking, and backlink number comes from the DataForSEO API. Skills refuse to fabricate metrics.
- **A deterministic core.** 26 SEO checks as YAML rules with embedded tests, plus an 11-criterion citation-readiness scorer — all evaluated in pure Python with zero model calls, so results are identical across all 400+ OpenCode models. Lint any page, gate your CI with `--min-score`, and apply mechanical fixes with the fix engine.
- **Three layers.** Atomic skills for focused tasks → workflow skills that chain them for end-to-end jobs → project memory (`seo-project.yml` or per-client profiles) that keeps outputs consistent.
- **AI-search first.** Ten skills for AI Overviews, AI Mode, ChatGPT, Perplexity, Gemini, and LLM citation readiness — evidence-based, no hype.
- **Optional Google tier.** Add a Google API key / service account for real CrUX field data, Search Console queries, and GA4 organic traffic when you have them.
- **British English by default.** All analysis, recommendations, and reports are written in British English unless you ask for another variant.
- **Monitoring built in.** Drift snapshots, a DataForSEO cost ledger, and response caching turn one-off audits into a repeatable system.
- **Client-ready output.** White-label HTML reports with charts, an executive one-pager, and before/after comparisons — one command away from any markdown report.

## Who it's for

- **Freelance SEO consultants.** Run a full audit on the discovery call, deliver a branded report with charts and a one-pager the same afternoon. The cost ledger keeps your DataForSEO spend visible per client.
- **Agencies.** Repeatable audit cadence across a client portfolio — same checks, same scoring, same report format every time, with drift snapshots proving progress between engagements.
- **In-house marketers.** Lint pages before they ship, gate releases with `--min-score` in CI, and monitor rankings drift monthly instead of discovering drops in the quarterly review.

## How it compares

| | Manual audit | Commercial SEO tools | OpenCode SEO Suite |
|---|---|---|---|
| **Time per audit** | 4-8 hours | 30-60 min crawl + review | 10-15 min |
| **Cost** | Senior hours | £99-£999/month subscription | Free (MIT) + pennies of DataForSEO spend |
| **Client report** | You write it yourself | Dashboard or generic PDF | Branded HTML + executive one-pager, one command |
| **CI quality gate** | No | No | Yes — `--min-score` exit codes |
| **Auto-fixes** | No | No | Mechanical patches with `.bak` backups |
| **AI-search readiness** | Depends on the analyst | Typically 6-12 months behind | 10 dedicated skills + citation scoring |
| **Where your data lives** | Your spreadsheet | The vendor's cloud | Your machine |

Commercial crawlers are excellent at being crawlers; the suite doesn't try to replace them. It adds what they don't do: judgment, workflows, fixes, monitoring, and the report you actually send the client.

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

## Sample output

Real, unedited `seo_lint.py --url <site> --format text` output (rule engine, deterministic):

```
https://example.com  —  score 70/100  (6 findings, 26 rules)
  ! high     multiple-h1 [actual: 3]
           why: Multiple H1s dilute the page's main topic, leaving search
           engines and assistive technology to guess which heading
           actually describes the page.
           fix: Keep the single H1 that best describes the page's topic
           and demote the rest to <h2>.
  - low      thin-answer-block [actual: 34]
           why: A substantive, self-contained paragraph directly after the
           first H2 gives search engines a quotable answer block.
           fix: Immediately below the first <h2>, write a 40-60 word
           paragraph that answers that heading's question completely.
  ...
```

And the fix engine turns each mechanical finding into a concrete patch:

```
READY  missing-canonical (medium)
  <link rel="canonical" href="https://acme.example/gear/best-coffee-grinders">
READY  missing-breadcrumb-schema (low)
  <script type="application/ld+json"> ... BreadcrumbList built from the URL path ... </script>
SKIP   missing-article-schema (low)
  reason: missing required values: title (pass --base-url for local files)
```

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
| `seo_fix.py` | Fix engine: lint findings → concrete patches with `.bak` backups |
| `citation_score.py` | Citation readiness: 11 weighted criteria → 0-100 score + recommendations |
| `indexnow.py` | Instant indexing pings to Bing/Yandex on publish |
| `report_pdf.py` | HTML reports → PDF via the headless browser already installed |

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

## FAQ

**How is this different from Screaming Frog or Ahrefs?**
Different jobs. Crawlers and link indexes give you raw data; the suite adds judgment on top: workflows, prioritised findings with the "why" attached, mechanical fixes, monitoring, and the client-ready report. Your data comes from DataForSEO's API — comparable to what the commercial tools charge subscriptions for — at pay-as-you-go prices, with a cache and cost ledger keeping spend visible.

**Do I need the Google APIs?**
No. DataForSEO alone powers everything. Google credentials are optional enrichment tiers: PageSpeed/CrUX field data, then Search Console, then GA4. See [docs/GOOGLE-APIS.md](docs/GOOGLE-APIS.md).

**What does DataForSEO actually cost me?**
Pennies per typical query (a keyword research session is usually well under $0.25). Every call is logged to the cost ledger (`python scripts/cost_ledger.py report`), and identical pulls within the cache TTL are free. Sandbox mode (`--sandbox`) costs nothing for testing.

**Does it work on JavaScript-heavy sites (React/Next/Vue)?**
The instant lint and on-page checks read the served HTML — if critical content only appears after JS rendering, run the DataForSEO crawl with `--javascript` so pages are rendered first. For most sites the default works fine.

**Is my data private?**
Everything is local-first: credentials in `~/.config/opencode/seo-suite/` (user-only permissions) or your project's `.env`, reports in your `SEO_REPORTS_DIR`, nothing sent anywhere except the official DataForSEO and Google API endpoints.

**Which AI models does it work with?**
All of them. The rule engine and linting are deterministic Python — zero model calls — so results are identical across OpenRouter.ai models. Skills are plain markdown procedures; any model that can follow instructions can run them.

## Requirements

- OpenCode (latest)
- Python 3.10+
- DataForSEO account ([register](https://app.dataforseo.com/register)) — pay-as-you-go, a few cents per typical query
- Optional: Google API key / service account for the enrichment tier

## License

MIT — see [LICENSE](LICENSE).
