---
name: keyword-gap
description: Finds keywords competitors rank for that the user's site does not, using DataForSEO domain intersection, then clusters and prioritizes them. Use when the user says keyword gap, competitor keywords, missing keywords, or what do competitors rank for that I don't.
---

# Keyword Gap

Quantifies the keyword universe where competitors are visible and the user
is not, then turns it into a prioritized targeting list.

## Inputs

- Required: user domain
- Optional: 2-3 competitor domains (else load from `seo-project.yml` via
  `python scripts/project_memory.py`, else discover with `competitors`),
  location/language

## Data pulls

Discover competitors if none were given:

```
python scripts/dfs_client.py competitors --target "<user-domain>" --limit 10
```

Pick the 2-3 most relevant (topical overlap, similar size — not Wikipedia or
Amazon), then run gap pulls in parallel:

```
python scripts/dfs_client.py intersection --target1 "<user-domain>" --target2 "<competitor-a>" --mode gap --limit 100
python scripts/dfs_client.py intersection --target1 "<user-domain>" --target2 "<competitor-b>" --mode gap --limit 100
python scripts/dfs_client.py intersection --target1 "<user-domain>" --target2 "<competitor-c>" --mode gap --limit 100
```

`--mode gap` returns keywords competitor B ranks for that the user does not.

If credentials are missing, stop and point the user to
docs/DATAFORSEO-SETUP.md. Do not invent numbers.

## Process

1. **Merge and dedupe** — combine gap lists across competitors; a keyword
   multiple competitors rank for (and the user doesn't) is a stronger signal
   than one found on a single domain. Tag each keyword with its competitor
   count.
2. **Filter noise** — drop competitor brand terms, navigational queries, and
   keywords irrelevant to the user's offering. Keep CPC as a
   commercial-value proxy.
3. **Cluster** — group surviving keywords into topic clusters (shared
   modifiers, shared intent, shared parent topic). Clusters, not individual
   keywords, should drive page decisions.
4. **Score** — for each cluster: combined volume, competitor coverage (how
   many competitors rank), relevance to the user's business (high/med/low),
   and best competitor position as a difficulty hint.
5. **Prioritize** — rank clusters by volume × relevance × competitor
   coverage. Flag clusters where all competitors rank in positions 11-30:
   weak incumbency, fastest path to parity.

## Output

- Cluster table: cluster | keywords | combined volume | competitors ranking
  | relevance | priority (P1-P3)
- Top 20 individual gap keywords: keyword | volume | best competitor
  position | competitor count
- For the top 3 clusters: one line on the page type needed to compete
- Single best next step (the cluster to build first and why)

Full keyword lists go to `KEYWORD-GAP-<domain>-<date>.md`; keep chat to the
top 20 rows.

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
