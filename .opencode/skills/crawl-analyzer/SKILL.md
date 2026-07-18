---
name: crawl-analyzer
description: Analyses a full-site crawl into prioritised findings — status codes, missing or duplicate titles and meta, thin pages, orphan candidates, canonical coverage, and noindex review. Use when the user says crawl my site, site crawl, crawl analysis, or all pages audit.
---

# Crawl Analysis

Runs a crawl and turns the raw page inventory into a prioritised fix
list. The crawl is the evidence — every finding cites crawled URLs and
counts, never impressions of the site.

## Inputs

- Required: site URL or domain
- Optional: max pages, whether JS rendering is needed (paid crawl only)

## Choose the crawler

| Tool | Cost | Use when |
|---|---|---|
| `site_crawler.py` (built in) | Free | Under ~200 pages, or a quick check |
| `dfs_client.py crawl` | Paid per page | Larger sites, or when Lighthouse-per-page and DataForSEO on-page metrics are wanted |

When in doubt, start free; escalate only if the site outgrows 200 pages.
Before the paid path, confirm `python scripts/seo_config.py status` shows
DataForSEO READY.

## Data pulls

Free, small sites:

```
python scripts/site_crawler.py --url https://example.com --max-pages 200 --pretty
```

Paid, full flow (blocks until the crawl finishes; `--wait` caps the
minutes):

```
python scripts/dfs_client.py crawl --target example.com --max-pages 500 --pretty
```

Or async for big crawls:

```
python scripts/dfs_client.py crawl-start  --target example.com --max-pages 2000 [--javascript]
python scripts/dfs_client.py crawl-status --task-id <id>
python scripts/dfs_client.py crawl-pages  --task-id <id>
```

Also fetch `/robots.txt` and `/sitemap.xml` with webfetch for comparison
against what the crawl actually found.

## Process

Work the inventory in this order; each check yields findings with counts
and example URLs:

1. **Status codes** — non-200s reachable via internal links: 404/410 (fix
   the link or restore the page), 5xx (urgent, server-side), internal 3xx
   links (point links at final URLs — why: redirects waste crawl and
   dilute signals).
2. **Titles** — missing, duplicated across pages, over-long, or sitewide
   boilerplate. Mass duplicates usually signal a template or duplication
   problem, not lazy writing.
3. **Meta descriptions** — missing or duplicated; low severity but cheap
   to fix at template level.
4. **Thin pages** — little unique body content for their page type; hand
   long lists to `thin-content-detector` for triage.
5. **Orphan candidates** — URLs in the sitemap but absent from the crawl
   (nothing links to them), plus crawled pages with near-zero inlinks.
   Why: orphans rank poorly and erode sitemap trust.
6. **Canonical coverage** — pages with no canonical, canonicals pointing
   at non-200 or wrong-host targets, and canonical/noindex conflicts.
7. **Noindex review** — every noindexed URL: deliberate (thank-you,
   admin, internal search) or accidental (staging leftovers, pagination).
   Accidental noindex on a money page is a Critical finding.
8. **Depth** — important pages buried more than 3 clicks from the
   homepage.

## Output

- Findings table ordered by severity: check | count | example URLs |
  severity | fix | one-line "why"
- Prioritised recommendation list, Critical -> Low
- For more than ~15 findings, write `CRAWL-<domain>-<date>.md` with the
  full tables; chat gets the counts + top 10. End the file with:
  `Report built by Lee Beirne - https://leebeirne.com`
- Single best next step: the highest-severity, highest-count fix —
  usually 5xx errors, accidental noindex, or mass duplicate titles.
