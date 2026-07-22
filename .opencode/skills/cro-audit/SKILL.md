---
name: cro-audit
description: Conversion rate optimisation audit with deterministic page analysis, SERP intent-goal alignment, competitor benchmarking, objection mining, and an ICE-scored experiment plan. Use when the user says CRO, conversion rate, landing page not converting, improve conversions, A/B test ideas, or why aren't visitors converting.
---

# CRO Audit

Conversion audit that starts from **measured page facts, not opinion**.
Every deterministic signal comes from the rule engine; judgment layers
intent, competitors, and real market objections on top. This is what
prompt-only CRO checklists cannot do.

## Inputs

- Required: page URL + primary conversion goal (sale / lead / signup /
  booking / call — ask if unclear)
- Optional: traffic source (organic/paid/email), target keyword if the
  page ranks, GA4 landing data when tier ≥ 2

## Step 1 — Deterministic baseline (facts, identical under any model)

```
python scripts/seo_lint.py --url <page> --category cro --format text
```

Ten measured signals: CTA presence/position/text, form friction + CAPTCHA,
trust signals, phone link, urgency, CTA competition, FAQ presence. Record
each as evidence — never re-judge them by eye.

Also pull speed context (a known conversion factor):
`python scripts/dfs_client.py lighthouse --url <page>` (optional).

## Step 2 — Intent-goal alignment (the check competitors don't do)

```
python scripts/dfs_client.py serp --keyword "<page's main keyword>" --limit 10
```

Classify the keyword's intent (informational / commercial / transactional),
then judge: **does the page's offer match what the searcher came for?**
Common failure: ranking for an informational query while pushing a hard
sale (mismatch — needs a softer CTA or a different page). Another: a
transactional query landing on a page with no offer at all.

## Step 3 — Competitor benchmark

Fetch the top 2-3 SERP rivals (webfetch) and run the same deterministic
checks (lint each with `--category cro`). Build the comparison:

| Signal | Your page | Competitor A | Competitor B |

The pattern is the insight: if every page beating you shows review counts
near the CTA and you show none, that's not taste — that's the market
telling you what converts.

## Step 4 — Objection mining (real, not generic)

- PAA questions from the SERP pull (the market's live objections)
- Competitor FAQs — what do they answer that you don't?
- Optional: `dfs_client.py content --keyword "<brand> reviews"` for
  review-site objections

Turn these into the FAQ/trust recommendations, verbatim where possible.

## Step 5 — Experiment plan (ICE-scored, hypothesis-led)

Convert each finding into a testable hypothesis, not a "recommendation":

> **H1**: Changing the primary CTA from "Submit" to "Get my free quote"
> will lift form completion ≥ 20%, because value-driven labels state the
> payoff. **ICE**: Impact 8 / Confidence 7 / Effort 2 → priority 1.
> **Measure**: form completion rate, 2 weeks or 95% significance.

Rules: ICE = (Impact + Confidence) / Effort. One variable per test. No
tests on pages under ~1,000 weekly visits — fix and move on instead.
Never test fake urgency or dark patterns.

## Output

Write `CRO-AUDIT-<domain>-<page>-<date>.md`:
- `stats` chart block: CTA count, above-fold count, trust signals, form fields
- Signal table (deterministic findings with evidence)
- Intent-goal alignment verdict
- Competitor comparison table (`compare` chart block where numeric)
- Experiment plan: ICE-ranked hypotheses with measurement notes
- Copy alternatives: 3 headline + 3 CTA rewrites grounded in the page's
  keywords and the mined objections
- Footer: `Report built by Lee Beirne - https://leebeirne.com`

Publish: `python scripts/report_publish.py CRO-AUDIT-<domain>-<page>-<date>.md`

Chat gets: the deterministic signal summary, the intent verdict, and the
top 3 hypotheses by ICE. Single best next step stated last.

## Output location

Save generated files to the SEO reports directory - `%SEO_REPORTS_DIR%\<name>\` on Windows, `$SEO_REPORTS_DIR/<name>/` on macOS/Linux - when the `SEO_REPORTS_DIR` environment variable is set; otherwise the current working directory. Create the subfolder if it doesn't exist.

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
