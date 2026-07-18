---
name: content-review
description: Holistic quality review of a single piece of content — accuracy, depth, structure, originality, and usefulness benchmarked against the live top 5 SERP results. Use when the user says review my content, content quality check, or is this article good.
---

# Content Review

Grades one piece of content against what actually ranks today. The verdict
is comparative, not abstract: a page is only "good" if it beats the current
top 5 on usefulness.

## Inputs

- Required: the content — a live URL or a pasted draft
- Optional: target keyword (inferred from the content if omitted),
  location/language

## Data pulls

```
python scripts/dfs_client.py serp --keyword "<target keyword>" --limit 10
```

Then fetch with webfetch (parallel): the user's URL and the top 5 organic
results. For a pasted draft with no URL, still fetch the top 5 — the SERP
is the benchmark.

If credentials are missing, stop and point the user to
docs/DATAFORSEO-SETUP.md. Do not guess what ranks.

## Process

1. **Identify the SERP benchmark** — from the serp pull, note the top 5,
   their page types, and the dominant intent. If the user's page type
   mismatches the SERP, say so first — nothing else will fix that.
2. **Score six dimensions** (1-5 each, evidence required):
   - Accuracy — claims check out; no stale stats or dead links
   - Depth — covers the subtopics the top 5 cover, plus something extra
   - Structure — logical H2/H3 flow, scannable, answer blocks where the
     query demands them
   - Originality — unique data, examples, or angle not present in the
     top 5; flag anything interchangeable with a competitor's text
   - Usefulness — the reader can act after reading; steps, not platitudes
   - Presentation — media, formatting, internal links, CTA fit
3. **Compare** — for each dimension, name the strongest competitor and
   what they do better.
4. **Verdict** — would an unbiased reader pick this page over the top 5?
   Yes / No / With fixes.

## Output

A scorecard table (dimension | score | evidence | best competitor) followed
by prioritized fixes: critical / high / medium, each with a one-line why.
End with the single change that would most improve the page. Write the full
review to `CONTENT-REVIEW-<slug>-<date>.md` when it exceeds ~100 lines.
