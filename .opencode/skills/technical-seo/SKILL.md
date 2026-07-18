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

webfetch these directly: the page itself, `/robots.txt`, `/sitemap.xml`,
and any redirecting variant (http://, www/non-www).

Optional Google layer (real index status, only if configured):
`python scripts/google_client.py gsc-inspect --url <url> --site <site>`

## Process

1. **Crawlability** — robots.txt disallows covering the URL, meta robots /
   X-Robots-Tag directives, and whether CSS/JS assets are blocked (which
   breaks rendering even when the page itself is allowed).
2. **Status codes** — expect a clean 200. Map redirect chains (more than
   one hop wastes crawl budget), 4xx on linked pages, and soft 404s
   (200 status with an error page body).
3. **Indexability** — canonical present and consistent (delegate deep
   canonical work to `canonical-review`), no noindex conflicts, no
   parameter-generated duplicate sets.
4. **Delivery** — HTTPS everywhere with no mixed content; http and
   www/non-www variants 301 to one canonical host; sitemap declared in
   robots.txt and actually fetchable.
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
