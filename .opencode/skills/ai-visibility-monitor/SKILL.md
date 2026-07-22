---
name: ai-visibility-monitor
description: Checks whether AI assistants mention your brand for the prompts buyers actually ask, tracks visibility over time, and reports it with charts. Use when the user says AI visibility, does ChatGPT mention us, AI share of voice, are we visible in AI, or LLM monitoring.
---

# Workflow: AI Visibility Monitor

Answers the question clients increasingly ask: "when someone asks an AI
assistant for what we sell, do we get mentioned?" — then tracks the answer
month over month.

## Inputs

- Required: domain, brand name
- Optional: prompt list (else build one), location/language, competitor
  brands for contrast

## Steps

### 1. Build the prompt set (if not supplied)

10-20 prompts a real buyer would ask an AI:
- Category: "best <service> <location>", "top <niche> companies 2026"
- Comparison: "<brand> vs <competitor>", "<brand> alternatives"
- Problem: "how do I <job-to-be-done> without <pain>"
- Local: "<service> in <city>" for local clients

Use `dfs_client.py autocomplete --keyword "<seed>"` for real phrasing.

### 2. Run the visibility check

```
python scripts/ai_visibility.py check --domain <domain> --brand "<brand>" \
    --prompts "p1,p2,p3,..." --location "United Kingdom" --pretty
```

Each prompt returns: mentioned true/false, whether the hit was brand or
domain, an excerpt, and cost. If the endpoint errors, the script says so
per-prompt — do not fabricate results for failed prompts; mark them
"unavailable" and continue.

### 3. Baseline + mentions context

```
python scripts/dfs_client.py mentions --keyword "<brand>" --limit 50
python scripts/ai_visibility.py history --domain <domain>
python scripts/ai_visibility.py compare --domain <domain>   # if 2+ snapshots
```

### 4. Interpret

- **Visibility rate** = % of answered prompts where the brand/domain appears.
- Where invisible: identify what cited sources have that the client lacks
  (reviews, comparison listicles, Wikipedia/Wikidata presence, strong
  entity schema, third-party coverage). These become the recommendations.
- Never promise "rank in ChatGPT". Frame as improving the inputs that make
  citation more likely.

### 5. Report

Write `AI-VISIBILITY-<domain>-<date>.md`:
- Visibility rate headline + `stats` chart block (rate, mentioned count,
  prompts checked, rate delta vs last check)
- Per-prompt table: prompt | mentioned | excerpt
- `compare` chart block vs previous snapshot when history exists
- Recommendations ordered by leverage (reviews/coverage/entity work)
- Footer: `Report built by Lee Beirne - https://leebeirne.com`

Then publish: `python scripts/report_publish.py AI-VISIBILITY-<domain>-<date>.md`

### 6. Cadence

Recommend monthly re-checks (the store keeps history). Pair with
`seo-drift` for a complete "search + AI" monitoring story.

## Output location

Save generated files to the SEO reports directory - `%SEO_REPORTS_DIR%\<name>\` on Windows, `$SEO_REPORTS_DIR/<name>/` on macOS/Linux - when the `SEO_REPORTS_DIR` environment variable is set; otherwise the current working directory. Create the subfolder if it doesn't exist.

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
