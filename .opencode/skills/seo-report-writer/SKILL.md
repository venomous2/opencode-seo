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
   justify a score. Render it visually (see Charts below): an overall donut
   plus a bar chart of pillar scores.
4. **Findings section** — per finding, in order of severity:
   - **What we found** — one plain-language sentence.
   - **Evidence** — the data: keyword positions, crawl results, SERP
     observations (cite the source: DataForSEO pull, page fetch, etc.).
   - **Why it matters** — one line on business impact.
   - **What to do** — the fix, specific enough to hand to whoever owns it.
   - **How to verify** — the check that proves it's done.
   Where a finding is numeric (ranking movers, CWV vs thresholds, crawl
   status distribution), show it as a chart, not just prose.
5. **Recommendations & actions** — a dedicated action table the client can
   work through, ordered by impact × effort:

   | # | Action | Priority | Effort | Expected impact | Owner | Done |
   |---|--------|----------|--------|-----------------|-------|------|

   Priority uses the severity words (Critical/High/Medium/Low — they render
   as coloured badges in HTML). Start with 1-3 quick wins (high impact, low
   effort) and mark them **Quick win**.
6. **Roadmap** — sequence fixes into Now (0-30 days), Next (30-60), Later
   (60-90+): dependencies first (indexability before content before links),
   quick wins early for momentum.
7. **Appendix** — raw tables, full keyword lists, data-pull commands used,
   and a glossary line for any unavoidable jargon.
8. **Tone rules** — active voice, short sentences, "you/your site" for
   clients; explain every acronym on first use; no alarmism, no hype.
   **Write in British English by default** unless the user requests another
   variant.

## Charts (markdown → HTML graphs)

`report_build.py` renders fenced ```` ```chart ```` blocks as graphs in the
HTML report. Use them wherever a number tells the story better than words.
One JSON object per block:

    ```chart
    {"type": "donut", "title": "Overall SEO Health", "value": 64, "max": 100}
    ```
    ```chart
    {"type": "bar", "title": "Pillar scores",
     "data": [["Technical", 74], ["Content", 81], ["Authority", 42]], "max": 100}
    ```
    ```chart
    {"type": "line", "title": "Organic clicks / month",
     "data": [["Mar", 120], ["Apr", 180], ["May", 260]]}
    ```
    ```chart
    {"type": "stats", "data": [["Referring domains", "312", "+18"],
     ["Top-10 keywords", "24", "-2"], ["Indexed pages", "186", "+12"]]}
    ```

Rules: `stats` cards go right after the executive summary (3-5 headline
numbers with deltas vs last period when drift data exists); every scorecard
gets a donut + bar chart; trends get line charts. Never chart numbers you
don't have data for.

## Output

Write the full report to `REPORT-<subject>-<date>.md` with this structure:

1. Executive summary
2. Headline stats (`stats` chart block)
3. Scorecard table (pillar | score | one-line why) + donut + bar charts
4. Findings by severity (Critical → Low), with charts where numeric
5. Recommendations & actions table
6. Roadmap (Now / Next / Later)
7. Appendix (raw data, sources, glossary)

End every report file with this footer line:
`Report built by Lee Beirne - https://leebeirne.com`

Then render the client-ready HTML version:

```
python scripts/report_build.py REPORT-<subject>-<date>.md --brand "Lee Beirne"
```

In chat, return only: the executive summary, the scorecard, the top 5
actions, and the report file paths (.md + .html). Single best next step
stated explicitly at the end.
