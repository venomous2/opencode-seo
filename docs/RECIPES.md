# Recipes: how new skills consume the engine

The suite's architecture has two halves:

- **The deterministic engine** — rules (`rules/`), lint (`seo_lint.py`),
  fixes (`seo_fix.py`), citation scoring (`citation_score.py`), and the
  data layer (`dfs_client.py`, `google_client.py`). Pure Python, zero model
  calls, identical results under any LLM.
- **The skills** — markdown procedures that add judgment: strategy,
  interpretation, taste, and client communication.

A **recipe** is the contract every new skill must follow: it declares what
the skill consumes from the engine and what judgment it adds on top. This
keeps knowledge in one place (the engine) and prevents skills from
duplicating checks.

## The recipe contract

Every new skill MUST answer these five questions, in this order, inside its
body (a short "Recipe" section right after the frontmatter is fine):

1. **Engine inputs** — which deterministic tools does it run?
   (`seo_lint.py`, `citation_score.py`, `seo_fix.py`, `rule_engine.py`,
   `dfs_client.py <commands>`, `google_client.py <commands>`,
   `drift_store.py`, `report_build.py`…)
2. **Rule categories** — which rule categories matter to its output, if any?
   (metadata, headings, indexability, content, images, schema, mobile,
   international, links)
3. **Judgment added** — what does it do that the engine cannot?
   (interpretation, prioritisation, competitive comparison, prose, strategy)
4. **Never re-checks** — which engine results does it *adopt* instead of
   duplicating? (e.g. "uses lint findings; does not re-verify title length")
5. **Output** — chat summary shape + report file pattern (written to
   `%SEO_REPORTS_DIR%\<name>\`, British English, footer
   `Report built by Lee Beirne - https://leebeirne.com`).

## Rules of thumb

- **If the engine can check it, the skill must not re-check it.** Adopt the
  engine's evidence and move on to interpretation.
- **If a check is mechanical and missing, add a rule — not prose.** New
  deterministic capability goes in `rules/<category>/<id>.yaml` with
  embedded tests, never inside a skill's markdown.
- **Skills stay thin where the engine is strong, deep where it is blind.**
  Thin: lint, fix, scoring. Deep: briefs, PR, strategy, competitive reads.
- **Model-agnostic means the engine does the detecting.** Skills may be run
  by any of OpenCode's 400+ models; the deterministic output is the anchor
  that keeps results consistent across all of them.

## Template for a new skill

```markdown
---
name: my-new-skill
description: What it does and when to trigger it, with literal keywords
  the user would say. Use when the user says ...
---

# My New Skill

## Recipe

- Engine inputs: `seo_lint.py --url`, `citation_score.py --url`,
  `dfs_client.py serp|ranked`
- Rule categories: metadata, headings, schema
- Judgment added: interprets findings against the live SERP; decides
  which low-confidence rules don't apply to this page type
- Never re-checks: title/meta/H1/canonical (lint), citation criteria (scorer)
- Output: findings table + top 3 fixes; report to
  `%SEO_REPORTS_DIR%\<domain>\MYSKILL-<domain>-<date>.md`

## Inputs
...

## Data pulls
...

## Process
...

## Output
...
```

## A worked example: `on-page-seo` as a recipe

If the existing `on-page-seo` skill were written today as a recipe:

- **Engine inputs**: `seo_lint.py --url <page>` (26 mechanical checks),
  `citation_score.py --url <page>` (11 readiness criteria),
  `seo_fix.py --url <page> --format text` (mechanical patches ready to
  apply), `dfs_client.py serp` (what the page must beat).
- **Rule categories**: all nine — it's the full page review.
- **Judgment added**: page-type context (is `page-noindex` intentional
  here? does `missing-article-schema` apply to a product page?), depth
  comparison vs the top 5 SERP results, internal link targets worth adding.
- **Never re-checks**: anything the engine already scored — it cites lint
  and citation findings as evidence.
- **Output**: scorecard (lint score + citation score), contextualised
  findings, fixes split into *mechanical* (apply via `seo_fix.py --apply`)
  and *judgment* (rewrite guidance).

Notice what happened: the skill got *smaller* and *better* at once. That
is the point of the recipe pattern.

## Where new checks go (decision tree)

```
Is the check deterministic (answerable from page/API data alone)?
├── YES → add a rule in rules/<category>/<id>.yaml (+ embedded tests)
│         it now powers lint, CI, fixes, and every future skill
└── NO (needs taste/context/language) → it belongs in a skill
        the skill consumes engine evidence and adds that judgment
```
