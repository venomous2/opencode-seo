---
name: on-page-seo
description: Full on-page optimization review of one URL covering title, meta, headings, content depth, internal links, images, and schema presence. Use when the user says optimize this page, on-page SEO, or page optimization.
---

# On-Page SEO

Deep single-URL optimization review benchmarked against the pages that
actually rank. Every comparison uses live data — never guesses at what
the SERP rewards.

## Inputs

- Required: the URL to optimize
- Optional: target keyword (else inferred from the page), location/language
  (defaults from `seo-project.yml`)

## Data pulls

```
python scripts/dfs_client.py onpage --url <url>
python scripts/dfs_client.py serp --keyword "<target keyword>" --limit 10
python scripts/dfs_client.py content --keyword "<target keyword>"
```

webfetch the target URL for raw HTML. If credentials are missing, stop and
point the user to docs/DATAFORSEO-SETUP.md — do not estimate competitor
word counts or SERP composition from memory.

## Process

1. **Metadata** — title and meta description vs the SERP winners: length,
   primary-keyword position, and whether the snippet sells the click.
2. **Headings** — one H1 matching search intent; H2/H3s covering the
   subtopics the ranking pages cover. Hand deep heading rewrites to
   `heading-optimizer` if the outline needs surgery.
3. **Content depth** — compare word count and subtopic coverage against
   the median of ranking URLs from the SERP pull. List the specific
   subtopics winners cover that this page misses; do not prescribe a
   raw word count as a goal by itself.
4. **Search intent fit** — informational vs commercial vs transactional;
   flag a mismatch (e.g. a product page targeting a how-to query).
5. **Internal links** — inlinks to this page and outlinks from it;
   descriptive anchors; links to the logical parent hub and siblings.
6. **Images** — alt text coverage, file weight, descriptive filenames.
7. **Schema** — detect existing JSON-LD; name the missing type for this
   page kind (Article, Product, FAQPage, HowTo, LocalBusiness...).
8. **Keyword usage** — primary keyword in title, H1, first 100 words, and
   URL slug; natural density, no stuffing.

## Output

A scorecard per section (metadata / structure / content / links / media /
schema) with evidence, then prioritized recommendations (critical / high /
medium / low) each with a one-line "why", then the single best next step.
Write the full review to `ONPAGE-<slug>-<date>.md` when it runs long;
chat carries the scorecard and top 5 actions.
