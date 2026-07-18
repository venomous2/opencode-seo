---
name: content-refresh
description: Refresh a single decaying page by confirming decay with live ranking data, replacing stale facts, and expanding coverage to match today's SERP. Use when the user says refresh content, update old post, or content decay.
---

# Content Refresh

Brings one aging page back to ranking shape: prove the decay, fix what's
stale, close the coverage gap versus today's top results.

## Inputs

- Required: page URL
- Optional: target keyword (inferred if omitted), domain, lookback window

## Data pulls

```
python scripts/dfs_client.py ranked --target "<domain>" --limit 200
python scripts/dfs_client.py serp   --keyword "<target keyword>" --limit 10
```

Optional enrichment when Google is configured:

```
python scripts/google_client.py gsc-queries --site <site> --page <url>
```

Then fetch the page and the current top 5 results with webfetch (parallel).
If credentials are missing, stop and point to docs/DATAFORSEO-SETUP.md.
Do not infer decay without data.

## Process

1. **Confirm decay** — decay holds when any of these are true:
   - Average position fell ≥ 3 places across the lookback window
   - Clicks or impressions fell ≥ 30% period-over-period (GSC, when
     available)
   - Page ranks 4-20 for terms with volume (striking distance)
   - Content is > 12 months old in a freshness-sensitive SERP
   If none hold, say so — the page may need something other than a refresh.
2. **Find stale elements** — dated statistics, old years in titles or H2s,
   dead outbound links, screenshots of retired UIs, discontinued products.
3. **Map today's SERP** — list subtopics, questions, and SERP features the
   top 5 satisfy that the page misses (compare H2s side by side).
4. **Rewrite plan** — update title/H1 dates only if the body genuinely
   changes; rebuild answer blocks to be quotable in 40-60 words; add
   missing subtopics as new sections rather than stuffing existing ones.
5. **Preserve equity** — keep the URL, keep sections that still earn
   links or rankings, and refresh internal links pointing at the page.

## Output

A refresh spec: decay evidence (numbers), stale-element list, sections to
add/rewrite with the competitor evidence for each, and new target keywords
from the serp pull. End with the single highest-impact fix. Write the full
spec to `CONTENT-REFRESH-<slug>-<date>.md`; re-check positions with
`dfs_client.py ranked` 2, 4, and 8 weeks after publishing.

## Output location

Save generated files to the SEO reports directory - `%SEO_REPORTS_DIR%\<name>\` on Windows, `$SEO_REPORTS_DIR/<name>/` on macOS/Linux - when the `SEO_REPORTS_DIR` environment variable is set; otherwise the current working directory. Create the subfolder if it doesn't exist.
