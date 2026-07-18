---
name: serp-analysis
description: Deep analysis of a single SERP using live DataForSEO data — ranking page types, domains, SERP features, and realistic difficulty. Use when the user says SERP analysis, analyze SERP, who ranks for, or what does Google reward for a query.
---

# SERP Analysis

Dissects one search results page to explain what Google is rewarding for the
query, which features are present, and whether the user can realistically
win a position.

## Inputs

- Required: target keyword/query
- Optional: user domain (to check current presence), location/language
  (defaults from `seo-project.yml` via `python scripts/project_memory.py`)

## Data pulls

```
python scripts/dfs_client.py serp   --keyword "<query>" --limit 100 --pretty
python scripts/dfs_client.py volume --keywords "<query>"          # volume + difficulty if not in serp payload
python scripts/dfs_client.py ranked --target "<user-domain>" --limit 100   # if user domain given
```

Then webfetch the top 3 organic results to confirm page type and depth — do
not judge pages by titles alone.

If credentials are missing, stop and point the user to
docs/DATAFORSEO-SETUP.md. Do not invent numbers.

## Process

1. **Inventory the SERP** — list every organic result (position, domain,
   URL) and every feature detected: AI Overview, People Also Ask, video
   carousel, local pack, featured snippet, images, shopping, knowledge panel.
   Features compress organic clicks — count how much screen real estate
   remains for classic results.
2. **Classify page types** — label each top-10 result: homepage, category,
   product, blog post, guide, tool, video, forum/UGC, news. The dominant type
   is what Google believes satisfies the intent; a mismatch with the user's
   planned page type is the single biggest failure predictor.
3. **Profile the domains** — note who ranks: aggregators (Reddit, Quora,
   Forbes), niche sites, brands, government/edu. Heavy UGC/forum presence
   signals weak incumbents and an opening; wall-to-wall enterprise brands
   signals high difficulty.
4. **Read intent signals** — singular vs plural, modifiers (best, vs, near
   me, free, template), and PAA questions reveal sub-intents a winning page
   must cover.
5. **Assess difficulty honestly** — combine keyword difficulty (if returned),
   incumbent domain strength, page-type match requirements, and feature
   crowding into a verdict: **winnable now / winnable with links / long-term
   play / not worth it**.

## Output

- SERP inventory table: position | domain | page type | notes
- Features present and their click impact
- Intent verdict: primary intent + required sub-intents (from PAA/AIO)
- Difficulty verdict with one-paragraph justification
- Recommendation: the exact page type and format to build (or how to adapt
  an existing page), plus the single most important thing the current
  top-ranking page does that must be matched or beaten
