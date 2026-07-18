---
name: keyword-research
description: Data-driven keyword research using live DataForSEO search volume, keyword ideas, and related-keyword expansion. Use when the user says keyword research, find keywords, search volume, keyword ideas, seed keywords, or what should I rank for.
---

# Keyword Research

Finds and prioritizes keywords with live DataForSEO data. Never estimates
volumes — every number comes from an API call.

## Inputs

- Required: seed keyword(s) or topic
- Optional: location/language (defaults: United States / English, or the
  values in `seo-project.yml`)

## Data pulls

Run these with bash (parallel when listing multiple seeds):

```
python scripts/dfs_client.py ideas   --keyword "<seed>" --limit 50
python scripts/dfs_client.py related --keyword "<seed>" --limit 30
python scripts/dfs_client.py volume  --keywords "kw1,kw2,kw3"
python scripts/dfs_client.py ranked  --target "<user-domain>"   # if given
```

If credentials are missing, stop and point the user to docs/DATAFORSEO-SETUP.md.
Do not invent numbers.

## Process

1. **Expand** — collect ideas + related keywords for each seed.
2. **Filter** — drop irrelevant terms; group the rest by intent
   (informational / commercial / transactional / navigational).
3. **Score** — for each keyword record: search volume, CPC (as a
   commercial-intent proxy), keyword difficulty when present, and trend.
4. **Prioritize** — rank by opportunity: volume × intent fit × attainability.
   Flag "quick wins" (volume present, difficulty low, domain already ranks
   4-30 when `ranked` data exists).
5. **Map** — assign each priority keyword to a new or existing page type.

## Output

A markdown table: keyword | volume | difficulty | CPC | intent | target page
type | priority (P1-P3). Follow with:
- 3-5 keyword cluster recommendations for content planning
- Notable SERP features worth targeting (check with `dfs_client.py serp`)
- One-line rationale for the top pick

Keep the chat table to the top 20 rows; write the full list to
`KEYWORDS-<topic>-<date>.md` when it exceeds that.

## Output location

Save generated files to the SEO reports directory - `%SEO_REPORTS_DIR%\<name>\` on Windows, `$SEO_REPORTS_DIR/<name>/` on macOS/Linux - when the `SEO_REPORTS_DIR` environment variable is set; otherwise the current working directory. Create the subfolder if it doesn't exist.
