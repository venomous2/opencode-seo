---
name: category-page-optimizer
description: Optimizes category and product-listing pages — intro copy, H1/title patterns, facet indexation rules, pagination canonicals, and internal linking. Use when the user says category page, PLP, collection page, or optimize a category.
---

# Category Page Optimizer

Optimizes one category/PLP page — the page type that carries the
highest-value commercial keywords in most stores.

## Inputs

- Required: category page URL
- Optional: target keyword (else derived from the page), location/language
  (defaults from `seo-project.yml` via `python scripts/project_memory.py`)

## Data pulls

```
python scripts/dfs_client.py onpage --url "<category URL>"
python scripts/dfs_client.py serp   --keyword "<target keyword>" --limit 20
python scripts/dfs_client.py volume --keywords "<category keyword>,<facet variants>"
```

Webfetch the category URL plus paginated page 2 and one filtered variant to
inspect canonicals and indexability in the real markup. If credentials are
missing, stop and point the user to docs/DATAFORSEO-SETUP.md. Do not invent
numbers.

## Process

1. **H1 & title pattern** — H1 = the exact category language searchers use
   (check SERP titles of ranking category pages). Title formula:
   `[Category] — [range/brand cue] | [Store]`. Unique per category; never
   the store name alone.
2. **Intro copy** — 50-150 words of genuinely useful text (what's here, who
   it's for, how to choose), placed so it doesn't push products below the
   fold on mobile. Not keyword stuffing; not 800 words of fluff above the
   grid.
3. **Filter-to-indexable-page rules** — audit the facet system:
   - For each facet combination, is there search demand? Verify with the
     `volume` pull (e.g., "women's waterproof hiking boots").
   - Demand-backed facets → static URL, unique title/H1, indexable, added
     to sitemap and internal links.
   - Everything else → noindex (or canonical to parent category). Parameter
     URLs must not multiply crawl paths.
4. **Pagination** — each page in the series self-canonicals (no
   canonical-to-page-1), unique title suffix ("Page 2 of ..."), crawlable
   next/prev links. Page 2+ products must be reachable without JavaScript.
5. **Canonical hygiene** — sorted/filtered variants canonical to the clean
   category URL; the fetched page-2 and filtered URLs from the webfetch step
   prove whether this holds.
6. **Internal links** — links to relevant buying guides/comparisons from the
   intro or below-grid copy; subcategory chips; breadcrumbs with
   BreadcrumbList schema
   (`python scripts/schema_gen.py breadcrumblist --field items="..." --script-tag`).
7. **Product grid basics** — product names as links with descriptive anchor,
   price visible, lazy-loaded images with alt text and set dimensions.

## Output

- Scorecard: H1/title | intro copy | facet rules | pagination | canonicals |
  internal links — pass/gap with evidence from the fetched markup
- Facet rule table: facet combination → demand (volume data) → index/noindex
- Proposed title, H1, and intro copy
- Fix list ordered by impact with one-line why each + single best next step

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
