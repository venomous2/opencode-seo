---
name: seo-roadmap-builder
description: Builds a 30/60/90-day or quarterly SEO roadmap from audit findings and goals, sequenced by dependency and impact with measurement checkpoints. Use when the user says SEO roadmap, 90 day plan, SEO strategy timeline, or what should we do next quarter.
---

# SEO Roadmap Builder

Sequences audit findings and goals into a time-boxed execution plan with
built-in measurement, so progress is provable at every checkpoint.

## Inputs

- Required: audit findings (or a prior report file) + business goal
- Optional: horizon (default 90 days; or quarterly), team capacity, current
  baselines (else pull fresh), project context from `seo-project.yml` via
  `python scripts/project_memory.py`

## Baseline pulls

If no recent baseline exists, capture one now — the roadmap's measurement
plan depends on it:

```
python scripts/dfs_client.py ranked --target "<domain>" --limit 100
python scripts/google_client.py gsc-queries --target "<domain>"   # optional Google layer
python scripts/google_client.py ga4-organic --target "<domain>"   # optional Google layer
```

If credentials are missing, stop and point the user to
docs/DATAFORSEO-SETUP.md. Never fabricate baselines — mark unavailable
sections and continue.

## Process

1. **Set the target state** — translate the goal into 2-4 measurable
   outcomes for the horizon: e.g., "15 priority keywords in top 10",
   "+30% organic sessions", "100% indexation of product pages". Each gets a
   baseline number (from the pulls) and a target number.
2. **Pool the work** — collect every open finding/recommendation from the
   audit and any quick-win lists (striking-distance keywords, gap
   clusters).
3. **Sequence by dependency, then impact**:
   - Dependency rule: indexability → technical/templates → content →
     authority. Never schedule promotion before the thing being promoted
     exists and is indexable.
   - Within each tier, order by impact ÷ effort; put one visible quick win
     in the first two weeks for stakeholder momentum.
4. **Lay out the timeline**:
   - **Days 1-30**: critical fixes + quick wins; measurement plumbing
     verified (GSC/GA4/rank tracking working).
   - **Days 31-60**: template-level improvements, first content batch,
     schema rollout.
   - **Days 61-90**: second content batch, first authority push, refresh of
     decaying pages.
   (For a quarterly roadmap, map the same arc to months 1/2/3.)
5. **Build measurement checkpoints** — at day 30/60/90, define exactly what
   gets re-measured and how:
   - Rankings: `python scripts/dfs_client.py ranked --target "<domain>"` —
     compare priority keyword set vs baseline.
   - Traffic: `google_client.py ga4-organic` / `gsc-queries` when
     configured.
   - Leading indicators: indexation count, impressions trend (moves before
     clicks do).
   Each checkpoint gets a decision rule: "if X hasn't moved, do Y" (e.g.,
   impressions up but clicks flat → rewrite titles/metas).
6. **Capacity-check** — if the plan exceeds stated team capacity, cut from
   the bottom of the impact list, never from the dependency chain's front.

## Output

- Targets table: metric | baseline | day-90 target
- Timeline: 3 blocks (1-30 / 31-60 / 61-90), each with activities, owner
  roles, and the deliverable that proves completion
- Checkpoint table: date | what to measure | command/tool | decision rule
- Top 3 risks with mitigations
- Single best next step

Write the full roadmap to `ROADMAP-<domain>-<date>.md`; chat shows the
targets, timeline summary, and first checkpoint only.

## Output location

Save generated files to the SEO reports directory - `%SEO_REPORTS_DIR%\<name>\` on Windows, `$SEO_REPORTS_DIR/<name>/` on macOS/Linux - when the `SEO_REPORTS_DIR` environment variable is set; otherwise the current working directory. Create the subfolder if it doesn't exist.

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
