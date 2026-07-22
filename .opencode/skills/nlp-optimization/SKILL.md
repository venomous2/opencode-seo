---
name: nlp-optimization
description: NLP-friendly writing pass that aligns content with how search engines parse language — clear subject-predicate sentences, answer-first paragraphs, consistent entity naming, and unambiguous references. Use when the user says NLP optimization, natural language optimization, or salience.
---

# NLP Optimization

Rewrites for machine readability: search engines extract entities,
relationships, and answers from text. This pass removes the ambiguity that
stops them from crediting the page.

## Inputs

- Required: the text (pasted, or a URL to fetch with webfetch)
- Optional: target query the passage should answer

## Data pulls

```
python scripts/dfs_client.py serp --keyword "<target query>" --limit 10
```

Only when a target query is supplied: check which passages and features
win (featured snippet, AI Overview style answers) to see the answer
format being rewarded. The rewrite pass itself needs no API.

## Process

1. **Answer-first paragraphs** — every section should open with the
   direct answer in the first sentence, then elaborate. Flag paragraphs
   that bury the point after two sentences of setup.
2. **Clear subject-predicate structure** — one entity doing one thing per
   sentence. Flag sentences where the subject is unclear, the verb is
   buried in a noun ("the implementation of" → "implement"), or clauses
   separate subject from verb.
3. **Consistent entity naming** — pick one name per entity and keep it;
   flag drifting between "the tool", "this platform", "it" and the
   product name. First mention per section should use the full name.
4. **Unambiguous references** — replace pronouns whose antecedent is more
   than one sentence back, and vague deixis ("this approach", "these
   results") with the named thing.
5. **Quotable answer blocks** — for definitional or how-to queries, craft
   40-60 word self-contained answers that make sense when lifted out of
   context (snippet and AI-citation ready).
6. **Salience placement** — key entities should appear in headings, the
   first 100 words, and near related attributes, not only at the end.

## Output

- Issue list: location | problem | why it confuses parsers | rewrite
- 3-5 before → after rewrites of the worst passages
- Rewritten answer block(s) for the target query, when supplied
- The single change that most improves machine readability (usually
  making the first sentence of each section answer-first)

Never change meaning — this is a clarity pass, not a content rewrite.
Long documents go to `NLP-PASS-<slug>-<date>.md`.

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
