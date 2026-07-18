---
name: core-web-vitals
description: Diagnoses Core Web Vitals problems (LCP, INP, CLS) using field data from CrUX and lab data from Lighthouse, then maps each failing metric to concrete fixes. Use when the user says Core Web Vitals, CWV, LCP, INP, CLS, or page speed.
---

# Core Web Vitals

Diagnoses the three current Core Web Vitals against Google's thresholds:

- **LCP** (Largest Contentful Paint): good < 2.5s
- **INP** (Interaction to Next Paint): good < 200ms — replaced FID in
  March 2024; never report FID as a current metric
- **CLS** (Cumulative Layout Shift): good < 0.1

Field (CrUX) data is the ranking signal; lab (Lighthouse) data is the
diagnostic tool. Never treat a lab score alone as pass/fail.

## Inputs

- Required: target URL or origin
- Optional: form factor (mobile is the default concern — mobile-first
  indexing), competitor URLs for comparison

## Data pulls

Field data (optional Google layer, when configured):

```
python scripts/google_client.py crux --target https://example.com --origin --form-factor PHONE
python scripts/google_client.py crux-history --target https://example.com --origin
python scripts/google_client.py pagespeed --url https://example.com/page --strategy mobile
```

Lab data (DataForSEO backbone):

```
python scripts/dfs_client.py lighthouse --url https://example.com/page --pretty
python scripts/dfs_client.py onpage --url https://example.com/page --pretty
```

If CrUX returns no data (low-traffic origin), say so and fall back to lab
data plus page-level CrUX. Never fabricate field numbers.

## Process

1. **Assess** — read the 75th-percentile field values for LCP, INP, CLS.
   Note the trend from `crux-history` (improving / regressing / flat).
2. **Reproduce in lab** — match the lab Lighthouse run against the failing
   field metric; lab LCP and CLS usually map directly, INP must be
   investigated via Total Blocking Time and long tasks as a proxy.
3. **Attribute causes**:
   - **LCP** — unoptimized hero image (no `fetchpriority="high"`, not
     preloaded, oversized), render-blocking CSS/JS, slow server TTFB,
     late-discovered LCP resource behind JS or CSS `background-image`
   - **INP** — heavy main-thread JS, long tasks from hydration, large
     event-handler work, third-party scripts (tag managers, chat widgets)
   - **CLS** — images/iframes without width/height or aspect-ratio,
     web fonts swapping late (FOIT/FOUT), dynamically injected banners or
     ads above content, late-loading embeds
4. **Prescribe fixes** — concrete and specific: size and preload the LCP
   image, serve WebP/AVIF, inline critical CSS, defer non-critical JS,
   code-split and trim bundles, add explicit dimensions or `aspect-ratio`
   to all media, use `font-display: swap` with size-adjusted fallbacks,
   reserve space for ads/embeds.
5. **Verify** — after fixes ship, re-run `lighthouse` for lab confirmation
   and check `crux-history` over the following weeks for the field trend.

## Output

- Metric table: metric | field p75 | threshold | status | lab value | trend
- For each failing metric: likely causes with evidence from the Lighthouse
  audit (specific URLs, byte sizes, task durations)
- Prioritized fix list, each with a one-line "why" and expected metric
  it moves
- Single best next step: the one fix with the largest expected field impact
