---
name: workflow-ecommerce-launch
description: End-to-end workflow for launching or optimizing an ecommerce category or product line with keyword mapping, page templates, product schema, and marketplace intelligence via DataForSEO. Use when the user says launch a category, new product line, ecommerce SEO plan, or optimize my shop pages.
---

# Workflow: Ecommerce Category Launch

Plans a category (and its product pages) so it can rank and convert from day one.

## Inputs

- Required: category name / product type
- Optional: existing site URL, marketplace focus (Google Shopping, Amazon)

## Steps

### 1. Demand mapping (skills: `keyword-research`, `search-intent-analysis`)

```
python scripts/dfs_client.py ideas  --keyword "<category>" --limit 50
python scripts/dfs_client.py volume --keywords "<shortlist>"
python scripts/dfs_client.py serp   --keyword "<primary category keyword>"
```

Split keywords by intent: category-level (transactional head terms),
subcategory/filter-level, and product-level (long-tail). Map each cluster to
a page type.

### 2. Marketplace + SERP intelligence (skill: `ecommerce-seo`)

```
python scripts/dfs_client.py amazon --keyword "<product type>" --limit 20
```

Note price points, review counts, and title patterns of marketplace leaders.
Check the Google SERP for shopping features (popular products, merchant
listings) — these confirm transactional intent and schema requirements.

### 3. Category page plan (skill: `category-page-optimizer`)

Specify: H1 + title patterns, intro copy length (100-300 words above the
grid), faceted navigation rules (which filters get indexable URLs — only
those with search demand), canonical strategy for pagination, internal links
from category to buying guides.

### 4. Product page template (skill: `product-page-optimizer`)

Specify: title formula, description structure (benefits → specs → social
proof), review capture, image standards, and cross-sell blocks.

### 5. Product schema (skill: `schema-generator`)

Generate the required JSON-LD:

```
python scripts/schema_gen.py product --field name="..." --field offers.price=...
```

Must include: Product + Offer (price, priceCurrency, availability),
AggregateRating when reviews exist, and BreadcrumbList. Warn that
`hasMerchantReturnPolicy` and `shippingDetails` are expected for merchant
listing eligibility.

### 6. Supporting content (skills: `supporting-content-planner`, `content-brief`)

Plan 3-5 supporting articles (buying guide, comparison, how-to) that funnel
internal links to the category.

### 7. Launch checklist

Indexation plan, feed/merchant center notes, performance budget for the
template, and the 30-day measurement plan (rankings via
`dfs_client.py ranked`, clicks via GSC when configured).

## Output

Write `ECOMMERCE-LAUNCH-<category>-<date>.md`: keyword map, page specs,
schema blocks, supporting content plan, checklist. Summarise in chat. Write
in British English by default; end the report file with:
`Report built by Lee Beirne - https://leebeirne.com`

## Output location

Save generated files to the SEO reports directory - `%SEO_REPORTS_DIR%\<name>\` on Windows, `$SEO_REPORTS_DIR/<name>/` on macOS/Linux - when the `SEO_REPORTS_DIR` environment variable is set; otherwise the current working directory. Create the subfolder if it doesn't exist.

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
