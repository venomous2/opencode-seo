---
name: schema-generator
description: Generates JSON-LD structured data for a page by choosing the right schema.org types, gathering properties from the page content, and emitting markup via schema_gen.py. Use when the user says schema, structured data, JSON-LD, generate schema, or rich results.
---

# Schema Generator

Produces valid JSON-LD for a page. Every property value comes from the page
or the user — never invent prices, ratings, dates, or author names.

## Inputs

- Required: target URL or pasted page content, plus page purpose (article,
  product, local business, FAQ, etc.) if not obvious
- Optional: property values the user wants included (price, rating, dates)

## Data pulls

Fetch the page with the webfetch tool and extract real values:

- Page title, meta description, canonical URL, publish/modified dates
- Author name, organization name, logo URL
- Product price/currency/availability, review ratings, business address

If a value needed for a required property is not on the page, ask the user
for it instead of guessing.

## Process

1. **Classify** — pick the most specific applicable type. One primary type
   per page; add secondary types only when the content genuinely supports
   them (e.g. `article` + `breadcrumblist`, `product` + `offer`).
2. **Map properties** — required properties first (per Google Search
   Central's structured data gallery), then recommended ones that have real
   values on the page. Skip properties with no trustworthy value.
3. **Generate** — run the CLI, using dot notation for nesting and commas
   for arrays:

   ```
   python scripts/schema_gen.py article --field headline="..." --field author.name="Jane Doe"
   python scripts/schema_gen.py product --field name="..." --field offers.price=29.99 --field offers.priceCurrency=USD
   python scripts/schema_gen.py breadcrumblist --field itemListElement="Home,https://ex.com/,Products,https://ex.com/p/"
   ```

   Add `--script-tag` to get a ready-to-paste `<script type="application/ld+json">` block.
4. **Combine** — when emitting multiple blocks for one page, keep them as
   separate JSON-LD script tags or a single `@graph`; cross-reference with
   `@id` (e.g. the webpage's `mainEntity` pointing at the product).
5. **Advise placement** — JSON-LD goes in the `<head>` (Google also reads
   it from `<body>`, but `<head>` is the convention). One source of truth:
   do not duplicate the same entity in both JSON-LD and microdata.
6. **Set expectations** — structured data makes a page *eligible* for rich
   results; it does not guarantee them. Note any types that no longer earn
   rich results (HowTo removed 2023, FAQ restricted to authoritative
   government/health sites since August 2023) so the user does not add
   markup expecting a payoff that no longer exists.

## Output

- The JSON-LD block(s), ready to paste, with `--script-tag` output
- A property table: property | value | source (page / user) — so the user
  can verify every value is real
- Notes on which rich-result types the page is now eligible for, and which
  recommended properties were skipped for lack of data
- Single best next step: paste into `<head>`, then validate with the
  schema-validator skill or Google's Rich Results Test
