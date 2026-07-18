---
name: readability-analysis
description: Analyzes supplied text for sentence and paragraph length, passive voice, jargon, and scanning aids, estimates grade level, and suggests meaning-preserving rewrites. Use when the user says readability, reading level, or simplify text.
---

# Readability Analysis

Measures how easy a text is to read and shows exactly where it fights the
reader. Pure text analysis — no API calls needed.

## Inputs

- Required: the text (pasted, or a URL to fetch with webfetch)
- Optional: target audience (default: general web reader, grade ~8),
  brand voice notes

## Process

1. **Sentence length** — flag sentences over 25 words; an average over 20
   is heavy for web reading. Long sentences carrying multiple clauses are
   the first rewrite targets.
2. **Paragraph length** — flag paragraphs over 4 sentences or ~70 words;
   walls of text kill scanning.
3. **Passive voice** — mark constructions like "was written by"; convert
   to active unless the actor is genuinely unknown or irrelevant.
4. **Jargon and filler** — list domain terms a general reader won't know;
   mark filler ("in order to", "it is important to note that", "due to
   the fact that") with the shorter form.
5. **Scanning aids** — check for subheadings every ~300 words, lists
   where items are parallel, bolding on key phrases. Note where a
   paragraph is secretly a list.
6. **Grade-level estimate** — Flesch-Kincaid style estimate from average
   sentence length and syllable density; state it as an approximation and
   compare against the audience target.

## Rewrite rules

- Preserve meaning exactly — shorter, not shallower.
- One idea per sentence; split at conjunctions.
- Lead paragraphs with the point, not the setup.
- Keep technical terms the audience needs; explain them inline once
  instead of removing them.
- Show rewrites as before → after pairs so the user can accept
  selectively.

## Output

- Summary line: estimated grade level vs target, average sentence length,
  passive-voice count, jargon count
- Issue table: location | issue | evidence | suggested fix
- 3-5 before → after rewrites of the worst passages
- Single highest-impact fix (usually splitting the longest sentences)

Keep rewrites in chat unless the full text is long; write
`READABILITY-<slug>-<date>.md` for full-document passes.
