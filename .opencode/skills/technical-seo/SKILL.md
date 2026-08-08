---
name: technical-seo
description: Technical SEO audit of crawlability, indexability, status codes, canonicals, robots directives, sitemap presence, HTTPS, hreflang, and rendering basics. Use when the user says technical SEO, crawl issues, indexation problems, or can't get indexed.
---

# Technical SEO

Diagnoses why search engines fail to crawl, render, or index a site.
Works from live fetches plus DataForSEO on-page/lighthouse data — never
assumes a cause without evidence.

## Inputs

- Required: domain or the specific URL(s) with problems
- Optional: the symptom (page not indexed, wrong URL ranking, traffic
  drop after migration), location/language from `seo-project.yml`

## Data pulls

```
python scripts/dfs_client.py onpage --url <url>
python scripts/dfs_client.py lighthouse --url <url>
```

Fetch directly: the page itself, `/robots.txt` and `/sitemap.xml`.
For protocol/host canonicalisation, use the no-follow trace — do **not**
infer the source status from a redirect-following fetch:

```
python scripts/site_crawler.py --url <canonical-url> --canonical-variants --pretty
```

Optional Google layer (real index status, only if configured):
`python scripts/google_client.py gsc-inspect --url <url> --site <site>`

## Process

1. **Crawlability** — robots.txt disallows covering the URL, meta robots /
   X-Robots-Tag directives, and whether CSS/JS assets are blocked (which
   breaks rendering even when the page itself is allowed).
2. **Status codes** — expect a clean 200. For every redirect claim, record
   requested URL, **initial** status, each Location target, final URL,
   final status and redirect count from `--canonical-variants` or
   `--trace-redirects`. A final 200 after a 301 is a working redirect, not
   a source URL serving 200. Flag chains (>1 hop), loops, missing Location
   headers, wrong final URLs, 4xx on linked pages and soft 404s.
3. **Indexability** — canonical present and consistent (delegate deep
   canonical work to `canonical-review`), no noindex conflicts, no
   parameter-generated duplicate sets.
4. **Delivery** — HTTPS everywhere with no mixed content; http and
   www/non-www variants 301 to one canonical host; record a separate
   medium-priority chain finding when a variant reaches that host in more
   than one hop. Sitemap declared in robots.txt and actually fetchable.
5. **International** — if hreflang is present, verify each annotation has
   a return link and a valid language/region code; x-default recommended.
6. **Rendering** — webfetch the HTML and look for an empty SPA shell
   (e.g. `<div id="root"></div>` with no text). If content only exists
   after JS execution, flag SSR/prerender/dynamic-rendering as the fix.
7. **Verify with Google (optional)** — gsc-inspect confirms whether
   Google actually indexes the URL and which canonical it selected.

## Output

Findings by category with the evidence for each (fetch result, API field,
or directive text), then recommendations ranked critical / high / medium /
low with a one-line "why" each, then the single best next step. Write
`TECHNICAL-SEO-<domain>-<date>.md` when the report exceeds ~15 findings;
chat stays at the summary plus the critical list.

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
