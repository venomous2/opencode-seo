---
name: site-audit
description: Atomic single-page or small-site SEO audit of metadata, headings, links, and indexability basics using webfetch and DataForSEO on-page data. Use when the user says audit this page, check this page SEO, on-page audit, or quick SEO check of a URL.
---

# Site Audit (Atomic)

Fast, self-contained audit of one URL — or a small set of pages (up to ~10).
This is the ATOMIC check. For a full multi-phase site audit with competitor
data and subagents, use the `workflow-site-audit` skill instead.

## Inputs

- Required: one URL (or a short list of URLs from the same site)
- Optional: the page's target keyword, location/language (defaults:
  United States / English, or the values in `seo-project.yml`)

## Data pulls

```
python scripts/dfs_client.py onpage --url <url>
python scripts/dfs_client.py lighthouse --url <url>   # only if speed is in scope
```

Also webfetch each URL to inspect the raw HTML directly. If DataForSEO
credentials are missing, run the HTML-only checks from webfetch and note
that API-backed fields are unavailable — do not invent values.

## Process

1. **Fetch** — webfetch the page. Record status code, title, meta
   description, canonical, meta robots, and the H1.
2. **Cross-check** — run `dfs_client.py onpage` and compare against what the
   HTML shows; mismatches (e.g. JS-injected titles) are findings.
3. **Indexability basics** — indexable status code (200), no `noindex` in
   meta robots or X-Robots-Tag, canonical present and sane.
4. **Metadata** — title ~50-60 chars, description ~150-160, both unique.
5. **Headings** — exactly one H1, logical H2/H3 nesting.
6. **Links** — count internal vs external links; flag broken anchors,
   empty anchor text, and pages with zero internal inlinks.
7. **Media** — images missing alt text; oversized hero images.
8. **Small-site mode** — with multiple URLs, also compare across pages:
   duplicate titles/descriptions/canonicals, conflicting H1s.

## Output

Findings table (check | result | evidence) followed by prioritized
recommendations (critical / high / medium / low), each with a one-line
"why", then the single best next step. For multi-page audits, write
`SITE-AUDIT-<domain>-<date>.md` with the full detail and keep the chat
reply to the top 10 items.
