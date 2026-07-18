---
description: Triage a content library into update / merge / redirect / prune with an execution queue
---

Run the workflow-content-refresh skill for: $ARGUMENTS

Build the URL inventory with live ranking data (scripts/dfs_client.py
ranked), detect decay and overlap, triage each URL, write refresh specs for
the "update" set, and output the prioritized execution queue in a
CONTENT-REFRESH report file. If $ARGUMENTS is empty, ask for the domain.
