---
name: javascript-seo
description: Audits JavaScript rendering risks for SEO — SPA shells, client-side-rendered content, hydration pitfalls — and recommends SSR, SSG, or prerendering where needed. Use when the user says JavaScript SEO, React SEO, Next.js SEO, or rendering.
---

# JavaScript SEO

Determines what of a page's content, links, and metadata actually exists
in the served HTML versus what only appears after JavaScript executes.
Google renders JS in a deferred second wave — content that needs
client-side rendering can be indexed late, incompletely, or not at all.

## Inputs

- Required: target URL (or a set of representative templates: home,
  listing, detail)
- Optional: framework if known (React, Vue, Angular, Next.js, Nuxt)

## Data pulls

Fetch the raw served HTML with the webfetch tool — this is the pre-render
view, equivalent to view-source. Record:

- Whether `<body>` contains real content or an empty shell
  (`<div id="root"></div>`, `<div id="app"></div>` with nothing inside)
- Title, meta description, canonical, hreflang, robots meta in served HTML
- Links: real `<a href>` in HTML vs links injected by JS on click
- Structured data present in served HTML vs injected client-side

Optional confirmation of what Google indexed:

```
python scripts/google_client.py gsc-inspect --url U --site S
```

(`gsc-inspect` shows Google's indexed view; compare it against the raw
fetch. A screenshot/diff of raw vs rendered DOM can be done locally with a
headless browser if one is available.)

## Process

1. **Detect the shell** — empty `div#root`/`div#app` with content only
   arriving via JS means a pure client-side-rendered SPA. Confirm by
   checking whether key text from the visible page appears in the raw HTML.
2. **Inventory what is missing pre-render** — headings, body copy, internal
   links, images (`src` vs lazy placeholders), meta tags, structured data.
   Anything business-critical that is absent from served HTML is a risk.
3. **Check link crawlability** — JS-only navigation (`onClick` + router
   push without `<a href>`) blocks PageRank flow and discovery of deep
   pages. Pagination done purely in JS hides page 2+ from crawlers.
4. **Hydration pitfalls** — content flicker/swap after hydration can cause
   CLS; hydration errors can blank content for the renderer; large bundles
   inflate INP. Note bundle size from the served script tags.
5. **Recommend the right rendering strategy**, in order of preference:
   - **SSG** (static generation) for content that rarely changes
   - **SSR** for dynamic, personalized, or frequently updated pages
   - **Prerendering** (static snapshot for crawlers) as a pragmatic bridge
     for existing SPAs that cannot be re-architected now
   - Pure CSR only for content behind logins or with no SEO value
6. **Verify the fix** — after changes, re-fetch raw HTML and confirm the
   critical content and links are now present pre-render; re-run
   `gsc-inspect` after Google recrawls.

## Output

- Findings: what is in served HTML vs JS-only, with evidence (the exact
  missing elements/links)
- Risk rating per finding (content invisible / links uncrawlable / metadata
  client-injected) with a one-line "why" each
- Rendering-strategy recommendation matched to the site's stack and
  constraints
- Single best next step: the smallest change that gets critical content
  into the served HTML
