---
name: image-seo
description: Audits and fixes image SEO — filenames, alt text, modern formats, responsive images, lazy loading, layout stability, and image sitemaps. Use when the user says image SEO, alt text, or optimize images.
---

# Image SEO

Optimizes images for both image search visibility and page performance.
Images are frequently the LCP element and the main CLS source, so this
overlaps Core Web Vitals work.

## Inputs

- Required: page URL(s) or site to audit
- Optional: a key template to prioritize (product page, article, gallery)

## Data pulls

Fetch the page HTML with the webfetch tool and inventory every `<img>`:
src/srcset, alt, width/height, loading attribute, format, and whether it
is likely the LCP element (hero/above-the-fold).

Optional live checks:

```
python scripts/dfs_client.py onpage     --url https://example.com/page --pretty
python scripts/dfs_client.py lighthouse --url https://example.com/page --pretty
```

The lighthouse run reports oversized images, offscreen images, and modern-
format opportunities with real byte savings — quote those, never estimate.

## Process

1. **Filenames** — descriptive, hyphenated, lowercase
   (`red-running-shoes-side-view.webp`, not `IMG_4521.jpg`). Renames on
   live sites need redirects for image URLs that already earn image-search
   traffic.
2. **Alt text** — describes the image as it functions on the page, in a
   natural sentence fragment; include a keyword only when it genuinely
   describes the image. Never keyword-stuff, never "image of...".
   Decorative images get empty `alt=""` (omitted alt is a bug; empty alt
   is a choice). Functional images (icons in links/buttons) describe the
   action, not the picture.
3. **Formats and compression** — serve WebP or AVIF instead of JPEG/PNG
   (AVIF smallest, WebP the safe baseline); keep a fallback via `<picture>`
   where needed. Compress: photographic ~80 quality is usually
   indistinguishable.
4. **Responsive sizing** — `srcset` + `sizes` so mobile never downloads a
   2400px desktop hero; the HTML `src` is the sensible middle size. Flag
   images served far larger than their rendered box (Lighthouse lists
   these with byte waste).
5. **Loading strategy** — `loading="lazy"` only below the fold; the LCP
   image must be eager with `fetchpriority="high"` and must NOT be lazy.
   Never lazy-load above-the-fold images.
6. **Layout stability** — every image carries `width` and `height` (or CSS
   `aspect-ratio`) so the browser reserves space and CLS stays under 0.1.
7. **Discovery** — images referenced in an image sitemap (or standard
   sitemap with `<image:image>` entries), especially JS-loaded or
   CDN-hosted images; confirm the CDN allows crawling (no robots.txt
   block on the image host).
8. **Structured data** — where relevant, include image properties in
   Product/Article schema so rich results can show them (hand off to the
   schema-generator skill).

## Output

- Findings table: image/template | issue (alt, format, size, lazy, CLS,
  sitemap) | evidence (exact src) | severity, one-line "why" each
- Rewritten alt text proposals for the most important images
- A per-template fix list the developer can apply once and propagate
- Byte-savings summary from the Lighthouse audit
- Single best next step: fix the LCP image (eager + fetchpriority + sized)
  on the highest-traffic template

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
