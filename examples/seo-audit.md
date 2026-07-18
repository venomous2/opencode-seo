# Example: Full Site Audit

```
/site-audit https://bakeology.example
```

**What happens:**

1. `seo-suite` verifies the data layer (`seo_config.py status` → DataForSEO
   READY, Google tier 1) and loads `seo-project.yml` if present.
2. Parallel DataForSEO pulls:

```
python scripts/dfs_client.py ranked      --target bakeology.example --limit 50
python scripts/dfs_client.py competitors --target bakeology.example --limit 10
python scripts/dfs_client.py backlinks   --target bakeology.example
python scripts/dfs_client.py onpage      --url https://bakeology.example
```

3. Four specialist agents run in parallel and return findings.
4. Synthesis produces the scorecard + report file.

**Chat output (abridged):**

```
SEO Audit: bakeology.example — 2026-07-17

Scorecard
  Technical ..... 74/100   CWV failing on mobile LCP (4.1s)
  Content ....... 81/100   strong recipes, weak E-E-A-T signals
  Authority ..... 42/100   38 ref domains vs competitor avg 210
  UX / CWV ...... 58/100   LCP + CLS issues on recipe template
  AI Search ..... 65/100   good answer blocks, missing author schema
  OVERALL ....... 64/100

Top actions
  1. [CRITICAL] Add fetchpriority=high + preload to hero image on the
     recipe template — LCP 4.1s → est. 2.3s (field data: CrUX p75).
  2. [HIGH] 47 posts lack Person/author schema — add via schema_gen.py
     to support E-E-A-T and AI citability.
  3. [HIGH] Keyword gap: competitors rank for 312 keywords you don't;
     top cluster: "gluten free sourdough" (12.1k vol combined).
  ...

Full report: SEO-AUDIT-bakeology.example-2026-07-17.md
```
