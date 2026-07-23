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

Deterministic, zero-dependency render tooling (use these FIRST):

```
python scripts/spa_detect.py --url <url> --pretty
```

`spa_detect` scores SPA signals (empty root shells, framework markers,
text/markup ratio) and returns a verdict: `spa` / `maybe` / `static` with
evidence per signal. Static pages skip rendering entirely — fast and free.

```
python scripts/render_page.py --url <url> --diff
```

`render_page` renders the page in the local headless browser (Edge/Chrome
`--dump-dom` with a virtual-time budget — no new dependencies; falls back
to DataForSEO JS rendering if no browser is present). `--diff` produces
the **rendered-vs-source gap**: word counts, links, schema blocks, title
changes, and the `js_content_ratio`. A ratio ≥ 1.5 means raw-HTML analysis
(and some crawlers) miss a third or more of the content.

```
python scripts/seo_lint.py --url <url> --render auto --format text
```

`--render auto` runs spa_detect first and only renders when needed
(`always` forces, `never` = raw). The full rule engine then runs on the
rendered DOM, including the `js-content-gap` rule.

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

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
