---
name: redirect-analysis
description: Audits redirect chains and loops, advises on 301 vs 302 vs 307 semantics, and builds redirect maps for migrations with ready-to-use server rules. Use when the user says redirects, 301, redirect chain, redirect map, or migration URLs.
---

# Redirect Analysis

Audits existing redirects and plans migration redirect maps. Preserving
link equity is the core goal: every old URL with backlinks or rankings
needs exactly one 301 to its closest new equivalent.

## Inputs

- Required: list of URLs to check (audit mode) or a CSV of old -> new URL
  pairs (migration mode)
- Optional: target server platform (nginx, Apache, Netlify, Vercel) for
  rule generation

## Data pulls

Check each URL's redirect behavior with the webfetch tool (follow the
Location chain hop by hop, recording status codes). For migration mode,
check which old URLs carry equity before writing rules:

```
python scripts/dfs_client.py backlinks  --target https://example.com/old-page --pretty
python scripts/dfs_client.py refdomains --target https://example.com/old-page --pretty
python scripts/dfs_client.py ranked     --target https://example.com/old-page --pretty
```

Never assume an old URL is worthless — verify with data before letting it
404.

## Process

1. **Trace** — for each URL, record the full hop sequence: status code,
   Location target, hop count, final status. Flag chains (>1 hop), loops,
   and chains ending in 404/soft-404.
2. **Semantics** — verify the right status is used:
   - **301** — permanent move; signals consolidate to the target. Correct
     for migrations and canonicalization.
   - **302 / 307** — temporary; original URL keeps its indexing signals.
     Wrong for permanent moves; 307 additionally guarantees method/body
     preservation (mostly irrelevant for SEO).
   - Flag any permanent move served as 302/307, and any long-lived
     "temporary" redirect (months old is permanent in practice).
3. **Fix chains** — update every rule so old URLs redirect in a single hop
   directly to the final URL; then update internal links to point at final
   URLs so redirects are not exercised on every crawl.
4. **Build the map** (migration mode) — from the CSV, one rule per old URL:
   - Every rule targets the closest topical equivalent, never the homepage
     (mass redirects to home are treated as soft 404s)
   - Old URLs with backlinks/rankings from the Data pulls get priority P1
   - Old URLs with no equivalent and no equity -> 410
5. **Generate rules** for the requested platform:
   - nginx: `rewrite ^/old-path$ /new-path permanent;` or a `map` block
   - Apache/.htaccess: `Redirect 301 /old-path /new-path` or RewriteRule
   - Netlify `_redirects`: `/old-path /new-path 301`
   - Vercel `vercel.json`: entries in the `redirects` array
   Keep rule order: most specific first, catch-alls last. Note trailing-
   slash and case-sensitivity behavior per platform.
6. **Post-launch checks** — after deployment, re-trace a sample; monitor
   GSC for 404 spikes; keep redirects live at least one year.

## Output

- Audit mode: table of URL | hops | chain (a->b->c) | status codes | issue
  | fix, with a one-line "why" per fix
- Migration mode: the complete redirect map as platform-ready rules, plus a
  P1 list (URLs with link equity — must not fail) and a 410 list
- Single best next step: implement the P1 rules first and re-trace them

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
