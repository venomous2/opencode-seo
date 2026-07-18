---
name: thin-content-detector
description: Detects thin and low-value pages using word-count floors by page type, doorway-page patterns, and boilerplate-ratio tests, then triages each into expand, merge, noindex, or remove. Use when the user says thin content, low quality pages, or doorway pages.
---

# Thin Content Detector

Finds pages that add little unique value and decides their fate. Thin is a
value judgment backed by tests, not just a word count.

## Inputs

- Required: domain or list of URLs to test
- Optional: page-type hints (blog, product, category, tag), custom floors

## Data pulls

```
python scripts/dfs_client.py ranked --target "<domain>" --limit 500
```

Pages with zero ranking keywords are prime thin candidates. Fetch each
candidate with webfetch (parallel, batch sensibly). If credentials are
missing, the URL-list path still works — fetch and test the supplied pages
only, and say ranking data was unavailable.

## Process

1. **Word-count floor by page type** (unique body text, not template):
   - Blog/article: < 300 words → flag
   - Product page: < 150 unique words → flag
   - Category page: < 100 words of unique intro → flag
   - Tag/author/archive: thin by default unless curated
2. **Boilerplate ratio** — if navigation, footer, and repeated blocks make
   up > 70% of the page's text, the unique core is too small.
3. **Doorway patterns** — pages that differ only by swapping a city,
   product name, or modifier into the same template; near-identical pages
   targeting keyword variants.
4. **No-unique-value test** — ask: what does this page offer that no other
   page on the site or the SERP offers? If the answer is nothing, flag it
   regardless of length.
5. **Cross-check performance** — a "thin" page that ranks and converts
   stays; a long page with zero impressions is still a candidate.

## Triage

| Action | When |
|---|---|
| **Expand** | Valid intent, decent URL/links, weak body — build it out |
| **Merge** | Overlaps a stronger page — consolidate, 301 to the survivor |
| **Noindex** | Useful for users, not for search (filters, tags) — keep, deindex |
| **Remove** | No traffic, links, or purpose — delete, 410, update sitemap |

## Output

Triage table: URL | page type | unique words | tests failed | action |
one-line why. Prioritize by recoverable value. Write the full list to
`THIN-CONTENT-<domain>-<date>.md` when over 20 rows; chat gets counts plus
the top 10. Single best next step: start with the highest-traffic "merge"
candidate — consolidation usually wins fastest.
