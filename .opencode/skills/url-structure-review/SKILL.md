---
name: url-structure-review
description: Reviews URL architecture for readability, crawl depth, consistency, parameter strategy, and breadcrumb alignment — and advises when changing URLs would do more harm than good. Use when the user says URL structure, URL review, slug, or permalink structure.
---

# URL Structure Review

Assesses the site's URL architecture. The default stance is conservative:
URLs that already rank and earn links should not be changed without a
compelling reason — review first, rename last.

## Inputs

- Required: site URL, or a list/export of URLs to review
- Optional: CMS/platform (WordPress, Shopify, custom), known constraints

## Data pulls

Fetch representative pages with the webfetch tool (home, a category, a few
leaf pages) to observe live URL patterns, canonicals, and breadcrumbs.
Enumerate the known URL set from the sitemap (`/sitemap.xml`).

Optional live data to decide whether change is safe:

```
python scripts/dfs_client.py ranked --target https://example.com --pretty
python scripts/dfs_client.py onpage --url https://example.com --pretty
```

## Process

1. **Readability** — slugs are short, lowercase, hyphen-separated words
   that describe the page (`/running-shoes/nike-pegasus-41`), not IDs,
   dates-by-default, or stuffed keywords. Query strings are not a
   substitute for a readable path on primary content.
2. **Depth** — every important page reachable within 3 clicks from home.
   Distinguish *URL* depth (slashes, mostly cosmetic) from *click* depth
   (the real problem). Flag orphan pages and hub pages that do not link
   down.
3. **Consistency policy** — one canonical form per page:
   - Lowercase everywhere; uppercase variants 301 to lowercase
   - One trailing-slash policy (with or without), enforced site-wide with
     301s, and matching canonicals/hreflang/internal links
   - One host: HTTPS only, www or non-www picked and enforced
4. **Parameters** — identify which parameters change content (page, filter)
   vs. which only track (utm, gclid). Tracking parameters must never
   appear in internal links or canonicals; filtered states need a
   deliberate index/noindex/canonical policy (coordinate with the
   crawl-budget skill).
5. **Breadcrumb alignment** — visible breadcrumbs mirror the URL path and
   use BreadcrumbList schema; mismatches signal architecture drift.
6. **When NOT to change URLs** — explicitly advise against renames when:
   - The URL ranks top 10 or has meaningful backlinks (verify with
     `ranked` / `backlinks` data)
   - The only gain is cosmetic
   - The site cannot guarantee clean 301s and full internal-link updates
   If change is justified, hand off to the redirect-analysis skill for the
   map.
7. **New-URL rules** — write the conventions for future URLs so the
   architecture stops degrading: pattern per page type, max slug length,
   stop-word policy, no dates in evergreen content URLs.

## Output

- Findings table: issue | example URLs | evidence | severity, each with a
  one-line "why"
- A written URL convention (the rules from step 7) the team can apply
- A short do-not-touch list of ranking/link-earning URLs
- Prioritized fixes (consistency enforcement first — cheap and safe)
- Single best next step: enforce the host/casing/trailing-slash policy
  site-wide

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
