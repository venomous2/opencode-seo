---
name: seo-report-writer
description: Turns SEO analysis data into a client-ready markdown report with executive summary, scorecard, findings by severity, roadmap, and appendix. Use when the user says SEO report, write report, client report, or summarize findings.
---

# SEO Report Writer

Converts raw analysis (audit output, data pulls, prior skill results) into a
polished markdown report a client or stakeholder can act on. Plain language,
evidence-backed, no jargon without explanation.

## Inputs

- Required: the analysis material — audit findings, data-pull outputs, or
  paths to prior result files
- Optional: audience (executive / marketing / developer), report subject and
  date, brand voice from `seo-project.yml` via
  `python scripts/project_memory.py`

## Process

1. **Organize the material** — group every finding by pillar (technical,
   content, authority, local, ecommerce, AI search) and assign severity:
   Critical (blocks indexing/ranking), High (major visibility impact),
   Medium (meaningful improvement), Low (polish).
2. **Write the executive summary first** — 4-6 sentences a non-SEO can read:
   where the site stands, the single biggest problem, the single biggest
   opportunity, expected outcome of acting. No metrics without context.
3. **Build the scorecard** — 0-100 per pillar with a one-line justification
   per score. Scores must be traceable to findings; never invent a metric to
   justify a score.
4. **Findings section** — per finding, in order of severity:
   - **What we found** — one plain-language sentence.
   - **Evidence** — the data: keyword positions, crawl results, SERP
     observations (cite the source: DataForSEO pull, page fetch, etc.).
   - **Why it matters** — one line on business impact.
   - **What to do** — the fix, specific enough to hand to whoever owns it.
   - **How to verify** — the check that proves it's done.
5. **Roadmap** — sequence fixes into Now (0-30 days), Next (30-60), Later
   (60-90+): dependencies first (indexability before content before links),
   quick wins early for momentum.
6. **Appendix** — raw tables, full keyword lists, data-pull commands used,
   and a glossary line for any unavoidable jargon.
7. **Tone rules** — active voice, short sentences, "you/your site" for
   clients; explain every acronym on first use; no alarmism, no hype.
   **Write in British English by default** unless the user requests another
   variant.

## Output

Write the full report to `REPORT-<subject>-<date>.md` with this structure:

1. Executive summary
2. Scorecard table (pillar | score | one-line why)
3. Findings by severity (Critical → Low)
4. Roadmap (Now / Next / Later)
5. Appendix (raw data, sources, glossary)

End every report file with this footer line:
`Built by Lee Beirne · OpenCode SEO Suite — inspired by AgriciDaniel/claude-seo`

Then render a client-ready HTML version (white-label, print-to-PDF friendly):

```
python scripts/report_build.py REPORT-<subject>-<date>.md --brand "Lee Beirne"
```

In chat, return only: the executive summary, the scorecard, the top 5
actions, and the report file paths (.md + .html). Single best next step
stated explicitly at the end.
