# Changelog

All notable changes to the OpenCode SEO Suite are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.19.3] - 2026-08-02

Branded report template overhaul.

### Changed
- **`report_build.py` template** — dark header with LB monogram, brand
  name/role, auto-detected report type, domain and date; score circle with
  conic gradient auto-extracted from the markdown (`71/100` → 255.6°,
  colour by band); findings-count tags auto-counted from severity tables;
  colour-coded stats row auto-extracted from content; bordered section
  titles; next-step dark gradient card; recommendations grid; roadmap
  3-column layout; checkmark working lists; dark footer with emerald link;
  one-pager mode scales every element to fit a single page
- `link_graph_render.py` passes the new template variables
  (`score_section`, `stats_row`, `report_type`, `site_domain`)

### Fixed
- Summary auto-extraction could slurp a table header row into the
  score-summary paragraph when no prose followed the score — markdown
  syntax lines (tables, fences, lists, headings) are now skipped
- Verified: validate.py + 190 tests passing, smoke-tested header/score
  extraction/tag counting end to end

## [0.19.2] - 2026-08-02

Rebrand compatibility fixes.

### Changed (already on main via ee3061d)
- `report_build.py` brand palette: teal/purple/pink → **navy `#1E3A8A` /
  emerald `#10B981` / orange `#C2410C`** (+ amber `#F59E0B` for medium),
  fonts Segoe UI → **Inter + Space Grotesk** (Bunny Fonts). Charts, badges,
  stat cards and table headers all use the new palette

### Fixed
- `link_graph_render.py` referenced the removed `TEAL/PURPLE/PINK/YELLOW/
  INK/MUTED` constants and crashed on import — remapped node colours and
  the `SHELL.format` call to the new palette
- 5 test assertions still expecting the old colours — updated to the new
  constants (behaviour unchanged)
- `docs/images/*.png` regenerated with the new branding so the README
  screenshots match what report_build now produces
- Full suite green again: validate + 190 tests passing

## [0.19.1] - 2026-07-29

README revamp and real Nike.com screenshots.

### Changed
- **README rewrite** — outcome-first opening ("Turn OpenCode into an SEO
  consultant that never hallucinates numbers"), "Just ask" section with
  natural-language examples, elevated deterministic engine story ("AI
  provides the reasoning. Python provides the truth."), real generated
  screenshots (lint, audit report, dashboard), compact skill map, "At a
  glance" benchmarks table, leaner architecture diagram, attribution
  moved to the end
- **`docs/images/`** — three real screenshots generated against Nike.com
  using the suite's own headless browser: `lint-cli.png` (30/100,
  deterministic findings), `audit-report.png` (branded HTML with charts),
  `dashboard.png` (mission control with seeded recommendation queue)
- **`scripts/generate_screenshots.py`** — repeatable screenshot generator
  (Edge/Chrome headless `--screenshot`, zero extra deps); generates the
  HTML artefacts from real lint data + seeded stores and captures PNGs

## [0.19.0] - 2026-07-24

The PR gate — SEO review on every pull request, for free.

### Added
- **`seo_lint.py --format github`** — findings as GitHub Actions workflow
  commands (`::error`/`::warning` with proper escaping), so they render as
  inline annotations on the PR Files tab; each page gets a `::notice` with
  its score. critical/high → error, medium/low → warning
- **`seo_pr_check.py`** — the PR reviewer: diffs changed HTML files against
  the base branch, lints both versions, annotates current findings, writes
  a markdown summary (score delta, new findings, fixed findings) to
  `$GITHUB_STEP_SUMMARY` and a comment file, and exits non-zero on
  regressions. Gate: new critical/high findings fail by default;
  `--min-score` and `--max-drop` add floors. Fully offline — no DataForSEO,
  no secrets, no model calls
- **`examples/seo-pr.yml`** — copy-paste workflow: clones the suite at
  runtime, runs the gate, posts/updates one summary comment per PR
- **`docs/CI-AND-PR.md`** — the recipe: three levels (CI gate →
  annotations → full PR gate), tuning flags, honest limits (file-level
  annotations, markdown caveat, what it deliberately doesn't check)
- README "Fail bad SEO in CI" section; USER-GUIDE points at the recipe
- 8 new tests (190 total), including a real-repo integration test that
  commits a regression and watches the gate trip then pass

### Design note
Same rules locally, in CI, and in the PR — one source of truth, so the
gate can't drift from what `seo_lint` tells you at your desk. What a PR
can't know (rankings, volumes, backlinks) stays where it belongs:
scheduled watch runs feeding the recommendation store.

## [0.18.1] - 2026-07-24

User-facing documentation.

### Added
- **`docs/GETTING-STARTED.md`** — the new-user journey: prerequisites,
  install, credentials, a free 30-second first insight (`seo_lint --save`),
  first briefing, first audit, project memory, scheduling watch, and the
  daily/weekly rhythm. Written for people, not agents
- **`docs/USER-GUIDE.md`** — the full reference: the mental model
  (engine/skills/stores), all 11 commands with cost guidance, the five
  stores with one-liners, queue workflow, forecasting and impact, reports,
  agency mode, CI gates, tips and troubleshooting

### Fixed
- README staleness: rules badge and rule counts (26 → 54), skill-map TOC
  anchor, sample-output rule count, and the monitoring bullet now describes
  watch/briefing; INSTALL.md and README both point at the new guides

## [0.18.0] - 2026-07-24

SEO depth: priority scoring, honest forecasting, change impact.

### Added
- **Priority scoring in the recommendation store** — every recommendation
  now carries a computed `priority` (impact × confidence; ×1.25 when
  auto-fixable; +10% per re-raise capped at +50%). When evidence carries an
  `est_monthly_clicks` value, a log-scaled value impact (100/mo → 3,
  1000/mo → 4) can outrank the severity base. Deterministic, explainable,
  computed on read so it never goes stale; `list --sort priority|severity`
- **`seo_forecast.py`** — click forecasting with the assumptions printed in
  the output: volume × position-CTR (curve included), low/expected/high
  band (0.6×/1.4×), flat `--scale` discount for feature-heavy SERPs, and an
  explicit "scenario planning, not a promise" honesty block. Keywords come
  from `--keywords` (billed volume pull) or the latest drift snapshot
  (free); `--snapshot` saves the scenario into drift
- **`impact_report.py`** — joins completed recommendations to the drift
  snapshots bracketing each completion: position movement for keyword
  fixes, URL-level average movement for page fixes, verdicts
  improved/no_change/worse/insufficient_data, all labelled
  "association, not causation"
- **watch now captures search volumes** in ranking snapshots and attaches
  `est_monthly_searches`/`est_monthly_clicks` (volume × CTR at the lost
  position) to rank-loss recommendations — so the most valuable losses
  float to the top of the queue automatically
- Dashboard top-actions table shows the priority score and the
  clicks-at-stake when known; briefing skill uses the priority order and
  can cite forecast/impact reports
- 10 new tests (182 total)

### Design note
Forecasting was the feature most likely to break the suite's no-hype rule,
so the model wears its workings on the outside: the exact CTR curve, the
band, and what is *not* modelled (SERP features, brand intent, seasonality,
revenue) ship in every response. Numbers a client can interrogate beat
numbers a client must trust.

## [0.17.0] - 2026-07-24

Watch — scheduled monitoring that feeds the stores.

### Added
- **`watch.py`** — one command runs a monitoring bundle for a domain,
  writing everything into the local stores so the briefing and dashboard
  stay fresh. Profiles: `daily` (lint + rankings, cheap) and `weekly`
  (+ backlinks, competitors, AI visibility). Flags fall back to
  `seo-project.yml` (competitors, brand); `--dry-run` lists what would run
  and calls nothing
- **Rankings diff → recommendations**: fresh DataForSEO rankings are
  snapshotted to drift; keywords that were top-20 and vanished or dropped
  5+ positions become `skill:watch` recommendations (severity by magnitude,
  capped at 10/run), and recoveries automatically resolve earlier loss
  recommendations
- **Competitor growth flags**: each competitor's rankings are snapshotted
  (namespaced `competitor-<domain>`); a competitor gaining 3+ new rankings
  raises one deduped recommendation with example keywords — the chat's
  "competitor X published 17 new pages" alert, grounded in real data
- **Lint on a cadence**: key pages are re-linted straight into the
  recommendation store (`seo_lint` + `save_lint_results`), so regressions
  reopen and fixed findings resolve themselves between audits
- **`watch.py schedule`** — prints the exact Windows `schtasks` and cron
  lines for the domain/profile. The OS does the scheduling; nothing daemons
- Every run logs a `watch_completed` event (feeds the briefing) and reports
  its own DataForSEO cost; per-check errors degrade to "data unavailable"
  instead of aborting the run
- `seo-briefing` suggests watch when stores are stale; `seo-drift`
  defers routine cadence to watch
- 9 new tests (172 total)

### Design note
No notification infrastructure was built: new findings land in the
recommendation store and events on the timeline, so the "inbox" is simply
the briefing/dashboard reading what watch put there — one queue, one
timeline, zero extra moving parts.

## [0.16.0] - 2026-07-24

Project home: event timeline, mission-control dashboard, morning briefing.

### Added
- **`event_log.py`** — per-domain JSONL timeline
  (`~/.config/opencode/seo-suite/events/<domain>.jsonl`). The data layer
  logs as it works: `rec_raised`, `rec_reopened` (regressions),
  `rec_status`, `lint_saved`, `snapshot_saved`, plus manual `note`s via the
  CLI. Best-effort by design — logging never breaks the caller
- **`project_dashboard.py --domain <d>`** — the "mission control" page:
  aggregates the recommendation queue, drift health (weighted pillar blend,
  delta vs previous snapshot, trend line), event timeline, wins and 30-day
  API spend into one branded standalone HTML file via `report_build.py`.
  Actions first, charts second; writes `DASHBOARD-<domain>-<date>.md/.html`
  to `$SEO_REPORTS_DIR/<domain>/`
- **`seo-briefing` skill + `/briefing` command** (87 skills, 11 commands) —
  the morning executive feed, entirely from local stores (zero API spend):
  health + delta, needs attention, regressions, recent wins, today's top
  3–5 actions, single best next step. Routed from `seo-suite`
- Data-layer integrations: `recommend_store` logs raises/reopens/status
  changes and lint saves; `drift_store` logs every snapshot
- 10 new tests (163 total)

### Design note
The dashboard is an *output*, not an application: a generated HTML view
over the stores, keeping the suite local-first and dependency-free. If a
live app ever ships, it reads the same JSONL stores and nothing is thrown
away. The event log is also the join table for Phase 4's change-impact
analysis ("you fixed X → traffic +19%").

## [0.15.0] - 2026-07-24

Recommendation store — findings get a status lifecycle.

### Added
- **`recommend_store.py`** — per-domain, append-only event log of
  recommendations (`~/.config/opencode/seo-suite/recommendations/<domain>.jsonl`).
  Every finding — from the rule engine, an audit skill, or a workflow — is a
  record with stable id, severity, confidence, evidence, fix guidance,
  `auto_fixable` flag and a status: `open → accepted → done`, plus `ignored`
  (stays ignored, keeps counting) and `resolved` (auto). Re-raising a done
  issue reopens it as a regression; replaying the log gives full history
  (`Recommended in January → ignored → re-raised → accepted → done`).
  CLI: `add` (stdin/--file), `list`, `set`, `get`, `summary`, `history`,
  `domains`
- **`seo_lint.py --save [--domain]`** — persists a lint run: raises every
  finding, auto-resolves previously-raised rules that now pass (only among
  rules that actually ran, so partial/category runs never resolve what they
  didn't check), and marks rules carrying a `fix.patch` as `auto_fixable`
- `workflow-site-audit` reads outstanding recommendations in Phase 0 (so
  repeat audits report fixed/ongoing/regressed) and saves lint findings in
  Phase 3; `seo-task-generator` accepts the store's open recommendations as
  input and marks accepted tasks back in the store
- 12 new tests (153 total)

### Design note
This is the contract layer for everything actionable in the suite: one
machine-readable queue that task generation, monitoring and (later) the
project dashboard all read — instead of every skill emitting prose that
nothing can aggregate.

## [0.14.0] - 2026-07-23

JavaScript/SPA rendering — with zero new dependencies.

### Added
- **`spa_detect.py`** — stdlib SPA heuristics (empty root shells, framework
  markers, text/markup ratio, link poverty, script density) returning a
  verdict + evidence: `spa` / `maybe` / `static`. Audits only pay render
  cost when it matters
- **`render_page.py`** — renders JS pages via the headless browser already
  installed (Edge/Chrome `--dump-dom` + virtual-time budget), falling back
  to DataForSEO JS rendering when no local browser exists. `--diff`
  produces the raw-vs-rendered gap report: word/link/schema deltas and the
  `js_content_ratio` ("what does Google see that curl doesn't?")
- **`seo_lint.py --render auto|always|never`** — auto runs spa_detect and
  renders only when needed; the full rule engine then runs on the rendered
  DOM. Rendered pages keep the raw fetch's response headers for the
  security rules
- **`js-content-gap` rule** (54 total) — fires when the rendered page has
  ≥50% more content than the raw HTML
- `javascript-seo` skill now leads with the deterministic render tooling;
  `workflow-site-audit` checks SPA risk before any "missing content" claims
- 5 new tests (141 total)

### Design note
No Playwright, no 400MB download: the suite renders with the browser it
already drives for PDF export, keeping the zero-heavy-dependency install.

## [0.13.0] - 2026-07-23

Conversion rate optimisation.

### Added
- **CRO category in the rule engine** — 10 rules (53 total) measuring what
  prompt-only CRO checklists can't: no CTA, no above-fold CTA (body-relative
  fold proxy), generic primary CTA text, missing trust signals, high form
  friction, CAPTCHA presence, missing phone link, no urgency signal,
  competing CTAs, missing FAQ
- **`cro-audit` skill + `/cro` command** (86 skills, 10 commands) — the
  deterministic baseline plus what competitors lack: SERP intent-goal
  alignment (does the offer match what the searcher came for?), competitor
  benchmarking with the same measured checks, objection mining from PAA and
  competitor FAQs, ICE-scored hypothesis experiment plans with measurement
  notes, and data-grounded copy alternatives
- Parser now detects: CTA presence/position/text (anchors + buttons),
  form field counts and CAPTCHA, tel: links, trust and urgency keyword
  signals, FAQ presence, live-chat widgets
- 8 new tests (136 total)

## [0.12.0] - 2026-07-22

Web accessibility auditing.

### Added
- **Accessibility category in the rule engine** — 12 new WCAG-cited rules
  (43 total): unlabelled form inputs, missing skip link, missing main/nav
  landmarks, heading-order skips, duplicate ids, empty links, empty
  buttons, generic link text, tables without headers, iframes without
  titles, positive tabindex. Each rule carries its WCAG criterion and
  conformance level (A/AA/AAA), passed through to lint findings
- **`accessibility-audit` skill** (85 skills total) — WCAG mapping table,
  pass-rate scorecard per level, prioritised fixes, and an explicit
  honesty split between machine-checked criteria and what needs manual
  testing (contrast, keyboard, screen reader, motion) with a manual-test
  checklist
- Parser now extracts: form label associations (label for / wrapped /
  aria-label — placeholders correctly do NOT count), skip links, landmarks,
  heading sequence, duplicate ids, empty links/buttons, generic anchor
  text, table headers, iframe titles, tabindex usage
- 13 new tests (128 total)

## [0.11.1] - 2026-07-22

### Added
- **`--platform all`**: one check now queries ChatGPT, Claude, Gemini and
  Perplexity in a single run
- **Google AI Overviews leg**: every visibility check also runs the prompt
  through the SERP API — reports whether an AIO exists, whether the brand
  is cited in it, and which domains were cited
- Platform defaults verified against DataForSEO's `/models` endpoints;
  per-platform capability handling (Gemini rejects the country ISO field)

### Verified live
All four platforms + AIO leg working: Deel visible on ChatGPT, Claude and
Gemini for "best employer of record UK" (75% rate), with exact cited
sources returned per platform

## [0.11.0] - 2026-07-22

API expansion and the AI visibility monitor.

### Added
- **9 new DataForSEO endpoints**: Google Maps SERP (local pack), Google
  News SERP, Bing SERP, YouTube SERP, Google Autocomplete, bulk keyword
  difficulty, backlinks history, bulk domain ranks, and technology-stack
  detection
- **`ai_visibility.py`** — answers "does AI mention us when buyers ask?":
  queries ChatGPT / Claude / Gemini / Perplexity via DataForSEO's LLM
  Responses API (web search enabled), detects brand/domain mentions,
  extracts the **exact sources the AI cited**, and stores dated snapshots
  with compare-over-time (gained/lost visibility + rate deltas)
- **`ai-visibility-monitor` skill** (84 skills total) — full workflow:
  buyer-prompt building (autocomplete-assisted), visibility check, mentions
  baseline, interpretation, charted client report, monthly cadence
- 6 new tests (payload batch, mention detection, cited sources, store +
  compare; 112 total)

### Notes
- LLM Responses payloads follow the documented contract (user_prompt +
  model_name, web_search + country ISO); platform defaults overridable
  with --model. Verified live: Deel correctly detected as cited for
  "best employer of record UK" with its exact cited sources returned

## [0.10.1] - 2026-07-21

### Added
- **`link_graph_render.py`** — client-facing visual link graph: branded
  radial SVG (homepage at the centre, depth rings, node size = inlinks,
  colour-coded by role: home/hub/orphan/unreachable) with legend, stats
  cards, most-linked tables, and orphan list. Pure SVG, no JavaScript —
  prints cleanly to PDF (`--pdf` flag). `crawl-analyzer` now produces it
  whenever the user asks to see the link graph
- 4 new tests (layout, roles, SVG, escaping; 107 total)

## [0.10.0] - 2026-07-21

Crawler v2 and the internal link graph.

### Added
- **site_crawler v2**: concurrent fetching (configurable workers + per-host
  politeness), sitemap.xml cross-check (crawled-not-in-sitemap,
  sitemap-not-crawled, non-200 in sitemap), near-duplicate detection
  (shingle Jaccard ≥ 0.9), soft-404 probe (detects infinite URL spaces),
  anchor text on every link, Open Graph / Twitter Card fields, mixed-content
  detection, and security headers (HSTS, CSP, X-Frame-Options,
  X-Content-Type-Options)
- **`link_graph.py`** — internal link graph analysis from crawl data:
  orphan pages, most-linked pages, hub pages, click-depth distribution,
  unreachable pages, and anchor-text quality (generic-anchor share)
- **5 new rules** (31 total): `missing-og-title`, `missing-twitter-card`
  (new social category), `mixed-content`, `missing-hsts`, `missing-csp`
  (new security category; header rules auto-skip for local files)

### Changed
- `fetch()` now returns headers alongside the body (callers updated)

## [0.9.0] - 2026-07-20

Client-facing deliverables everywhere.

### Added
- **`report_publish.py`** — one command turns any suite markdown report
  into the full client set: branded HTML + print-ready PDF, plus executive
  one-pager HTML + PDF. Skips PDF gracefully when no headless browser is
  present
- The publish step is now wired into **all 37 file-producing skills and
  workflows** — every completed skill/workflow produces client-facing
  HTML + PDF as standard, not just `.md` files
- Full reports (not only one-pagers) now get PDF versions as standard in
  the report writer
- 6 new tests (103 total)

## [0.8.1] - 2026-07-20

### Added
- Location alias normalisation in `dfs_client.py`: "UK", "GB", "USA", etc.
  auto-correct to official DataForSEO location names (prevents 40501
  "Invalid Field: 'location_name'" task failures)
- Task-level error messages now surface in CLI output (`task_errors`) so
  parameter problems are no longer mistaken for credential failures

## [0.8.0] - 2026-07-19

Data enrichment and distribution.

### Added
- **Google Trends** in `dfs_client.py`: `trends --keywords a,b,c
  [--date-from --date-to]` — interest-over-time data for seasonality in
  content calendars and briefs (cached 7 days)
- **IndexNow submitter** (`scripts/indexnow.py`): per-domain key
  generation and management, submit single URLs, URL lists, or whole
  sitemaps to Bing/Yandex on publish
- **PDF export** (`scripts/report_pdf.py`): renders HTML reports to PDF
  using the headless browser already installed (Edge on Windows, Chrome/
  Chromium elsewhere) — zero new dependencies. `seo-report-writer` now
  exports the one-pager to PDF for emailing
- 6 new tests (97 total); repository is now public with topics and a
  proper description

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
