---
name: topic-clustering
description: Groups a keyword list into topic clusters (pillar + spokes) using live DataForSEO keyword data, with an internal-linking map. Use when the user says topic cluster, content cluster, keyword grouping, hub and spoke, or content architecture.
---

# Topic Clustering

Turns a flat keyword list into a pillar-and-spoke cluster map with
internal-linking implications. All grouping is backed by live volume and
relatedness data — no invented keywords.

## Inputs

- Required: seed topic or an existing keyword list (pasted or file)
- Optional: location/language (defaults: United States / English, or the
  values in `seo-project.yml`); user's domain, to mark keywords already
  covered

## Data pulls

Run with bash:

```
python scripts/dfs_client.py ideas   --keyword "<seed>" --limit 100
python scripts/dfs_client.py related --keyword "<seed>" --limit 50
python scripts/dfs_client.py volume  --keywords "kw1,kw2,..."   # batch, comma-separated
python scripts/dfs_client.py ranked  --target "<user-domain>"   # if domain given
```

If no keyword list is provided, build one from ideas + related first.

## Process

1. **Pool** — combine the user list + ideas + related; dedupe; batch-pull
   volumes for everything kept.
2. **Group by SERP-level meaning** — cluster keywords that a single page
   could rank for (same core entity + same intent). When unsure,
   spot-check two keywords with `dfs_client.py serp`: if their top-10
   URLs differ entirely, they need separate pages.
3. **Pick the pillar** — the broadest, highest-volume head term that can
   overview the whole topic. Everything narrower becomes a spoke.
4. **Validate spokes** — each spoke needs enough volume or strategic
   value to justify its own page; fold orphans back into the pillar as
   sections.
5. **Mark coverage** — when `ranked` data exists, flag keywords the site
   already ranks for: update/merge existing pages rather than create
   duplicates.

## Output

A cluster map. For each cluster: pillar keyword (volume), spoke keywords
(volumes, intent), suggested URL slugs, and an internal-linking note —
every spoke links up to the pillar, the pillar links out to every spoke,
and 2-3 lateral spoke-to-spoke links where topically adjacent. Then:
- Prioritized cluster build order (highest combined volume × intent fit
  first), with a one-line "why" per cluster
- Cannibalization warnings where two candidate clusters overlap, with
  the SERP evidence
- Single best next step: the first cluster to build and its first page

Write the full map to `CLUSTERS-<topic>-<date>.md`; chat summarizes the
top 3 clusters only.

## Output location

Save generated files to the SEO reports directory - `%SEO_REPORTS_DIR%\<name>\` on Windows, `$SEO_REPORTS_DIR/<name>/` on macOS/Linux - when the `SEO_REPORTS_DIR` environment variable is set; otherwise the current working directory. Create the subfolder if it doesn't exist.
