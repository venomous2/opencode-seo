---
name: canonical-review
description: Canonical tag audit — self-referencing canonicals, cross-domain canonicals, pagination, parameter handling, canonical chains and conflicts, and when to use canonical vs 301 vs noindex. Use when the user says canonical, canonical tag, duplicate URLs, or URL parameters.
---

# Canonical Review

Audits rel=canonical implementation and resolves duplicate-URL
situations with the right tool: canonical, 301, or noindex.

## Inputs

- Required: URL(s) or domain to review
- Optional: known parameter patterns (utm, sort, filter, session IDs),
  syndication partners if cross-domain is in scope

## Data pulls

- webfetch each URL and its variants; record status code, canonical
  target, meta robots, and whether content is materially identical.
- `python scripts/dfs_client.py onpage --url <url>` for parsed canonical
  data on key pages.

## Process

1. **Baseline** — every indexable page should carry a self-referencing
   canonical. Missing is a medium flag (Google will guess), conflicting
   signals are critical.
2. **Conflicts** — canonical pointing at a different URL than expected;
   canonical chains (A→B→C — collapse to A→C); canonical targets that
   are redirected, 404, or noindexed (a noindexed canonical target
   wastes the signal entirely).
3. **Parameters** — test tracking/filter/sort variants (?utm=, ?color=,
   ?sort=): each should canonical to the clean URL. Variants with real
   unique value (a filter that deserves to rank) keep self-canonicals.
4. **Pagination** — page 2+ of a series self-canonicalizes; do NOT
   canonical all pages to page 1 (that tells Google the deeper pages
   are duplicates, which they are not). rel=next/prev is no longer a
   Google signal — skip it.
5. **Cross-domain** — syndicated copies must canonical to the original;
   verify partners actually implement it. Your own regional/language
   alternates belong in hreflang, not cross-domain canonicals.
6. **Decision guide** — recommend per duplicate set:
   - **301** when the duplicate URL should not exist for users at all
     (old slug, http→https, www consolidation).
   - **canonical** when both URLs must stay live (tracking parameters,
     print views, filtered listings).
   - **noindex** when the page must exist but never rank (thank-you
     pages, internal search results, staging).
7. **Consistency** — canonical targets must match the URLs in the XML
   sitemap and internal links; mixed signals get flagged.

## Output

Per-URL findings with evidence (fetched canonical vs expected), the
duplicate-set decision table (URL set | chosen fix | 301/canonical/
noindex), recommendations ranked critical / high / medium / low with a
one-line "why" each, then the single best next step. Full detail goes to
`CANONICAL-<domain>-<date>.md` for more than a handful of URLs.

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
