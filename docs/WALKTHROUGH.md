# Walkthrough: everything the OpenCode SEO Suite can do

The guided tour, from first install to the autonomous agent. Companion to
[GETTING-STARTED.md](GETTING-STARTED.md) (15-minute setup) and
[USER-GUIDE.md](USER-GUIDE.md) (command reference). This document shows how
the whole system fits together and which tool to reach for at each job.

## The mental model (60 seconds)

```
You ask (chat, slash command, or CLI)
        |
Skills + workflows      the judgement layer (markdown, model-written prose)
        |
Scripts (35)            the data layer (Python, deterministic)
        |
Rules (54 YAML)         the truth layer (self-testing, zero model calls)
        |
Stores                  memory: recommendations, events, drift, costs, project
```

**AI provides the reasoning. Python provides the truth.** Every skill is
required to consume engine output rather than re-check anything itself, so
the numbers in a report never depend on which of the 400+ models wrote it.

Five stores remember everything between sessions (all plain JSON/JSONL in
`~/.config/opencode/seo-suite/`): **recommendations** (the action queue),
**events** (timeline), **drift** (dated snapshots), **costs** (API spend)
and **project memory** (`seo-project.yml` / `clients/*.yml`).

---

# Part 1: install and prove it works

```powershell
# Windows
git clone https://github.com/venomous2/opencode-seo.git
powershell -ExecutionPolicy Bypass -File opencode-seo\install.ps1
```

```bash
# macOS / Linux
git clone https://github.com/venomous2/opencode-seo.git
bash opencode-seo/install.sh
```

The installer copies skills, agents and commands into OpenCode's config,
creates an isolated Python environment, and offers to store DataForSEO
credentials. **Restart OpenCode afterwards**: skills load at startup.

Verify (all offline, all free):

```powershell
python validate.py                 # 95 skills, 35 scripts, 54 rules
python -m pytest tests/ -q         # 215 tests
python scripts/seo_config.py status   # want: DataForSEO status .... READY
```

Then the 30-second proof that costs nothing:

```powershell
python scripts/seo_lint.py --url https://your-site.com --format text
```

54 self-testing rules run against the page. No API spend, no model call.

---

# Part 2: configure

| What | How | Required? |
|---|---|---|
| DataForSEO | `python scripts/setup_wizard.py` or [DATAFORSEO-SETUP.md](DATAFORSEO-SETUP.md) | Yes, for live volumes, rankings and backlinks |
| Google APIs | [GOOGLE-APIS.md](GOOGLE-APIS.md) | No, optional enrichment (GSC, GA4, PageSpeed, CrUX) |
| Report folder | `SEO_REPORTS_DIR` env var | Recommended |
| Project memory | `python scripts/project_memory.py --init` | Recommended |

```powershell
# Windows: reports then file themselves under <dir>\<domain>\
[Environment]::SetEnvironmentVariable("SEO_REPORTS_DIR", "C:\SEO-Reports", "User")
```

```bash
# macOS / Linux: add to your shell profile
export SEO_REPORTS_DIR="$HOME/seo-reports"
```

`seo-project.yml` (audience, brand voice, competitors, goals, entities) is
read by every workflow, so briefs match your voice and competitor checks
know who your rivals are. Agencies use one file per client:

```powershell
python scripts/project_memory.py --client acme --init
python scripts/project_memory.py --list-clients
python scripts/project_memory.py entities --client acme
```

---

# Part 3: three ways to drive it

**1. Just ask.** The `seo-suite` orchestrator routes to the right skill:

> Why has my traffic dropped?
> Audit nike.com and compare me to adidas.com
> What should I publish next in the coffee niche?
> How visible am I in ChatGPT and Perplexity?
> Fix the SEO issues on my pricing page
> Review this pull request for SEO regressions

**2. Slash commands** (`.opencode/commands/`): the high-frequency jobs.

| Command | Job |
|---|---|
| `/briefing` | 30-second morning feed: health, what changed, today's top actions |
| `/site-audit` | Full audit: technical, content, competitive and AI-search |
| `/compare` | You versus one competitor, side by side |
| `/serp-analysis` | What Google rewards for one keyword |
| `/keyword-research` | Volumes, ideas and clusters from seed keywords |
| `/keyword-gap` | Keywords rivals rank for and you do not |
| `/new-post` | Plan a post end to end (keyword to publish checklist) |
| `/content-refresh` | Revive a decaying page with live evidence |
| `/citation-check` | LLM citation readiness of a page |
| `/schema` | Generate JSON-LD for a page |
| `/cro` | Conversion audit and experiment plan |
| `/sxo` | Does the landing experience match the search intent? |
| `/humanize` | Detect and rewrite AI-sounding copy |

**3. Direct script CLIs**: precise, scriptable and CI-friendly (Part 5).

**Subagents** (`.opencode/agents/`) run the deep analysis in parallel:
`seo-technical-analyst`, `seo-content-analyst`, `seo-competitive-analyst`
and `seo-ai-search-analyst`. Workflows dispatch them for you; you rarely
call them directly.

---

# Part 4: the tour by job

## 4.1 Audit a site end to end

```text
/site-audit your-site.com
```

Or the workflow equivalent for a campaign: `workflow-site-audit` chains
technical, on-page, content, competitive and AI-search work with live
DataForSEO data.

What you get: a 0-100 scorecard, a prioritised top 10 with evidence,
`SEO-AUDIT-<domain>-<date>.md` plus branded HTML, PDF and an executive
one-pager, a drift snapshot, and every finding in the recommendation store.

Building blocks if you want them individually:

```powershell
python scripts/site_crawler.py --url https://your-site.com --max-pages 200 --pretty
python scripts/seo_lint.py --url https://your-site.com --save --domain your-site.com
python scripts/citation_score.py --url https://your-site.com --format text
python scripts/drift_store.py save --domain your-site.com --file snapshot.json
```

## 4.2 Lint, fix and validate a single page

```powershell
# detect
python scripts/seo_lint.py --file page.html --format text

# fix mechanically (dry-run first; --apply writes .bak and re-lints)
python scripts/seo_fix.py --file page.html --base-url https://site.com/page
python scripts/seo_fix.py --file page.html --base-url https://site.com/page --apply

# structured data
python scripts/schema_gen.py article --field headline="My Post" --field author.name="Jane Doe"
```

`seo_fix.py` only applies patches the rules declare (`fix.patch` in
`rules/<category>/<id>.yaml`). Canonical, viewport, html lang and JSON-LD
scaffolds are mechanical; title and meta copy arrives as drafts with TODO
markers for you to finish.

Specialist page skills add the judgement on top: `on-page-seo`,
`metadata-optimizer`, `heading-optimizer`, `image-seo`, `internal-linking`,
`schema-validator`, `product-page-optimizer`, `category-page-optimizer`,
`thin-content-detector`, `duplicate-content-review`, `canonical-review`,
`redirect-analysis`, `url-structure-review`, `robots-advisor`,
`sitemap-builder`, `javascript-seo`, `core-web-vitals`, `mobile-seo` and
`accessibility-audit`.

## 4.3 Research: keywords, SERPs, gaps and clusters

```powershell
python scripts/dfs_client.py volume --keywords "espresso grinder,best grinder"
python scripts/dfs_client.py ideas --keyword "espresso grinder"
python scripts/dfs_client.py serp --keyword "best espresso grinder"
```

Skills: `keyword-research`, `serp-analysis`, `search-intent-analysis`,
`keyword-gap`, `topical-coverage-comparison`, `topic-clustering`,
`topical-authority-planner`, `content-gap-analysis`,
`content-opportunity-finder`, `competitor-audit`,
`backlink-opportunity-planner` and `digital-pr-planner`.

## 4.4 Plan and produce content

- **Strategy**: `content-marketing`, `pillar-page-designer`,
  `supporting-content-planner`, `content-calendar`, `programmatic-seo`
- **Briefing**: `content-brief` (live volumes, competitor outlines, entities,
  questions), `seo-checklist-generator`, `seo-roadmap-builder`,
  `seo-task-generator`
- **Writing**: `workflow-new-content`, `faq-generator`, `entity-extraction`,
  `semantic-seo`, `nlp-optimization`, `readability-analysis`,
  `fact-verification`, `the-humanizer`
- **Refresh**: `content-refresh`, `workflow-content-refresh`,
  `content-review`

Every brief cites live DataForSEO numbers; `seo-project.yml` keeps the
voice yours.

## 4.5 AI search: AEO, GEO and LLM visibility

```powershell
python scripts/citation_score.py --url https://your-site.com/guide --format text
python scripts/ai_visibility.py check --domain your-site.com --brand "YourBrand" --prompts "best tool uk,tool vs rival"
python scripts/ai_visibility.py history --domain your-site.com
```

Skills: `answer-engine-optimization`, `ai-overviews-optimization`,
`ai-mode-optimization`, `llm-citation-readiness`,
`chatgpt-citation-optimizer`, `perplexity-optimization`,
`gemini-optimization`, `retrieval-optimization`, `entity-seo`,
`knowledge-graph-enhancement`, `eeat-review`, `parasite-seo-check`,
`ai-visibility-monitor`, `news-seo`, `video-seo`, `local-seo`,
`gbp-advisor` and `international-seo`.

Honesty rule the suite enforces: never promise "rank in ChatGPT". Report
mention share, citation readiness and crawler access as evidence.

## 4.6 Monitor, drift and prove impact

```powershell
# one monitoring run (lint, rankings, backlinks, competitors, AI visibility)
python scripts/watch.py --domain your-site.com --profile weekly --pages https://your-site.com/,https://your-site.com/pricing

# print the OS scheduler line (schtasks / cron) to automate it
python scripts/watch.py schedule --domain your-site.com --profile weekly

# what changed between two snapshots
python scripts/drift_store.py compare --domain your-site.com

# did the fixes move anything?
python scripts/impact_report.py --domain your-site.com --days 90
python scripts/seo_forecast.py --domain your-site.com --keywords "espresso grinder" --target-position 3
```

Skills: `seo-drift`, `seo-briefing`, `log-file-analysis` and
`crawl-budget`.

Fixed findings auto-resolve on the next lint run; ranking losses become
recommendations with click estimates; regressions reopen with a
`times_raised` counter.

## 4.7 Reports, dashboards and client delivery

```powershell
python scripts/report_publish.py SEO-AUDIT-your-site.com-2026-10-02.md
python scripts/project_dashboard.py --domain your-site.com
```

`report_publish` produces branded HTML, PDF and an executive one-pager from
any report markdown. `project_dashboard` is mission control: health, action
queue, wins and activity. Charts come from `report_build.py`; the SVG link
graph comes from `link_graph_render.py --file crawl.json --pdf`.

Skills: `seo-report-writer`, `workflow-quarterly-review`.

Generated reports end with the footer `Report built by Lee Beirne -
https://leebeirne.com` and are written to `$SEO_REPORTS_DIR/<domain>/`.

## 4.8 CI gates and pull requests

Fail a build when SEO regresses (offline and deterministic):

```yaml
- run: python scripts/seo_lint.py --dir ./dist --min-score 80
```

Gate a PR against the base branch (inline annotations and a markdown
summary):

```powershell
python scripts/seo_pr_check.py --base origin/main --all-changed
```

Copy [examples/seo-pr.yml](../examples/seo-pr.yml) for a merge-blocking
check; [docs/CI-AND-PR.md](CI-AND-PR.md) covers the details.

## 4.9 The autonomous SEO agent

The full loop (scan, fix, ship) with no prompt required:

```powershell
python scripts/seo_agent.py scan --dir ./public --domain your-site.com --base-url https://your-site.com --format text
python scripts/seo_agent.py fix  --dir ./public --domain your-site.com --base-url https://your-site.com
python scripts/seo_agent.py run  --dir ./public --domain your-site.com --base-url https://your-site.com --apply --pr
```

- `scan` lints every HTML page and labels findings **NEW / PERSISTING /
  REGRESSED** against the recommendation store
- `fix` applies only engine-declared mechanical patches (`.bak` first, then
  re-lints for the score delta); `--mechanical-only` skips draft copy
- `ship` branches, commits only the files it patched, and opens a
  review-ready PR with the brief as the body
- everything is **dry-run until you pass `--apply` / `--pr`**

To automate: copy `.github/workflows/seo-agent.yml` into the site repo and
set repository variables `SEO_AGENT_DOMAIN`, `SEO_AGENT_BASE_URL` and
(optionally) `SEO_AGENT_DIR`. The weekly cron opens one PR; human review is
the merge guardrail. Skill entry point: `autonomous-seo-agent`.

## 4.10 Specialist programmes

Multi-step workflows in `.opencode/skills/`: `workflow-site-audit`,
`workflow-new-content`, `workflow-content-refresh`, `workflow-migration`
(baselines, redirect maps, post-launch drift), `workflow-ecommerce-launch`,
`workflow-quarterly-review`, `workflow-sxo`, `ecommerce-seo`, `local-seo`,
`news-seo`, `international-seo` and `cro-audit`.

Free client-facing tools worth knowing: `schema-generator`, `faq-generator`,
`sitemap-builder`, `seo-checklist-generator` and `readability-analysis`.

---

# Part 5: script reference

| Script | What it does |
|---|---|
| `seo_lint.py` | Deterministic lint of URL, file or directory; `--save` persists findings |
| `seo_fix.py` | Turn findings into concrete HTML patches; `--apply` rewrites safely |
| `rule_engine.py` | `list` / `run` / `test` the 54 YAML rules |
| `seo_agent.py` | Autonomous scan, fix and ship loop |
| `seo_pr_check.py` | PR gate: diff changed HTML vs base branch, fail on regressions |
| `site_crawler.py` | Full crawl, redirect traces, canonical variant audit |
| `spa_detect.py` / `render_page.py` | JS-rendering risk and the raw versus rendered gap |
| `citation_score.py` | LLM citation readiness (weighted, 0 to 100) |
| `sxo_analyser.py` | Search experience versus SERP page-type consensus |
| `dfs_client.py` | DataForSEO: serp, volume, ideas, rankings, backlinks, crawl |
| `google_client.py` | Optional: PageSpeed, CrUX, GSC, GA4 |
| `ai_visibility.py` | Brand mention share in AI answers, plus history |
| `watch.py` | Scheduled monitoring bundle and `schedule` helper |
| `recommend_store.py` | The action queue (list, add, set, summary, history) |
| `drift_store.py` | Dated snapshots: save, list, latest, compare, chart |
| `event_log.py` | Append-only project timeline |
| `impact_report.py` | Join fixes to ranking outcomes |
| `seo_forecast.py` | Traffic potential for target positions |
| `cost_ledger.py` | API spend per command |
| `project_memory.py` | `seo-project.yml`, per-client profiles and entities |
| `project_dashboard.py` | Mission-control report |
| `report_build.py` / `report_pdf.py` / `report_publish.py` | Branded HTML, PDF and one-pager |
| `schema_gen.py` | JSON-LD generation from fields or memory |
| `link_graph.py` / `link_graph_render.py` | Internal link analysis and visual graph |
| `log_analyzer.py` | Server log crawl stats and waste |
| `indexnow.py` | Instant indexing submissions |
| `mcp_server.py` | Expose the suite to MCP clients |
| `seo_config.py` / `setup_wizard.py` / `cache.py` | Credentials, setup, response cache |
| `generate_screenshots.py` | Visual evidence for reports |

---

# Part 6: extend the rule engine

If a check is deterministic, it belongs in `rules/`, not in prose:

```yaml
# rules/metadata/my-rule.yaml
id: my-rule
category: metadata
severity: high
confidence: high
detect: {field: title, condition: empty}
why: >- human explanation, shown in every finding
fix:
  guidance: >- what to do
  patch:            # optional: makes the rule auto-fixable
    type: title
    target: head
    requires: [title_draft]
    template: "<title>{{title_draft}}</title>"
test:
  expect_fail: {title: ""}
  expect_pass: {title: "A real title"}
```

Then `python scripts/rule_engine.py test` and `python validate.py`. Every
rule self-tests, and the moment it lands it powers lint, CI, the fix
engine, the PR gate and every future skill. See
[RULE-ENGINE.md](RULE-ENGINE.md).

---

# Part 7: where everything lives

| What | Where |
|---|---|
| Recommendation queue | `~/.config/opencode/seo-suite/recommendations/<domain>.jsonl` |
| Event timeline | `~/.config/opencode/seo-suite/events/<domain>.jsonl` |
| Drift snapshots | `~/.config/opencode/seo-suite/drift/<domain>/<ts>.json` |
| API spend ledger | `~/.config/opencode/seo-suite/costs.jsonl` |
| Credentials | `~/.config/opencode/seo-suite/credentials.json` |
| Reports | `$SEO_REPORTS_DIR/<domain>/` |
| Project context | `seo-project.yml`, `clients/*.yml` |

No cloud account and no lock-in: plain files you can read, diff and back up.

---

# Part 8: rhythms

```text
Each morning      /briefing                      30s: what changed, what to do
Weekly (auto)     watch.py run                   lint, rankings, competitors
Weekly (auto)     seo_agent run (in the site PR)  one review-ready SEO PR
When you ship     fixes resolve themselves on the next lint run
Monthly           project_dashboard + impact_report
Quarterly         /workflow-quarterly-review     wins, losses, next-quarter plan
Any time          just ask: "why has traffic dropped?"
```

---

# Part 9: troubleshooting

| Symptom | Fix |
|---|---|
| `DataForSEO status .... MISSING` | `python scripts/setup_wizard.py`, or [DATAFORSEO-SETUP.md](DATAFORSEO-SETUP.md) |
| A skill does not trigger | Restart OpenCode (skills load at startup); check `validate.py` |
| Rules disagree with your page type | They are page-type-blind by design. Dismiss contextually in the skill, or add a rule with a `test` block |
| Reports in the wrong place | Set `SEO_REPORTS_DIR` |
| JS site, empty lint results | `spa_detect.py --url`, then `render_page.py --url --diff`, or lint the built HTML |
| Costs unclear | `python scripts/cost_ledger.py report` |
| Tests to run after any change | `python validate.py`, `python -m py_compile scripts/*.py`, `python -m pytest tests/ -q` |

---

## Further reading

- [GETTING-STARTED.md](GETTING-STARTED.md): first 15 minutes
- [USER-GUIDE.md](USER-GUIDE.md): every command, the five stores, tips
- [ARCHITECTURE.md](ARCHITECTURE.md): how the three layers fit
- [RECIPES.md](RECIPES.md): the contract every new skill must follow
- [RULE-ENGINE.md](RULE-ENGINE.md): write your own checks
- [CI-AND-PR.md](CI-AND-PR.md): gates and pull-request checks
- [REPORTS.md](REPORTS.md): branded deliverables
- [SXO.md](SXO.md): search experience optimisation
- [MCP.md](MCP.md): expose the suite to MCP clients
- [DATAFORSEO-SETUP.md](DATAFORSEO-SETUP.md) and [GOOGLE-APIS.md](GOOGLE-APIS.md): credentials