---
name: robots-advisor
description: robots.txt and meta robots authoring and audit — Disallow vs noindex semantics, AI crawler rules (GPTBot, ClaudeBot, PerplexityBot, Google-Extended) with blocking trade-offs, and sitemap directives. Use when the user says robots.txt, robots meta, block crawlers, or AI crawlers.
---

# Robots Advisor

Writes and audits robots.txt and meta robots directives. The core mental
model: robots.txt controls CRAWLING, meta robots controls INDEXING —
they are not interchangeable.

## Inputs

- Required: domain to audit, OR a stack description to generate for
  (CMS/framework, paths to protect)
- Optional: the user's stance on AI crawlers (allow all / block training
  crawlers / block all AI bots)

## Data pulls

- webfetch `/robots.txt` and `/sitemap.xml`.
- webfetch a sample of pages to check for meta robots and X-Robots-Tag
  conflicts with the robots.txt rules.

## Process

1. **Audit semantics** — the classic bug: a URL both Disallowed AND
   noindexed. A blocked crawler never fetches the page, so it never sees
   the noindex — the URL can still appear in results as a bare link.
   Rule: to keep a URL out of the index, allow crawling and use
   `noindex` in meta robots or X-Robots-Tag; use Disallow only for
   crawl-budget control and endless spaces (faceted combos, calendars,
   internal search).
2. **Trap check** — wildcards or broad disallows accidentally blocking
   CSS/JS (breaks rendering sitewide) or whole sections that should rank.
3. **Sitemap directive** — robots.txt should declare
   `Sitemap: https://<domain>/sitemap.xml`; flag if absent.
4. **AI crawlers** — present the trade-off plainly and let the user
   decide before writing rules:
   - Blocking GPTBot, ClaudeBot, PerplexityBot, or Google-Extended
     limits use of content for training/answers — but forfeits AI-search
     citations and visibility in those products.
   - Google-Extended does NOT affect classic Google Search ranking.
   - Blocking via robots.txt is a request; well-behaved bots honor it.
5. **Generate** — base template: `User-agent: *` + `Allow: /` + the
   sitemap line, then stack-appropriate disallows (WordPress: `/wp-admin/`
   with an admin-ajax allowance; Shopify: cart/checkout/search;
   staging: full disallow PLUS noindex). Write the file to disk as
   `robots.txt` when asked.
6. **Per-page directives** — recommend meta robots / X-Robots-Tag for
   page-level control (noindex thank-you pages, noarchive where needed).

## Output

Audit findings with the exact directive lines as evidence, or the
generated robots.txt file, then recommendations ranked critical / high /
medium / low with a one-line "why" each, then the single best next step.

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
