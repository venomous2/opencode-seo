---
name: accessibility-audit
description: Web accessibility audit against WCAG success criteria with a machine-checked findings report, WCAG mapping, and an honest manual-testing scope statement. Use when the user says accessibility, a11y, WCAG, ARIA, WAI-ARIA, screen reader, accessible website, or EAA compliance.
---

# Accessibility Audit

Audits pages against WCAG success criteria using the rule engine's
accessibility category. Sits at the SEO/UX/legal intersection — and with
the European Accessibility Act and Equality Act in force, it is a
sellable, recurring service, not a checkbox.

## The honesty contract (read first, repeat to clients)

Static analysis can only verify a slice of WCAG. This audit covers the
**machine-checkable** criteria (~12 rules below plus existing checks for
alt text, H1, and page language). It **cannot** verify, and never claims
to verify: colour contrast ratios, keyboard operability, focus visibility,
screen-reader output quality, motion/animation safety, or resize/reflow
behaviour. Every report must state this split explicitly — a client who
believes a static scan equals WCAG compliance is a liability, and a client
who understands the split trusts you more.

## Inputs

- Required: URL(s) to audit (page list, or crawl first via `site_crawler.py`)
- Optional: WCAG level focus (A / AA / AAA)

## Machine-checked criteria

Run the linter with the accessibility category:

```
python scripts/seo_lint.py --url <url> --category accessibility --format text
```

| Rule | WCAG | Level | Severity |
|---|---|---|---|
| form-input-unlabelled | 1.3.1 + 4.1.2 | A | High |
| empty-link | 2.4.4 | A | High |
| empty-button | 4.1.2 | A | High |
| duplicate-id | 4.1.1 | A | High |
| missing-skip-link | 2.4.1 | A | Medium |
| missing-main-landmark | 1.3.1 | A | Medium |
| heading-order-skip | 1.3.1 | A | Medium |
| table-missing-headers | 1.3.1 | A | Medium |
| iframe-missing-title | 4.1.2 | A | Medium |
| positive-tabindex | 2.4.3 | A | Medium |
| generic-link-text | 2.4.4 | AAA | Low |
| missing-nav-landmark | 1.3.1 | A | Low |

Also map these existing rules into the a11y report: images-missing-alt
(WCAG 1.1.1), missing-h1 / heading structure (1.3.1), missing-html-lang
(3.1.1), missing-title (2.4.2).

## Process

1. **Machine pass** — lint every URL; collect findings per WCAG criterion.
2. **Severity call** — A-level failures with real user impact first
   (unlabelled forms, empty links/buttons, duplicate ids), then structure
   (landmarks, headings, tables), then polish (generic link text).
3. **Manual-test checklist** — always append what the scan cannot see:
   - Keyboard walkthrough: Tab through the page — is every control
     reachable, in a sane order, with a visible focus ring?
   - Contrast: run key text through a contrast checker (4.5:1 body, 3:1 large)
   - Screen-reader spot-check: 5 minutes with NVDA/VoiceOver on the
     homepage and one form
   - Zoom to 200%: does anything break or overlap?
   - Motion: any autoplaying carousels/animations with no pause control?
   - Tools: axe DevTools and WAVE for a second automated opinion
4. **Fix guidance** — every finding carries its rule's fix (labels,
   skip links, landmarks, unique ids, table headers, iframe titles).

## Output

Write `A11Y-AUDIT-<domain>-<date>.md`:
- Scorecard: machine-check pass rate per WCAG level (A / AA / AAA)
- Findings table: WCAG criterion | level | count | example | severity | fix
- The honesty split: "Verified by scan" vs "Needs manual testing" sections
- Manual-test checklist (above)
- Prioritised fixes, quick wins first
- Footer: `Report built by Lee Beirne - https://leebeirne.com`

Then publish: `python scripts/report_publish.py A11Y-AUDIT-<domain>-<date>.md`

Chat gets: pass rate, top 5 issues by severity, and the manual-testing
next step. Position it as **phase one of accessibility work** — the
scan finds the mechanical failures; the checklist finishes the job.

## Output location

Save generated files to the SEO reports directory - `%SEO_REPORTS_DIR%\<name>\` on Windows, `$SEO_REPORTS_DIR/<name>/` on macOS/Linux - when the `SEO_REPORTS_DIR` environment variable is set; otherwise the current working directory. Create the subfolder if it doesn't exist.

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
