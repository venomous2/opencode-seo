---
name: sitemap-builder
description: XML sitemap generation and audit — accepts a list of URLs or crawled pages and writes a valid urlset XML file to disk, with lastmod/changefreq/priority guidance, sitemap indexes for over 50k URLs, and image sitemap basics. Use when the user says sitemap, XML sitemap, or generate sitemap.
---

# Sitemap Builder

Generates valid XML sitemaps from a supplied URL list, or audits an
existing one. Output is a real file written to disk.

## Inputs

- Required: list of URLs (pasted, from a file, or from a crawl/export),
  OR a domain whose existing sitemap should be audited
- Optional: lastmod dates per URL, images per URL for image entries,
  preferred output filename (default `sitemap.xml`)

## Data pulls

- Audit mode: webfetch `/sitemap.xml` (and `/robots.txt` to find the
  declared sitemap location).
- Generation mode: webfetch a sample of the supplied URLs to confirm
  they return 200 and are indexable before including them.

## Process

1. **Clean the URL set** — include only canonical, indexable, 200-status
   HTML pages. Drop: redirects, 404s, noindexed pages, URLs that
   canonicalize elsewhere, non-HTML assets, and duplicates. A sitemap
   full of junk trains Google to distrust it.
2. **Build the XML** — write a valid `<urlset>` (xmlns
   `http://www.sitemaps.org/schemas/sitemap/0.9`) to disk. `<loc>` is
   required and must be absolute; everything else is optional.
3. **Field guidance** —
   - `<lastmod>`: include ONLY with real modification dates; a wrong or
     auto-stamped lastmod is worse than omitting it (Google ignores
     lastmod it considers unreliable).
   - `<changefreq>` and `<priority>`: ignored by Google; include only
     if the user asks — never present them as ranking levers.
4. **Scale** — above 50,000 URLs or 50MB uncompressed, split into child
   sitemaps (by section or date) and write a `<sitemapindex>` file as
   the entry point.
5. **Image entries** — when image discovery matters (galleries,
   products), add the image namespace and `<image:image>`/`<image:loc>`
   entries per page; keep it to the page's primary images.
6. **Audit mode** — check an existing sitemap for: junk URLs (step 1),
   lastmod accuracy, size/count limits, consistency with robots.txt
   (declared?) and with on-page canonicals (sitemap URL = canonical
   URL?).
7. **Next step** — advise submitting the sitemap in Search Console and
   referencing it in robots.txt.

## Output

The generated XML file path (or audit findings with sample offending
lines as evidence), then recommendations ranked critical / high /
medium / low with a one-line "why" each, then the single best next
step. Long audit details go to `SITEMAP-AUDIT-<domain>-<date>.md`;
chat stays to the file path plus the key decisions made.

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
