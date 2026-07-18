---
name: content-calendar
description: Turns keyword and cluster data into a prioritized publishing calendar with cadence, seasonality from trend data, and page-type assignments. Use when the user says content calendar, publishing schedule, editorial calendar, or plan my content.
---

# Content Calendar

Converts keyword/cluster research into a dated, prioritized publishing
schedule. Volumes and trends come from live DataForSEO pulls; dates and
cadence are planning decisions, clearly framed as such.

## Inputs

- Required: keyword list or cluster map (from keyword-research /
  topic-clustering, or pasted); publishing cadence (e.g., 2 posts/week)
- Optional: start date, location/language, user's domain

## Data pulls

Run with bash (volumes in batches; serp only for head terms):

```
python scripts/dfs_client.py volume --keywords "kw1,kw2,..."   # includes trend data
python scripts/dfs_client.py serp   --keyword "<head-term>"    # page-type confirmation
```

Check each keyword's trend data for seasonality before scheduling.

## Process

1. **Score opportunity** — per keyword: volume × intent fit ×
   attainability (difficulty when present). Quick wins go first.
2. **Assign page types** — confirm with `serp` for any ambiguous term:
   guide, comparison, product/category page, tool, FAQ.
3. **Sequence for seasonality** — read the volume trend data: schedule
   seasonal pieces 6-8 weeks before their peak so they can rank in time;
   evergreen pieces fill the gaps.
4. **Order for architecture** — pillars publish before their spokes;
   interlink each spoke on publication day.
5. **Lay out cadence** — map the ordered list onto the user's cadence
   and start date; never schedule two same-intent (competing) pieces in
   the same week.

## Output

A markdown table calendar: week/date | title | target keyword | volume |
intent | page type | cluster (pillar/spoke) | notes (seasonality,
interlinks). Then:
- Top 3 priority pieces with a one-line "why" each
- Seasonal flags: which pieces must ship by which date, and why
- Single best next step: the first piece to brief (offer content-brief)

Write calendars longer than 12 rows to `CALENDAR-<topic>-<date>.md`;
chat shows the first 12 rows plus the priority picks.
