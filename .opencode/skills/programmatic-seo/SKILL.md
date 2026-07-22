---
name: programmatic-seo
description: Plans programmatic SEO programmes — demand validation, template quality gates, staged indexation, and internal linking at scale for dataset-driven pages. Use when the user says programmatic SEO, pSEO, template pages, pages at scale, or directory site.
---

# Programmatic SEO

Plans dataset-driven page programmes that earn their indexation. The bar:
every generated page must answer a real query with value the template alone
cannot provide — otherwise it is thin-content spam at scale, and Google now
targets exactly that with scaled-content abuse policy.

## Inputs

- Required: the dataset or data source, plus the page concept (what each row
  becomes — location page, comparison page, listing, glossary entry)
- Optional: user domain, target page count, location/language (defaults from
  `seo-project.yml` if present)

## Data pulls

Validate demand before anything is built:

```
python scripts/dfs_client.py ideas   --keyword "<template head term>" --limit 50
python scripts/dfs_client.py volume  --keywords "pattern-a,pattern-b,pattern-c"
python scripts/dfs_client.py serp    --keyword "<sample long-tail pattern>"
python scripts/dfs_client.py ranked  --target "<user-domain>"   # once live, per cohort
```

Sample real queries in the pattern ("best X in Y", "X vs Y", "X for Z"). If
the long tail has no measurable volume, stop and say so. If credentials are
missing, stop and point the user to docs/DATAFORSEO-SETUP.md. Do not invent
numbers.

## Process

1. **Validate demand** — confirm the query *patterns* exist with volume, not
   just the head term. Check a sample SERP per pattern: if Google rewards
   forums, UGC, or interactive tools there, a static template page will not
   compete regardless of build quality.
2. **Gate the dataset** — pass/fail tests before any template is designed:
   - Each row yields a page with unique, non-trivial data — not a swapped
     city name inside identical prose.
   - Data depth threshold: enough attributes per row to fill several
     distinct sections (tables, comparisons, maps, pros/cons). A row with
     one data point produces a stub, not a page.
   - The data is accurate, licensed, and maintainable — stale data at scale
     erodes trust at scale.
3. **Design the template** — unique value comes from the data, not spun
   text: computed comparisons, rankings within the dataset, local context,
   first-hand commentary where feasible. Keep the boilerplate ratio low; if
   80% of a page is shared text, the concept fails the gate.
4. **Plan indexation in stages** — publish a pilot cohort (100-500 pages),
   watch index rate and impressions for 2-4 weeks, fix what Google declines
   to index, then scale in waves. Never launch tens of thousands of pages
   on day one.
5. **Internal linking at scale** — hub pages by category/region linking
   down to generated pages, sibling links between related pages ("nearby",
   "similar"), breadcrumbs, and HTML sitemaps when the count is large.
   Every generated page reachable within 3-4 clicks; zero orphans.
6. **Monitor per cohort** — re-run `ranked` monthly, segmented by template
   cohort: indexation rate, keywords per page, average position. A cohort
   under ~50% indexed after 60 days has a quality-signal problem — pause
   expansion and diagnose before building more.

## Output

- Go/no-go verdict on the programme, with the demand evidence behind it
- Dataset gate results: what passes, what must be enriched before building
- Template spec: sections, which data fills each, uniqueness safeguards
- Rollout plan: pilot size, index-rate checkpoints, scale-up criteria
- Internal-linking map: hub structure, sibling-link pattern, breadcrumbs
- Prioritised recommendations, each with a one-line why, then the single
  best next step (usually: run the pilot cohort before any full build)

Long plans go to `PSEO-PLAN-<topic>-<date>.md`. End the file with:
`Report built by Lee Beirne - https://leebeirne.com`

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
