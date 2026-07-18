---
name: heading-optimizer
description: H1-H6 heading hierarchy audit — single H1, logical nesting, keyword-aligned natural headings, and question-form headings for AI search. Use when the user says headings, H1, heading structure, or heading hierarchy.
---

# Heading Optimizer

Audits and rewrites the H1-H6 outline of a page. Headings serve two
readers: scanning humans, and engines (including AI answer engines)
that lift structure directly.

## Inputs

- Required: URL(s) to audit, or pasted page content/outline
- Optional: target keyword; location/language from `seo-project.yml`

## Data pulls

- webfetch each URL and extract every heading tag in document order
  (level + text).
- To see what structure currently wins:
  `python scripts/dfs_client.py serp --keyword "<target keyword>" --limit 10`
  then webfetch 2-3 of the top-ranking pages and compare outlines.

## Process

1. **Inventory** — list all headings with level and text, in order.
2. **H1 check** — exactly one H1; it states the page topic and aligns
   with the title tag without being a copy-paste of it. Multiple or
   missing H1s are critical findings.
3. **Nesting** — levels descend logically (H2 → H3, never H2 → H4 with
   no H3). Flag headings used purely for visual styling (a bold line
   wrapped in an H-tag) — those should be CSS, not structure.
4. **Coverage** — H2s map to the subtopics the SERP rewards; compare
   against the winning outlines from the SERP pull and list gaps.
5. **Keyword alignment** — primary keyword in the H1, variations in H2s
   where they fit naturally. Never force a keyword into a heading that
   reads awkwardly — clarity beats exact match.
6. **AI-search readiness** — headings phrased as the real questions
   users ask (e.g. "How much does X cost?") are directly citable;
   each question heading must be answered in the first sentence or two
   of the paragraph beneath it. Flag vague headings ("Overview",
   "More Info") for rewrite.
7. **Rewrite** — deliver the corrected outline as a nested list.

## Output

Current outline vs proposed outline, a findings list with evidence
(line/heading text), recommendations ranked critical / high / medium /
low with a one-line "why" each, then the single best next step. For
multi-page work, write `HEADINGS-<domain>-<date>.md`; chat shows one
page's before/after plus the critical issues across the rest.

## Output location

Save generated files to the SEO reports directory - `%SEO_REPORTS_DIR%\<name>\` on Windows, `$SEO_REPORTS_DIR/<name>/` on macOS/Linux - when the `SEO_REPORTS_DIR` environment variable is set; otherwise the current working directory. Create the subfolder if it doesn't exist.
