---
name: autonomous-seo-agent
description: Autonomous SEO agent that scans a site's HTML, applies mechanical fixes from the rule engine, and opens a review-ready pull request on a schedule. Use when the user says autonomous SEO agent, SEO agent, PR bot, auto-fix my SEO, ship SEO fixes, open a PR with fixes, SEO autopilot, or scheduled SEO fixes.
---

# Autonomous SEO Agent

Runs the suite's full loop: scan the repo's HTML, label every finding NEW /
PERSISTING / REGRESSED against the recommendation store, apply the mechanical
patches the fix engine already resolved, and ship them as one reviewable pull
request. Deterministic detection, human-approved merge.

## Recipe

- **Engine inputs**: `seo_agent.py scan|fix|ship|run`, which wrap
  `seo_lint.py` (`parse_html`, `lint_pages`), `rule_engine.py run`,
  `seo_fix.py` (`collect_patches`, `apply_patches`), `recommend_store.py`
  (`save_lint_results`, `replay` - the fingerprint lifecycle),
  `event_log.py` (`agent_pr` events).
- **Rule categories**: whatever fires on the scanned HTML - metadata,
  headings, indexability, schema, social, mobile, international, links,
  images. Patches only exist for rules carrying `fix.patch`.
- **Judgment added**: decides *whether* to ship (scope, one PR per run,
  branch naming), interprets regressed vs persisting findings for the
  reviewer, and writes the brief's "next step". It also decides when a
  draft patch's derived copy is good enough to include or should be left
  to a human.
- **Never re-checks**: the engine owns detection and scoring. The agent
  adopts `rule_engine.run` findings and `seo_fix` patch records verbatim -
  it does not re-verify title length, canonical shape, schema validity,
  or any other rule condition.
- **Output**: `SEO-AGENT-<domain>-<date>.md` brief (pages, new/persisting/
  regressed findings, fixes applied with score deltas, draft copy to
  review, one next step) written to `%SEO_REPORTS_DIR%\<domain>\` (Windows)
  / `$SEO_REPORTS_DIR/<domain>/` (Unix), or the current directory when the
  env var is unset. Footer:
  `Report built by Lee Beirne - https://leebeirne.com`

## Inputs

- `--domain <key>` - the recommendation-store key (usually the domain)
- `--dir <folder>` - the HTML root of the site repository
- `--base-url <url>` - public base URL (canonical/schema patch values)
- Optional: `--only <rule-id>`, `--mechanical-only`, `--exclude <dir>`,
  `--branch`, `--base-branch`

## Data pulls

Nothing from DataForSEO or Google - the agent is fully offline and runs on
the files in the repository. Site memory comes from the local stores:
`recommendations\<domain>.jsonl` (issue fingerprints, `times_raised`,
status lifecycle) and `events\<domain>.jsonl`. Live monitoring stays with
`watch.py`; ranking evidence stays with `dfs_client.py`.

## Process

1. **Confirm scope.** The agent edits HTML in a git repository. If the
   user's site is a framework build (Next.js, Astro), point the agent at
   the built HTML (`--dir dist`) or fix the source with the coding agent
   using the lint findings - `seo_fix` patches rendered HTML only.
2. **Scan first.**

   ```
   python scripts/seo_agent.py scan --dir <folder> --domain <domain> \
       --base-url <url> --format text
   ```

   Findings are labelled NEW (first sight), PERSISTING (open on earlier
   scans), REGRESSED (was closed, is back - usually a deploy regression).
3. **Preview the fixes** (dry-run by default):

   ```
   python scripts/seo_agent.py fix --dir <folder> --domain <domain> \
       --base-url <url> --format text
   ```

   Only engine patches with `status: ready` are candidates. `draft: true`
   patches (title/meta copy derived from page text) are listed separately -
   review that wording or pass `--mechanical-only`.
4. **Apply and ship.**

   ```
   python scripts/seo_agent.py run --dir <folder> --domain <domain> \
       --base-url <url> --apply --pr
   ```

   `--apply` rewrites files (`.bak` backups first) and re-lints to show the
   score delta. `--pr` branches, commits only the patched files, and opens
   a pull request whose body is the brief. Without `--pr` it is a dry-run
   and prints the git commands it would run.
5. **Schedule it** by copying `.github/workflows/seo-agent.yml` into the
   site repository and setting `SEO_AGENT_DOMAIN`, `SEO_AGENT_BASE_URL`,
   and optionally `SEO_AGENT_DIR`. Weekly cron opens one PR; the human
   review is the merge guardrail.

## Output

- Chat: page scores, then a table of NEW / PERSISTING / REGRESSED findings
  with a one-line why each, then what the agent would ship (or shipped) and
  the single best next step.
- File: the brief named above. Client-facing versions via
  `python scripts/report_publish.py <brief>.md`.
- Evidence standard: every claim cites a rule id, a file path, and the
  score delta. Never promise rankings - the agent ships correctness.

Guardrails worth stating to the user: the agent never touches copy that
needs product knowledge, never merges its own PRs, and never stages files
it did not patch. If a finding is a judgment call (a deliberate noindex, a
missing schema that does not fit the page type), leave it open and say why.