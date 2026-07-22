"""Rule engine for the OpenCode SEO Suite.

MODEL-AGNOSTIC BY DESIGN: the engine is deterministic Python evaluating
YAML rule definitions against extracted page data. It makes zero model
calls, so it behaves identically regardless of which LLM OpenCode is
running. Models only ever consume the engine's JSON output.

A rule (rules/<category>/<id>.yaml):

    id: missing-title
    category: metadata
    severity: critical            # critical | high | medium | low
    confidence: high              # how certain the detection itself is
    detect:
      field: title
      condition: empty
    why: >
      One or two sentences explaining the mechanism — shown to clients.
    fix:
      guidance: What to do, specific enough to hand to whoever owns it.
    test:
      expect_fail: {title: ""}
      expect_pass: {title: "My Page"}

Usage:
    python scripts/rule_engine.py list [--category metadata]
    python scripts/rule_engine.py run --page '{"title": "", ...}'
    python scripts/rule_engine.py test            # self-test every rule
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REQUIRED_KEYS = {"id", "category", "severity", "detect", "why", "fix"}
SEVERITIES = ("critical", "high", "medium", "low")
SEVERITY_WEIGHT = {"critical": 25, "high": 15, "medium": 8, "low": 3}

RULES_DIR = Path(__file__).resolve().parent.parent / "rules"


class RuleError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# Loading + validation
# ---------------------------------------------------------------------------

def load_rules(rules_dir: Path | None = None,
               category: str | None = None) -> list[dict[str, Any]]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuleError("PyYAML not installed. Run: pip install pyyaml") from exc

    directory = rules_dir or RULES_DIR
    if not directory.is_dir():
        raise RuleError(f"Rules directory not found: {directory}")

    rules: list[dict[str, Any]] = []
    errors: list[str] = []
    for path in sorted(directory.rglob("*.yaml")):
        try:
            rule = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            errors.append(f"{path.name}: YAML error: {exc}")
            continue
        if not isinstance(rule, dict):
            errors.append(f"{path.name}: not a mapping")
            continue
        missing = REQUIRED_KEYS - set(rule)
        if missing:
            errors.append(f"{path.name}: missing keys {sorted(missing)}")
            continue
        if rule["severity"] not in SEVERITIES:
            errors.append(f"{path.name}: bad severity '{rule['severity']}'")
            continue
        detect = rule["detect"]
        if not isinstance(detect, dict) or "field" not in detect \
                or "condition" not in detect:
            errors.append(f"{path.name}: detect needs field + condition")
            continue
        rule["_path"] = str(path)
        rules.append(rule)

    if errors:
        raise RuleError("Invalid rule files:\n  " + "\n  ".join(errors))
    if category:
        rules = [r for r in rules if r["category"] == category]
    return rules


# ---------------------------------------------------------------------------
# Condition evaluation
# ---------------------------------------------------------------------------

def _length(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, (list, tuple, dict)):
        return len(value)
    return len(str(value))


ZERO_MEANS_ABSENT = {
    "h1_count", "h2_count", "word_count", "images_total",
    "images_missing_alt", "schema_blocks", "internal_link_count",
    "external_link_count", "first_h2_para_words",
}


def evaluate(detect: dict[str, Any], page: dict[str, Any]) -> bool:
    """True = the rule FIRES (the problem is present)."""
    field = detect["field"]
    condition = detect["condition"]
    expected = detect.get("value")
    value = page.get(field)

    if condition == "empty":
        if value is None or value == "" or value == []:
            return True
        # numeric zero counts as "absent" only for count-style fields
        return value == 0 and field in ZERO_MEANS_ABSENT
    if condition == "not_empty":
        return not evaluate({"field": field, "condition": "empty"}, page)
    if condition == "equals":
        return value == expected
    if condition == "not_equals":
        return value != expected
    if condition == "is_true":
        return value is True
    if condition == "is_false":
        return value is False or value is None
    if condition == "min_length":
        return _length(value) < int(expected)      # fires when TOO SHORT
    if condition == "max_length":
        return _length(value) > int(expected)      # fires when TOO LONG
    if condition == "min":
        return _num(value) < float(expected)       # fires when BELOW
    if condition == "max":
        return _num(value) > float(expected)       # fires when ABOVE
    if condition == "gte":
        return _num(value) >= float(expected)      # fires when AT LEAST
    if condition == "lte":
        return _num(value) <= float(expected)      # fires when AT MOST
    if condition == "contains":
        return str(expected).lower() in str(value or "").lower()
    if condition == "not_contains":
        return str(expected).lower() not in str(value or "").lower()
    if condition == "list_contains":
        return any(str(expected).lower() == str(item).lower()
                   for item in (value or []))
    if condition == "list_not_contains":
        return not evaluate({"field": field, "condition": "list_contains",
                             "value": expected}, page)
    if condition == "matches":
        return bool(re.search(str(expected), str(value or ""), re.IGNORECASE))
    raise RuleError(f"Unknown condition: {condition}")


def _num(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


# ---------------------------------------------------------------------------
# Running rules against a page
# ---------------------------------------------------------------------------

def run(page: dict[str, Any], rules: list[dict[str, Any]]) -> dict[str, Any]:
    findings = []
    for rule in rules:
        try:
            fired = evaluate(rule["detect"], page)
        except RuleError as exc:
            raise RuleError(f"Rule {rule['id']}: {exc}") from exc
        if not fired:
            continue
        detect = rule["detect"]
        findings.append({
            "id": rule["id"],
            "category": rule["category"],
            "severity": rule["severity"],
            "confidence": rule.get("confidence", "medium"),
            **({"wcag": rule["wcag"]} if rule.get("wcag") else {}),
            **({"wcag_level": rule["wcag_level"]} if rule.get("wcag_level") else {}),
            "evidence": {
                "field": detect["field"],
                "condition": detect["condition"],
                "expected": detect.get("value"),
                "actual": page.get(detect["field"]),
            },
            "why": rule["why"].strip(),
            "fix": (rule["fix"].get("guidance", "")
                    if isinstance(rule["fix"], dict) else str(rule["fix"])).strip(),
        })
    order = {s: i for i, s in enumerate(SEVERITIES)}
    findings.sort(key=lambda f: order[f["severity"]])
    score = max(0, 100 - sum(SEVERITY_WEIGHT[f["severity"]] for f in findings))
    return {
        "score": score,
        "rules_run": len(rules),
        "passed": len(rules) - len(findings),
        "failed": len(findings),
        "findings": findings,
    }


# ---------------------------------------------------------------------------
# Rule self-tests (embedded expect_fail / expect_pass fixtures)
# ---------------------------------------------------------------------------

def test_rules(rules: list[dict[str, Any]]) -> dict[str, Any]:
    results = []
    for rule in rules:
        fixture = rule.get("test") or {}
        entry = {"id": rule["id"], "ok": True, "detail": ""}
        for mode, should_fire in (("expect_fail", True), ("expect_pass", False)):
            if mode not in fixture:
                entry["ok"] = False
                entry["detail"] = f"missing {mode} fixture"
                break
            fired = evaluate(rule["detect"], fixture[mode])
            if fired != should_fire:
                entry["ok"] = False
                entry["detail"] = (f"{mode} expected fire={should_fire}, "
                                   f"got {fired}")
                break
        results.append(entry)
    failed = [r for r in results if not r["ok"]]
    return {"rules": len(results), "failed": len(failed),
            "failures": failed, "ok": not failed}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rule_engine",
                                     description="SEO rule engine")
    parser.add_argument("action", choices=["list", "run", "test"])
    parser.add_argument("--category", help="restrict to one category")
    parser.add_argument("--rules-dir", help="override rules directory")
    parser.add_argument("--page", help="page record JSON (run); omit for stdin")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    try:
        rules = load_rules(Path(args.rules_dir) if args.rules_dir else None,
                           category=args.category)
        if args.action == "list":
            print(json.dumps([
                {"id": r["id"], "category": r["category"],
                 "severity": r["severity"],
                 "confidence": r.get("confidence", "medium")}
                for r in rules], indent=2 if args.pretty else None))
            return 0
        if args.action == "test":
            result = test_rules(rules)
            print(json.dumps(result, indent=2 if args.pretty else None))
            return 0 if result["ok"] else 1
        # run
        raw = args.page or sys.stdin.read()
        page = json.loads(raw)
        print(json.dumps(run(page, rules),
                         indent=2 if args.pretty else None, ensure_ascii=False))
        return 0
    except (RuleError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
