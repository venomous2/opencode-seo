---
name: mobile-seo
description: Reviews a site against mobile-first indexing — content parity, viewport configuration, tap targets, font sizes, intrusive interstitials, and mobile Core Web Vitals. Use when the user says mobile SEO, mobile friendly, or mobile-first indexing.
---

# Mobile SEO

Google indexes the mobile version of the site (mobile-first indexing):
content, links, structured data, and metadata that exist only on desktop
effectively do not exist. This review verifies parity and mobile usability.

## Inputs

- Required: site URL (and whether mobile is responsive, dynamic serving,
  or a separate m. subdomain)
- Optional: key templates to check first

## Data pulls

Fetch pages with the webfetch tool (which retrieves a desktop-style view)
and compare against the mobile experience. Record from the served HTML:

- `<meta name="viewport">` presence and value
  (`width=device-width, initial-scale=1` expected; flag `user-scalable=no`
  and fixed-width viewports)
- Responsive images (`srcset`), media queries in CSS, fixed-width elements

Optional mobile field and lab data:

```
python scripts/google_client.py pagespeed --url https://example.com/page --strategy mobile
python scripts/google_client.py crux --target https://example.com --origin --form-factor PHONE
python scripts/dfs_client.py lighthouse --url https://example.com/page --pretty
```

For separate m. sites or dynamic serving, also check: correct
`rel="alternate"`/`rel="canonical"` pairings between desktop and mobile
URLs, and Vary: User-Agent on dynamic serving. Never fabricate scores.

## Process

1. **Parity audit** — compare mobile vs desktop for: primary content,
   internal links (including nav and footer), structured data, meta robots,
   canonicals, hreflang, images and videos, and lazy-loaded content that
   requires interaction (Googlebot does not scroll, tap, or click — content
   behind tabs/accordions must still be in the DOM).
2. **Viewport and rendering** — correct viewport meta; no content wider
   than the screen; CSS uses relative units; no horizontal scrolling.
3. **Tap targets and readability** — tap targets at least ~48px with
   adequate spacing; base font at least 16px; sufficient contrast; no
   pinch-zoom disabled.
4. **Interstitials** — flag intrusive interstitials on the transition from
   search results: full-page app-install banners, newsletter popups
   covering main content, forced age gates without main content visible.
   Small banners and legally required notices (cookie consent, age
   verification done compactly) are acceptable.
5. **Mobile CWV** — evaluate mobile field data (crux PHONE) against
   thresholds (LCP <2.5s, INP <200ms, CLS <0.1); mobile networks and CPUs
   make failures far more common than on desktop. For deep diagnosis hand
   off to the core-web-vitals skill.
6. **Separate-config checks** — m. subdomains need bidirectional
   annotations (desktop `rel="alternate"` -> mobile; mobile canonical ->
   desktop), identical structured data on both, and mobile 200-status
   parity for every desktop URL (no blanket m. homepage redirects).

## Output

- Findings table: check | status (pass/fail/risk) | evidence | severity,
  each with a one-line "why"
- Parity gap list (content/links/schema present on desktop, missing on
  mobile) — the highest-stakes section under mobile-first indexing
- Usability fixes (tap targets, font, interstitials) in priority order
- Mobile CWV snapshot from field data when available
- Single best next step: close the worst parity gap or fix the viewport,
  whichever fails

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
