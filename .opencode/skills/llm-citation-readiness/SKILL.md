---
name: llm-citation-readiness
description: Scores how ready a page is to be cited by LLM-based search engines against a citability checklist, with a mention baseline and prioritized fix list. Use when the user says LLM citations, citation readiness, AI citations, or get cited by AI.
---

# LLM Citation Readiness

A scoring audit: how ready is this page to be found, extracted, and cited
by LLM-based search (AI Overviews, AI Mode, ChatGPT search, Perplexity)?
Honest framing: readiness improves the controllable inputs — clarity,
citability, discoverability. It does not and cannot guarantee citation.

## Inputs

- Required: target URL(s) or pasted page content, brand name
- Optional: competitor URLs for comparison scoring

## Data pulls

```
python scripts/dfs_client.py mentions --keyword "<brand>" --limit 50 --pretty
python scripts/dfs_client.py serp     --keyword "<page target keyword>" --limit 20
```

`mentions` gives the current AI-citation baseline; the SERP pull shows
whether an AI Overview exists for the target query and who gets cited.
Fetch each target page with webfetch. If credentials are missing, stop
and point the user to docs/DATAFORSEO-SETUP.md.

## Process

Score each page 0-2 per checklist item (0 = absent, 1 = partial,
2 = solid):

1. **Answer blocks** — direct, self-contained answers (~130-170 words)
   under question-form headings, near the top of the page.
2. **Sourcing** — key claims carry named sources, numbers, and dates;
   no unsupported superlatives.
3. **Authorship** — visible author with credentials; organization
   identity with linked about/contact pages.
4. **Dates** — honest publish and modified dates, visible in the content
   and matching the schema.
5. **Structure** — descriptive headings, one idea per section, lists and
   tables only where they genuinely fit, no critical info trapped in
   images.
6. **Access** — indexable, server-rendered, and not blocked for the
   search/AI crawlers the user wants to reach.
7. **Entity clarity** — brand and product names used consistently;
   Organization/Person schema with sameAs present.

## Output

- Score table: checklist item | score (0-2) | evidence | fix
- Mention baseline: current mentions vs. the competitor set (from
  `mentions`), with the total score per page
- Prioritized fix list (critical/high/medium/low), each with a one-line
  "why"
- Single best next step: the lowest-scoring item with the highest
  leverage — usually answer blocks or sourcing

Write the full scorecard to `CITATION-READINESS-<domain>-<date>.md` when
auditing more than ~5 pages.

## Output location

Save generated files to the SEO reports directory - `%SEO_REPORTS_DIR%\<name>\` on Windows, `$SEO_REPORTS_DIR/<name>/` on macOS/Linux - when the `SEO_REPORTS_DIR` environment variable is set; otherwise the current working directory. Create the subfolder if it doesn't exist.
