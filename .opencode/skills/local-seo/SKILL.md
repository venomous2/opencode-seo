---
name: local-seo
description: Builds a local SEO program covering NAP consistency, local pack factors, landing pages, reviews, citations, and LocalBusiness schema with live DataForSEO checks. Use when the user says local SEO, local rankings, map pack, local search, or rank in a city.
---

# Local SEO

Plans and checks a local search program grounded in the three local pack
factors: relevance, distance, prominence. Uses live GBP and geo-located SERP
data — never assumes rankings from a single location.

## Inputs

- Required: business name + city/region (and domain if one exists)
- Optional: target keywords, service-area vs storefront, location/language
  (defaults from `seo-project.yml` via `python scripts/project_memory.py`)

## Data pulls

```
python scripts/dfs_client.py serp-maps --keyword "<target keyword>" --location "<City,England,United Kingdom>" --limit 20
python scripts/dfs_client.py business  --keyword "<business name + city>"
python scripts/dfs_client.py serp      --keyword "<target keyword>" --location "<City,England,United Kingdom>" --limit 20
python scripts/dfs_client.py ranked    --target "<domain>" --limit 100   # if domain given
```

**Methodology rules (hard requirements — a wrong-URL or wrong-market audit
is worse than no audit):**

1. **Maps first for local-pack truth.** Local pack visibility is checked
   with `serp-maps` at CITY level (e.g. "Manchester,England,United Kingdom"),
   never inferred from an organic SERP. Organic `serp` with the same city
   location is run alongside for organic positions.
2. **Discover pages from the sitemap before checking anything.** Fetch
   /sitemap.xml (or run `site_crawler.py --max-pages 30`) and choose real
   location/landing URLs from it. NEVER audit a guessed URL — a 404 on an
   invented path is not evidence of a missing page, and a page you didn't
   check is not a page that doesn't exist.
3. **Schema verdicts from the real page's raw HTML.** Before claiming
   "no schema", fetch the actual location page from the sitemap and check
   for `application/ld+json` blocks (our parser reads them). If content is
   JS-injected, verify with `dfs_client.py onpage --url <real-url>` (JS
   rendering enabled). One page's lack of schema ≠ "no schema anywhere".
4. **Bad data = unavailable, not a conclusion.** If a pull errors or
   returns the wrong market (e.g. US results for a UK query), mark that
   section "data unavailable" and say why. Never draw conclusions from
   data you already know is wrong.

If credentials are missing, stop and point the user to
docs/DATAFORSEO-SETUP.md. Do not invent numbers.

## Process

1. **Baseline** — from `business`, record current GBP state: categories,
   rating, review count, hours, attributes. From the geo-located `serp`,
   record whether the business appears in the local pack and where the
   domain ranks organically.
2. **NAP consistency** — Name, Address, Phone must be byte-identical across
   the website, GBP, and citations. Check the site footer/contact page via
   webfetch and compare against GBP data. Any variation (St. vs Street, old
   phone numbers) is a fix item.
3. **Local pack factors** — assess each:
   - *Relevance*: categories, keyword-bearing (but real) business
     description, services listed, landing-page content match.
   - *Distance*: fixed — do not promise to beat it; set expectations.
   - *Prominence*: review count/recency, citations, local links, brand
     search volume.
4. **Landing pages** — each physical location needs a unique page: local
   H1, embedded map, unique local copy (not boilerplate with the city name
   swapped), local testimonials, NAP in text. Service-area businesses need
   genuine per-area pages only where they have real presence/evidence.
5. **Reviews strategy** — a compliant ask-flow (post-service email/SMS,
   direct GBP review link), response policy (all reviews, within days, no
   incentives, never gated).
6. **Citations** — core set first: GBP, Bing Places, Apple Business
   Connect, major data aggregators, then niche/local directories. Fix
   duplicates and stale listings before adding new ones.
7. **Schema** — generate markup:
   `python scripts/schema_gen.py localbusiness --field name="..." --field telephone="..." --field address="..." --script-tag`
   and place it on the homepage/location pages.

## Output

- Baseline snapshot: GBP state + local pack/organic positions per keyword
- Findings by factor (relevance/distance/prominence) with evidence
- Prioritized recommendations with one-line why each (NAP fixes → GBP →
  landing pages → reviews → citations → schema)
- Single best next step

Full detail goes to `LOCAL-SEO-<business>-<date>.md`.

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
