---
name: backlink-opportunity-planner
description: Plans ethical link acquisition using competitor referring-domain gaps, anchor patterns, and pitchable asset ideas from live DataForSEO backlink data. Use when the user says link building, backlink opportunities, get backlinks, digital PR, or who links to competitors.
---

# Backlink Opportunity Planner

Finds where competitors earn links, identifies realistic prospects the user
lacks, and designs assets worth pitching. Quality and relevance over volume —
no link schemes, no paid-link farms, no PBNs.

## Inputs

- Required: user domain
- Optional: 2-3 competitor domains (else from `seo-project.yml` via
  `python scripts/project_memory.py`, else discover with `competitors`)

## Data pulls

```
python scripts/dfs_client.py refdomains --target "<user-domain>" --limit 100
python scripts/dfs_client.py refdomains --target "<competitor-a>" --limit 100
python scripts/dfs_client.py refdomains --target "<competitor-b>" --limit 100
python scripts/dfs_client.py anchors    --target "<competitor-a>" --limit 50
python scripts/dfs_client.py backlinks  --target "<competitor-a>" --limit 100
```

Run competitor pulls in parallel. If credentials are missing, stop and point
the user to docs/DATAFORSEO-SETUP.md. Do not invent numbers.

## Process

1. **Build the link gap** — set difference: domains linking to ≥1 competitor
   but not to the user. Domains linking to multiple competitors are the
   warmest prospects (they demonstrably link out in this niche).
2. **Qualify prospects** — for each gap domain, classify the link type from
   the `backlinks` rows: editorial mention, resource list, guest post,
   directory, tool/integration page, press. Discard directories and obvious
   paid placements; keep editorial and resource links — those are winnable.
3. **Read anchor patterns** — from `anchors`, note what text competitors
   earn: brand, naked URL, exact-match keyword, descriptive. Heavy
   exact-match anchors are a risk pattern to avoid copying; natural profiles
   are mostly brand/URL anchors.
4. **Trace link-worthy content** — which competitor URLs attract the most
   referring domains? Those pages reveal what the niche rewards: original
   data, free tools, definitive guides, statistics pages.
5. **Design pitchable assets** — propose 3-5 assets the user could build
   that match proven link magnets but improve on them (fresher data, better
   UX, unique angle). Each asset needs a pitch angle: why would the prospect
   domain link to it?

## Output

- Link-gap table: prospect domain | competitors linking | link type |
  target page on their site | suggested approach
- Anchor-text summary: competitor patterns + what a healthy profile looks
  like for the user
- 3-5 asset ideas, each with: concept, why it earns links (evidence from
  competitor data), target prospect list, pitch angle in one sentence
- Outreach principles reminder: personalize, lead with value, one follow-up
  max, never buy links
- Single best next step (highest-fit prospect + asset pairing)

Full prospect lists go to `LINK-PROSPECTS-<domain>-<date>.md`.
