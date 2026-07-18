---
name: crawl-budget
description: Finds and fixes crawl waste on larger sites — faceted navigation explosion, parameter sprawl, infinite spaces, soft 404s, and redirect chains — so crawlers spend budget on pages that matter. Use when the user says crawl budget, crawl waste, or faceted navigation.
---

# Crawl Budget

Optimizes how search engines spend crawl capacity. Crawl budget only
matters at scale — sites under roughly 10k indexable URLs rarely have a
budget problem; say so if the site is small instead of manufacturing work.

## Inputs

- Required: site URL and approximate page count
- Optional: server log samples, robots.txt, XML sitemap(s), list of known
  parameterized URL patterns

## Data pulls

Fetch with the webfetch tool:

- `/robots.txt` — current disallow rules
- `/sitemap.xml` (and any sitemap index) — declared canonical URLs
- Representative faceted/listing pages — count filter combinations and
  check how links to parameterized URLs are exposed

Optional live checks:

```
python scripts/dfs_client.py onpage --url https://example.com --pretty
```

Google Search Console's Crawl Stats report (Settings > Crawl Stats) is the
authoritative source for actual crawl volume — ask the user for exports if
available. Never invent crawl counts.

## Process

1. **Quantify URL space** — estimate total crawlable URLs vs. genuinely
   valuable ones. Faceted navigation is the classic multiplier:
   N filters × M options each = combinatorial URL explosion.
2. **Classify waste sources**:
   - Faceted/filtered URLs with no search demand (sort, price ranges,
     color/size permutations)
   - Session IDs, tracking parameters (`utm_*`, `gclid`) in internal links
   - Infinite spaces — calendars paginating to year 9999, endless
     "next page" archives
   - Soft 404s — empty category/search pages returning 200
   - Redirect chains and loops consuming requests
   - Duplicated HTTP/HTTPS or www/non-www hosts answering 200
3. **Choose the right control per waste class**:
   - `robots.txt` disallow for parameter patterns that must never be
     crawled (note: disallowed URLs can still index without content —
     pair with noindex only when the URL can still be crawled)
   - `noindex` + follow for thin pages that should consolidate signals
     but may be crawled
   - Canonicals for near-duplicates that users legitimately reach
   - Parameter-free internal linking — link only to canonical, valuable
     URL states; make filter states JS-driven or POST-based
   - Return real 404/410 for empty results; cap calendars and archives
4. **Sitemap hygiene** — sitemaps list only canonical, 200-status,
   indexable URLs; keep under 50k URLs / 50MB per file; accurate
   lastmod dates.
5. **Chain cleanup** — internal links point directly at final URLs, not
   through redirects (hand off to the redirect-analysis skill for maps).

## Output

- Findings table: waste source | estimated URL share | evidence | severity
- Prioritized fixes with a one-line "why" each (control type: robots /
  noindex / canonical / linking / status code)
- Proposed `robots.txt` additions, with a warning for each rule about what
  it does NOT do (e.g. noindex vs disallow)
- Single best next step: the one change that removes the largest share of
  crawl waste
