---
name: workflow-migration
description: End-to-end site migration workflow covering pre-launch baselines and redirect mapping, launch-day checks, and post-launch drift monitoring, so rankings and link equity survive a domain move, replatform, or redesign. Use when the user says site migration, domain migration, replatform, redesign SEO, or move domain.
---

# Workflow: Site Migration

Migrations fail in predictable ways: missing 301s, staging noindex tags
shipped to production, and nobody watching the weeks after launch. This
workflow sequences the work so none of that happens.

## Inputs

- Required: old domain/URLs, new domain/structure, launch date
- Optional: URL mapping CSV (old -> new), server platform, whether the
  domain itself is changing

## Phase 0 — Baseline (2-4 weeks before launch)

1. Snapshot the old domain so "did the migration hurt?" has an answer:

   ```
   python scripts/dfs_client.py ranked    --target <old-domain> --limit 200
   python scripts/dfs_client.py backlinks --target <old-domain>
   python scripts/dfs_client.py mentions  --keyword "<brand>"
   ```

   Assemble the snapshot JSON and save it:
   `python scripts/drift_store.py save --domain <old-domain> --file snapshot.json`
2. Crawl the old site for the complete URL inventory:
   `python scripts/dfs_client.py crawl --target <old-domain> --max-pages 500`
   (or `python scripts/site_crawler.py --url <old-site>` for small
   sites). The inventory is the redirect map's source of truth — every
   crawlable URL needs a decision.
3. Find the URLs that must not fail — check equity per important URL:

   ```
   python scripts/dfs_client.py backlinks  --target <url>
   python scripts/dfs_client.py refdomains --target <url>
   ```

   Any URL with referring domains or rankings is P1.
4. Build the redirect map with the `redirect-analysis` skill: one 301 per
   old URL to its closest new equivalent; never mass-redirect to the
   homepage (treated as soft 404s); 410 for content with no equivalent
   and no equity. Generate server-ready rules for the target platform.
5. State the golden rule to the user: never change a URL without a 301.
   Redesigns that keep URLs identical are far safer than ones that rename
   everything — push back on unnecessary slug changes.

## Phase 1 — Staging review (before cutover)

Fetch staging pages with webfetch and verify: robots meta noindex present
on staging (correct — but diarise its removal), canonicals referencing
the NEW domain rather than the staging host, hreflang clusters updated to
new URLs, internal links using final new URLs (not through redirects),
and an XML sitemap generated with the new URLs.

## Phase 2 — Launch day

1. Deploy the redirects; verify a P1 sample immediately with webfetch —
   single hop, 301 status, correct target.
2. Remove noindex; confirm robots.txt allows crawling with no legacy
   `Disallow: /`.
3. Submit the new sitemap in Search Console; use Change of Address for a
   domain move (verify listed sitemaps with
   `python scripts/google_client.py gsc-sitemaps --site sc-domain:<domain>`
   when configured). Optional spot checks:
   `python scripts/google_client.py gsc-inspect --url <new-url> --site sc-domain:<domain>`
4. Re-run the P1 equity URLs through webfetch one final time.

## Phase 3 — Post-launch (8 weeks)

1. Re-crawl the new site (`crawl-analyzer`): hunt 404s, redirect chains,
   accidental noindex, and canonicals still pointing at the old domain.
2. Weekly drift: snapshot the new domain, then
   `python scripts/drift_store.py compare --domain <domain> --from <pre-launch-ts>`.
   Ranking wobble for 2-4 weeks is normal; P1 keywords that have not
   recovered after 4 weeks are a finding.
3. Watch GSC coverage for 404 spikes — each spike maps back to a missed
   redirect rule.
4. Keep every redirect live for at least one year, and renew the old
   domain too — the equity dies with it otherwise.

## Output

Write `MIGRATION-<old>-to-<new>-<date>.md`: phase checklist with status,
the P1 URL list (equity holders), redirect map location, launch-day
verification results, and the 8-week monitoring schedule. Chat gets the
checklist summary plus anything red. British English; end the file with:
`Report built by Lee Beirne - https://leebeirne.com`
Single best next step: finish and test the P1 redirect rules before
anything else goes live.

## Output location

Save generated files to the SEO reports directory - `%SEO_REPORTS_DIR%\<name>\` on Windows, `$SEO_REPORTS_DIR/<name>/` on macOS/Linux - when the `SEO_REPORTS_DIR` environment variable is set; otherwise the current working directory. Create the subfolder if it doesn't exist.

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
