---
name: fact-verification
description: Fact-checks a draft by extracting factual claims — statistics, dates, named studies — and verifying each against authoritative sources, returning a claim-by-claim verdict table with citations. Use when the user says fact check, verify claims, or check accuracy.
---

# Fact Verification

Extracts every checkable claim in a draft and verifies it against primary
or authoritative sources. Output is a verdict table, not a vibe.

## Inputs

- Required: the draft (pasted text, or a URL to fetch with webfetch)
- Optional: topic context, sources the user already trusts

## Process

1. **Extract claims** — pull out every verifiable statement: statistics,
   percentages, dates, prices, named studies/reports, quotes, "first /
   largest / only" superlatives, legal or medical assertions. Skip pure
   opinion and clearly hedged commentary.
2. **Classify each claim** — stat, date, study, quote, legal/medical,
   superlative. Classification determines what counts as an authoritative
   source (a government dataset for stats, the journal for studies, the
   primary transcript for quotes).
3. **Verify with webfetch** — for each claim, fetch the primary source:
   - Statistics → the original survey or dataset, not a blog citing it
   - Studies → the paper or its official abstract; check the year, the
     sample, and whether the draft overstates the finding
   - Dates/events → official announcements or reputable news archives
   - Superlatives → require a source explicitly supporting the claim
   Fetch sources in parallel. If two authoritative sources conflict,
   report both.
4. **Verdict per claim**:
   - **Verified** — primary source confirms as stated
   - **Verified with fix** — right fact, wrong number/date/wording;
     give the corrected version
   - **Unverified** — no authoritative source found; mark for removal
     or sourcing
   - **Contradicted** — an authoritative source says otherwise; quote it

## Output

Claim-by-claim table: # | claim (as written) | type | verdict | source
(URL) | note/correction. Summary counts on top. Every unverified or
contradicted claim gets a one-line action (fix to X / add citation /
delete). End with the riskiest claim — the one most damaging if wrong
(usually a stat in the intro or a medical/legal assertion). Write
`FACT-CHECK-<slug>-<date>.md` for drafts with more than ~15 claims.

Never mark a claim verified from memory — a fetched source or it stays
unverified.

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
