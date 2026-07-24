---
description: Morning briefing — health, changes and today's top actions from the local SEO stores (no API spend)
---

Run the seo-briefing skill for: $ARGUMENTS

Follow the seo-briefing skill exactly:
1. Resolve the domain ($ARGUMENTS, else seo-project.yml, else ask)
2. Pull the local stores: recommend_store summary + list, drift latest/compare,
   event_log recent — no DataForSEO calls
3. Produce the executive feed: health + delta, needs attention, recent wins,
   today's top 3-5 actions, single best next step
4. Offer `python scripts/project_dashboard.py --domain <domain>` for the
   HTML mission-control version

If $ARGUMENTS is empty and no project memory exists, ask which domain.
