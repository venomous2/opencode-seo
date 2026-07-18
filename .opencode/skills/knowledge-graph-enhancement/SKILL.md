---
name: knowledge-graph-enhancement
description: Strengthens brand knowledge graph presence through Organization schema with sameAs, honest Wikidata and Wikipedia eligibility checks, and cross-web naming consistency. Use when the user says knowledge graph, knowledge panel, entity home, or Wikidata.
---

# Knowledge Graph Enhancement

Builds the brand's machine-readable identity so search engines and AI
systems resolve "who is this" confidently. Knowledge panels and entity
grounding are earned from consistent, corroborated facts across the web —
this skill organizes the controllable inputs and stays honest about what
cannot be forced.

## Inputs

- Required: brand/organization name, domain
- Optional: list of official profiles, founding date, founders, logo URL,
  current Wikidata/Wikipedia status

## Data pulls

```
python scripts/dfs_client.py serp     --keyword "<brand>" --limit 20 --pretty
python scripts/dfs_client.py mentions --keyword "<brand>" --limit 50
python scripts/dfs_client.py content  --keyword "<brand>" --limit 30
```

The branded SERP shows whether a knowledge panel exists; `mentions` and
`content` show how consistently the brand is described elsewhere. Fetch
the home/about pages with webfetch. If credentials are missing, stop and
point the user to docs/DATAFORSEO-SETUP.md.

## Process

1. **Entity home page** — designate one page (usually the homepage or
   /about) as the canonical entity home: the single page that states the
   organization's facts (name, logo, founding date, founders, contact,
   description) in consistent form.
2. **Organization schema** — on the entity home, emit Organization
   JSON-LD with `name`, `url`, `logo`, `description`, `foundingDate`,
   `founder`, `contactPoint`, and `sameAs` pointing to every
   authoritative profile: LinkedIn, Crunchbase, official social accounts,
   app-store listings, Wikidata (if an entry exists). Use the
   schema-generator skill for the markup.
3. **sameAs quality control** — link only profiles the brand controls or
   that are authoritative about it; a sameAs to a weak or wrong profile
   does harm. Verify every URL resolves and names the brand identically.
4. **Wikidata / Wikipedia eligibility — honest check** — Wikipedia
   requires significant coverage in independent reliable sources;
   Wikidata requires demonstrable notability. Assess the `content` pull:
   if independent coverage is thin, say so plainly and recommend earning
   coverage first. Non-notable entries get deleted and damage
   credibility.
5. **Naming consistency** — from the pulls, list every variant of the
   brand name in use across the site and the web; standardize on one
   form (including legal suffixes, capitalization, and spacing).

## Output

- Findings: knowledge panel status, naming-variant table, sameAs
  inventory (exists / missing / broken), notability assessment
- Prioritized recommendations (critical/high/medium/low), each with a
  one-line "why"
- Single best next step (usually: publish corrected Organization schema
  on the entity home page)

Write the full entity audit to `KG-<brand>-<date>.md` when it exceeds
~100 lines.

## Output location

Save generated files to the SEO reports directory - `%SEO_REPORTS_DIR%\<name>\` on Windows, `$SEO_REPORTS_DIR/<name>/` on macOS/Linux - when the `SEO_REPORTS_DIR` environment variable is set; otherwise the current working directory. Create the subfolder if it doesn't exist.
