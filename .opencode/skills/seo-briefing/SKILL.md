---
name: seo-briefing
description: Morning briefing / CEO mode — a 30-second executive feed of site health, what changed, what needs attention and today's top actions, read from the local recommendation store, drift snapshots and event timeline. Use when the user says briefing, morning briefing, what should I do today, CEO mode, dashboard, or daily standup.
---

# SEO Briefing

The "good morning" feed: thirty seconds, no new API calls, everything read
from the local stores the suite already maintains. It answers one question —
**what should I do next?** — and points at the HTML dashboard when the user
wants the visual version.

## Inputs

- Optional: domain. If omitted, resolve it from `seo-project.yml`
  (`python scripts/project_memory.py` → `site.url`), or from
  `python scripts/project_memory.py --list-clients` when several client
  profiles exist. If there is no way to know, ask.

## Data pulls (all local — no DataForSEO spend)

```
python scripts/recommend_store.py summary --domain <domain>
python scripts/recommend_store.py list --domain <domain>
python scripts/drift_store.py latest --domain <domain>
python scripts/event_log.py list --domain <domain> --limit 15
```

If two or more drift snapshots exist, also
`python scripts/drift_store.py compare --domain <domain>` for "what changed".

## Process

1. **Health** — overall score and delta vs the previous snapshot. No
   snapshots yet → say tracking starts after the first audit.
2. **Needs attention** — critical/high open recommendations, regressions
   (reopened items), anything raised since the last snapshot.
3. **Recent wins** — recommendations resolved or marked done since the last
   snapshot, plus positive drift movements (rankings up, mentions up).
4. **Today's actions** — the top 3–5 open recommendations, each with its
   one-line why and whether `seo_fix` can patch it automatically.
5. **Single best next step** — the one action to start with, and the exact
   command or skill that does it.

## Output

Keep it under ~40 lines in chat, in this shape:

```
Good morning — <domain>

Health: 82/100 (+3 vs last snapshot)

Needs attention
• 2 critical findings open (canonical chain, missing H1 on /pricing)
• 1 regression: title removed on /blog (was fixed last month)

Recent wins
• 4 findings auto-resolved by Tuesday's deploy
• Rankings: "espresso grinder" 8 → 5

Today's actions
1. Fix canonical chain on /category — link equity is split three ways
2. …
3. …

Best next step: run `python scripts/seo_fix.py --url <page> …` — 3 of the
5 open findings are auto-fixable.
```

Empty stores (new project): say so honestly and give the fastest path to
first insight — `python scripts/seo_lint.py --url <homepage> --save
--domain <domain>` (free, offline) or a full `workflow-site-audit`.

Offer the visual version when it would help:
`python scripts/project_dashboard.py --domain <domain>` renders the
branded HTML mission-control page (action queue, health trend, wins,
activity timeline) alongside the markdown source.

Never fabricate numbers: every figure in the feed comes from the stores.
If a store read fails, say the store is unavailable — do not estimate.
