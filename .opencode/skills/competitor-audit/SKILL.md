---
name: competitor-audit
description: Profiles a competitor's SEO using live DataForSEO rankings, backlinks, and page-level analysis of their top content. Use when the user says competitor audit, analyze competitor, competitor SEO, or what is a rival doing in search.
---

# Competitor Audit

Builds an evidence-based profile of one competitor's SEO strategy: what they
rank for, which pages drive their visibility, who links to them, and what is
worth copying versus avoiding.

## Inputs

- Required: competitor domain
- Optional: user domain (for gap context), location/language (defaults from
  `seo-project.yml` via `python scripts/project_memory.py`)

## Data pulls

Run these with bash (in parallel):

```
python scripts/dfs_client.py ranked      --target "<competitor>" --limit 100
python scripts/dfs_client.py backlinks   --target "<competitor>" --limit 50
python scripts/dfs_client.py refdomains  --target "<competitor>" --limit 50
python scripts/dfs_client.py competitors --target "<competitor>" --limit 10
python scripts/dfs_client.py intersection --target1 "<user-domain>" --target2 "<competitor>" --mode gap   # if user domain given
```

Then webfetch the competitor's top 3-5 ranking pages (URLs taken from the
`ranked` output) to study their content patterns directly.

If credentials are missing, stop and point the user to
docs/DATAFORSEO-SETUP.md. Do not invent numbers.

## Process

1. **Rankings profile** — from `ranked`, summarize: total keywords visible,
   distribution across positions 1-3 / 4-10 / 11-30, and their highest-volume
   terms. Note which topics dominate.
2. **Traffic-driving pages** — group ranked keywords by landing URL; the URLs
   holding the most position 1-10 keywords are their workhorses.
3. **Backlink profile** — from `refdomains`, note the strongest linking
   domains and any patterns (directories, press, guest posts, tools). Use
   `anchors` if anchor-text patterns matter.
4. **Content patterns** — from the webfetch reads: page formats (guides,
   tools, comparisons), approximate depth, schema presence, update cadence,
   internal linking habits, and CTAs.
5. **Synthesize** — classify each observation as one of:
   - **Copy** — proven tactic that fits the user's site (e.g., a format
     winning featured snippets).
   - **Counter** — strength to outflank, not imitate head-on (e.g., dominant
     domain authority on head terms).
   - **Avoid** — weakness or risk (thin pages ranking on links alone, spammy
     anchors, neglected sections).

## Output

A markdown profile containing:

- Snapshot table: keywords by position band | top 10 keywords with volume
  and position | estimated authority signals (referring domain count)
- Top 5 traffic-driving pages with what makes each work
- Backlink summary: top referring domains and link-type patterns
- **Copy / Counter / Avoid** list (3-5 items each, one-line why per item)
- Single best next step for the user (e.g., "target their 12 striking-distance
  keywords where your domain already has topical content")

If the gap pull ran, append the top 15 gap keywords as a table. Long detail
goes to `COMPETITOR-AUDIT-<domain>-<date>.md`.
