"""Project memory loader for the OpenCode SEO Suite.

Workflow skills call this to load persistent SEO context so outputs stay
consistent across sessions. Supports two modes:

  * Single project:  seo-project.yml in the project directory
  * Client mode:     clients/<name>.yml for freelancers/agencies managing
                     several sites (use --client <name>)

Usage:
    python scripts/project_memory.py [--path seo-project.yml] [--init]
    python scripts/project_memory.py --client acme [--init] [--check]
    python scripts/project_memory.py --list-clients
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

TEMPLATE = """# OpenCode SEO Suite - project memory
# Workflow skills read this file to keep outputs consistent.
# Every field is optional; fill in what you know.

site:
  name: "Example Site"
  url: "https://example.com"
  type: "saas"              # saas | ecommerce | publisher | local | agency | other
  language: "en"
  country: "United States"  # DataForSEO location_name default

audience:
  description: "Who the site serves"
  pain_points: []

brand:
  voice: "clear, expert, friendly"
  tone_notes: []

goals:
  primary: "grow qualified organic signups"
  kpis: []

competitors: []             # ["competitor1.com", "competitor2.com"]

focus_keywords: []          # priority keywords for this quarter

schema:
  preferred_types: ["Organization", "WebSite", "BreadcrumbList"]

constraints:
  cms: ""                   # wordpress | shopify | webflow | custom | ...
  deploy_notes: ""

notes: ""
"""

DEFAULT_NAME = "seo-project.yml"
CLIENTS_DIR = "clients"


def client_path(name: str, start: Path | None = None) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name.lower())
    base = (start or Path.cwd()).resolve()
    return base / CLIENTS_DIR / f"{safe}.yml"


def list_clients(start: Path | None = None) -> list[str]:
    directory = (start or Path.cwd()).resolve() / CLIENTS_DIR
    if not directory.is_dir():
        return []
    return sorted(p.stem for p in directory.glob("*.yml"))


def find_project_file(start: Path | None = None) -> Path | None:
    current = (start or Path.cwd()).resolve()
    for directory in (current, *current.parents):
        for name in (DEFAULT_NAME, "seo-project.yaml"):
            candidate = directory / name
            if candidate.is_file():
                return candidate
    return None


def load(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError:
        return {"error": "PyYAML not installed. Run: pip install pyyaml",
                "path": str(path)}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - surface any YAML error plainly
        return {"error": f"Cannot parse {path}: {exc}", "path": str(path)}
    return {"path": str(path), "project": data or {}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="project_memory",
                                     description="Project memory loader")
    parser.add_argument("--path", help="explicit path to seo-project.yml")
    parser.add_argument("--client", help="load/create clients/<name>.yml")
    parser.add_argument("--list-clients", action="store_true",
                        help="list all client profiles")
    parser.add_argument("--init", action="store_true",
                        help="create a starter memory file")
    parser.add_argument("--check", action="store_true",
                        help="validate and report problems")
    args = parser.parse_args(argv)

    if args.list_clients:
        print(json.dumps({"clients": list_clients()}))
        return 0

    if args.init:
        target = client_path(args.client) if args.client \
            else Path(args.path or DEFAULT_NAME)
        if target.exists():
            print(json.dumps({"error": f"{target} already exists"}))
            return 1
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(TEMPLATE, encoding="utf-8")
        print(json.dumps({"created": str(target.resolve())}))
        return 0

    if args.client:
        path = client_path(args.client)
        if not path.is_file():
            print(json.dumps({"error": f"No profile for client '{args.client}'. "
                                       f"Create one with: python scripts/project_memory.py "
                                       f"--client {args.client} --init"}))
            return 1
    else:
        path = Path(args.path) if args.path else find_project_file()
    if not path or not path.is_file():
        print(json.dumps({
            "error": "No seo-project.yml found. Create one with: "
                     "python scripts/project_memory.py --init"}))
        return 1

    result = load(path)
    if args.check:
        project = result.get("project") or {}
        problems = []
        if not (project.get("site") or {}).get("url"):
            problems.append("site.url is not set")
        if not project.get("competitors"):
            problems.append("competitors list is empty (recommended)")
        result["check"] = "ok" if not problems else problems
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if "error" not in result else 1


if __name__ == "__main__":
    sys.exit(main())
