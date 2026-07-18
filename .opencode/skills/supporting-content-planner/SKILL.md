---
name: supporting-content-planner
description: Plans supporting (spoke) articles around a pillar — titles, live target keywords, differentiated angles, and the interlinking pattern back to the pillar. Use when the user says supporting content, spoke articles, cluster content plan, or what articles support my pillar.
---

# Supporting Content Planner

Plans the spoke articles that surround a pillar page, each with a unique
keyword target and angle so spokes never cannibalize each other or the
pillar. All keywords are validated with live data.

## Inputs

- Required: pillar topic (or pillar URL); candidate spoke topics, if the
  user has them
- Optional: location/language; user's domain

## Data pulls

Run with bash:

```
python scripts/dfs_client.py ideas   --keyword "<pillar-topic>" --limit 100
python scripts/dfs_client.py related --keyword "<pillar-topic>" --limit 50
python scripts/dfs_client.py volume  --keywords "kw1,kw2,..."
python scripts/dfs_client.py serp    --keyword "<spoke-candidate>"   # per ambiguous spoke
```

## Process

1. **Pool candidates** — long-tail and question keywords from
   ideas + related; dedupe against the pillar's own target keyword.
2. **One keyword, one page** — group candidates that share SERP intent
   (spot-check with `serp`); each surviving group becomes one spoke.
   Overlap with the pillar or another spoke = merge, never publish both.
3. **Differentiate angles** — give each spoke a distinct job: how-to,
   comparison, listicle, troubleshooting, pricing, beginner vs advanced,
   audience-specific. No two spokes with the same angle and same intent.
4. **Title & target** — draft an H1-level title per spoke with its
   primary keyword and live volume.
5. **Interlinking pattern** — every spoke links to the pillar within its
   first two paragraphs using descriptive anchor text on the pillar
   keyword; the pillar adds a matching link out to each spoke; add 1-2
   lateral links between adjacent spokes.

## Output

A markdown table: spoke title | primary keyword | volume | intent |
angle | link-back anchor text | priority (P1-P3). Then:
- The spoke-to-pillar link map spelled out explicitly (who links where,
  with which anchor)
- Cannibalization warnings where candidates were merged, with the SERP
  evidence
- Single best next step: brief the P1 spoke (offer content-brief)

Write plans over 15 spokes to `SPOKES-<topic>-<date>.md`; chat shows the
top 15 rows.
