# OpenCode SEO Suite — Agent Guide

This repo is an OpenCode skill pack. If you are an agent working inside it:

## Layout

- `.opencode/skills/<name>/SKILL.md` - 88 skills (frontmatter: `name` + `description` only)
- `.opencode/agents/*.md` — 4 subagent-mode specialists
- `.opencode/commands/*.md` - 12 slash commands (`$ARGUMENTS` = user input)
- `.opencode/plugins/*.ts` — optional OpenCode plugin (project-memory nudge)
- `scripts/` — Python data layer (DataForSEO mandatory, Google optional,
  plus cache / cost ledger / drift store / recommendation store / event log /
  dashboard / watch (monitoring) / forecast + impact / crawlers /
  report builder)
- `tests/` — pytest suite (offline; `python -m pytest tests/ -q`)
- `docs/` — user guides (GETTING-STARTED, USER-GUIDE), setup and
  architecture docs
- `examples/` — copy-paste workflow templates (PR gate) + sample outputs
- `validate.py` — structure validator; run after adding/changing skills

## Conventions

- **Shell**: on Windows, OpenCode uses PowerShell — never bashisms (`head`,
  `tail`, `grep`, `&&`). Use `Select-Object -First N`, `Select-String`, and
  `cmd1; if ($?) { cmd2 }` for chaining. Prefer script `--pretty`/JSON flags
  over piping.
- Skill frontmatter: ONLY `name` (must equal folder name) and `description`
  (≥30 chars, trigger keywords). No `tags`, `tools`, or `model` fields —
  OpenCode ignores/rejects them.
- Never fabricate SEO metrics. Live numbers come from
  `python scripts/dfs_client.py`. Google data is optional enrichment via
  `python scripts/google_client.py`.
- Skill bodies: Inputs → Data pulls → Process → Output. Findings with
  evidence, prioritized recommendations with a one-line "why", single best
  next step. Long output goes to a named `.md` file.
- New skills follow the **recipe contract** (docs/RECIPES.md): declare
  engine inputs + judgment added, never re-check what the deterministic
  engine (rules/, seo_lint, seo_fix, citation_score) already covers.
- Generated reports go to `%SEO_REPORTS_DIR%\<name>\` (Windows) /
  `$SEO_REPORTS_DIR/<name>/` (Unix) when the env var is set — never into
  the suite repository itself.
- **Write all output in British English by default** unless the user asks
  for another variant.
- Reports written to files end with the footer:
  `Report built by Lee Beirne - https://leebeirne.com`
- Tone: evidence-based, no hype. Never promise "rank in ChatGPT".

## After changes

```bash
python validate.py
python -m py_compile scripts/*.py
python -m pytest tests/ -q
```

## Install for local testing

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1   # Windows
bash install.sh                                        # macOS/Linux
```

Restart OpenCode afterwards — skills load at startup.
