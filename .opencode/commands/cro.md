---
description: Conversion rate optimisation audit with deterministic signals, SERP intent alignment, and an ICE-scored experiment plan
---

Run the cro-audit skill for: $ARGUMENTS

Follow the cro-audit skill exactly:
1. Deterministic baseline (seo_lint --category cro)
2. SERP intent-goal alignment for the page's main keyword
3. Competitor benchmark (lint 2-3 SERP rivals with the same checks)
4. Objection mining from PAA + competitor FAQs
5. ICE-scored hypothesis experiment plan with measurement notes
6. Write the CRO-AUDIT report with chart blocks and publish via
   report_publish.py

If $ARGUMENTS is missing the page URL or conversion goal, ask for them.
