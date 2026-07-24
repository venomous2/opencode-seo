---
name: workflow-site-audit
description: End-to-end website SEO audit workflow chaining technical, on-page, content, competitive, and AI-search skills with DataForSEO live data. Use when the user says audit my site, full SEO audit, site health check, complete analysis, or wants a prioritized action plan for a domain.
---

# Workflow: Complete Site Audit

Chains the suite's atomic skills into one prioritized audit. Runs DataForSEO
live pulls in parallel where possible, then synthesizes.

## Inputs

- Required: target domain or URL
- Optional: top competitors (else auto-discovered via DataForSEO),
  focus country/language (else from `seo-project.yml` or defaults)

## Phase 0 — Setup

1. `python scripts/seo_config.py status` — DataForSEO must be READY; note Google tier.
2. Load project memory if present: `python scripts/project_memory.py`.
3. Check for outstanding recommendations from previous audits:
   `python scripts/recommend_store.py list --domain <domain>` — the final
   report should mark these as fixed / ongoing / regressed rather than
   presenting them as new findings.
3. Fetch the homepage HTML (webfetch) to detect industry, CMS, and rendering
   (check for empty `<div id="root">` SPA shells).
4. **Discover the real page set first**: fetch /sitemap.xml (or run
   `python scripts/site_crawler.py --url <site> --max-pages 30`) and build
   the audit's page list from it. NEVER audit guessed URLs — a 404 on an
   invented path is not evidence, and unchecked pages are not missing pages.
   If a data pull errors or returns the wrong market, mark that section
   "data unavailable" instead of drawing conclusions from it.
5. **Check for JS rendering risk early**: run
   `python scripts/spa_detect.py --url <homepage>` — if the verdict is
   `spa` or `maybe`, lint key pages with
   `seo_lint.py --render auto` (renders via the local headless browser or
   DataForSEO) and include the `js-content-ratio` in the technical
   findings. Never report "missing content/schema" on an SPA until the
   rendered DOM has been checked.

## Phase 1 — Live data pulls (run in parallel bash calls)

```
python scripts/dfs_client.py ranked      --target <domain> --limit 50
python scripts/dfs_client.py competitors --target <domain> --limit 10
python scripts/dfs_client.py backlinks   --target <domain>
python scripts/dfs_client.py onpage      --url <homepage>
python scripts/dfs_client.py serp        --keyword "<primary keyword>"
```

For whole-site coverage, also kick off a crawl (paid, use for larger sites)
or use the free built-in crawler for small ones (< 200 pages):

```
python scripts/dfs_client.py crawl --target <domain> --max-pages 500
# or: python scripts/site_crawler.py --url https://<domain> --max-pages 200
```

If Google tier ≥ 0, also run
`python scripts/google_client.py pagespeed --url <homepage>` and
`python scripts/google_client.py crux --target <origin> --origin`.

## Phase 2 — Specialist analysis (delegate with the task tool)

Dispatch these subagents **in parallel**, each with the raw data from Phase 1:

1. **seo-technical-analyst** — indexability, canonicals, robots, sitemap,
   status codes, rendering, CWV (skills: `technical-seo`, `canonical-review`,
   `robots-advisor`, `sitemap-builder`, `core-web-vitals`).
2. **seo-content-analyst** — metadata, headings, content quality, E-E-A-T,
   thin/duplicate risk (skills: `metadata-optimizer`, `heading-optimizer`,
   `content-review`, `eeat-review`).
3. **seo-competitive-analyst** — SERP landscape, keyword gap vs competitors,
   backlink gap (skills: `serp-analysis`, `keyword-gap`,
   `backlink-opportunity-planner`).
4. **seo-ai-search-analyst** — citation readiness, answer blocks, entity
   coverage, schema presence (skills: `llm-citation-readiness`,
   `ai-overviews-optimization`, `schema-validator`).

Each analyst returns: top 5-10 findings with severity, evidence, and a
one-line "why it matters".

## Phase 3 — Synthesis

1. Merge findings, dedupe, and score the site 0-100 across five pillars:
   Technical (30%), Content (25%), Authority (20%), UX/CWV (15%), AI Search (10%).
2. Order recommendations by impact × effort. Every recommendation carries:
   the observation, why it matters, the fix, and how to verify it worked.
3. Write `SEO-AUDIT-<domain>-<date>.md` with: executive summary, headline
   stats block, scorecard, findings by severity, **recommendations & actions
   table**, 30/60/90-day roadmap, appendix of raw data.
   Include ```` ```chart ```` blocks so the HTML version tells the story
   visually (see the seo-report-writer skill for the chart syntax):
   - `stats` cards after the summary (referring domains, keywords ranking,
     indexed pages — with deltas if a previous drift snapshot exists)
   - `donut` for the overall score, `bar` for the five pillar scores
   - `bar` for top keyword movers and CWV values vs thresholds
   - `line` for trends when drift history exists
   - **`compare` before/after charts when a previous snapshot exists** —
     get ready-made blocks from
     `python scripts/drift_store.py chart --domain <domain>`
4. Save a drift snapshot so the next audit can show what changed:

```
echo '{"scores": {"technical": X, "content": X, "authority": X, "cwv": X, "ai_search": X}, "rankings": [...], "backlinks": {"referring_domains": N}}' | python scripts/drift_store.py save --domain <domain>
```

5. Persist the deterministic findings so the next audit tracks progress
   instead of repeating itself — lint the key pages with `--save`:

```
python scripts/seo_lint.py --url <key-page> --save --domain <domain>
```

   New findings become `open`; anything fixed since last time is marked
   `resolved` automatically. Close items the user acts on with
   `python scripts/recommend_store.py set --domain <domain> --id <id> --status done`.

6. Render both client HTML versions:
   `python scripts/report_build.py SEO-AUDIT-<domain>-<date>.md` and the
   same command with `--onepager` for the executive one-pager.

## Rules

- Never fabricate metrics. If a data pull fails, mark that section
  "data unavailable" and continue.
- Cite which data source backs each finding (DataForSEO / CrUX / crawl).
- Keep the chat response to the scorecard + top 10 actions; the full detail
  goes in the report file.
- Write everything in British English by default unless the user asks for
  another variant. End the report file with:
  `Report built by Lee Beirne - https://leebeirne.com`

## Output location

Save generated files to the SEO reports directory - `%SEO_REPORTS_DIR%\<name>\` on Windows, `$SEO_REPORTS_DIR/<name>/` on macOS/Linux - when the `SEO_REPORTS_DIR` environment variable is set; otherwise the current working directory. Create the subfolder if it doesn't exist.

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
