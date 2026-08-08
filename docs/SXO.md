# Search Experience Optimisation

Search Experience Optimisation (SXO) asks whether a searcher lands on the
**right kind of page**, can understand and trust it, and can complete the
task they came to do.

OpenCode SEO Suite treats SXO as a measured bridge:

```text
Search intent -> landing-page experience -> task completion -> learning
```

It is not a claim that bounce rate or dwell time are direct Google ranking
factors. Search evidence, page evidence and first-party outcome evidence
are reported separately.

## When to use it

Use SXO when a page is technically sound but still fails to rank, satisfy
searchers or convert. Typical prompts:

```text
/sxo https://example.com/grinder-guide "best coffee grinder" buy

Why does this technically good page not rank for "project management software"?

Does our pricing page match what people expect for "CRM pricing"?
```

The workflow needs:

- A URL
- A **confirmed** keyword
- The intended visitor task: learn, compare, buy, sign up, book, call,
  calculate, and so on

If you omit the keyword, the analyser shows a title/H1-derived candidate
but deliberately does **not** spend on DataForSEO until you confirm it.

## Fast deterministic baseline

```powershell
python scripts/sxo_analyser.py `
  --url https://example.com/grinder-guide `
  --keyword "best coffee grinder" `
  --render auto `
  --save
```

This makes one live SERP pull and returns JSON containing:

- Primary and secondary page type, with structural evidence
- Live SERP page-type consensus, sample size and confidence
- SERP-fit verdict: `aligned`, `partially_aligned`, `mismatch`, or `mixed`
- Existing deterministic CRO and accessibility baselines
- Evidence coverage, including whether first-party outcomes are absent

When a high-confidence page-type mismatch is found, `--save` persists it
to the recommendation store:

```powershell
python scripts/recommend_store.py list --domain example.com
```

The analyser never claims business truth. A page can have an article and a
landing-page model at once; it returns ranked candidates and confidence
instead of forcing one arbitrary label.

## What page types mean

The deterministic classifier uses observable signals such as schema,
title/H1/URL patterns, CTA/form signals, tables, author/date signals and
contact links. It recognises:

| Type | Typical measured signals |
|---|---|
| Product | Product/Offer schema, product URL, buy/shop language |
| Comparison | versus/alternatives language, comparison-capable tables |
| Local | LocalBusiness schema, location/contact URLs, telephone link |
| Tool | WebApplication/SoftwareApplication schema, forms, tool language |
| Service | Service/ProfessionalService schema, consulting/service language |
| Article | Article schema, author/date signals, editorial URL |
| Landing | Multiple CTAs, form, concise conversion-oriented depth |
| Hybrid | Strong editorial and conversion signals together |

The SERP classifier works from DataForSEO organic result title/URL signals.
If fewer than three results are classifiable, or no type reaches 40%, it
reports a fragmented/mixed SERP rather than inventing a consensus.

## The SXO scorecard

Do not rely on one magic SXO number. A good report separates the pillars:

| Pillar | Evidence | Meaning |
|---|---|---|
| SERP-fit | Live DataForSEO SERP | Is the page type/format aligned with what currently ranks? |
| Experience baseline | CRO and accessibility rules | Can visitors identify, trust and act on the page? |
| Performance/mobile | CrUX/Lighthouse/manual review | Does the delivered experience work across devices? |
| Conversion outcome | Optional GA4/GSC and research | Do visitors complete the intended task? |
| Evidence coverage | Data-source inventory | What is measured, inferred or unavailable? |

A mismatch in the first two pillars is actionable today. The latter pillars
must say `unavailable` until you connect or provide first-party evidence.

## Searcher segments, not invented personas

PAA, related queries, adverts and result formats reveal **SERP-derived
searcher segments**. They are useful planning evidence, but they are not
validated customer personas.

Every segment in an SXO report must include its signal source:

```text
Segment: Comparison-focused evaluator
Evidence: 6/8 classifiable SERP pages are comparisons; PAA includes
"X vs Y"; related queries include "alternatives".
Need: A side-by-side criteria matrix and a clear best-for verdict.
Confidence: High
```

Project memory can hold validated audience evidence:

```yaml
audience:
  personas: []
  research_sources: ["sales-call themes", "2026 customer survey"]

goals:
  conversion:
    primary_task: "book"
    primary_event: "generate_lead"
    guardrail_metrics: ["qualified_lead_rate"]
```

When supplied, first-party evidence takes precedence over inferred SERP
segments.

## Implementation blueprint

SXO outputs a **mobile-first implementation blueprint**, not a mockup that
pretends to replace a designer. It should specify:

- Semantic section order: hero, proof, comparison, FAQ, final CTA
- Exact content, CTA and link placeholders tied to SERP/research evidence
- Required schema, media and internal links
- Intended visitor task per section
- Testable acceptance criteria for writer, designer and developer
- Manual checks the suite cannot prove: visual hierarchy, real viewport
  prominence, keyboard journey and assistive-technology behaviour

Example acceptance criterion:

```text
After the comparison matrix, include a "See pricing" CTA linking to
/pricing#enterprise. The matrix must compare the three criteria recurring
in PAA questions. Verify on a 375px rendered viewport and re-lint the DOM.
```

## SXO versus CRO

| CRO audit | SXO workflow |
|---|---|
| Starts with on-page conversion signals | Starts with searcher expectation and page type |
| Asks whether visitors can convert | Asks whether the page deserves to be the landing experience for this query |
| Uses intent-to-offer alignment | Uses live SERP page-type consensus plus experience/task fit |
| Ends in ICE experiments | Ends in a page decision, implementation blueprint, persisted backlog and measurement plan |

Use `/cro` for a conversion problem on an already-correct landing page. Use
`/sxo` when the query, page type, searcher task and landing experience may
be misaligned.

## Close the loop

1. Persist the page-type mismatch and strategic actions to the
   recommendation store.
2. Implement one primary change at a time, with an acceptance criterion.
3. Use `watch.py` to catch regressions.
4. Use `impact_report.py` for ranking association after completion.
5. When GA4/GSC conversion evidence is available, report it as an outcome
   signal, not proof that the SXO change caused it.

See [USER-GUIDE.md](USER-GUIDE.md) for the broader workflow and
[GOOGLE-APIS.md](GOOGLE-APIS.md) for optional Google-data setup.
