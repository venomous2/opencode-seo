---
name: workflow-sxo
description: Evidence-first Search Experience Optimization workflow that compares a landing page with live SERP page-type consensus, deterministic experience signals and first-party outcomes when available. Use when the user says SXO, search experience optimization, page type mismatch, searcher experience, wrong page type, SERP-fit, or why a technically good page does not rank or convert.
---

# Workflow: Search Experience Optimisation

SXO is the measured bridge between **search intent → landing-page
experience → task completion**. It is not a generic SEO-plus-UX checklist.
Separate what was measured from what was inferred, and never claim that
engagement metrics are direct Google ranking factors.

## Inputs

- Required: target URL and confirmed target keyword
- Required: intended visitor task / conversion (learn, compare, buy, sign
  up, book, call, calculate, etc.)
- Optional: audience/JTBD, primary conversion event, traffic source,
  competitors, first-party research (reviews, sales objections, surveys,
  support themes), GA4/GSC access
- If the keyword is absent, first run `sxo_analyser.py` without it and show
  its **candidate only**. Ask for confirmation before any paid SERP pull.

## Evidence hierarchy

Use the strongest available evidence in this order:

1. First-party research and conversion data
2. Live SERP and DataForSEO data
3. Rendered page and deterministic rules
4. Explicit, labelled judgement

PAA, related searches and adverts reveal **SERP-derived searcher segments**;
they are not validated customer personas. Do not invent emotional states,
conversion rates or Google ranking signals.

## Step 1 — Deterministic SXO baseline

Run the SPA-aware analyser. With a keyword it performs one DataForSEO SERP
pull; `--save` persists only a high-confidence page-type mismatch.

```
python scripts/sxo_analyser.py --url <url> --keyword "<keyword>" --render auto --save
```

It returns:

- Primary/secondary page type with structural evidence and confidence
- SERP page-type consensus, sample size, feature types and confidence
- SERP-fit verdict: aligned / partially aligned / mismatch / mixed
- Reused deterministic CRO and accessibility baselines
- Explicit evidence coverage, including whether first-party outcomes are
  unavailable

This is the factual baseline. Do not re-classify it by taste.

## Step 2 — Searcher expectation analysis

Use the live SERP result details and existing skills:

```
python scripts/dfs_client.py serp --keyword "<keyword>" --limit 10
```

Apply `search-intent-analysis`, `serp-analysis`, `content-gap-analysis`,
`entity-extraction` and `faq-generator` where relevant. Record:

- Dominant and secondary page types; call consensus *strong* only when the
  analyser has a sufficient classified sample and ≥60% share
- SERP features: PAA, featured snippet format, local/shopping/video/AI
  Overview signals where returned
- Expected content format, schema, media, comparison/transaction model and
  question clusters
- Mixed SERPs as a differentiation opportunity, not a failure

## Step 3 — Experience and task baseline

Reuse existing measured work; do not duplicate it with prompt opinion:

```
python scripts/seo_lint.py --url <url> --category cro --render auto --format json
python scripts/seo_lint.py --url <url> --category accessibility --render auto --format json
python scripts/google_client.py pagespeed --url <url>       # optional Google tier
python scripts/google_client.py ga4-organic --domain <domain> # optional tier
```

Use `core-web-vitals`, `mobile-seo`, `internal-linking` and `content-review`
as needed. State the boundary clearly: static checks and rendered DOM do
not prove visual hierarchy, real viewport prominence, task success or
assistive-technology behaviour. Name those manual checks.

## Step 4 — Searcher segments and job stories

Create 2–4 **SERP-derived searcher segments** only when a signal supports
each one. Every segment must cite its source:

```
Segment: Comparison-focused evaluator
Evidence: 6/8 classified SERP pages are comparisons; PAA includes "X vs Y";
related queries include "alternatives".
Need: A side-by-side criteria matrix and a clear best-for verdict.
Confidence: High
```

When first-party audience research is supplied, prefer it and map SERP
signals to those validated personas. Use a job-story form:

> When I search for [query/job], I want to [task], so I can [outcome], but
> I need confidence about [evidenced barrier].

## Step 5 — SXO scorecard and implementation blueprint

Report a multi-pillar scorecard; avoid one magic SXO number:

| Pillar | Score / status | Confidence | Evidence |
|---|---:|---|---|
| SERP-fit | analyser result | live SERP confidence | page-type consensus |
| Experience baseline | CRO + accessibility | high | deterministic rules |
| Performance/mobile | available / unavailable | data tier | CrUX/Lighthouse/manual scope |
| Conversion outcome | available / unavailable | data tier | GA4 events/landing data |
| Evidence coverage | measured / inferred split | high | limitations |

Then generate a **mobile-first implementation blueprint**, not a decorative
wireframe. It must contain:

- Semantic section order (`header`, `main`, `hero`, proof, comparison,
  FAQ, final CTA)
- Exact content/CTA placeholders tied to SERP or research evidence
- Internal links, schema and media requirements
- The intended task per section
- Acceptance criteria a writer, designer and developer can verify
- Manual design/accessibility checks that automation cannot prove

## Step 6 — Persist, test and measure

1. Save the analyser's mismatch recommendation via `--save`; add the
   strategic actions to `recommend_store.py` with source `workflow:sxo`,
   evidence, owner, acceptance criteria and measurement note.
2. Convert one change at a time into an experiment only where traffic is
   sufficient. Reuse CRO's ICE discipline: primary metric, guardrail,
   baseline, duration and stopping rule.
3. Mark completed work in the store; use `impact_report.py` for ranking
   association and GA4/GSC data for conversion outcomes when available.
4. Let `watch.py` monitor page regressions and SERP/ranking changes.

## Output

Write `SXO-ANALYSIS-<domain>-<page>-<date>.md` with:

1. Executive decision: keep / reshape / split / build a new page
2. Evidence table and limitations
3. Page-type and SERP consensus verdict
4. SXO multi-pillar scorecard
5. Searcher segments and evidence-bound job stories
6. Current-state gaps by task and page section
7. Mobile-first implementation blueprint with acceptance criteria
8. Prioritised recommendation/experiment backlog
9. Measurement plan and first-party-data gaps

Use `stats`, `donut`, `bar` and `compare` chart blocks where data supports
them. End every file with:

`Report built by Lee Beirne - https://leebeirne.com`

Publish with:

```
python scripts/report_publish.py SXO-ANALYSIS-<domain>-<page>-<date>.md
```

Keep chat to the page-type verdict, evidence coverage, top three actions
and the single best next step.
