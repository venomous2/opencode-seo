---
name: perplexity-optimization
description: Optimizes content for the Perplexity answer engine with PerplexityBot access, quotable stat-rich passages, freshness, and top-of-page direct answers. Use when the user says Perplexity, Perplexity optimization, or PerplexityBot.
---

# Perplexity Optimization

Improves the likelihood that Perplexity retrieves and cites the site's
content. Perplexity is a citation-first answer engine: it quotes sources
inline, favors recent pages, and needs passages it can lift verbatim. The
goal is citability and clarity — placement can never be guaranteed.

## Inputs

- Required: domain and/or target URL(s), brand name
- Optional: competitor set, refresh cadence constraints

## Data pulls

```
python scripts/dfs_client.py mentions --keyword "<brand>" --limit 50 --pretty
python scripts/dfs_client.py content  --keyword "<topic>" --limit 30
```

Fetch robots.txt and target pages with webfetch (check the `PerplexityBot`
rules). If credentials are missing, stop and point the user to
docs/DATAFORSEO-SETUP.md.

## Process

1. **Bot access** — confirm `PerplexityBot` is allowed in robots.txt for
   the citable sections, and that pages render server-side. Perplexity
   fetches the pages it cites; JS-only or login-walled content is
   invisible to it.
2. **Direct answers at the top** — the first 1-2 sentences under the H1
   should answer the page's core question directly. Perplexity favors
   pages where the answer is immediately extractable; burying the lede
   under intros and hero copy wastes the page.
3. **Quotable passages** — write stat-rich, self-contained sentences that
   survive being quoted alone: "X grew 34% in 2025, according to <source>"
   beats "growth has been strong." Keep the number, the named entity, and
   the date in the same sentence.
4. **Clear attribution** — cite sources inline by name (study, dataset,
   official page). Answer engines prefer sources that themselves show
   provenance; unsourced claims are harder to reuse.
5. **Freshness** — Perplexity visibly favors recent content. Check that
   pages carry honest, visible publish/modified dates, that statistics
   are current, and that evergreen pages get real updates (not date-only
   bumps). Recommend a refresh cadence for freshness-sensitive topics.
6. **Baseline check** — compare the `mentions` results for the brand
   against competitors to see who is already being cited on AI answer
   surfaces, and note what their cited pages do that ours do not.

## Output

- Findings: bot access status, freshness audit (page | visible date |
  staleness flags), quotability notes with rewrite examples
- Prioritized recommendations (critical/high/medium/low), each with a
  one-line "why"
- Single best next step (usually: move the direct answer to the top of
  the highest-traffic target page)

Write the full audit to `PERPLEXITY-<domain>-<date>.md` when it exceeds
~100 lines.

## Output location

Save generated files to the SEO reports directory - `%SEO_REPORTS_DIR%\<name>\` on Windows, `$SEO_REPORTS_DIR/<name>/` on macOS/Linux - when the `SEO_REPORTS_DIR` environment variable is set; otherwise the current working directory. Create the subfolder if it doesn't exist.
