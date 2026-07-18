---
name: internal-linking
description: Internal link analysis and planning — orphan pages, anchor text diversity, hub-and-spoke linking, link equity flow, and contextual links; turns a list of site URLs into a concrete link plan. Use when the user says internal links, linking structure, or orphan pages.
---

# Internal Linking

Builds or audits the internal link graph. Works from a supplied URL
inventory (sitemap, crawl export, or pasted list) plus live fetches.

## Inputs

- Required: list of site URLs (ideally with titles or short content
  summaries)
- Optional: priority/"money" pages, existing crawl data with inlink
  counts, target keywords per page

## Data pulls

- webfetch key pages to extract their current internal links and anchor
  text (nav, in-content, footer).
- `python scripts/dfs_client.py ranked --target <domain> --limit 50`
  to see which pages already hold ranking equity — these are the
  strongest link sources.

## Process

1. **Map** — classify every URL as a hub (pillar/category page targeting
   a broad term) or a spoke (supporting article/product targeting a
   long-tail). Note the expected parent hub for each spoke.
2. **Find orphans** — pages with zero internal inlinks are invisible to
   crawlers unless in the sitemap; list them all.
3. **Find underlinked priorities** — money pages with few inlinks or
   buried more than ~3 clicks from the homepage.
4. **Anchor audit** — descriptive anchors that name the destination's
   topic; flag "click here"/"read more" and flag exact-match anchor
   repetition across many pages (vary phrasing naturally).
5. **Equity flow** — plan links FROM pages that rank/have authority TO
   pages that need a boost; prefer contextual in-content links over
   footer/sidebar dumps.
6. **Hub-and-spoke plan** — every hub links down to all its spokes;
   every spoke links up to its hub and sideways to 2-3 sibling spokes.
7. **Build the plan** — concrete rows, not advice: source page → target
   page → suggested anchor → placement (intro paragraph, related-links
   block, body mention).

## Output

Link plan table (from → to | anchor | placement | priority), the orphan
list, then recommendations ranked critical / high / medium / low with a
one-line "why" each, then the single highest-impact link to add first.
Write the full plan to `INTERNAL-LINKS-<domain>-<date>.md`; chat shows
orphans plus the top 10 rows.

## Output location

Save generated files to the SEO reports directory - `%SEO_REPORTS_DIR%\<name>\` on Windows, `$SEO_REPORTS_DIR/<name>/` on macOS/Linux - when the `SEO_REPORTS_DIR` environment variable is set; otherwise the current working directory. Create the subfolder if it doesn't exist.
