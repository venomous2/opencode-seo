---
name: seo-project-planner
description: Plans an SEO project or engagement with phases, milestones, deliverables, and dependencies, and can scaffold the seo-project.yml memory file. Use when the user says SEO project plan, plan SEO engagement, or scope an SEO project.
---

# SEO Project Planner

Turns a goal ("grow organic", "recover traffic", "launch a new site") into a
phased engagement plan with clear deliverables — and optionally initializes
the project's memory file so every later skill run has context.

## Inputs

- Required: domain + primary goal
- Optional: timeline (default 6 months), budget/team constraints, known
  competitors, site type (ecommerce, local, SaaS, publisher)

## Setup

1. Check for existing project memory: `python scripts/project_memory.py`.
2. If none exists and the user wants persistent context, scaffold it:
   `python scripts/project_memory.py --init` — then fill in domain, location,
   language, competitors, brand voice, and goals with the user's answers.
3. Baseline reality check (keep it light — this is planning, not a full
   audit):
   ```
   python scripts/dfs_client.py ranked   --target "<domain>" --limit 50
   python scripts/dfs_client.py onpage   --url "<homepage>"
   ```
   If credentials are missing, note it and plan anyway — but never fabricate
   baseline numbers.

## Process

1. **Define success** — convert the goal into measurable targets: organic
   sessions, keywords in top 10, revenue/leads from organic, indexation
   coverage. Each target gets a number and a date.
2. **Phase the work** — standard five-phase arc, adapted to the site type:
   - **Phase 1 — Foundation (weeks 1-4)**: crawl/index fixes, analytics and
     Search Console verification, baseline benchmarks, keyword research.
   - **Phase 2 — Technical (weeks 3-8)**: architecture, canonicals, CWV,
     schema, rendering. Depends on Phase 1 findings.
   - **Phase 3 — Content (weeks 6-16)**: priority pages, gap clusters,
     refreshes. Depends on keyword research.
   - **Phase 4 — Authority (weeks 10-24)**: digital PR, link-worthy assets.
     Starts only after content worth linking exists.
   - **Phase 5 — Iterate (ongoing)**: measure, refresh, expand.
3. **Milestones & deliverables** — each phase ends with a named, checkable
   deliverable: audit report, fixed-template deploy, content batch of N
   pages, asset + outreach campaign, quarterly report.
4. **Map dependencies explicitly** — list what blocks what (e.g., "no link
   outreach before 5 linkable assets live"). This prevents the classic
   mistake of promoting content that doesn't exist yet.
5. **Resourcing** — per phase, note who's needed (dev, writer, designer,
   SEO) and flag external dependencies (client approvals, dev release
   cycles).

## Output

- Goal + measurable targets table
- Phase plan: phase | weeks | key activities | deliverable | depends on
- Milestone calendar
- Risk list (top 3, each with mitigation)
- Whether `seo-project.yml` was created/updated
- Single best next step (usually: run the baseline audit)

Long plans go to `PROJECT-PLAN-<domain>-<date>.md`.

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
