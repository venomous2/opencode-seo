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
3. Fetch the homepage HTML (webfetch) to detect industry, CMS, and rendering
   (check for empty `<div id="root">` SPA shells).

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
3. Write `SEO-AUDIT-<domain>-<date>.md` with: executive summary, scorecard,
   findings by severity, 30/60/90-day roadmap, appendix of raw data.
4. Save a drift snapshot so the next audit can show what changed:

```
echo '{"scores": {"technical": X, "content": X, "authority": X, "cwv": X, "ai_search": X}, "rankings": [...], "backlinks": {"referring_domains": N}}' | python scripts/drift_store.py save --domain <domain>
```

5. Offer to render the client HTML version:
   `python scripts/report_build.py SEO-AUDIT-<domain>-<date>.md`

## Rules

- Never fabricate metrics. If a data pull fails, mark that section
  "data unavailable" and continue.
- Cite which data source backs each finding (DataForSEO / CrUX / crawl).
- Keep the chat response to the scorecard + top 10 actions; the full detail
  goes in the report file.
- Write everything in British English by default unless the user asks for
  another variant. End the report file with:
  `Built by Lee Beirne · OpenCode SEO Suite — inspired by AgriciDaniel/claude-seo`
