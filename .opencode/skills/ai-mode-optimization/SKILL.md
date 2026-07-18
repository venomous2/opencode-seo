---
name: ai-mode-optimization
description: Optimizes content for Google AI Mode conversational search by covering full question spaces, follow-up chains, and decision-stage comparisons. Use when the user says AI Mode, Google AI Mode, or conversational search.
---

# AI Mode Optimization

Prepares content for Google AI Mode, where users ask multi-part questions
and follow-ups in a conversational flow. Per Google's AI optimization
guidance, AI Mode runs on the same index and ranking systems as classic
Search — classic SEO is the foundation; this skill adds coverage-depth
and structure layers for conversational journeys.

## Inputs

- Required: topic area or target URL(s)
- Optional: audience segment, location/language (defaults from
  `seo-project.yml` if present)

## Data pulls

Map the question space with live data — never assume which follow-ups
users ask:

```
python scripts/dfs_client.py serp    --keyword "<head term>" --limit 20 --pretty
python scripts/dfs_client.py ideas   --keyword "<head term>" --limit 50
python scripts/dfs_client.py related --keyword "<head term>" --limit 30
```

Extract People Also Ask questions from the SERP items — the closest
public proxy for follow-up chains. Fetch target pages with webfetch. If
credentials are missing, stop and point the user to
docs/DATAFORSEO-SETUP.md.

## Process

1. **Map the question space** — cluster the PAA questions, ideas, and
   related keywords into a follow-up chain: the head question, the 3-6
   natural next questions, and the decision-stage questions (cost,
   comparison, "is it worth it", "best option for X").
2. **Coverage audit** — check each chain question against the target
   page(s): answered explicitly, answered vaguely, or missing. AI Mode
   synthesizes across a whole conversation; a page that covers the full
   chain stays useful at every turn, not just the first.
3. **Passage structure** — one question per section, descriptive heading,
   self-contained answer in the first paragraph, supporting detail after.
   Conversational systems quote passages, not pages.
4. **Decision content** — for complex queries, add comparison and
   decision-stage material: pros/cons tables, "X vs Y" sections, "best
   for <use case>" verdicts with explicit criteria. Follow-up chains in
   AI Mode trend toward decisions.
5. **Consolidate, do not splinter** — prefer one comprehensive page
   covering a question space over thin scattered posts; consolidate
   overlapping URLs where they exist so authority is not diluted.

## Output

- Question-chain map: head question -> follow-ups -> decision questions,
  each marked covered / weak / missing, with evidence
- Prioritized recommendations (critical/high/medium/low), each with a
  one-line "why"
- Single best next step (usually: the missing chain section whose PAA
  question has the highest presence across the serp pulls)

Write the full question-space audit to `AI-MODE-<topic>-<date>.md` when
it exceeds ~100 lines.
