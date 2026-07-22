---
name: seo-checklist-generator
description: Generates role-specific SEO checklists — pre-publish, launch, migration, quarterly review — tailored to the site type from project memory. Use when the user says SEO checklist, pre-publish checklist, launch checklist, or migration checklist.
---

# SEO Checklist Generator

Produces a concrete, role-tagged checklist for a recurring SEO moment,
tailored to the actual site — not a generic list copied from a blog.

## Inputs

- Required: checklist type — one of: **pre-publish** (new content going
  live), **launch** (new site/section), **migration** (domain/platform/
  structure change), **quarterly** (periodic health review)
- Optional: site type (else from `seo-project.yml` via
  `python scripts/project_memory.py` — ecommerce, local, SaaS, publisher),
  CMS/platform, roles on the team

## Process

1. **Load context** — read project memory for site type, competitors, and
   past issues. A checklist for a Shopify store differs from one for a
   WordPress publisher; tailor, don't generalize.
2. **Select the base list** for the requested type:
   - *Pre-publish*: keyword target mapped, title/meta unique, H1 + heading
     hierarchy, intent match vs live SERP, internal links in and out, image
     alt text and compression, schema where relevant, canonical correct,
     mobile rendering, proofread + E-E-A-T signals (author, sources, dates).
   - *Launch*: everything in pre-publish plus — robots.txt and meta robots
     audit (no leftover noindex from staging), XML sitemap generated and
     submitted, analytics/Search Console verified, 301 map from any old
     URLs, 404 page, CWV baseline, staging access blocked.
   - *Migration*: full redirect map (old→new, one-to-one, 301), redirect
     testing plan, pre/post crawl comparison, canonical and hreflang
     updates, sitemap swap, GBP/citation NAP updates if domain changed,
     rankings baseline before cutover, daily monitoring for 2 weeks post
     (via `python scripts/dfs_client.py ranked --target <domain>`).
   - *Quarterly*: rankings movement review, striking-distance refresh list,
     new keyword-gap pull vs competitors, broken-link and redirect-chain
     sweep, CWV re-check, indexation coverage review, content decay audit
     (pages losing traffic), schema validation.
3. **Tag every item with a role** — [SEO], [Dev], [Content], [Design],
   [Client]. Nobody acts on orphan checkboxes.
4. **Add verification where data applies** — attach the exact check command
   to items that can be machine-verified (e.g., sitemap validity, onpage
   re-crawl, ranked-position movement) so "done" is provable.
5. **Order by execution sequence** — the checklist must be runnable
   top-to-bottom, dependencies first.

## Output

A markdown checklist grouped by phase/section:

```
## <Section>
- [ ] <task> — [Role] — verify: <command or check, if applicable>
```

Followed by:
- Items flagged as launch-blockers (vs nice-to-haves)
- The 3 items most commonly missed for this site type
- Single best next step

Write the checklist to `CHECKLIST-<type>-<domain>-<date>.md` when it exceeds
~40 items.

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
