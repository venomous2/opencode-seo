---
name: product-page-optimizer
description: Optimizes a single product page — title formula, unique copy, reviews, images, Product+Offer schema, cross-sells, and UGC. Use when the user says product page, optimize product page, or improve a product listing.
---

# Product Page Optimizer

Turns one product page into its best ranking and converting self, using
live SERP data for the target query and the page's actual markup.

## Inputs

- Required: product page URL
- Optional: target keyword (else derived from page content), competitor
  product URLs

## Data pulls

```
python scripts/dfs_client.py onpage --url "<product URL>"
python scripts/dfs_client.py serp   --keyword "<target keyword>" --limit 20
python scripts/dfs_client.py volume --keywords "<target keyword>,<variant keyword>"
```

Webfetch the product URL and 1-2 top-ranking competitor product pages from
the SERP. If credentials are missing, stop and point the user to
docs/DATAFORSEO-SETUP.md. Do not invent numbers.

## Process

1. **Title & H1** — formula: `[Brand] [Product Name] — [key attribute or
   use case]`. Match the language searchers use (check SERP titles of
   ranking pages), keep under ~60 characters where possible, unique across
   the catalog.
2. **Description quality** — read the fetched copy. If it's manufacturer
   boilerplate (identical to other retailers — the SERP makes this obvious),
   flag as the top fix: rewrite for the buyer's questions — fit, use cases,
   materials, compatibility, care. Structure: scannable spec block +
   benefit-led prose.
3. **Schema** — check the `onpage` output for existing markup; generate
   what's missing:
   ```
   python scripts/schema_gen.py product --field name="..." --field image="..." --field description="..." --script-tag
   python scripts/schema_gen.py offer   --field price="..." --field priceCurrency="USD" --field availability="InStock"
   python scripts/schema_gen.py aggregaterating --field ratingValue="..." --field reviewCount="..."
   ```
   Include merchant return policy and shipping details — required for full
   Google shopping rich-result eligibility.
4. **Reviews & UGC** — review capture mechanism present? Reviews rendered in
   HTML (not JS-only)? Photo reviews and Q&A sections add unique,
   self-refreshing content competitors can't copy.
5. **Images** — multiple angles + in-context shots, descriptive file names
   and alt text (`brand-product-color-angle.jpg`), compressed modern formats,
   dimensions set to avoid CLS.
6. **Cross-sells & internal links** — related products, accessories,
   "complete the look/kit", and links from relevant buying guides. These
   spread authority and lift average order value.
7. **Trust elements** — stock status, delivery estimate, returns summary,
   warranty near the buy button; they also feed schema fields.

## Output

- Element scorecard: title | description | schema | reviews | images |
  cross-sells | trust — each pass/gap with evidence
- Rewritten title and meta description proposals
- Ready-to-paste schema JSON-LD blocks
- Fix list ordered by impact with one-line why each
- Single best next step
