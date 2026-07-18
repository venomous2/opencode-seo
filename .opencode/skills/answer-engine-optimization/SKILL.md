---
name: answer-engine-optimization
description: Applies answer engine optimization (AEO) fundamentals by researching real questions from SERP data and restructuring content into direct-answer blocks. Use when the user says AEO, answer engine optimization, or answer optimization.
---

# Answer Engine Optimization

AEO fundamentals: structure content so any answer engine — featured
snippets, AI Overviews, ChatGPT search, Perplexity — can lift a complete
answer directly from the page. AEO is a structure layer on top of classic
SEO: the page still has to rank and be trusted before its answers get
reused.

## Inputs

- Required: target URL(s) or topic
- Optional: location/language (defaults from `seo-project.yml` if present)

## Data pulls

Real questions come from SERP data, not brainstorming:

```
python scripts/dfs_client.py serp    --keyword "<kw>" --limit 20 --pretty
python scripts/dfs_client.py related --keyword "<kw>" --limit 30
python scripts/dfs_client.py ideas   --keyword "<kw>" --limit 50
```

Extract People Also Ask questions from the SERP items; use related/ideas
to catch phrasing variants. Fetch the target page with webfetch. If
credentials are missing, stop and point the user to
docs/DATAFORSEO-SETUP.md.

## Process

1. **Question inventory** — list the real questions for the topic from
   PAA and related searches; rank them by relevance to the page's intent.
2. **Placement audit** — for each question the page should own: is the
   answer present, and where? Flag buried answers (answer appears after
   hundreds of words of preamble), implied answers (the reader must
   infer), and missing answers.
3. **Answer block patterns** — rewrite using the pattern that fits the
   question:
   - **Definition** — "X is ..." in one sentence, then the two or three
     properties that distinguish it.
   - **Steps** — numbered list, one action per step, no skipped
     prerequisites.
   - **Comparison** — table or parallel sentences naming the options and
     the deciding criteria.
   - **List** — bulleted items with a one-line explanation each.
4. **Heading hygiene** — put the question (or a close paraphrase) in the
   heading; answer in the first paragraph; detail after.
5. **Restraint** — answer the question asked, then stop. Answer blocks
   padded with tangents are less liftable, not more complete.

## Output

- Question table: question | source (PAA/related) | answered? | location
  on page | fix needed
- Rewritten answer blocks for the top-priority questions, in the correct
  pattern
- Prioritized recommendations (critical/high/medium/low), each with a
  one-line "why"
- Single best next step

Write the full question inventory to `AEO-<topic>-<date>.md` when it
exceeds ~100 lines.
