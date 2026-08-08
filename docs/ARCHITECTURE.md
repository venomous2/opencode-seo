# Architecture

The suite has three layers, following how OpenCode discovers skills, agents,
and commands.

## Layer 1 — Skills (`.opencode/skills/<name>/SKILL.md`)

88 skills in three tiers:

**Orchestrator** — `seo-suite` is the entry point. It detects user intent,
verifies the data layer (`seo_config.py status`), loads project memory, and
routes to a workflow or atomic skill.

**Workflows (7)** — chain atomic skills and dispatch specialist agents for
end-to-end jobs:

| Workflow | Chains |
|---|---|
| `workflow-site-audit` | technical + content + competitive + AI-search analysts in parallel |
| `workflow-new-content` | keyword-research → serp-analysis → competitor outlines → content-brief → AEO layer → checklist |
| `workflow-ecommerce-launch` | keyword mapping → marketplace intel → category/product specs → schema → supporting content |
| `workflow-content-refresh` | inventory → decay detection → overlap scan → triage → refresh specs → queue |
| `workflow-migration` | pre-launch baselines + redirect map → launch-day checks → post-launch drift monitoring |
| `workflow-quarterly-review` | drift diffs + GSC/GA4 trends + decay triage → wins/losses narrative → next-quarter plan |
| `workflow-sxo` | deterministic page type + live SERP consensus → experience baseline → implementation blueprint → measured backlog |

**Atomic skills (80)** — each does one focused job. Grouped into 8
collections (Foundation, Content Strategy, Content Optimization, Technical,
AI Search, Competitive, Local & Commerce, Automation).

### Skill conventions

Every SKILL.md follows the same contract:
- Frontmatter: `name` (matches folder) + `description` (trigger keywords).
- Never fabricate metrics — live numbers come from `dfs_client.py`.
- Findings with evidence → prioritized recommendations with a one-line "why"
  → single best next step.
- Long reports are written to files; chat output stays concise.

## Layer 2 — Agents (`.opencode/agents/*.md`)

Four subagent-mode specialists dispatched in parallel by workflows:

- `seo-technical-analyst` — indexability, rendering, CWV
- `seo-content-analyst` — metadata, headings, quality, E-E-A-T
- `seo-competitive-analyst` — SERP landscape, keyword/backlink gaps
- `seo-ai-search-analyst` — citability, answer blocks, AI crawler access

Each returns a fixed compact format (findings table, top fixes, pillar
score) so the orchestrator can synthesize a 0-100 site score.

## Layer 3 — Data layer (`scripts/*.py`)

| Script | Role |
|---|---|
| `dfs_client.py` | DataForSEO CLI: 17 instant commands + task-based full-site crawl (`crawl`, `crawl-start`, `crawl-status`, `crawl-pages`) |
| `google_client.py` | Optional tiers: pagespeed, crux, crux-history, gsc-queries, gsc-inspect, gsc-sitemaps, ga4-organic |
| `seo_config.py` | Credential resolution (env → .env → user config) + `status` report |
| `cache.py` | Disk response cache with per-endpoint TTLs |
| `cost_ledger.py` | JSONL ledger of every billed DataForSEO call |
| `drift_store.py` | Timestamped per-domain SEO snapshots + compare |
| `recommend_store.py` | Per-domain recommendation store (append-only event log): every finding gets a status lifecycle (open/accepted/done/ignored/resolved) so re-audits track progress instead of repeating advice |
| `event_log.py` | Per-domain event timeline (JSONL): findings raised/resolved, lint saves, drift snapshots, manual notes — the chronological feed behind the dashboard and briefing |
| `project_dashboard.py` | Mission-control HTML dashboard: aggregates recommendation queue + drift health + event timeline + cost ledger into one branded page via report_build |
| `watch.py` | Scheduled monitoring bundle (daily/weekly profiles): lint → store, rankings diff → loss/recovery recommendations, competitor growth flags, backlinks + AI visibility into drift; `schedule` prints Task Scheduler/cron lines |
| `sxo_analyser.py` | Deterministic SXO baseline: page-type candidates, live SERP consensus, SERP-fit verdict and existing CRO/accessibility experience scores; persists high-confidence mismatch recommendations |
| `seo_forecast.py` | Honest click forecasting: volume × position-CTR with a printed uncertainty band and every assumption in the output; can snapshot the scenario into drift |
| `impact_report.py` | Change-impact analysis: joins completed recommendations to bracketing drift snapshots (keyword/URL movement) with association-not-causation verdicts |
| `site_crawler.py` | Built-in concurrent crawler (v2): sitemap cross-check, near-duplicate detection, soft-404 probe, anchors, OG/Twitter, mixed content, security headers and no-follow redirect/canonical-variant traces |
| `link_graph.py` | Internal link graph analysis (orphans, hubs, depth, anchor quality) from crawl data |
| `link_graph_render.py` | Visual radial link graph (branded SVG → HTML/PDF) |
| `spa_detect.py` | SPA heuristics (verdict + evidence) — decides when rendering is needed |
| `render_page.py` | Zero-dependency JS rendering via local headless browser (--dump-dom), DataForSEO fallback, raw-vs-rendered diff |
| `ai_visibility.py` | AI visibility monitor: LLM mention checks across ChatGPT/Claude/Gemini/Perplexity with cited-source capture and history |
| `log_analyzer.py` | Access-log bot/crawl behaviour analysis |
| `report_build.py` | Markdown → branded standalone HTML reports |
| `schema_gen.py` | JSON-LD generator for 18 schema.org types |
| `project_memory.py` | `seo-project.yml` + per-client profiles (clients/*.yml) |
| `mcp_server.py` | Optional MCP server (10 DataForSEO tools) |
| `setup_wizard.py` | Interactive first-time setup |
| `rule_engine.py` | Deterministic rule engine: evaluates YAML rules against page data — zero model calls, model-agnostic |
| `seo_lint.py` | "ESLint for SEO" CLI: lint URL/file/dir, 0-100 scores, `--min-score` CI gate |

Skills call these via bash and parse the JSON output. The scripts are
installed to `~/.config/opencode/seo-suite/scripts/`; skills reference them
as `python scripts/<name>.py` from the project root.

### The rule engine (`rules/`)

SEO checks live as structured YAML rules (`rules/<category>/<id>.yaml`),
each with severity, detection condition, client-facing rationale, fix
guidance, and embedded test fixtures. This is the single source of truth:
`seo_lint.py`, CI gates, and (increasingly) audit skills all consume the
same rules instead of duplicating logic in prompts. Detection is fully
deterministic — which is what makes the suite model-agnostic across
OpenCode's 400+ models. See docs/RULE-ENGINE.md.

Design split: **the engine handles everything checkable without taste;
skills keep everything that needs taste** (briefs, PR, strategy).

### Cross-cutting services

- **Cache**: every instant DataForSEO call checks the disk cache first
  (TTLs per endpoint; `--no-cache` bypasses). Saves real money on repeated
  research sessions.
- **Cost ledger**: every billed call appends one JSON line; report with
  `python scripts/cost_ledger.py report --by command`.
- **Drift store**: audits and monthly checks save snapshots; `compare`
  turns two snapshots into a change report.
- **Recommendation store**: `seo_lint --save` and audit skills append every
  finding as a recommendation with a status lifecycle. Re-linting
  auto-resolves fixed rules, reopens regressions, and leaves `ignored`
  items alone — the shared queue that task generation and dashboards read.
- **Event log**: data-layer modules append timeline events (finding raised,
  status changed, lint saved, snapshot saved) as they work. `seo-briefing`
  and `project_dashboard.py` render it; change-impact analysis joins it to
  drift diffs later.

## Project memory (`seo-project.yml`)

Persistent per-project context (site, audience, brand voice, competitors,
goals, preferred schema) that workflows load at the start. Created with
`python scripts/project_memory.py --init`.

## Where things live after install

| What | Repo | Installed |
|---|---|---|
| Skills | `.opencode/skills/` | `~/.config/opencode/skills/` |
| Agents | `.opencode/agents/` | `~/.config/opencode/agents/` |
| Commands | `.opencode/commands/` | `~/.config/opencode/commands/` |
| Scripts | `scripts/` | `~/.config/opencode/seo-suite/scripts/` |
| Credentials | `.env` (gitignored) | `~/.config/opencode/seo-suite/credentials.json` |

## Design rules

1. **DataForSEO mandatory, Google optional.** No live-data skill works by
   guessing; Google tiers only enrich.
2. **Skills are markdown, not code.** All logic lives in the data layer;
   skills encode judgment and procedure.
3. **Evidence-based AI-search posture.** The suite teaches structure and
   citability on top of SEO fundamentals — no "rank in ChatGPT" promises.
4. **Local-first.** Credentials never leave the machine except to the
   official DataForSEO / Google endpoints.
