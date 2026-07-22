---
name: entity-extraction
description: Identifies the named entities (people, brands, products, concepts) content should mention to demonstrate topical completeness, benchmarked against top-ranking pages. Use when the user says entities, entity SEO, NLP entities, or what entities should I mention.
---

# Entity Extraction

Finds the named entities a piece of content must mention to look
topically complete to search engines, by comparing against what
top-ranking pages actually mention. No guessed entity lists — everything
is benchmarked against live pages.

## Inputs

- Required: target keyword (plus the draft text or URL of the user's
  content, if it exists)
- Optional: location/language

## Data pulls

Run with bash:

```
python scripts/dfs_client.py serp    --keyword "<target>" --limit 10
python scripts/dfs_client.py related --keyword "<target>" --limit 30
```

Fetch the top 5 organic results with the webfetch tool; if the user has
a draft or live URL, fetch that too.

## Process

1. **Extract competitor entities** — from each fetched top page, list
   the named entities: people, brands, products, tools, organizations,
   standards, places, and defining concepts (e.g., "E-E-A-T", "Core Web
   Vitals") — not generic words.
2. **Build the consensus set** — entities mentioned on 3+ of 5 pages are
   mandatory; entities on 1-2 pages are optional differentiators.
3. **Audit the user's content** — if a draft/URL was fetched, mark each
   mandatory entity present or missing; missing mandatory entities are
   the gap list.
4. **Placement guidance** — assign each mandatory entity to the section
   where it belongs: definitions in the intro or a glossary section,
   products/brands in comparison sections, people/organizations in
   evidence or examples. Entities must appear in natural prose — never
   as a stuffed list.
5. **Salience tip** — mention the most important entities early (intro
   or first H2) and tie them to the page's primary entity by name.

## Output

An entity checklist table: entity | type (person/brand/product/concept)
| consensus (x/5 pages) | in user's content? | suggested placement |
priority (must/should/optional). Then:
- The gap list: missing mandatory entities with a one-line "why" each
- 2-3 differentiator entities competitors missed, with a one-line "why"
  each
- Single best next step: revise the draft to close the top 3 gaps (or
  fold the checklist into content-brief if no draft exists yet)

Write checklists over 25 entities to `ENTITIES-<keyword>-<date>.md`;
chat shows must-have gaps and differentiators only.

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
