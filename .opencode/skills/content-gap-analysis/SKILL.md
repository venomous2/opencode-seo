---
name: content-gap-analysis
description: Finds subtopics competitors cover that the user's page or site misses by comparing coverage against live top SERP results in a gap matrix. Use when the user says content gap, what am I missing, or gap analysis.
---

# Content Gap Analysis

Shows exactly what to add: the subtopics the ranking pages cover that the
user's content doesn't, prioritized by how universally competitors cover
them.

## Inputs

- Required: the user's page URL (or site section) + target keyword/topic
- Optional: specific competitor URLs, location/language

## Data pulls

```
python scripts/dfs_client.py serp         --keyword "<target keyword>" --limit 10
python scripts/dfs_client.py intersection --targets "<comp1>,<comp2>" --limit 50
```

Then fetch with webfetch (parallel): the user's page plus the top 5
organic results. Site-level mode: add
`python scripts/dfs_client.py ranked --target "<competitor>" --limit 500`
per competitor and compare keyword sets. If credentials are missing, stop
and point to docs/DATAFORSEO-SETUP.md.

## Process

1. **Extract competitor coverage** — from each fetched top-5 page, list
   the H2/H3 sections and the questions each answers.
2. **Build the coverage matrix** — rows: subtopics found across
   competitors; columns: each page (user + top 5); cells: covered /
   shallow / missing.
3. **Score each gap** — priority = (how many of the top 5 cover it) ×
   (intent importance). A subtopic in 4-5 of the top 5 that the user
   misses is P1; a subtopic in 1 of 5 is a differentiator opportunity,
   not a gap.
4. **Query-level gaps** — from the serp pull, note questions (People Also
   Ask style) and SERP features the user's page can't win because the
   content doesn't exist on it.
5. **Distinguish gap types**:
   - Missing sections → add to the existing page
   - Missing pages → the subtopic deserves its own URL (site-level mode)
   - Shallow coverage → expand, with specifics competitors lack

## Output

- Coverage matrix (compact — top 5 competitors + user)
- Prioritized add list: section/keyword | covered by N/5 | where to add |
  why (one line each)
- Differentiators: subtopics only one competitor covers that fit the
  user's angle
- Single best next step: the P1 section to write first

Write the full matrix and section specs to
`CONTENT-GAP-<keyword>-<date>.md` when it exceeds ~100 lines; chat gets
the top 10 gaps.
