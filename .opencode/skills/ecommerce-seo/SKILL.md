---
name: ecommerce-seo
description: Plans an ecommerce SEO program covering catalog architecture, faceted navigation, product/category page standards, Product schema, and marketplace context. Use when the user says ecommerce SEO, shop SEO, online store SEO, or SEO for a product catalog.
---

# Ecommerce SEO

Designs the organic program for an online store: crawlable catalog
architecture, disciplined faceted navigation, page-level standards, rich
results eligibility, and marketplace awareness.

## Inputs

- Required: store domain
- Optional: platform (Shopify, WooCommerce, Magento, custom), priority
  categories, location/language (defaults from `seo-project.yml` via
  `python scripts/project_memory.py`)

## Data pulls

```
python scripts/dfs_client.py ranked   --target "<domain>" --limit 200
python scripts/dfs_client.py onpage   --url "<key category URL>"
python scripts/dfs_client.py serp     --keyword "<priority category keyword>" --limit 20
python scripts/dfs_client.py amazon   --keyword "<flagship product>" --limit 20
```

Webfetch the homepage, one category page, and one product page to inspect
templates, schema presence, and rendering. If credentials are missing, stop
and point the user to docs/DATAFORSEO-SETUP.md. Do not invent numbers.

## Process

1. **Architecture** — flat, crawlable catalog: home → category →
   (subcategory) → product, every product reachable in ≤3 clicks. Breadcrumbs
   everywhere (plus BreadcrumbList schema). One canonical URL per product
   even if it appears in multiple categories.
2. **Faceted navigation rules** — the classic ecommerce SEO failure. Default
   stance: filters are crawlable but **noindexed** (or blocked via
   robots/parameter handling) with canonicals to the parent category.
   Exception: a facet combination earns its own static, indexable page ONLY
   when it has proven search demand — verify with
   `python scripts/dfs_client.py volume --keywords "red running shoes,..."`.
   Everything else stays noindex to prevent crawl-budget burn and duplicate
   thin pages.
3. **Category page standards** — unique H1/title matching search language,
   short intro copy, links to subcategories and buying guides, paginated
   series handled with self-canonicals and crawlable links.
4. **Product page standards** — unique descriptions (never manufacturer
   boilerplate — it duplicates every other retailer), review capture,
   descriptive image alt text, stock/price kept current.
5. **Schema requirements** — every product page needs Product markup with
   offers (price, priceCurrency, availability), and Google now expects
   merchant return policy and shipping details for full rich-result
   eligibility. Generate with:
   `python scripts/schema_gen.py product --field name="..." --script-tag` and
   `python scripts/schema_gen.py offer --field price="..." --field availability="InStock"`.
6. **Marketplace context** — from the `amazon` pull: which products compete
   with Amazon listings on price/reviews, and which keywords Amazon owns in
   the SERP. Where Amazon dominates, differentiate on content, expertise,
   and long-tail variants instead of head terms.

## Output

- Architecture assessment + facet rule table (facet → index/noindex → why)
- Page-standard checklists for category and product templates
- Schema snippets to deploy (product, offer, breadcrumblist)
- Marketplace reality check from Amazon data
- Prioritized recommendation list with one-line why each + single best next
  step

Full program detail goes to `ECOMMERCE-SEO-<domain>-<date>.md`.
