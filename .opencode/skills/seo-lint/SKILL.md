---
name: seo-lint
description: Deterministic SEO linting of a URL, HTML file, or directory using the suite's rule engine — 26+ checks with scores, severity-ranked findings, and a CI quality gate. Use when the user says lint, SEO lint, check this page, SEO tests, CI SEO check, or quality gate.
---

# SEO Lint

Runs the suite's rule engine against a page or set of pages. The engine is
**deterministic and model-agnostic**: detection happens in Python against
YAML rules, never in an LLM, so results are identical regardless of which
model is driving OpenCode. Your job is to run it, interpret the output, and
prioritise.

## Inputs

- One of: `--url <live page>`, `--file <local.html>`, `--dir <folder>`
- Optional: `--category` (metadata, headings, indexability, content,
  images, schema, mobile, international, links), `--min-score` (CI gate),
  `--format text` for human-readable output

## Run it

```
python scripts/seo_lint.py --url <url> --format text
python scripts/seo_lint.py --file <page.html> --format text
python scripts/seo_lint.py --dir <folder> --min-score 80
python scripts/rule_engine.py list                 # every available rule
python scripts/rule_engine.py test                 # self-test all rules
```

## Process

1. **Run the linter** and read the findings (severity, evidence, why, fix).
2. **Triage** — group findings by severity: critical first (indexability,
   missing title/H1, very thin content), then high, then polish.
3. **Contextualise** — rules are page-type-blind by design. Dismiss
   low-confidence rules that don't apply (e.g. `missing-article-schema` on
   a product page, `page-noindex` on a deliberate noindex) and say why.
4. **Fix mechanically where possible** — run the fix engine to generate
   concrete patches (JSON-LD, canonical, meta description draft, viewport,
   html lang) and apply them to local files:

   ```
   python scripts/seo_fix.py --url <url> --format text        # dry-run
   python scripts/seo_fix.py --file <page.html> --base-url <prod-url> --apply
   ```

   `--apply` writes a `.bak` backup, rewrites the file, and re-lints to
   show the new score. Draft patches contain TODO markers — complete them
   before publishing. Schema gaps can also be generated directly with
   `python scripts/schema_gen.py <type> --field ...`.
5. **Re-lint after fixes** to confirm the score improved.

## CI usage

Add to the project's pipeline for a hard quality gate:

```yaml
- run: python scripts/seo_lint.py --dir ./dist --min-score 80
```

Exit code is 1 when any page scores below the gate. Recommend `--min-score`
80 as a starting threshold; tighten to 85-90 once the baseline is clean.

## Output

- Chat: score per page, findings table (severity | rule | why-one-liner |
  fix-one-liner), then the top 3 fixes in order.
- When the user wants rules tuned (different thresholds, new checks), point
  them at the `rules/` directory — every rule is a small YAML file with its
  own embedded test; see docs/RULE-ENGINE.md.
