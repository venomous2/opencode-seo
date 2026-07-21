---
name: llm-citation-readiness
description: Scores how ready a page is to be cited by LLM-based search engines against a citability checklist, with a mention baseline and prioritized fix list. Use when the user says LLM citations, citation readiness, AI citations, or get cited by AI.
---

# LLM Citation Readiness

A scoring audit: how ready is this page to be found, extracted, and cited
by LLM-based search (AI Overviews, AI Mode, ChatGPT search, Perplexity)?
Honest framing: readiness improves the controllable inputs — clarity,
citability, discoverability. It does not and cannot guarantee citation.

## Inputs

- Required: target URL(s) or pasted page content, brand name
- Optional: competitor URLs for comparison scoring

## Data pulls

Deterministic baseline (model-agnostic, always run this first):

```
python scripts/citation_score.py --url <page> --format text
```

This scores the page 0-100 across 11 weighted criteria (answer block,
question headings, author, dates, sourcing, editorial schema, structure,
depth, factual density, image accessibility, indexation) with per-criterion
recommendations. It never calls a model, so results are identical under
any LLM. Your job is to interpret the criteria, not re-check them by hand.

Then the live baselines:

```
python scripts/dfs_client.py mentions --keyword "<brand>" --limit 50 --pretty
python scripts/dfs_client.py serp     --keyword "<page target keyword>" --limit 20
```

`mentions` gives the current AI-citation baseline; the SERP pull shows
whether an AI Overview exists for the target query and who gets cited.
Fetch each target page with webfetch. If credentials are missing, stop
and point the user to docs/DATAFORSEO-SETUP.md.

## Process

1. **Run the deterministic scorer** (`citation_score.py`) — adopt its
   11-criterion breakdown as the objective baseline.
2. **Layer judgment where the scorer is blind** — the script cannot assess
   entity coverage vs competitors, claim accuracy, or prose quality. For
   those, compare against the pages that actually rank (and get cited) for
   the target query:
   - Entity clarity — brand/product naming consistent; Organization/Person
     schema with sameAs present
   - Access — server-rendered content; robots rules for the AI crawlers the
     user wants (check robots.txt with webfetch)
   - Competitive citability — what do cited competitors have that this page
     lacks (unique data, tools, expert quotes)?
3. **Combine** into one scorecard: deterministic criteria + judgment items,
   each with evidence and fix.

## Output

- Citation score (0-100, from the scorer) + grade, then the criterion
  table: criterion | status | evidence | fix
- Mention baseline: current mentions vs. the competitor set (from
  `mentions`)
- Prioritised fix list (critical/high/medium/low), each with a one-line
  "why" — deterministic fixes first (they're provable), judgment fixes second
- Single best next step: the lowest-scoring criterion with the highest
  leverage — usually the answer block or sourcing

Write the full scorecard to `CITATION-READINESS-<domain>-<date>.md` when
auditing more than ~5 pages.

## Output location

Save generated files to the SEO reports directory - `%SEO_REPORTS_DIR%\<name>\` on Windows, `$SEO_REPORTS_DIR/<name>/` on macOS/Linux - when the `SEO_REPORTS_DIR` environment variable is set; otherwise the current working directory. Create the subfolder if it doesn't exist.

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
