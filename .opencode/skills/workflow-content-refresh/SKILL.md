---
name: workflow-content-refresh
description: Site-scale content refresh campaign workflow that finds decaying, thin, and overlapping pages using DataForSEO ranking data, then triages each URL into update, merge, redirect, or prune. Use when the user says content decay, refresh old posts, content pruning, or content audit campaign.
---

# Workflow: Content Refresh Campaign

Triage for a whole content library: find what's decaying, decide what to do
with each URL, and produce an execution queue.

## Inputs

- Required: domain
- Optional: content directory path (e.g. /blog), lookback window

## Steps

### 1. Inventory + performance baseline

```
python scripts/dfs_client.py ranked --target <domain> --limit 500
```

If GSC is configured (tier ≥ 1), pull clicks per page for two equal periods
to measure decay:
```
python scripts/google_client.py gsc-queries --site sc-domain:<domain> ...
```

### 2. Decay detection (skill: `content-refresh`)

A URL is a refresh candidate when any of these hold:
- Average position fell ≥ 3 places over the window
- Clicks/impressions fell ≥ 30% period-over-period (GSC data)
- It ranks 4-20 for a keyword with volume (striking distance)
- Content is > 12 months old in a freshness-sensitive SERP

### 3. Quality + overlap scan (skills: `thin-content-detector`, `duplicate-content-review`)

Fetch candidate URLs (webfetch, parallel). Flag thin pages (< 300 words of
unique value), overlapping pages targeting the same intent (cannibalization
risk), and pages with stale statistics or dead links.

### 4. Triage decision per URL

| Action | When |
|---|---|
| **Update** | Ranks 4-20, decaying, still matches intent — refresh data, expand coverage, new date |
| **Merge** | 2+ URLs overlap the same intent — consolidate into the strongest, 301 the rest |
| **Redirect** | Outdated offer/obsolete page with backlinks — 301 to nearest equivalent |
| **Prune** | No rankings, no links, no business value — remove + 410, update sitemap |
| **Leave** | Performing well — recheck next cycle |

### 5. Refresh specs

For each "update" URL, produce a mini-brief: new target keywords (re-run
`dfs_client.py serp` for freshness), sections to add/rewrite (compare
against today's top 5), statistics to replace, and internal links to add.

### 6. Execution queue + measurement

Order the queue by recoverable traffic (volume × current CTR gap). Define
the measurement loop: re-check positions 2/4/8 weeks post-refresh with
`dfs_client.py ranked`.

## Output

Write `CONTENT-REFRESH-<domain>-<date>.md` with the triage table (one row
per URL: action, evidence, spec link) and the prioritized execution queue.
Chat gets the summary counts + top 10 opportunities. Write in British
English by default; end the report file with:
`Report built by Lee Beirne - https://leebeirne.com`

## Output location

Save generated files to the SEO reports directory - `%SEO_REPORTS_DIR%\<name>\` on Windows, `$SEO_REPORTS_DIR/<name>/` on macOS/Linux - when the `SEO_REPORTS_DIR` environment variable is set; otherwise the current working directory. Create the subfolder if it doesn't exist.

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
