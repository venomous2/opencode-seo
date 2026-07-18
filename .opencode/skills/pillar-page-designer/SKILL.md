---
name: pillar-page-designer
description: Designs a pillar (hub) page — scope, structure, sections, spoke linking, word count guidance, and Article + BreadcrumbList schema. Use when the user says pillar page, hub page, cornerstone content, or design a pillar.
---

# Pillar Page Designer

Designs the hub page for a topic cluster: what it covers, how it is
structured, and how it distributes links to spokes. Section scope is
validated against live SERP data.

## Inputs

- Required: pillar topic / head keyword; cluster spoke list (from
  topic-clustering, if available)
- Optional: location/language; user's domain

## Data pulls

Run with bash:

```
python scripts/dfs_client.py serp   --keyword "<pillar-keyword>" --limit 10
python scripts/dfs_client.py volume --keywords "pillar-kw,spoke-kw1,spoke-kw2"
```

Fetch 2-3 top-ranking pillar pages with the webfetch tool to study their
section coverage and internal-link patterns.

## Process

1. **Confirm intent** — the SERP must show guide/overview page types. If
   it shows product or category pages, the keyword is not a pillar
   candidate — say so and stop.
2. **Set scope** — the pillar covers the whole topic at overview depth:
   one section per spoke, each answering the sub-question in 100-300
   words and linking to the spoke for depth. No section may duplicate
   its spoke's full content.
3. **Structure** — H1 = pillar keyword; H2s map 1:1 to spokes (H3s only
   where a spoke has natural sub-parts); add a jump-link table of
   contents near the top.
4. **Word count** — size to the SERP, not a fixed rule: pillars typically
   run 2,000-4,000 words; set the target from the word counts of the
   fetched top pages.
5. **Link pattern** — the pillar links out to every spoke with
   contextual anchor text on the spoke's keyword; every spoke must link
   back to the pillar from its first or second paragraph.
6. **Schema** — generate Article + BreadcrumbList JSON-LD with
   `python scripts/schema_gen.py` (run with `--help` for exact arguments);
   include both blocks on the page.

## Output

A design spec: H1 + meta title/description, full H2/H3 outline with
per-section word counts, spoke link map (section -> spoke URL -> anchor
text), word count target, and schema snippets. Then:
- 3 key design decisions with a one-line "why" each (e.g., why this
  section order)
- Single best next step: brief the first spoke (offer
  supporting-content-planner or content-brief)

Write the full spec to `PILLAR-<topic>-<date>.md`; chat shows the
outline and link map only.

## Output location

Save generated files to the SEO reports directory - `%SEO_REPORTS_DIR%\<name>\` on Windows, `$SEO_REPORTS_DIR/<name>/` on macOS/Linux - when the `SEO_REPORTS_DIR` environment variable is set; otherwise the current working directory. Create the subfolder if it doesn't exist.
