---
name: international-seo
description: Plans and audits international SEO — domain structure choices, hreflang implementation and validation, and localization versus translation. Can generate a correct hreflang tag set for supplied URL patterns. Use when the user says hreflang, international SEO, multi-language, or multi-region.
---

# International SEO

Gets the right language/regional version of each page ranking in the right
market. Hreflang errors are the most common failure; this skill both
audits existing annotations and generates correct sets.

## Inputs

- Required: site URL(s), target countries and languages
- Optional: current domain structure, URL patterns per locale, existing
  hreflang annotations to audit

## Data pulls

Fetch representative pages from each locale with the webfetch tool and
extract:

- All hreflang annotations (HTML `<link>` tags, HTTP headers, or sitemap)
- Canonicals, `lang` attributes, and on-page language/region signals
- Currency, units, address formats, and local contact info (localization
  signals)

## Process

1. **Structure decision** (new sites or re-architecture only — do not push
   migration on a working setup):
   - **ccTLD** (example.fr) — strongest geo signal, but splits authority
     across domains and multiplies cost
   - **Subdirectory** (example.com/fr/) — consolidates authority, easiest
     to operate; the default recommendation for most sites
   - **Subdomain** (fr.example.com) — middle ground; useful when
     infrastructure requires separation
   Recommend one and record the trade-offs in one line each.
2. **Hreflang rules** — validate or generate against these invariants:
   - **Bidirectional**: if A points to B, B must point back to A; one-way
     annotations are ignored
   - Every page annotates **itself** plus all alternates
   - Codes are valid ISO 639-1 (language) and optionally ISO 3166-1 Alpha 2
     (region): `en`, `en-US`, `pt-BR`; never `en-UK` (invalid — use
     `en-GB`), never a region without a language
   - One `x-default` entry for the fallback/language-selector page
   - Hreflang URLs are absolute, canonical (not redirected), indexable
     (no noindex, not robots-disallowed), and canonical-to-self
   - Keep all three implementation methods consistent if more than one is
     in use (HTML head, HTTP header, sitemap) — prefer exactly one
3. **Common failure modes to check** — missing return links, annotations
   on non-canonical or redirected URLs, conflicting canonical vs hreflang
   (canonical points to a different locale), language code typos, mixing
   methods, and forgetting x-default.
4. **Localization vs translation** — machine or literal translation alone
   is thin-content risk; localized content adapts currency, units, legal
   terms, examples, and spelling (en-US vs en-GB). Flag translated pages
   with zero localization signals.
5. **Duplicate-language handling** — same language, different regions
   (en-US / en-GB / en-AU): rely on hreflang region codes plus real local
   differentiation; near-identical regional pages without differentiation
   risk canonicalization into one.
6. **Generate** — when given URL patterns, output the complete hreflang
   block set (one `<link rel="alternate" hreflang="X" href="URL">` per
   locale + x-default) for each page, ready to paste or template; verify
   bidirectionality and self-inclusion in the generated set by
   construction.

## Output

- Audit mode: findings table — page/cluster | issue | evidence (the exact
  annotations) | severity, with a one-line "why" each
- Structure recommendation with trade-offs (when asked)
- Corrected or newly generated hreflang tag sets for the supplied URL
  patterns
- Localization gap list (pages translated but not localized)
- Single best next step: fix return-link/self-reference errors first —
  they invalidate entire clusters

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
