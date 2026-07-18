---
name: content-brief
description: Generates a complete writer's brief — live keyword volumes, intent, competitor outline analysis, H2/H3 outline, word count, entities, questions, internal links, schema, and meta drafts. Use when the user says content brief, writing brief, outline for, or brief for.
---

# Content Brief

Produces everything a writer needs to create a rankable article on the
first draft. Every competitive claim is based on live SERP data and
fetched competitor pages — nothing is assumed.

## Inputs

- Required: target keyword (plus the page URL, if improving an existing
  page)
- Optional: secondary keywords, location/language, word-count constraint

## Data pulls

Run with bash:

```
python scripts/dfs_client.py serp    --keyword "<target>" --limit 10
python scripts/dfs_client.py volume  --keywords "target,secondary1,secondary2"
python scripts/dfs_client.py related --keyword "<target>" --limit 20
```

Then fetch the top 5 organic results with the webfetch tool and extract
each page's H2/H3 structure, approximate word count, and the entities
and questions it covers.

## Process

1. **Intent lock** — state the dominant intent and page type from the
   SERP; the brief must match them.
2. **Competitor outline analysis** — merge the five fetched outlines:
   sections appearing on 3+ pages are mandatory; sections unique to one
   page are differentiation opportunities. Note the median word count.
3. **Build the outline** — an H2/H3 skeleton covering all mandatory
   sections plus at least two differentiators, with per-section word
   counts summing to the target (competitor median, adjusted for any
   user constraint).
4. **Keywords & entities** — primary keyword + 3-8 secondaries with live
   volumes; an entity and question checklist drawn from the competitor
   pages and the related pull (questions the writer must answer).
5. **Internal links** — name the exact pages to link to (pillar, sibling
   spokes) with suggested anchor text, and the pages that must link back.
6. **Schema & meta** — recommend schema types (Article, BreadcrumbList;
   generate with `python scripts/schema_gen.py`); draft a meta title
   (<=60 chars) and meta description (<=155 chars) containing the
   primary keyword.

## Output

The full brief goes to `BRIEF-<keyword>-<date>.md`: intent statement,
keyword table, competitor coverage summary, complete outline with word
counts, entity/question checklist, internal-link plan, schema notes,
meta drafts. Chat shows only:
- The outline, plus the top 3 mandatory sections with a one-line "why"
  each
- Single best next step: hand the brief to a writer, or offer
  faq-generator for the FAQ block
