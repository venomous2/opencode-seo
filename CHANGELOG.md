# Changelog

All notable changes to the OpenCode SEO Suite are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
