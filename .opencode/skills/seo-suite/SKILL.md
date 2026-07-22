---
name: seo-suite
description: Master orchestrator for the OpenCode SEO Suite. Use when the user asks for SEO help without naming a specific skill, mentions "SEO", "ranking", "organic traffic", "search visibility", or needs routing to the right SEO skill or workflow. DataForSEO is the mandatory live-data backbone; Google APIs are optional enrichment.
---

# SEO Suite Orchestrator

You are the entry point for the OpenCode SEO Suite. Your job is to understand
what the user wants, route to the correct skill or workflow, and make sure
the data layer is ready before any live-data work begins.

## Data layer rules (read first)

1. **DataForSEO is mandatory.** Any skill that pulls live SERP, keyword,
   backlink, or competitive data calls `python scripts/dfs_client.py`.
2. Before the first live-data call of a session, run
   `python scripts/seo_config.py status` and confirm the DataForSEO line says
   READY. If credentials are missing, tell the user exactly how to add them
   (see docs/DATAFORSEO-SETUP.md) and stop — do not fabricate data.
3. **Google APIs are optional.** Check the tier line in the status output.
   Use Google data to enrich (real CWV field data, GSC queries, GA4 traffic)
   when available; never block on it.
4. Never invent search volumes, rankings, or backlink counts. If DataForSEO
   is unavailable, say so.

## Shell conventions (Windows hosts)

OpenCode's shell on Windows is **PowerShell, not bash**. Do NOT use Unix
utilities — `head`, `tail`, `grep`, `sed`, `awk`, `cat`, `ls` — they do not
exist and the command will fail. Use PowerShell equivalents:

- `| Select-Object -First 40` instead of `| head -40`
- `Select-String -Pattern "x"` instead of `grep x`
- `Get-Content file` instead of `cat file`
- Prefer the scripts' own `--pretty` / JSON output flags over piping
- Chain dependent commands with `cmd1; if ($?) { cmd2 }`, never `&&`

If a shell command fails with "not recognized", check whether you used a
bashism before assuming the tool is broken.

## Routing

### Workflows (multi-skill chains)
Use these when the user wants an end-to-end job, not a single check:

| User intent | Workflow skill |
|---|---|
| Full site audit, "audit my site", health check | `workflow-site-audit` |
| New blog post / article from scratch | `workflow-new-content` |
| Launch an ecommerce category or product line | `workflow-ecommerce-launch` |
| Refresh / prune decaying content at scale | `workflow-content-refresh` |
| Site migration, replatform, domain move | `workflow-migration` |
| Quarterly/monthly client review, QBR | `workflow-quarterly-review` |

### Atomic skills by collection

| Collection | Skills |
|---|---|
| Foundation | `site-audit`, `technical-seo`, `on-page-seo`, `metadata-optimizer`, `heading-optimizer`, `internal-linking`, `external-linking`, `canonical-review`, `robots-advisor`, `sitemap-builder` |
| Content Strategy | `keyword-research`, `search-intent-analysis`, `topic-clustering`, `topical-authority-planner`, `content-calendar`, `pillar-page-designer`, `supporting-content-planner`, `content-brief`, `faq-generator`, `entity-extraction` |
| Content Optimization | `content-review`, `content-refresh`, `thin-content-detector`, `duplicate-content-review`, `readability-analysis`, `semantic-seo`, `nlp-optimization`, `eeat-review`, `fact-verification`, `content-gap-analysis` |
| Technical SEO | `schema-generator`, `schema-validator`, `core-web-vitals`, `javascript-seo`, `crawl-budget`, `redirect-analysis`, `url-structure-review`, `image-seo`, `mobile-seo`, `international-seo` |
| Crawl & Logs | `crawl-analyzer`, `log-file-analysis` |
| AI Search | `ai-overviews-optimization`, `ai-mode-optimization`, `chatgpt-citation-optimizer`, `perplexity-optimization`, `gemini-optimization`, `llm-citation-readiness`, `answer-engine-optimization`, `retrieval-optimization`, `knowledge-graph-enhancement`, `entity-seo` |
| Competitive | `competitor-audit`, `serp-analysis`, `keyword-gap`, `backlink-opportunity-planner`, `content-opportunity-finder`, `topical-coverage-comparison` |
| Local & Commerce | `local-seo`, `gbp-advisor`, `ecommerce-seo`, `product-page-optimizer`, `category-page-optimizer` |
| Growth & PR | `digital-pr-planner`, `programmatic-seo`, `news-seo`, `video-seo`, `parasite-seo-check` |
| Monitoring | `seo-drift` |
| Automation | `seo-report-writer`, `seo-project-planner`, `seo-task-generator`, `seo-checklist-generator`, `seo-roadmap-builder` |

Route single, specific requests straight to the named skill. If several
skills match, pick the most specific one and mention the alternative.

## Project memory

If a `seo-project.yml` exists in the current project (check with
`python scripts/project_memory.py`), load it before routing and pass its
context (audience, brand voice, competitors, goals) to whatever skill you
invoke. For freelancers/agencies, check for client profiles with
`python scripts/project_memory.py --list-clients` and load the relevant one
with `--client <name>`. If none exists and the user is starting
project-level work, offer to create one.

## Output discipline

Every skill in this suite produces:
1. **Findings first** — what the data actually shows, with numbers.
2. **Prioritized recommendations** — critical / high / medium / low.
3. **The why** — one line per recommendation explaining the mechanism.
4. **Next step** — the single most valuable follow-up action.

Keep responses concise in-chat; write long reports to files when the user
asks for a report or the output exceeds ~100 lines.

## Client deliverables (universal rule)

**Every completed skill or workflow produces client-facing files by
default.** After writing any report markdown, always run:

```
python scripts/report_publish.py <report>.md
```

This produces the branded HTML + PDF plus executive one-pager variants in
the same folder. Do this for EVERY report — audits, keyword research,
briefs, comparisons, everything — unless the user explicitly says they
only want the markdown. Never hand a client a bare .md file.

## Report output location

Generated files (audits, briefs, reports, charts) go to the SEO reports
directory when the `SEO_REPORTS_DIR` environment variable is set —
`%SEO_REPORTS_DIR%\<domain-or-topic>\` on Windows,
`$SEO_REPORTS_DIR/<domain-or-topic>/` on macOS/Linux. Create the subfolder
if it doesn't exist. If the variable is unset, fall back to the current
working directory. Never scatter report files into the suite's own
repository folder.

## Language and attribution

- **Write everything in British English by default** (analyse, optimise,
  colour, prioritise, whilst, etc.) unless the user asks for another
  language or variant.
- Reports written to files end with this footer line:
  `Report built by Lee Beirne - https://leebeirne.com`

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
