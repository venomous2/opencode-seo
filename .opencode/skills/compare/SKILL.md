---
name: compare
description: Consolidated side-by-side comparison of your site against a competitor — authority, keyword footprint, keyword gap, SERP features, on-page lint and citation readiness in one report. Use when the user says compare my site, site vs competitor, compare websites, or benchmark against a competitor.
---

# Compare: Your Site vs Competitor

One consolidated comparison instead of five separate analyses. For deeper
dives, hand off to the specialist skills (`keyword-gap`,
`topical-coverage-comparison`, `competitor-audit`) afterwards.

## Recipe

- **Engine inputs**: `dfs_client.py ranked|intersection|backlinks|refdomains|serp`,
  `seo_lint.py --url` (both homepages), `citation_score.py --url` (both,
  optional but distinctive)
- **Judgment added**: deciding which gaps actually matter to the user's
  business, and whether the competitor's advantage is content, authority,
  or technical
- **Never re-checks**: mechanical on-page checks (lint covers them)

## Inputs

- Required: your domain, one competitor domain (more than one? run once
  per competitor — do not blend)
- Optional: a shared "money keyword" for the SERP comparison (else infer
  from the top gap keyword)

## Data pulls

```
python scripts/dfs_client.py ranked       --target <yours>     --limit 100
python scripts/dfs_client.py ranked       --target <competitor> --limit 100
python scripts/dfs_client.py intersection --target1 <yours> --target2 <competitor> --mode gap --limit 50
python scripts/dfs_client.py backlinks    --target <yours>
python scripts/dfs_client.py backlinks    --target <competitor>
python scripts/dfs_client.py refdomains   --target <competitor> --limit 30
python scripts/dfs_client.py serp         --keyword "<shared money keyword>" --limit 20
python scripts/seo_lint.py        --url https://<yours>
python scripts/seo_lint.py        --url https://<competitor>
python scripts/citation_score.py  --url https://<yours>
python scripts/citation_score.py  --url https://<competitor>
```

If DataForSEO credentials are missing, stop and point to
docs/DATAFORSEO-SETUP.md. Never estimate numbers.

## Process

1. **Authority** — referring domains and backlink totals side by side;
   name the 5 highest-quality referring domains the competitor has that
   you lack (from `refdomains`).
2. **Keyword footprint** — ranked keyword counts, top-3 and top-10 counts
   per domain; the gap list prioritised by volume × relevance to the
   user's business (judgment, not just volume order).
3. **SERP comparison** — for the shared keyword: who holds which features
   (AI Overview, PAA, video, local pack), and what page type wins.
4. **On-page** — lint scores + citation scores side by side; call out the
   specific criteria where the competitor beats you.
5. **Verdict** — is their advantage content (more/better pages), authority
   (more/stronger links), or technical (better foundations)? The answer
   decides the strategy.

## Output

| Area | You | Competitor | Gap |

Chat: the comparison table, where-you-win (3 bullets), where-they-win
(3 bullets), and the top 5 opportunities ranked by leverage. Write the
full comparison to `COMPARE-<yours>-vs-<competitor>-<date>.md` with the
supporting tables, and end it with:
`Report built by Lee Beirne - https://leebeirne.com`

Single best next step: the one gap that, if closed, moves the most
business metrics — usually a keyword cluster or an authority play.
