---
name: ai-overviews-optimization
description: Optimizes pages for Google AI Overviews with answer-block structure, question-form headings, and SERP feature tracking via DataForSEO. Use when the user says AI Overviews, AIO, SGE, or Google AI answers.
---

# AI Overviews Optimization

Improves a page's eligibility and citability for Google AI Overviews (AIO).
Grounding fact: per Google's AI optimization guidance, AI Overviews and AI
Mode are built on the same index and ranking systems as classic Search —
there is no separate "AI ranking" to crack. Classic SEO fundamentals are
the foundation; this skill adds structure and citability layers on top.

## Inputs

- Required: target URL(s) or page content, plus the keyword each page targets
- Optional: location/language (defaults: United States / English, or the
  values in `seo-project.yml`)

## Data pulls

Confirm which keywords actually trigger an AI Overview before changing
anything — do not optimize blind:

```
python scripts/dfs_client.py serp   --keyword "<kw>" --limit 20 --pretty
python scripts/dfs_client.py ranked --target "<domain>" --limit 200
```

Inspect the SERP `items` array for `ai_overview` entries and the sources
they reference. Fetch each target page with webfetch to audit structure.
If credentials are missing, stop and point the user to
docs/DATAFORSEO-SETUP.md. Never guess which SERPs show AIOs.

## Process

1. **Gate check** — AIOs only cite pages that are indexed and eligible to
   show a snippet. Confirm: crawlable, indexable (no noindex), and not
   restricted by nosnippet / max-snippet rules. Verify the page already
   ranks reasonably for the query — pages outside the index cannot be
   cited.
2. **Track AIO keywords** — from the serp pulls, list which target
   keywords currently trigger an AI Overview and which domains get cited.
   Prioritize keywords where an AIO is present and the site ranks but is
   not cited.
3. **Answer blocks** — for each target question, write or tighten a
   self-contained answer block of ~130-170 words that fully answers the
   question without leaning on surrounding context. Place it directly
   under its heading, high in the section.
4. **Question-form H2s** — rewrite vague headings ("Overview", "Details")
   as the actual questions users ask ("How much does X cost?"). One
   question per heading; the first paragraph beneath it answers it.
5. **Passage-level clarity** — every passage should stand alone: name the
   subject explicitly, state facts plainly, avoid pronouns whose
   antecedent sits paragraphs away.
6. **Structured data alignment** — ensure schema markup (Article, FAQPage
   only where a genuine visible FAQ exists) matches the visible copy
   exactly. Mismatches erode trust; markup never substitutes for visible
   text.

## Output

- AIO keyword table: keyword | triggers AIO (y/n) | cited domains | our
  position | cited? — evidence from the serp pulls
- Prioritized recommendations (critical/high/medium/low), each with a
  one-line "why"
- Single best next step (usually: rewrite the top page's first answer
  block, then re-check the SERP in 2-4 weeks)

Write the full audit to `AIO-AUDIT-<domain>-<date>.md` when it exceeds
~100 lines.

## Output location

Save generated files to the SEO reports directory - `%SEO_REPORTS_DIR%\<name>\` on Windows, `$SEO_REPORTS_DIR/<name>/` on macOS/Linux - when the `SEO_REPORTS_DIR` environment variable is set; otherwise the current working directory. Create the subfolder if it doesn't exist.

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
