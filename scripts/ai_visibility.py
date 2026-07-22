"""AI visibility monitor for the OpenCode SEO Suite.

Answers the question clients increasingly ask: "when someone asks an AI
assistant for what we sell, do we get mentioned?"

For each prompt you give it, the monitor queries DataForSEO's LLM
endpoints, checks whether your brand/domain appears in the response, and
stores a dated snapshot so you can track visibility over time.

Usage:
    python scripts/ai_visibility.py check --domain agility.com --brand "Agility" \
        --prompts "best employer of record UK,EOR vs umbrella,top EOR providers"
    python scripts/ai_visibility.py history --domain agility.com
    python scripts/ai_visibility.py compare --domain agility.com

Requires DataForSEO credentials (same as the rest of the suite). The LLM
endpoints live in LLM_ENDPOINTS below — DataForSEO's AI Optimization API
is new, so adjust the paths there if they move.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

import dfs_client  # noqa: E402
from seo_config import SUITE_DIR  # noqa: E402

# DataForSEO AI Optimization endpoints (per-platform LLM Responses, live).
LLM_ENDPOINTS = {
    "chat_gpt": "/v3/ai_optimization/chat_gpt/llm_responses/live",
    "claude": "/v3/ai_optimization/claude/llm_responses/live",
    "gemini": "/v3/ai_optimization/gemini/llm_responses/live",
    "perplexity": "/v3/ai_optimization/perplexity/llm_responses/live",
}
DEFAULT_PLATFORM = "chat_gpt"

# Default model per platform (check `models` action for what your account
# supports; override with --model).
MODEL_DEFAULTS = {
    "chat_gpt": "gpt-4.1-mini",
    "claude": "claude-sonnet-4",
    "gemini": "gemini-2.0-flash",
    "perplexity": "sonar",
}

LOCATION_TO_ISO = {
    "united kingdom": "GB", "united states": "US", "ireland": "IE",
    "canada": "CA", "australia": "AU", "germany": "DE", "france": "FR",
    "spain": "ES", "netherlands": "NL", "italy": "IT", "poland": "PL",
    "india": "IN", "brazil": "BR", "japan": "JP", "sweden": "SE",
    "norway": "NO", "denmark": "DK", "philippines": "PH", "estonia": "EE",
}

STORE_DIR = SUITE_DIR / "ai_visibility"


class VisibilityError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# Response checking
# ---------------------------------------------------------------------------

def _texts(node: Any, out: list[str]) -> list[str]:
    """Collect every string from a nested API response."""
    if isinstance(node, str):
        out.append(node)
    elif isinstance(node, dict):
        for value in node.values():
            _texts(value, out)
    elif isinstance(node, list):
        for item in node:
            _texts(item, out)
    return out


def brand_mentioned(response_body: dict[str, Any], brand: str,
                    domain: str) -> dict[str, Any]:
    """Case-insensitive brand/domain detection across all response text."""
    original = " ".join(_texts(response_body, []))
    haystack = original.lower()
    brand_hit = bool(brand) and brand.lower() in haystack
    domain_hit = bool(domain) and domain.lower() in haystack
    excerpt = ""
    if brand_hit:
        idx = haystack.index(brand.lower())
        excerpt = original[max(0, idx - 80): idx + len(brand) + 80].strip()
    elif domain_hit:
        idx = haystack.index(domain.lower())
        excerpt = original[max(0, idx - 80): idx + len(domain) + 80].strip()
    return {"mentioned": brand_hit or domain_hit,
            "brand_hit": brand_hit, "domain_hit": domain_hit,
            "excerpt": excerpt}


def query_llm(prompt: str, location: str, language: str,
              platform: str = DEFAULT_PLATFORM, model: str | None = None,
              web_search: bool = True, sandbox: bool = False) -> dict[str, Any]:
    path = LLM_ENDPOINTS.get(platform)
    if not path:
        raise VisibilityError(
            f"Unknown platform '{platform}'. Choose from: "
            + ", ".join(sorted(LLM_ENDPOINTS)))
    task: dict[str, Any] = {
        "user_prompt": prompt,
        "model_name": model or MODEL_DEFAULTS.get(platform, "gpt-4.1-mini"),
        "web_search": web_search,
    }
    iso = LOCATION_TO_ISO.get(location.strip().lower())
    if web_search and iso:
        task["web_search_country_iso_code"] = iso
    return dfs_client.post(path, [task], sandbox=sandbox)


def cited_sources(response_body: dict[str, Any]) -> list[dict[str, str]]:
    """Extract the sources the AI cited (annotations) from the response."""
    sources: list[dict[str, str]] = []
    seen: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if "annotations" in node and isinstance(node["annotations"], list):
                for ann in node["annotations"]:
                    url = (ann or {}).get("url", "")
                    if url and url not in seen:
                        seen.add(url)
                        sources.append({"title": ann.get("title", ""),
                                        "url": url})
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(response_body)
    return sources


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------

def _domain_dir(domain: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9.-]", "_", domain.strip().lower())
    return STORE_DIR / safe


def save_snapshot(domain: str, snapshot: dict[str, Any]) -> Path:
    directory = _domain_dir(domain)
    directory.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    path = directory / f"{ts}.json"
    while path.exists():
        ts += 1
        path = directory / f"{ts}.json"
    snapshot = dict(snapshot)
    snapshot["_saved_at"] = ts
    path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False),
                    encoding="utf-8")
    return path


def list_snapshots(domain: str) -> list[int]:
    directory = _domain_dir(domain)
    if not directory.is_dir():
        return []
    return sorted(int(p.stem) for p in directory.glob("*.json")
                  if p.stem.isdigit())


def load(domain: str, ts: int) -> dict[str, Any]:
    return json.loads((_domain_dir(domain) / f"{ts}.json").read_text(
        encoding="utf-8"))


def compare(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    """Per-prompt visibility change between two snapshots."""
    old_p = {r["prompt"]: r for r in old.get("results", [])}
    new_p = {r["prompt"]: r for r in new.get("results", [])}
    gained = sorted(p for p in set(new_p) - set(old_p)
                    if new_p[p].get("mentioned"))
    lost = sorted(p for p in set(old_p) - set(new_p)
                  if old_p[p].get("mentioned"))
    changed = []
    for prompt in set(old_p) & set(new_p):
        before = bool(old_p[prompt].get("mentioned"))
        after = bool(new_p[prompt].get("mentioned"))
        if before != after:
            (gained if after else lost).append(prompt)
        elif after:
            changed.append(prompt)
    return {
        "from": old.get("_saved_at"), "to": new.get("_saved_at"),
        "visibility_gained": gained,
        "visibility_lost": lost,
        "still_visible": changed,
        "rate_from": old.get("visibility_rate"),
        "rate_to": new.get("visibility_rate"),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cmd_check(args: argparse.Namespace) -> int:
    prompts = [p.strip() for p in args.prompts.split(",") if p.strip()]
    if not prompts:
        print(json.dumps({"error": "No prompts given (--prompts a,b,c)"}))
        return 1
    location = dfs_client.normalise_location(args.location)
    results = []
    for prompt in prompts:
        record: dict[str, Any] = {"prompt": prompt, "platform": args.platform}
        try:
            body = query_llm(prompt, location, args.language,
                             platform=args.platform, model=args.model,
                             web_search=not args.no_web_search,
                             sandbox=args.sandbox)
            task_errors = [t for t in dfs_client.tasks(body)
                           if t.get("status_code") not in (20000, None)]
            if task_errors:
                record["error"] = "; ".join(
                    f"{t.get('status_code')} {t.get('status_message')}"
                    for t in task_errors)
                record["mentioned"] = None
            else:
                detection = brand_mentioned(body, args.brand, args.domain)
                record.update(detection)
                record["cited_sources"] = cited_sources(body)
                record["cost"] = body.get("cost")
        except (dfs_client.DfsError, dfs_client.ConfigError,
                VisibilityError) as exc:
            record["error"] = str(exc)
            record["mentioned"] = None
        results.append(record)

    answered = [r for r in results if r.get("mentioned") is not None]
    rate = (round(100 * sum(1 for r in answered if r["mentioned"])
                  / len(answered), 1) if answered else None)
    snapshot = {
        "domain": args.domain, "brand": args.brand,
        "location": location, "language": args.language,
        "results": results,
        "prompts_checked": len(results),
        "prompts_answered": len(answered),
        "prompts_mentioned": sum(1 for r in answered if r["mentioned"]),
        "visibility_rate": rate,
    }
    path = save_snapshot(args.domain, snapshot)
    snapshot["saved"] = str(path)
    print(json.dumps(snapshot, indent=2 if args.pretty else None,
                     ensure_ascii=False))
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    snapshots = list_snapshots(args.domain)
    entries = []
    for ts in snapshots:
        snap = load(args.domain, ts)
        entries.append({"ts": ts, "rate": snap.get("visibility_rate"),
                        "mentioned": snap.get("prompts_mentioned"),
                        "checked": snap.get("prompts_checked")})
    print(json.dumps({"domain": args.domain, "snapshots": entries},
                     indent=2))
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    snapshots = list_snapshots(args.domain)
    if len(snapshots) < 2:
        print(json.dumps({"error": f"Need 2+ snapshots for {args.domain}. "
                                   "Run check twice on different days."}))
        return 1
    old = load(args.domain, snapshots[-2])
    new = load(args.domain, snapshots[-1])
    print(json.dumps(compare(old, new), indent=2, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ai_visibility",
                                     description="AI visibility monitor")
    parser.add_argument("action", choices=["check", "history", "compare"])
    parser.add_argument("--domain", required=True)
    parser.add_argument("--brand", default="", help="brand name to look for")
    parser.add_argument("--prompts", help="comma-separated prompts (check)")
    parser.add_argument("--location", default="United States")
    parser.add_argument("--language", default="English")
    parser.add_argument("--platform", default=DEFAULT_PLATFORM,
                        choices=sorted(LLM_ENDPOINTS),
                        help="which LLM to query (default chat_gpt)")
    parser.add_argument("--model", help="model name override (per platform)")
    parser.add_argument("--no-web-search", action="store_true",
                        help="disable web search (default: enabled)")
    parser.add_argument("--sandbox", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    if args.action == "check":
        return cmd_check(args)
    if args.action == "history":
        return cmd_history(args)
    return cmd_compare(args)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    sys.exit(main())
