---
name: workflow-quarterly-review
description: Quarterly SEO business review workflow that turns drift snapshots, GSC and GA4 trends, and content decay triage into a wins/losses narrative and next-quarter plan, rendered as a client-ready HTML pack. Use when the user says quarterly review, QBR, SEO report for client, monthly report, or stakeholder update.
---

# Workflow: Quarterly SEO Review

The client-facing review: what changed this quarter, why, and what we do
next. Built from stored snapshots and live pulls — never from vibes.

## Inputs

- Required: client domain
- Optional: client name (loads context via
  `python scripts/project_memory.py --client <name>`), quarter
  boundaries, last quarter's priority list (to grade delivery)

## Steps

### 1. Frame the quarter from stored drift

```
python scripts/drift_store.py list --domain <domain>
python scripts/drift_store.py compare --domain <domain> --from <quarter-start-ts> --to <latest-ts>
```

This yields score deltas, keywords gained/lost/moved, and link growth
across the whole period. If no start-of-quarter snapshot exists, compare
the two closest available and say so — never reconstruct history from
memory.

### 2. Traffic and query trend (optional Google layer)

If the Google tier is configured, pull two equal periods and compare
(e.g. this quarter vs last):

```
python scripts/google_client.py gsc-queries --site sc-domain:<domain> --start <d1> --end <d2>
python scripts/google_client.py gsc-queries --site sc-domain:<domain> --start <d3> --end <d4>
python scripts/google_client.py ga4-organic --start <d1> --end <d2>
```

Rising queries are wins to name; falling queries are losses to explain.
Skip silently if not configured; do not estimate traffic.

### 3. Fresh snapshot as next quarter's baseline

```
python scripts/dfs_client.py ranked    --target <domain> --limit 200
python scripts/dfs_client.py backlinks --target <domain>
python scripts/dfs_client.py mentions  --keyword "<brand>"
```

Save via `drift_store.py save` so next quarter starts from a clean
baseline. For engagement cost context:
`python scripts/cost_ledger.py report`.

### 4. Content decay triage

From the drift diff and GSC drops, list the top 5-10 declining URLs by
recoverable value. Hand the list to the `workflow-content-refresh` skill
for per-URL triage (update / merge / redirect / prune) — do not duplicate
its analysis here; cite its output.

### 5. Wins / losses narrative

One paragraph each, written for a non-SEO:

- Wins: specific — keyword, page, or metric, plus what we did that caused
  it
- Losses: honest — separate what we controlled (missed refreshes,
  technical regressions) from what we did not (core updates, seasonality,
  new competitors). Never blame the algorithm before checking our own
  changes first.
- Grade last quarter's priorities: delivered / partial / not done, with
  the measured result where drift or GSC shows one.

### 6. Next-quarter priorities

Three to five priorities, each carrying: the action, a one-line "why",
the metric it should move, and a suggested owner. Sequence dependencies
first — indexability before content before links.

### 7. Write and render

Write `QBR-<client>-<year>-Q<n>.md`: executive summary, quarter scorecard
(drift deltas), wins, losses, priority grades, decay triage summary,
next-quarter plan, appendix of raw pulls. Then render the client pack:

```
python scripts/report_build.py QBR-<client>-<year>-Q<n>.md -o QBR-<client>-<year>-Q<n>.html --brand "Lee Beirne"
```

## Output

- Files: the markdown report plus the rendered HTML pack. End the
  markdown file with:
  `Report built by Lee Beirne - https://leebeirne.com`
- Chat: the scorecard table, a three-line wins/losses summary, next
  quarter's top 3 priorities, and the file paths.
- Single best next step: the first next-quarter priority, stated plainly.
- British English throughout; no hype — the review's credibility is the
  deliverable.
