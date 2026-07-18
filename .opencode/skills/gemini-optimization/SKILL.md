---
name: gemini-optimization
description: Optimizes for Google Gemini surfaces (Gemini app and AI features in Search) via shared AI Overviews fundamentals, Google-Extended trade-off review, and entity grounding. Use when the user says Gemini, Gemini optimization, or Google Gemini.
---

# Gemini Optimization

Covers Google's Gemini surfaces: the Gemini app and Gemini-powered AI
features in Search. Much of the work overlaps AI Overviews fundamentals —
Gemini features in Search are grounded in the same Google index and
ranking systems, per Google's AI optimization guidance. This skill adds
the Gemini-specific layers: crawler controls and entity grounding.

## Inputs

- Required: domain and/or target URL(s), brand/entity name
- Optional: stance on AI-training use of content (for the Google-Extended
  decision), list of official brand profiles

## Data pulls

```
python scripts/dfs_client.py serp     --keyword "<brand>" --limit 20 --pretty
python scripts/dfs_client.py mentions --keyword "<brand>" --limit 50
```

Fetch robots.txt, the home/about pages, and key target pages with
webfetch. The branded SERP pull shows whether a knowledge panel or other
entity result already exists. If credentials are missing, stop and point
the user to docs/DATAFORSEO-SETUP.md.

## Process

1. **Shared fundamentals first** — run the eligibility checks from the
   ai-overviews-optimization skill (indexed, snippet-eligible, answer
   blocks, clear structure). Gemini-in-Search inherits these; reference
   the existing findings instead of duplicating effort.
2. **Google-Extended trade-off** — `Google-Extended` is a robots.txt
   control over AI-training use of content. Explain plainly: blocking it
   may limit use of content for training Gemini models, but it does not
   remove pages from Search or AI Overviews (those follow normal
   Googlebot crawling and snippet controls). Present the trade-off; the
   user decides.
3. **Entity grounding** — Gemini answers lean on Google's knowledge graph
   for who/what a brand is. Check: Organization schema on the entity home
   page with `sameAs` links to authoritative profiles (LinkedIn,
   Crunchbase, Wikidata if eligible, official social accounts);
   consistent naming; knowledge panel presence in the branded SERP pull.
4. **Attribution clarity** — pages should state plainly who published
   them (byline, organization, date) so attribution in generated answers
   is unambiguous.
5. **Gap report** — if competitors have panels and sameAs networks and
   the user does not, say so. Entity grounding is earned across the web,
   not toggled on-page; list the corroboration gaps honestly.

## Output

- Findings: fundamentals status (referenced from AIO checks),
  Google-Extended current state plus recommendation, entity-grounding
  checklist results
- Prioritized recommendations (critical/high/medium/low), each with a
  one-line "why"
- Single best next step (usually: ship corrected Organization schema with
  a complete sameAs set on the entity home page)

Write the full audit to `GEMINI-<domain>-<date>.md` when it exceeds
~100 lines.

## Output location

Save generated files to the SEO reports directory - `%SEO_REPORTS_DIR%\<name>\` on Windows, `$SEO_REPORTS_DIR/<name>/` on macOS/Linux - when the `SEO_REPORTS_DIR` environment variable is set; otherwise the current working directory. Create the subfolder if it doesn't exist.
