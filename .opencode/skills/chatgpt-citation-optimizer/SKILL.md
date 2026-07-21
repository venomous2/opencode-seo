---
name: chatgpt-citation-optimizer
description: Improves the likelihood of being cited by ChatGPT web search through crawler access, factual sourcing, and entity consistency, with mention baselines from DataForSEO. Use when the user says ChatGPT optimization, ChatGPT citations, or cited by ChatGPT.
---

# ChatGPT Citation Optimizer

Increases the odds that ChatGPT's web search finds, understands, and
cites the site's content. Honest framing: nobody can promise citation by
ChatGPT. This skill improves the controllable inputs — crawlability,
clarity, citability, and discoverability.

## Inputs

- Required: domain and/or target URL(s), brand name
- Optional: robots.txt content (else fetched), competitor brands for
  comparison

## Data pulls

Establish the current mention baseline, then pull the pages:

```
python scripts/dfs_client.py mentions --keyword "<brand>" --limit 50 --pretty
python scripts/dfs_client.py content  --keyword "<core topic>" --limit 30
```

Fetch robots.txt and the target pages with webfetch. `mentions` shows
existing LLM/AI citation mentions; `content` shows how the brand and
topic are discussed across the web. If credentials are missing, stop and
point the user to docs/DATAFORSEO-SETUP.md.

## Process

1. **Crawler access** — check robots.txt for the two OpenAI bots and
   treat them differently:
   - `OAI-SearchBot` — used for ChatGPT search; blocking it keeps pages
     out of cited results. It must be allowed on pages the user wants
     cited.
   - `GPTBot` — the training crawler; the user may allow or disallow it
     independently of search visibility.
   Present the trade-off and let the user decide; never conflate the two.
   Also confirm pages return 200 to bot user agents (no WAF challenge)
   and are not behind login or JS-only rendering.
2. **Citable statements** — audit pages for clear, factual, self-contained
   statements: specific claims with numbers, dates, and named sources.
   Rewrite vague marketing claims into verifiable ones. Each key claim
   should name its source (study, dataset, official doc) inline.
3. **Entity consistency** — brand name, product names, and key people
   spelled identically across the site and matching external profiles.
   Inconsistent naming splits the entity and confuses attribution.
4. **Baseline vs. reality** — compare the `mentions` baseline against the
   named competitors. If competitors are mentioned and the user is not,
   determine whether the gap is access, clarity, or authority.
5. **Authority reinforcement** — where third-party coverage is the real
   gap, say so: LLM answers lean on sources the web already trusts. Flag
   digital-PR or original-data opportunities rather than pretending
   on-page fixes close an authority gap.

## Output

- Findings: crawler access status per bot, mention baseline numbers,
  citable-statement audit with before/after examples
- Prioritized fix list (critical/high/medium/low), each with a one-line
  "why"
- Single best next step (usually: fix OAI-SearchBot access, then rewrite
  the top page's key claims into sourced statements)

Write the full audit to `CHATGPT-CITATIONS-<domain>-<date>.md` when it
exceeds ~100 lines.

## Output location

Save generated files to the SEO reports directory - `%SEO_REPORTS_DIR%\<name>\` on Windows, `$SEO_REPORTS_DIR/<name>/` on macOS/Linux - when the `SEO_REPORTS_DIR` environment variable is set; otherwise the current working directory. Create the subfolder if it doesn't exist.

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
