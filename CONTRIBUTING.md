# Contributing

Contributions are welcome. The suite is deliberately simple: markdown skills
+ a small Python data layer.

## Adding a skill

1. Create `.opencode/skills/<your-skill>/SKILL.md`.
2. Frontmatter — exactly two fields:
   ```yaml
   ---
   name: your-skill
   description: What it does and when to trigger it, with literal keywords
     a user would say (e.g. "Use when the user says ...").
   ---
   ```
3. Body structure: `# Title` → `## Inputs` → `## Data pulls` (if it needs
   live data) → `## Process` → `## Output`.
4. Rules every skill must follow:
   - Live SEO metrics come from `python scripts/dfs_client.py` — never
     instruct the model to estimate volumes, rankings, or link counts.
   - Google APIs are optional enrichment only (`scripts/google_client.py`).
   - End with prioritized recommendations + one best next step.
5. Run `python validate.py` — it must pass.

## Adding a DataForSEO endpoint

1. Add the endpoint path to `ENDPOINTS` in `scripts/dfs_client.py`.
2. Add a payload builder branch in `build_payload()`.
3. Document the new command in `docs/DATAFORSEO-SETUP.md`.

## Style

- Skills: imperative, concrete, current. Cite thresholds (e.g. title length
  ~50-60 chars, LCP < 2.5s, INP < 200ms) rather than vague advice.
- **British English by default** in all skill text and generated output
  (analyse, optimise, prioritise) unless the user requests otherwise.
- No hype about AI search. Frame GEO/AEO work as structure + citability on
  top of SEO fundamentals.
- Python: stdlib + `requests`/`pyyaml` only. Keep CLIs JSON-in/JSON-out.
- Reports written to files carry the footer:
  `Report built by Lee Beirne - https://leebeirne.com`

## Testing

```bash
python validate.py
python -m py_compile scripts/*.py
python scripts/seo_config.py status
```
