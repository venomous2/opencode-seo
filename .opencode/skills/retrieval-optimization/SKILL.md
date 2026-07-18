---
name: retrieval-optimization
description: Makes content retrieval-friendly for RAG-style AI systems with chunk-surviving passages, unambiguous references, and consistent terminology. Use when the user says retrieval optimization, RAG, or chunk-friendly content.
---

# Retrieval Optimization

Prepares content for retrieval-augmented generation (RAG) systems, which
split pages into chunks, embed them, and retrieve passages in isolation.
A passage that only makes sense in the flow of the full page often fails
retrieval or gets quoted out of context. This is a clarity layer — it
helps every reader, human or machine.

## Inputs

- Required: target URL(s) or pasted content
- Optional: the queries the content should be retrieved for

## Data pulls

Fetch target pages with webfetch. To check which queries the pages are
actually candidates for:

```
python scripts/dfs_client.py ranked --target "<domain>" --limit 200
python scripts/dfs_client.py serp   --keyword "<target query>" --limit 20
```

If credentials are missing, stop and point the user to
docs/DATAFORSEO-SETUP.md.

## Process

1. **Chunk test** — mentally split the page at heading and paragraph
   boundaries. Read each chunk alone. Flag any chunk that fails
   standalone comprehension: undefined subjects, dangling references,
   missing context.
2. **Pronoun and reference repair** — replace "it", "this", "the
   company", "the former/latter" with the explicit name wherever the
   antecedent lives in another chunk. The first mention per section
   names the entity in full.
3. **Terminology consistency** — one name per thing across the page and
   site: pick the canonical term, define it once, use it consistently.
   Rotating synonyms splits retrieval across different embeddings.
4. **Descriptive headings** — headings must carry the topic ("Pricing
   for the Team plan", not "Details"). In chunked retrieval the heading
   is often the only context a passage keeps.
5. **Un-trap critical info** — any fact that matters (prices,
   requirements, limits, dates) must also exist as prose. Information
   living only in images, infographics, or complex tables is frequently
   lost in chunking and extraction. Keep tables simple and pair each
   with a prose summary.
6. **Section completeness** — each section should end having fully
   answered its heading's promise; retrieval systems rank whole chunks,
   and half-answers retrieve poorly.

## Output

- Chunk test findings: passages that fail standalone reading, with the
  fix for each
- Terminology map: concept -> chosen term -> variants to replace
- Prioritized recommendations (critical/high/medium/low), each with a
  one-line "why"
- Single best next step

Write the full chunk audit to `RETRIEVAL-<domain>-<date>.md` when it
exceeds ~100 lines.

## Output location

Save generated files to the SEO reports directory - `%SEO_REPORTS_DIR%\<name>\` on Windows, `$SEO_REPORTS_DIR/<name>/` on macOS/Linux - when the `SEO_REPORTS_DIR` environment variable is set; otherwise the current working directory. Create the subfolder if it doesn't exist.
