---
name: topical-coverage-comparison
description: Compares topical coverage between the user's site and competitors by clustering live ranked-keyword data and scoring each domain per topic. Use when the user says topical coverage, coverage comparison, competitor topics, or content gap by topic.
---

# Topical Coverage Comparison

Answers "which topics do competitors own that we don't?" by clustering each
domain's ranked keywords into topics and scoring coverage side by side.

## Inputs

- Required: user domain
- Optional: 1-3 competitor domains (else from `seo-project.yml` via
  `python scripts/project_memory.py`, else discover with `competitors`),
  location/language

## Data pulls

```
python scripts/dfs_client.py competitors --target "<user-domain>" --limit 10   # if competitors unknown
python scripts/dfs_client.py ranked --target "<user-domain>"   --limit 200
python scripts/dfs_client.py ranked --target "<competitor-a>"  --limit 200
python scripts/dfs_client.py ranked --target "<competitor-b>"  --limit 200
python scripts/dfs_client.py ranked --target "<competitor-c>"  --limit 200
```

Run the `ranked` pulls in parallel. If credentials are missing, stop and
point the user to docs/DATAFORSEO-SETUP.md. Do not invent numbers.

## Process

1. **Build the keyword union** — merge ranked-keyword lists from all
   domains; dedupe. Record per keyword: which domains rank and their best
   position.
2. **Cluster into topics** — group keywords by shared parent topic and
   modifier patterns (e.g., "pricing", "how to", "vs", "templates"). Aim for
   8-20 clusters; merge clusters too small to act on.
3. **Score coverage per domain per topic** — for each (domain, topic) cell:
   - keyword count ranking anywhere in top 100
   - count in positions 1-10 (real visibility)
   - best position
   Convert to a simple grade: **Strong** (multiple top-10s), **Present**
   (ranks but page 2+), **Absent** (nothing).
4. **Expose weak zones** — topics where ≥2 competitors are Strong and the
   user is Absent are structural gaps. Topics where the user is Present but
   competitors are Strong are improvement zones.
5. **Sanity-check** — webfetch one representative competitor page per major
   gap topic to confirm the cluster maps to a real content hub, not one
   accidental page.

## Output

- Coverage matrix: topic | user grade | competitor A | B | C (Strong /
  Present / Absent, with top-10 counts)
- Gap summary: topics ranked by (competitor strength × user weakness ×
  combined volume)
- Per top-3 gap topics: the content hub needed (pillar + supporting pages
  sketch) with one-line why
- Note topics where the user leads — worth defending with refreshes
- Single best next step (the one topic to build out first)

The full matrix and keyword-to-topic mapping go to
`TOPICAL-COVERAGE-<domain>-<date>.md`.

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
