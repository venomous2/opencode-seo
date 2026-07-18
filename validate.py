"""Validate the OpenCode SEO Suite installation.

Checks:
  1. Every .opencode/skills/<name>/SKILL.md exists and has valid frontmatter
     (name matches folder, description present and >= 30 chars).
  2. Every .opencode/agents/*.md and .opencode/commands/*.md has frontmatter.
  3. All scripts/*.py compile.
  4. Core docs exist.

Exit code 0 = all checks pass.

Usage:  python validate.py
"""

from __future__ import annotations

import py_compile
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

errors: list[str] = []
warnings: list[str] = []


def check_skills() -> int:
    skills_dir = ROOT / ".opencode" / "skills"
    count = 0
    for folder in sorted(skills_dir.iterdir()):
        if not folder.is_dir():
            continue
        count += 1
        skill = folder / "SKILL.md"
        if not skill.is_file():
            errors.append(f"{folder.name}: missing SKILL.md")
            continue
        text = skill.read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
        if not match:
            errors.append(f"{folder.name}: no YAML frontmatter block")
            continue
        front = match.group(1)
        name = re.search(r"^name:\s*(\S+)", front, re.MULTILINE)
        desc = re.search(r"^description:\s*(.+)", front, re.MULTILINE)
        if not name or name.group(1) != folder.name:
            errors.append(f"{folder.name}: name field missing or != folder name")
        if not desc or len(desc.group(1).strip()) < 30:
            errors.append(f"{folder.name}: description missing or too short")
        for banned in ("tools:", "model:", "tags:"):
            if re.search(rf"^{re.escape(banned)}", front, re.MULTILINE):
                warnings.append(f"{folder.name}: non-standard frontmatter field '{banned.rstrip(':')}'")
        body = text[match.end():]
        if len(body.strip()) < 400:
            warnings.append(f"{folder.name}: body looks thin ({len(body.strip())} chars)")
    return count


def check_md_frontmatter(directory: Path, label: str) -> int:
    count = 0
    for md in sorted(directory.glob("*.md")):
        count += 1
        text = md.read_text(encoding="utf-8")
        if not re.match(r"^---\n.*?\n---\n", text, re.DOTALL):
            errors.append(f"{label}/{md.name}: no YAML frontmatter block")
    return count


def check_scripts() -> int:
    count = 0
    for py in sorted((ROOT / "scripts").glob("*.py")):
        count += 1
        try:
            py_compile.compile(str(py), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(f"scripts/{py.name}: {exc}")
    return count


def main() -> int:
    n_skills = check_skills()
    n_agents = check_md_frontmatter(ROOT / ".opencode" / "agents", "agents")
    n_commands = check_md_frontmatter(ROOT / ".opencode" / "commands", "commands")
    n_scripts = check_scripts()

    for doc in ("README.md", "INSTALL.md", "docs/DATAFORSEO-SETUP.md",
                "docs/GOOGLE-APIS.md", "docs/ARCHITECTURE.md"):
        if not (ROOT / doc).is_file():
            warnings.append(f"missing doc: {doc}")

    print(f"skills   : {n_skills} checked")
    print(f"agents   : {n_agents} checked")
    print(f"commands : {n_commands} checked")
    print(f"scripts  : {n_scripts} compiled")
    for w in warnings:
        print(f"  WARN   : {w}")
    if errors:
        print()
        for e in errors:
            print(f"  ERROR  : {e}")
        print(f"\nVALIDATION FAILED ({len(errors)} errors)")
        return 1
    print("\nVALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
