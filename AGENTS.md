# OpenCode SEO Suite — Agent Guide

This repo is an OpenCode skill pack. If you are an agent working inside it:

## Layout

- `.opencode/skills/<name>/SKILL.md` — 81 skills (frontmatter: `name` + `description` only)
- `.opencode/agents/*.md` — 4 subagent-mode specialists
- `.opencode/commands/*.md` — 8 slash commands (`$ARGUMENTS` = user input)
- `.opencode/plugins/*.ts` — optional OpenCode plugin (project-memory nudge)
- `scripts/` — Python data layer (DataForSEO mandatory, Google optional,
  plus cache / cost ledger / drift store / crawlers / report builder)
- `tests/` — pytest suite (offline; `python -m pytest tests/ -q`)
- `docs/` — setup and architecture docs
- `validate.py` — structure validator; run after adding/changing skills

## Conventions

- Skill frontmatter: ONLY `name` (must equal folder name) and `description`
  (≥30 chars, trigger keywords). No `tags`, `tools`, or `model` fields —
  OpenCode ignores/rejects them.
- Never fabricate SEO metrics. Live numbers come from
  `python scripts/dfs_client.py`. Google data is optional enrichment via
  `python scripts/google_client.py`.
- Skill bodies: Inputs → Data pulls → Process → Output. Findings with
  evidence, prioritized recommendations with a one-line "why", single best
  next step. Long output goes to a named `.md` file.
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
