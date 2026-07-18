---
name: search-intent-analysis
description: Classifies keywords by search intent (informational / commercial / transactional / navigational) using the live SERP instead of guesswork. Use when the user says search intent, intent analysis, what intent is this keyword, or what kind of page should I build for X.
---

# Search Intent Analysis

Determines what Google actually rewards for a keyword — page types, SERP
features, and the page the user should build. Every classification uses
live SERP data; never assumes intent from keyword wording alone.

## Inputs

- Required: one or more keywords to classify
- Optional: location/language (defaults: United States / English, or the
  values in `seo-project.yml`); the user's existing page URL, if checking
  whether it matches intent

## Data pulls

Run with bash (one serp call per keyword; parallelize when listing several):

```
python scripts/dfs_client.py serp   --keyword "<keyword>" --limit 20
python scripts/dfs_client.py volume --keywords "kw1,kw2"   # CPC as commercial proxy
```

If the user has an existing page, fetch it with the webfetch tool to
compare its type against what ranks.

## Process

1. **Read the SERP** — for each keyword, note the dominant page type in
   positions 1-10: blog post, category page, product page, tool, video,
   forum, homepage. The majority type is the dominant intent.
2. **Check SERP features** — featured snippet / People Also Ask
   (informational), shopping results / heavy ads (transactional), reviews
   and comparisons (commercial investigation), sitelinks to one brand
   (navigational).
3. **Classify** — informational / commercial / transactional /
   navigational, with a mixed-intent flag when the top 10 splits (e.g.,
   6 informational + 4 product pages). Mixed intent: pick the majority
   type, or plan one page per intent.
4. **Prescribe the page** — state exactly which page type to build, or
   whether an existing page type mismatches the SERP and must be reworked
   before anything else will work.
5. **Flag traps** — high-volume keywords whose intent the user's site
   cannot satisfy (e.g., navigational queries for a competitor's brand).

## Output

A markdown table: keyword | dominant intent | mixed? | dominant page type
| key SERP features | page to build. Follow with:
- Evidence per keyword: the actual page types found in the top 10
- Prioritized list of mismatches (user page type ≠ SERP page type),
  highest traffic opportunity first, with a one-line "why" each
- Single best next step: the one keyword/page to fix or build first

Write the full classification to `INTENT-<topic>-<date>.md` when it
exceeds 20 keywords; keep chat concise.
