---
name: seo-task-generator
description: Converts SEO audit findings into a prioritized task list with impact/effort scoring, owner suggestions, and acceptance criteria, formatted for issue trackers. Use when the user says SEO tasks, task list, action items, or turn findings into tickets.
---

# SEO Task Generator

Transforms findings from an audit or any analysis skill into concrete,
assignable, verifiable tasks ready to paste into Jira, Linear, GitHub
Issues, or Asana.

## Inputs

- Required: the findings — audit report, analysis output, or a path to a
  prior results file (e.g., `SEO-AUDIT-*.md`)
- Optional: team roles available (dev, content, design), tracker format
  preference, project context from `seo-project.yml` via
  `python scripts/project_memory.py`

## Process

1. **Explode findings into tasks** — one task per discrete fix. Split any
   finding that bundles multiple changes ("fix titles and add schema" becomes
   two tasks). Merge duplicates that appear across findings.
2. **Score impact × effort** — per task:
   - *Impact* (1-5): expected effect on rankings/traffic/revenue. Critical
     indexability fixes = 5; cosmetic polish = 1.
   - *Effort* (1-5): dev-hours/content-hours realistically required.
     One-line meta edit = 1; template re-architecture = 5.
   - *Priority* = impact ÷ effort, bucketed: P1 quick wins (high impact, low
     effort), P2 major projects (high/high), P3 fill-ins (low/low), P4
     question-marks (low impact, high effort — do last or not at all).
3. **Sequence dependencies** — flag tasks that block others (indexation
   before content promotion; templates before page-level rollouts).
4. **Assign owners** — suggest a role, not a person: SEO, developer,
   content writer, designer, or client/stakeholder (for approvals).
5. **Write acceptance criteria** — every task gets testable "done when"
   lines. Bad: "improve titles". Good: "All 47 product page titles match the
   pattern [Brand] [Product] — [attribute]; verified by re-crawl or
   `python scripts/dfs_client.py onpage --url <sample>`".

## Output

For each task, emit a block formatted for direct paste into an issue
tracker:

```
[P1] <Imperative title, ≤60 chars>
Impact: 5 | Effort: 1 | Owner: Developer
Depends on: #<task number> (or "none")
Why: <one line tying to the finding's evidence>
Acceptance criteria:
- [ ] <testable condition>
- [ ] <verification method>
```

Presentation order:

1. Summary table: # | task | priority | impact | effort | owner
2. Task blocks grouped P1 → P4
3. Dependency notes
4. Single best next step (the P1 task to start today)

If the list exceeds ~15 tasks, write the full set to
`TASKS-<domain>-<date>.md` and show only the summary table + P1 blocks in
chat.
