---
name: semantic-seo
description: Semantic completeness analysis that maps a topic's full meaning space — the related concepts, attributes, and relationships top-ranking pages share — into a coverage checklist for writers. Use when the user says semantic SEO, semantic coverage, or topical completeness.
---

# Semantic SEO

Builds the semantic coverage checklist for a topic: what the top results
collectively talk about, so a page covers the full meaning space instead of
repeating one keyword.

## Inputs

- Required: topic or target keyword
- Optional: existing draft/URL to audit, location/language

## Data pulls

```
python scripts/dfs_client.py serp    --keyword "<topic>" --limit 10
python scripts/dfs_client.py related --keyword "<topic>" --limit 30
python scripts/dfs_client.py ideas   --keyword "<topic>" --limit 50
```

Then fetch the top 5 organic results with webfetch (parallel). If
credentials are missing, stop and point to docs/DATAFORSEO-SETUP.md.

## Process

1. **Harvest concepts** — from the fetched pages, extract the recurring
   entities (people, products, standards, places), sub-attributes (price,
   size, steps, risks), and relationships (X causes Y, X is a type of Y)
   that appear across multiple top results.
2. **Cluster by facet** — group concepts into facets such as definitions,
   types, how-to steps, costs, comparisons, mistakes, and tools. Facets
   present in ≥ 3 of the top 5 are mandatory coverage.
3. **Add query-space concepts** — fold in related/ideas keywords that
   imply facets the pages missed (questions, modifiers like "vs",
   "cost", "near me").
4. **Note relationships, not just terms** — search engines model how
   concepts connect; the checklist must say *how* to relate them
   ("explain that X is a type of Y"), not just "mention X".
5. **Audit mode** (draft given) — check the draft against the checklist:
   covered / mentioned-but-shallow / missing.

## Output

A semantic coverage checklist for the writer, grouped by facet:

- **Must cover** (in ≥ 3 of top 5): concept — and the relationship to state
- **Differentiators** (in ≤ 1 of top 5): concepts worth adding to stand out
- **Query-implied gaps**: facets the keyword data shows searchers want
  but top pages under-serve

Audit mode adds a coverage table: concept | status | where in draft |
what to add. End with the 3 missing must-cover items to write first.
Write `SEMANTIC-COVERAGE-<topic>-<date>.md` for large checklists.

## Output location

Save generated files to the SEO reports directory - `%SEO_REPORTS_DIR%\<name>\` on Windows, `$SEO_REPORTS_DIR/<name>/` on macOS/Linux - when the `SEO_REPORTS_DIR` environment variable is set; otherwise the current working directory. Create the subfolder if it doesn't exist.
