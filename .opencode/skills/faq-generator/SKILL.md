---
name: faq-generator
description: Generates FAQ sections from real People-Also-Ask and related-keyword questions pulled from the live SERP, with self-contained 40-60 word answers. Use when the user says FAQ, FAQ section, people also ask, or questions to answer.
---

# FAQ Generator

Builds an FAQ block from questions searchers actually ask, pulled from
the live SERP and related keywords. Answers are written to stand alone.

## Inputs

- Required: topic or target keyword
- Optional: number of questions (default 6-8); location/language

## Data pulls

Run with bash:

```
python scripts/dfs_client.py serp    --keyword "<topic>" --limit 20   # PAA questions
python scripts/dfs_client.py related --keyword "<topic>" --limit 50   # question-form keywords
python scripts/dfs_client.py volume  --keywords "q1,q2,..."           # size the best ones
```

## Process

1. **Harvest questions** — collect People-Also-Ask entries from the SERP
   pull and question-form keywords (who/what/when/where/why/how/can/
   does) from the related pull.
2. **Select & dedupe** — merge near-duplicates; keep 6-8 questions that
   (a) show volume or repeated PAA presence and (b) the page has not
   already answered verbatim in body copy.
3. **Write self-contained answers** — 40-60 words each. The answer must
   make sense if lifted out of context (AI answers and voice assistants
   may quote it): lead with the direct answer in the first sentence,
   then one supporting detail. Never "as mentioned above".
4. **Order** — most-asked / highest-volume first; group logically if the
   FAQ is long.
5. **Schema note** — FAQPage JSON-LD can be generated with
   `python scripts/schema_gen.py`, but set expectations: Google
   restricted FAQ rich results to authoritative government and health
   sites in August 2023, so the markup is an entity/relevance signal and
   AI-citation aid, not a rich-result play.

## Output

A markdown list: each question as an H3, followed by its 40-60 word
answer. Then:
- Source note per question (PAA / related keyword + volume where known)
- 2-3 questions deliberately excluded, with a one-line "why" each
  (already answered in body, off-intent, zero demand)
- Single best next step: add the block to the page and validate the
  FAQPage JSON-LD in Google's Rich Results Test

Write FAQs longer than 10 questions to `FAQ-<topic>-<date>.md`.
