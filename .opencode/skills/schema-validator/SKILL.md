---
name: schema-validator
description: Audits a page's existing structured data for syntax errors, missing required or recommended properties, deprecated types, and conflicts between blocks. Use when the user says validate schema, schema errors, structured data audit, or check my markup.
---

# Schema Validator

Fetches a page and audits every structured-data block it finds: JSON-LD,
microdata, and RDFa. Findings cite the exact block and property.

## Inputs

- Required: target URL (or pasted HTML)
- Optional: expected type ("this should be a Product page") to check the
  markup matches intent

## Data pulls

Fetch the page HTML with the webfetch tool, then extract:

Rules before you conclude anything:
- **Verify the URL exists first** (status 200). A 404 on a guessed path is
  not evidence of missing schema — confirm the real page URL from the
  site's sitemap.xml or navigation before auditing it.
- **Raw HTML may not be the whole story.** If no JSON-LD is visible in the
  raw fetch, check whether the site injects it via JavaScript before
  reporting "no schema": verify with
  `python scripts/dfs_client.py onpage --url <url>` (JS rendering enabled)
  or ask the user to confirm how their schema is deployed. Report what you
  verified, and how — never "no schema" from a single raw fetch.

- All `<script type="application/ld+json">` blocks (there may be several)
- Microdata (`itemscope`/`itemtype`/`itemprop`) and RDFa attributes
- The rendered DOM is not needed — validate what is served in the HTML,
  since that is what crawlers parse most reliably

Optionally confirm indexing status with
`python scripts/google_client.py gsc-inspect --url U --site S` when the
Google layer is configured.

## Process

1. **Syntax** — parse each JSON-LD block as JSON. Flag trailing commas,
   unquoted keys, HTML entities inside strings, and multiple JSON objects
   in one script tag without an array or `@graph`.
2. **Type checks** — for each detected `@type`, verify required properties
   per Google's structured data documentation, then recommended ones.
   Report missing required as errors, missing recommended as warnings.
3. **Value sanity** — dates in ISO 8601, URLs absolute, `priceCurrency` a
   valid ISO 4217 code, ratings within `bestRating`/`worstRating` bounds,
   image URLs fetchable (not 404, not relative).
4. **Deprecation and policy flags** — warn when:
   - `HowTo` markup is used for rich results (Google removed HowTo rich
     results in 2023; markup is harmless but earns nothing)
   - `FAQPage` appears on a page that is not an authoritative government
     or health site (FAQ rich results restricted August 2023)
   - Review snippets are self-serving (`review`/`aggregateRating` about the
     site's own Organization/LocalBusiness — ineligible)
5. **Conflicts** — same entity described in two blocks with different
   values (e.g. two `Product` blocks with different prices), JSON-LD
   contradicting microdata, or markup contradicting visible page content.
6. **Eligibility** — state which rich-result types the current markup can
   actually earn, and what is blocking eligibility.

## Output

- Findings table: block # / type | severity (error/warning/info) | issue |
  exact property path | evidence
- Prioritized fixes, each with a one-line "why" (required for eligibility,
  deprecated, conflicting, etc.)
- Corrected JSON-LD for blocks with errors (regenerate with
  `python scripts/schema_gen.py <type> --field key=value` when useful)
- Single best next step: fix the highest-severity error, then re-run this
  validator and confirm in Google's Rich Results Test

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
