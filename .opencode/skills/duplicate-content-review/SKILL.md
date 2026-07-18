---
name: duplicate-content-review
description: Finds internal duplicate and near-duplicate content — parameter URLs, protocol and www variants, pagination overlap, shared boilerplate — and prescribes canonical, 301, or noindex per case. Use when the user says duplicate content, content duplication, or near-duplicate.
---

# Duplicate Content Review

Detects duplication within a site and prescribes the right consolidation
signal for each case. Different causes get different fixes — never
blanket-canonical everything.

## Inputs

- Required: domain or list of suspect URLs
- Optional: known parameter patterns, CMS type

## Data pulls

```
python scripts/dfs_client.py ranked --target "<domain>" --limit 500
python scripts/dfs_client.py onpage --url "<url>"      # per suspect page
```

Fetch suspect URL groups with webfetch (parallel). Two URLs ranking for
the same keyword in the ranked pull is the strongest duplication signal.
If credentials are missing, audit the supplied URLs from webfetch alone.

## Process

1. **Variant sweep** — check each key URL under http/https, www/non-www,
   trailing slash or not. All variants should 301 to one canonical form;
   any 200 response on a variant is a duplication bug.
2. **Parameter URLs** — sort, filter, session-ID, and tracking parameters
   (utm_*) rendering full duplicate pages at 200 status.
3. **Near-duplicate bodies** — compare fetched pages' main content; pages
   sharing > ~85% of body text are near-duplicates even at different URLs
   (common with printer versions, AMP leftovers, location-swap pages).
4. **Pagination** — page/2+ repeating page 1's intro, or view-all pages
   competing with paginated sets.
5. **Boilerplate-heavy pages** — legal/footer blocks outweighing unique
   content (see `thin-content-detector` for the ratio test).
6. **Existing signals audit** — read each page's canonical tag and robots
   meta; flag conflicting signals (canonical to A but 301 to B, canonical
   chains, noindexed pages in sitemaps).

## Prescriptions

| Case | Fix |
|---|---|
| Protocol/host/slash variants | 301 to the canonical form |
| Parameter duplicates | Canonical to the clean URL; fix internal links |
| True duplicate pages | 301 to the survivor |
| Near-duplicates, both valuable | Differentiate content, or merge + 301 |
| Pages users need, search doesn't | Noindex, keep accessible |
| Paginated series | Self-canonical each page; unique intro on page 1 |

## Output

Duplication table: URL group | cause | evidence | fix | priority (by
impressions/links at stake). Write `DUPLICATE-CONTENT-<domain>-<date>.md`
for large sites. End with the single most damaging case — usually a live
http or www variant splitting link equity.
