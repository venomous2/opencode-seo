---
name: entity-seo
description: Applies entity-first SEO by defining the site's key entities, connecting them with sameAs and knowsAbout schema, and auditing entity consistency. Use when the user says entity SEO, entities, named entities, or entity building.
---

# Entity SEO

Entity-first SEO: search engines and AI systems reason about things —
people, organizations, products, concepts — not just strings. This skill
defines the site's key entities, wires them together with schema and
content, and keeps their naming consistent so machines resolve each as
one thing.

## Inputs

- Required: domain, brand name, and the 3-10 entities that matter most
  (products, people, concepts) — or a request to discover them
- Optional: competitor domains for entity-gap context

## Data pulls

```
python scripts/dfs_client.py ranked  --target "<domain>" --limit 300
python scripts/dfs_client.py serp    --keyword "<brand>" --limit 20 --pretty
python scripts/dfs_client.py content --keyword "<core topic>" --limit 30
```

Fetch the homepage, about page, and top pages (from `ranked`) with
webfetch to inventory existing schema and naming. If credentials are
missing, stop and point the user to docs/DATAFORSEO-SETUP.md.

## Process

1. **Entity inventory** — list the site's key entities: the organization,
   each product/service, key people, and the core concepts the site wants
   authority for. For each: canonical name, aliases, home URL, and a
   one-line definition.
2. **Schema wiring** — connect entities with JSON-LD: Organization with
   `sameAs` on the entity home; Person schema for authors/founders;
   `knowsAbout` on the Organization and on authors to declare the
   concepts the site covers; `about` / `mentions` on Articles pointing
   at the right entities. Use the schema-generator skill for markup.
3. **Relationship content** — check that content states entity
   relationships explicitly: "X is a product of <Brand>", "Jane Doe is
   the founder of <Brand>", "<Brand> specializes in <concept>". Machines
   learn relationships from sentences like these, not from proximity.
4. **Hub pages per entity** — each major entity deserves one definitive
   page that defines it and links to everything related; internal links
   use consistent anchor text naming the entity.
5. **Consistency audit** — sweep the site for naming drift: aliases used
   interchangeably, outdated product names, author names spelled two
   ways. Every variant dilutes the entity.
6. **External corroboration** — note where external sources (from the
   `content` pull) describe the entities differently; consistent
   third-party descriptions reinforce the graph.

## Output

- Entity inventory table: entity | type | canonical name | aliases |
  home URL | schema present? | issues
- Relationship map: which entities connect to which, and where each
  connection is asserted (schema / content / both / neither)
- Prioritized recommendations (critical/high/medium/low), each with a
  one-line "why"
- Single best next step

Write the full entity audit to `ENTITY-SEO-<domain>-<date>.md` when it
exceeds ~100 lines.
