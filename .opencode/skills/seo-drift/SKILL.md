---
name: seo-drift
description: Captures dated SEO snapshots for a domain — audit scores, live rankings, backlink counts, and AI mentions — and diffs any two snapshots into an evidence-based change report. Use when the user says drift, what changed, rankings dropped, compare snapshots, or SEO monitoring.
---

# SEO Drift Monitoring

Point-in-time snapshots plus diffs. Answers "what changed since last
month?" with stored evidence instead of memory and guesswork.

## Inputs

- Required: domain
- Capture mode: nothing else needed — reuse pillar scores from the last
  audit file when one exists
- Compare mode: optional `--from` / `--to` snapshot timestamps (defaults:
  oldest vs newest)

## When to snapshot

- After every audit — the audit's pillar scores become the `scores` section
- On a monthly cadence for retained clients, same week each month
- Immediately before and after migrations, redesigns, and major releases
- After a confirmed Google core update finishes rolling out

## Data pulls (capture mode)

Run live pulls in parallel, then assemble one JSON snapshot:

```
python scripts/dfs_client.py ranked    --target <domain> --limit 100
python scripts/dfs_client.py backlinks --target <domain>
python scripts/dfs_client.py mentions  --keyword "<brand name>"
```

Snapshot JSON shape (every section optional — save what you have):

```json
{
  "scores":    {"technical": 74, "content": 81, "authority": 60},
  "rankings":  [{"keyword": "...", "position": 5, "url": "..."}],
  "backlinks": {"referring_domains": 120, "backlinks": 3400},
  "mentions":  {"ai_mentions": 12},
  "notes":     "core update finished 12 Mar; homepage redesigned"
}
```

Save it and confirm it landed:

```
python scripts/drift_store.py save --domain <domain> --file snapshot.json
python scripts/drift_store.py list --domain <domain>
```

(`save` also reads JSON from stdin when `--file` is omitted.) Never
fabricate numbers to fill a section — omit whatever could not be pulled.

## Process (compare mode)

1. Pull the diff:

   ```
   python scripts/drift_store.py compare --domain <domain> [--from TS] [--to TS]
   ```

2. Interpret with significance rules — do not report noise:
   - Score deltas ≥ 5 points are meaningful; smaller is wobble
   - Position moves ≥ 3 places matter; 1-2 place shuffles are normal churn
   - Keywords gained/lost matter in proportion to volume — re-check the
     important ones with `dfs_client.py volume` and inspect intent shifts
     with `dfs_client.py serp`
   - Referring-domain movement ≥ 5% is a trend; below that, call it flat
   - AI mention changes are directional only (small samples)
3. Attribute causes only where evidence exists: match changes against the
   `notes` trail, releases the user mentions, and known update dates. Say
   "cause unknown" when there is no evidence — never invent a reason.
4. Recommend actions only for significant negative movements, each with a
   one-line "why".

## Output

- Chat: delta table (pillar scores old -> new), keywords gained / lost /
  moved ≥ 3 places (top 15 by volume), referring-domain and mention
  deltas, then prioritised actions.
- Visual diffs: `python scripts/drift_store.py chart --domain <domain>`
  prints ready-made ```` ```chart ```` blocks (compare bars for scores and
  metrics, stats cards for ranking movement) — paste them into the report
  so `report_build.py` renders the before/after story as graphs.
- When the diff is large or spans a quarter, write
  `DRIFT-<domain>-<date>.md` with the full tables and end it with:
  `Report built by Lee Beirne - https://leebeirne.com`
- Single best next step: the one regression to investigate first —
  usually the highest-volume lost keyword or the largest score drop.
