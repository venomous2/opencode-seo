# Changelog

All notable changes to the OpenCode SEO Suite are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.7.1] - 2026-07-19

### Added
- **Model-tolerant chart parsing**: `report_build.py` now accepts YAML and
  bare label/value lists in ```` ```chart ```` blocks (not just JSON), so
  reports render graphs regardless of which of the 400+ models wrote the
  markdown. Unparseable blocks degrade to a labelled fallback box instead
  of raw text
- **Multi-segment donuts** with legends (donut specs may carry a `data`
  list instead of a single value)
- 6 new tests (91 total)

## [0.7.0] - 2026-07-18

Recipes, entity registry, and consolidated comparison.

### Added
- **docs/RECIPES.md** — the recipe contract for new skills: declare engine
  inputs, judgment added, and what the skill never re-checks. New
  deterministic checks go in `rules/`, not in skill prose. Includes a
  decision tree and a worked example
- **Entity registry** in project memory: `entities:` sections in
  `seo-project.yml` / `clients/<name>.yml` (people, organisations,
  products with aliases, roles, descriptions, sameAs links).
  `python scripts/project_memory.py entities --client <name>` prints the
  registry; `--check` validates it
- **`schema_gen.py --from-memory <client>`** — generate Organization /
  Person JSON-LD straight from the entity registry (explicit `--field`
  args override memory values)
- **`compare` skill + `/compare` command** — consolidated site-vs-
  competitor comparison: authority, keyword footprint, keyword gap, SERP
  features, plus lint and citation scores for both homepages in one report
- 6 new tests (entity normalisation, entities CLI, from-memory schema
  generation; 86 total)

### Changed
- README reframe: leads with "An AI-native SEO platform for OpenCode"
  instead of the skill count (counts moved to the detail line)
- `clients/` is now gitignored — client profiles are user data, never
  committed

## [0.6.0] - 2026-07-18

Deterministic citation readiness scoring.

### Added
- **`citation_score.py`** — scores a page 0-100 across 11 weighted
  citation-readiness criteria: answer block (tiered), question-form
  headings, author signal, date signals, outbound sourcing, editorial
  schema, structure & scannability, content depth, factual density
  (low-confidence heuristic), image accessibility, indexation basics.
  Hard gates for noindex / non-200 pages. Every partial/failed criterion
  carries a concrete recommendation; grades from "Not ready" to "Strong
  citation candidate", with an explicit "cannot guarantee citation"
  disclaimer. Zero model calls — identical results under any LLM.
- Parser now also extracts: H2 texts, list counts, JSON-LD date flags,
  meta author / rel=author signals, `<time>` elements, and a numeric
  factual-density proxy
- 9 new tests (tiers, gates, partial credit, recommendation coverage;
  80 total)

### Changed
- `llm-citation-readiness` skill now adopts `citation_score.py` as its
  objective baseline and layers judgment (entity coverage, crawler access,
  competitive citability) on top instead of hand-scoring everything

## [0.5.0] - 2026-07-18

The fix engine: lint findings become concrete patches.

### Added
- **Fix engine** (`scripts/seo_fix.py`): rules with `fix.patch` specs get
  their templates resolved against real page data — canonical, meta
  description draft, title draft, viewport, html lang, WebPage/Article/
  Organization/BreadcrumbList JSON-LD (breadcrumbs auto-built from the URL
  path). `--dry-run` prints patches with ready/skipped status; `--apply`
  rewrites local HTML (with `.bak` backup) and re-lints to prove the new
  score. Drafts carry `TODO-*` markers — the engine never invents content.
  Fully idempotent.
- 9 rules now carry patch specs (metadata ×2, indexability, mobile,
  international, schema ×4, plus the JSON-LD base rule)
- 8 new tests (template resolution, breadcrumbs, meta drafts, apply +
  idempotency, HTML escaping; 71 total)
- Parser also captures the first-H2 paragraph text (drives meta
  description drafts)

### Changed
- `seo-lint` skill now runs `seo_fix.py` for mechanical fixes before
  escalating to human judgment fixes

## [0.4.0] - 2026-07-18

The deterministic core: rule engine + SEO linting.

### Added
- **Rule engine** (`scripts/rule_engine.py` + `rules/`): 26 SEO checks as
  structured YAML rules across 9 categories (metadata, headings,
  indexability, content, images, schema, mobile, international, links).
  Every rule carries severity, confidence, client-facing rationale, fix
  guidance, and embedded test fixtures. Fully deterministic — zero model
  calls, so it works identically across all of OpenCode's 400+ models
- **`seo_lint.py`** — "ESLint for SEO": lint a live URL, local HTML file,
  or directory of files; 0-100 scores with severity-ranked findings;
  `--min-score` CI quality gate (exit 1 below threshold); `--format text`
  human output; URL-dependent rules auto-skip for local files
- **`seo-lint` skill** — thin skill that runs the linter, triages findings,
  and dismisses page-type-inappropriate rules with reasons
- Rule self-testing: `python scripts/rule_engine.py test` runs every rule's
  embedded fixtures; `validate.py` now validates the rules directory
- 24 new tests (conditions matrix, scoring, lint parsing, gate exit codes,
  good-page benchmark; 63 total)
- docs/RULE-ENGINE.md — full schema, field and condition reference

### Changed
- `site_crawler.py` parser now also extracts: images total/missing alt,
  JSON-LD block count and @types, H2 count, viewport presence, html lang,
  internal/external link counts, and an answer-block heuristic
  (first-H2 paragraph word count)
- Installers now copy `rules/` into the suite home

## [0.3.1] - 2026-07-18

Before/after reporting and the executive one-pager.

### Added
- **`compare` chart type** — before/after bars with deltas (grey = previous,
  colour = current); ideal for drift-powered progress reporting
- **`drift_store.py chart`** — prints ready-made ```` ```chart ```` blocks
  comparing two snapshots (scores, backlinks/mentions, ranking movement)
- **`--onepager` mode** on `report_build.py` — renders an executive
  one-pager (summary + charts + top 5 actions) to `<name>-onepager.html`
- 5 new tests (compare charts, onepager extraction, drift chart specs;
  39 total)

### Changed
- `drift_store.py compare`/`chart` now default to comparing the two most
  recent snapshots (was: oldest vs newest)
- `seo-report-writer` and `workflow-site-audit` produce the one-pager
  alongside the full HTML report and include compare charts whenever a
  previous drift snapshot exists

## [0.3.0] - 2026-07-18

Report experience overhaul.

### Added
- **Charts in reports**: fenced ```` ```chart ```` blocks render as inline
  SVG graphs in HTML reports — `donut` (score gauges), `bar` (comparisons),
  `line` (trends), `stats` (KPI cards with deltas)
- **Auto table of contents** in HTML reports (from H2/H3 headings)
- **Severity badges**: Critical/High/Medium/Low table cells render as
  coloured pills
- **Recommendations & actions** is now a required report section: a
  priority/effort/impact/owner action table with quick wins flagged
- 8 new tests for charts, badges, and TOC (34 total)

### Changed
- Report footer is now `Report built by Lee Beirne - https://leebeirne.com`
  (replaces the previous suite attribution line in all report-producing
  skills and docs)
- HTML report theme rebuilt on the brand palette: teal #00E0BA, purple
  #91008D, pink #FF3483, yellow #FFCF00
- `workflow-site-audit` reports now include charts (stats cards, score
  donut, pillar bars, trend lines when drift history exists)

## [0.2.0] - 2026-07-18

Monitoring, crawl depth, client tooling, and new skill territory.

### Added
- **Full-site crawl**: `dfs_client.py crawl` (DataForSEO On-Page API,
  task-based) plus a free built-in mini crawler (`site_crawler.py`)
- **Drift monitoring**: `drift_store.py` snapshot store + `seo-drift` skill
- **Cost ledger**: `cost_ledger.py` — every billed DataForSEO call logged;
  `report` and `tail` views
- **Response caching**: `cache.py` with per-endpoint TTLs; `--no-cache` flag
- **White-label HTML reports**: `report_build.py` renders any suite markdown
  report to branded standalone HTML
- **Client profiles**: `project_memory.py --client <name>` (clients/*.yml)
- **Setup wizard**: `setup_wizard.py` (credentials check, tiers, first profile)
- **MCP server**: `mcp_server.py` exposes 10 DataForSEO tools natively
- **OpenCode plugin**: `.opencode/plugins/seo-suite-context.ts` reminds the
  session to load project memory
- **Log analysis**: `log_analyzer.py` + `log-file-analysis` skill
- **9 new skills**: `crawl-analyzer`, `seo-drift`, `log-file-analysis`,
  `workflow-migration`, `workflow-quarterly-review`, `programmatic-seo`,
  `news-seo`, `video-seo`, `parasite-seo-check`, `digital-pr-planner`
  (81 skills total)
- **Tests + CI**: 26 pytest tests in `tests/`, GitHub Actions workflow

### Changed
- `workflow-site-audit` now offers full-crawl coverage and saves a drift
  snapshot at the end of every audit
- `seo-report-writer` also renders the white-label HTML version of reports

## [0.1.1] - 2026-07-17

### Changed
- Attribution: suite is now credited "Built by Lee Beirne", with documented
  inspiration credit to AgriciDaniel/claude-seo (README, LICENSE).
- All output now defaults to British English (orchestrator, agents,
  report writer, project conventions).
- Reports written to files now end with an attribution footer.

## [0.1.0] - 2026-07-17

Initial release.

### Added
- 71 OpenCode skills: orchestrator (`seo-suite`), 4 workflow skills, and 66
  atomic skills across 8 collections (Foundation, Content Strategy, Content
  Optimization, Technical SEO, AI Search, Competitive, Local & Commerce,
  Automation)
- 4 specialist subagents for parallel audits (technical, content,
  competitive, AI search)
- 8 slash commands: `/site-audit`, `/keyword-research`, `/new-post`,
  `/serp-analysis`, `/keyword-gap`, `/citation-check`, `/content-refresh`,
  `/schema`
- Python data layer:
  - `dfs_client.py` — DataForSEO CLI (17 commands, mandatory backbone)
  - `google_client.py` — optional Google tiers (PSI, CrUX, GSC, GA4)
  - `seo_config.py` — credential resolution (env / .env / user config)
  - `schema_gen.py` — JSON-LD generator (18 schema.org types)
  - `project_memory.py` — `seo-project.yml` project memory
- Installers for Windows (`install.ps1`) and Unix/macOS (`install.sh`),
  uninstallers, and `validate.py` structure validator
- Docs: setup guides for DataForSEO and Google APIs, architecture, install,
  contributing; 3 usage examples
