---
name: gbp-advisor
description: Audits and optimizes a Google Business Profile using live DataForSEO business data — categories, description, services, photos, posts, Q&A, and reviews. Use when the user says Google Business Profile, GBP, Google My Business, or optimize my business listing.
---

# GBP Advisor

Audits the current Google Business Profile against local ranking best
practice and produces a concrete optimization plan. Everything starts from
the live profile, not assumptions.

## Inputs

- Required: business name (plus city if the name is generic)
- Optional: target keywords, competitor GBP names for benchmarking

## Data pulls

```
python scripts/dfs_client.py business --keyword "<business name> <city>"
python scripts/dfs_client.py business --keyword "<competitor name> <city>"   # benchmark, optional
python scripts/dfs_client.py serp     --keyword "<primary keyword>" --location "<city>" --limit 20
```

If credentials are missing, stop and point the user to
docs/DATAFORSEO-SETUP.md. Do not invent numbers. If the business data pull
returns nothing, verify the exact business name and city before concluding
the profile is unclaimed.

## Process

Audit each element against the standard:

1. **Categories** — one precise primary category (the single strongest
   ranking lever in GBP), plus every genuinely applicable secondary
   category. Compare with competitors' categories from the benchmark pull.
2. **Name & description** — business name must be the real-world name only
   (no keyword stuffing — it risks suspension). Description: what you do,
   who you serve, differentiators, in plain language.
3. **Services / products** — every service listed with a real description
   and price where applicable; these surface in profile searches.
4. **Photos** — logo, cover, exterior, interior, team, work/product shots.
   Fresh, geotagged-by-reality (not EXIF tricks), added regularly. Profiles
   with strong photo sets earn more actions.
5. **Posts cadence** — weekly minimum: updates, offers, events. Posts decay;
   a stale last-post date is a finding.
6. **Q&A** — seed and answer the real questions customers ask (anyone can
   ask and answer — the owner should control the narrative). Flag
   unanswered public questions as urgent.
7. **Reviews** — count, recency, average vs competitors. Response policy:
   reply to all reviews, thank specifics, never argue, move disputes
   offline. No incentivized or gated reviews — that violates policy.
8. **Attributes, hours, booking/menu links** — complete every applicable
   attribute; special hours for holidays; correct action links.

## Output

- Current-state table: element | live value (from data) | pass/gap
- Benchmark line vs competitors (review count, rating, categories)
- Gap list ordered by ranking impact, each with the exact fix and one-line
  why
- Cadence plan: weekly posts, monthly photo adds, ongoing review asks
- Single best next step (usually: fix primary category or answer open Q&A)
