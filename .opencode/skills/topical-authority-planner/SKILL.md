---
name: topical-authority-planner
description: Plans complete topical coverage for a niche — entity map, subtopic inventory, coverage scoring against competitors, and a prioritized publishing sequence. Use when the user says topical authority, topical map, cover a niche, or content coverage plan.
---

# Topical Authority Planner

Builds a full coverage plan for a niche: every subtopic that must exist
for Google to treat the site as an authority, scored against what
competitors already cover. All data is live — no assumed gaps.

## Inputs

- Required: the niche / core topic; the user's domain
- Optional: 1-3 known competitors (auto-discovered otherwise);
  location/language

## Data pulls

Run with bash:

```
python scripts/dfs_client.py competitors  --target "<user-domain>" --limit 10
python scripts/dfs_client.py ranked       --target "<user-domain>" --limit 200
python scripts/dfs_client.py ranked       --target "<top-competitor>" --limit 200
python scripts/dfs_client.py intersection --target1 "<user>" --target2 "<competitor>" --mode gap
python scripts/dfs_client.py ideas        --keyword "<niche>" --limit 100
```

Repeat `ranked` / `intersection` for up to 3 competitors.

## Process

1. **Entity map** — list the core entities of the niche (products,
   problems, methods, audiences, comparisons) from the ideas pull and
   the competitor keyword sets.
2. **Subtopic inventory** — expand entities into a complete subtopic
   list; each subtopic = one potential page or cluster.
3. **Coverage scoring** — mark each subtopic for the user:
   covered-and-ranking (in the `ranked` data), covered-but-weak
   (position 30+), or missing. Score competitors the same way; the gap
   pull shows where competitors rank and the user has nothing.
4. **Gap analysis** — prioritize subtopics where 2+ competitors rank in
   the top 20 and the user has no page at all.
5. **Sequence** — foundational (broad, heavily interlinked) subtopics
   ship first; long-tail spokes follow their pillars.

## Output

A markdown table: subtopic | user status (ranking / weak / missing) |
best competitor rank | combined volume | priority (P1-P3). Then:
- Coverage score: % of the inventory the user covers vs the top
  competitor — the headline metric
- Prioritized publishing sequence in phases, with a one-line "why" per
  phase
- Single best next step: the first subtopic to publish or fix

Write the full plan to `TOPICAL-AUTHORITY-<niche>-<date>.md`; chat shows
the coverage score and the top 10 gaps only.
