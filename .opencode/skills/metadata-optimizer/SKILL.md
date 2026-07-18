---
name: metadata-optimizer
description: Title tag and meta description optimization — length limits, uniqueness, keyword placement, and CTR copywriting; rewrites pasted lists of URLs and titles. Use when the user says title tags, meta descriptions, rewrite titles, or CTR.
---

# Metadata Optimizer

Audits and rewrites title tags and meta descriptions. Hard rules:
titles ~50-60 characters (≈580px) before truncation, descriptions
~150-160 characters, every page unique.

## Inputs

- Required: URL(s) to audit, OR a pasted list of URLs with current
  titles/descriptions (batch mode)
- Optional: target keyword per page; brand name and where it should sit

## Data pulls

- webfetch each URL to read the live `<title>` and meta description.
- If the target keyword is unclear:
  `python scripts/dfs_client.py ranked --target <domain> --limit 20`
  to see what each page already ranks for, or
  `python scripts/dfs_client.py serp --keyword "<kw>"` to study the
  snippet style of current winners.

## Process

1. **Audit** — flag each item as: missing, duplicate, too long, too
   short, keyword absent, keyword stuffed, or brand-inconsistent.
2. **Rewrite titles** — primary keyword near the front; one clear
   value hook; brand last (" - Brand") unless the brand IS the hook;
   no ALL-CAPS, no separator spam, no repeated boilerplate.
3. **Rewrite descriptions** — expand on the title (never repeat it),
   include the keyword once naturally, end with a specific benefit or
   soft CTA; numbers and concrete outcomes lift CTR more than adjectives.
4. **CTR copywriting levers** — current year, numbers, brackets, question
   formats — used honestly; never promise what the page doesn't deliver.
5. **Uniqueness sweep** — in batch mode, diff all proposed titles
   against each other; near-duplicates get differentiated by their
   actual page angle.
6. **Length check** — count characters on every proposal; anything over
   the limit gets tightened, not waved through.

## Output

Table: URL | current title/meta | issue | proposed title | proposed
description | char counts. Below the table: recommendations ranked
critical / high / medium / low (duplicates and missing tags are
critical; length and CTR polish are medium/low) with a one-line "why"
each, then the single best next step. For batches over ~20 URLs, write
`METADATA-<domain>-<date>.md` and show only the critical rows in chat.
