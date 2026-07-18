---
name: content-opportunity-finder
description: Finds new content opportunities from striking-distance keywords, underserved SERP intents, and question keywords with weak current results. Use when the user says content opportunities, what content should I create, easy wins, or quick SEO wins.
---

# Content Opportunity Finder

Surfaces the cheapest organic growth available: keywords the site nearly
ranks for, intents nobody serves well, and questions with weak incumbents.
Every claim is backed by a live data pull.

## Inputs

- Required: user domain
- Optional: seed topics (else derived from ranked data), location/language
  (defaults from `seo-project.yml` via `python scripts/project_memory.py`)

## Data pulls

```
python scripts/dfs_client.py ranked  --target "<user-domain>" --limit 200
python scripts/dfs_client.py ideas   --keyword "<top seed>" --limit 50
python scripts/dfs_client.py related --keyword "<top seed>" --limit 50
python scripts/dfs_client.py serp    --keyword "<candidate query>" --limit 20
```

Run `ideas`/`related` for the 2-3 strongest seed topics. Pull `serp` only for
shortlisted candidate queries (validate before recommending).

If credentials are missing, stop and point the user to
docs/DATAFORSEO-SETUP.md. Do not invent numbers.

## Process

1. **Striking distance** — from `ranked`, extract keywords in positions 4-20
   with meaningful volume. These pages already have Google's partial trust;
   a content refresh, better intent match, or internal links can move them
   onto page one. This is the highest-ROI bucket.
2. **Underserved intents** — for shortlisted SERPs, check whether the
   top-10 page types actually match the query intent. Signals of weakness:
   forums/UGC ranking high, old content, page-type mismatch (e.g., product
   pages ranking for an informational query), no dedicated page for a PAA
   sub-question.
3. **Question mining** — from `ideas` and `related`, filter interrogatives
   (how, what, why, can, does, is). Cross-check volume; a question with
   volume and weak SERP incumbents is a standalone article or FAQ block
   candidate.
4. **Score each opportunity** — volume × attainability (current position or
   incumbent weakness) × business relevance. Split into two actions:
   - **Optimize existing** — striking-distance keywords with a live URL.
   - **Create new** — underserved intents and questions with no matching URL.
5. **Deduplicate** — one keyword cluster maps to one page; flag cannibalization
   risk if two existing URLs split a cluster.

## Output

Two tables:

- **Optimize existing**: keyword | position | volume | current URL | the one
  fix most likely to move it
- **Create new**: topic/question | volume | evidence of weak SERP | proposed
  page type | priority (P1-P3)

Follow with the top 3 picks and a one-line why each, then the single best
next step. Full lists go to `CONTENT-OPPORTUNITIES-<domain>-<date>.md`.
