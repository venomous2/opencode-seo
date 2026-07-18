---
description: Score a page's readiness to be cited by AI search (AI Overviews, ChatGPT, Perplexity)
---

Run the llm-citation-readiness skill for: $ARGUMENTS

Check answer blocks, passage citability, sourcing, authorship, structured
data, and AI crawler access; pull the brand mention baseline via
scripts/dfs_client.py mentions. Produce the citability checklist and
prioritized fixes. If $ARGUMENTS is empty, ask for the URL.
