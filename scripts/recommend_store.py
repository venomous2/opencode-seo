"""Recommendation store for the OpenCode SEO Suite.

Every finding the suite produces — from the deterministic rule engine, an
audit skill, or a workflow — can be persisted here as a recommendation with
a status lifecycle, so re-audits show progress instead of repeating the
same advice forever.

Storage: ~/.config/opencode/seo-suite/recommendations/<domain>.jsonl
Append-only event log; current state is derived by replaying it.

Events:
    {"event": "raise",  "ts": 1721..., "rec": {...}}   # new or re-detected
    {"event": "status", "ts": 1721..., "id": "...", "status": "...", "note": "..."}

Recommendation shape (all timestamps unix):
    id            stable 12-char hash of domain|url|source|key-or-finding
    domain, url   url may be "" for domain-level recommendations
    source        "rule:<rule-id>" | "skill:<skill-name>" | "manual"
    key           optional stable slug for skill findings (dedup anchor)
    category      rule category or skill area
    severity      critical | high | medium | low
    confidence    high | medium | low
    finding       short label (rule id for rule findings)
    why           rationale, client-facing
    fix           guidance, specific enough to hand to whoever owns it
    evidence      optional dict (field/condition/expected/actual for rules)
    auto_fixable  true when seo_fix can patch it
    status        open | accepted | done | ignored | resolved
    times_raised  how often the issue has been (re-)detected
    created, updated

Status lifecycle:
    open      newly raised, needs a decision
    accepted  will be actioned
    done      fixed by the user (re-raising reopens it — a regression)
    ignored   consciously dismissed (re-raising keeps it ignored but counts)
    resolved  no longer detected by a lint run that checked for it

Usage:
    python scripts/recommend_store.py add --domain example.com --file recs.json
    echo '[{...}]' | python scripts/recommend_store.py add --domain example.com
    python scripts/recommend_store.py list --domain example.com [--status open]
    python scripts/recommend_store.py set --domain example.com --id abc123 --status accepted
    python scripts/recommend_store.py summary --domain example.com
    python scripts/recommend_store.py history --domain example.com --id abc123
    python scripts/recommend_store.py domains
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

from seo_config import SUITE_DIR
import event_log

RECS_DIR = SUITE_DIR / "recommendations"

STATUSES = ("open", "accepted", "done", "ignored", "resolved")
CLOSED = ("done", "ignored", "resolved")
SEVERITIES = ("critical", "high", "medium", "low")
CONFIDENCES = ("high", "medium", "low")

_SEVERITY_ORDER = {s: i for i, s in enumerate(SEVERITIES)}


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

def _path(domain: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9.-]", "_", domain.strip().lower())
    return RECS_DIR / f"{safe}.jsonl"


def _append(domain: str, event: dict[str, Any]) -> None:
    RECS_DIR.mkdir(parents=True, exist_ok=True)
    with _path(domain).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False) + "\n")


def events(domain: str) -> list[dict[str, Any]]:
    path = _path(domain)
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def domains() -> list[str]:
    if not RECS_DIR.is_dir():
        return []
    return sorted(p.stem for p in RECS_DIR.glob("*.jsonl"))


# ---------------------------------------------------------------------------
# Normalisation + replay
# ---------------------------------------------------------------------------

def make_id(domain: str, url: str, source: str, anchor: str) -> str:
    raw = "|".join([domain.strip().lower(), url.strip(), source.strip(),
                    anchor.strip().lower()])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def normalise(domain: str, rec: dict[str, Any]) -> dict[str, Any]:
    """Fill defaults and validate an incoming recommendation."""
    finding = str(rec.get("finding", "")).strip()
    if not finding:
        raise ValueError("recommendation needs a 'finding' label")
    source = str(rec.get("source", "manual")).strip() or "manual"
    url = str(rec.get("url", "")).strip()
    key = str(rec.get("key", "")).strip()
    severity = str(rec.get("severity", "medium")).lower()
    if severity not in SEVERITIES:
        severity = "medium"
    confidence = str(rec.get("confidence", "medium")).lower()
    if confidence not in CONFIDENCES:
        confidence = "medium"
    return {
        "id": make_id(domain, url, source, key or finding),
        "domain": domain,
        "url": url,
        "source": source,
        "key": key,
        "category": str(rec.get("category", "general")),
        "severity": severity,
        "confidence": confidence,
        "finding": finding,
        "why": str(rec.get("why", "")),
        "fix": str(rec.get("fix", "")),
        "evidence": rec.get("evidence"),
        "auto_fixable": bool(rec.get("auto_fixable", False)),
        "status": "open",
        "times_raised": 1,
        "created": 0,
        "updated": 0,
    }


def replay(domain: str) -> dict[str, dict[str, Any]]:
    """Fold the event log into current state, keyed by recommendation id."""
    state: dict[str, dict[str, Any]] = {}
    for event in events(domain):
        kind = event.get("event")
        ts = int(event.get("ts", 0))
        if kind == "raise":
            incoming = dict(event["rec"])
            rid = incoming["id"]
            current = state.get(rid)
            if current is None:
                incoming.setdefault("status", "open")
                incoming.setdefault("times_raised", 1)
                incoming["created"] = ts
                incoming["updated"] = ts
                state[rid] = incoming
                continue
            # re-detected: refresh detail fields, keep the user's decision
            for field in ("severity", "confidence", "why", "fix",
                          "evidence", "auto_fixable", "category"):
                if incoming.get(field) not in (None, ""):
                    current[field] = incoming[field]
            current["times_raised"] = current.get("times_raised", 1) + 1
            current["updated"] = ts
            if current["status"] in ("done", "resolved"):
                current["status"] = "open"  # regression: it came back
        elif kind == "status":
            current = state.get(event.get("id"))
            if current is not None and event.get("status") in STATUSES:
                current["status"] = event["status"]
                current["updated"] = ts
                if event.get("note"):
                    current["last_note"] = event["note"]
    return state


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def raise_rec(domain: str, rec: dict[str, Any]) -> dict[str, Any]:
    """Persist a (re-)detected recommendation; returns its current state."""
    domain = domain.strip().lower()
    record = normalise(domain, rec)
    prior = replay(domain).get(record["id"])
    now = int(time.time())
    _append(domain, {"event": "raise", "ts": now, "rec": record})
    after = dict(record)
    after["created"] = prior["created"] if prior is not None else now
    after["updated"] = now
    if prior is not None:
        after["times_raised"] = prior.get("times_raised", 1) + 1
        after["status"] = prior["status"]
        if prior["status"] in ("done", "resolved"):
            after["status"] = "open"
    if prior is None:
        event_log.log(domain, "rec_raised",
                      f"[{after['severity']}] {after['finding']}"
                      + (f" — {after['url']}" if after["url"] else ""),
                      {"id": after["id"], "source": after["source"]})
    elif after["status"] == "open" and prior["status"] in ("done", "resolved"):
        event_log.log(domain, "rec_reopened",
                      f"Regression: {after['finding']}"
                      + (f" — {after['url']}" if after["url"] else ""),
                      {"id": after["id"], "source": after["source"]})
    return after


def set_status(domain: str, rec_id: str, status: str,
               note: str = "") -> dict[str, Any] | None:
    if status not in STATUSES:
        raise ValueError(f"status must be one of {', '.join(STATUSES)}")
    state = replay(domain)
    if rec_id not in state:
        return None
    _append(domain, {"event": "status", "ts": int(time.time()),
                     "id": rec_id, "status": status, "note": note[:300]})
    rec = state[rec_id]
    event_log.log(domain, "rec_status",
                  f"{rec['finding']} → {status}"
                  + (f" ({note})" if note else ""),
                  {"id": rec_id, "status": status})
    updated = dict(rec)
    updated["status"] = status
    if note:
        updated["last_note"] = note
    return updated


def get(domain: str, rec_id: str) -> dict[str, Any] | None:
    return replay(domain).get(rec_id)


def list_recs(domain: str, status: str | None = None,
              severity: str | None = None,
              include_closed: bool = False) -> list[dict[str, Any]]:
    recs = list(replay(domain).values())
    if status:
        recs = [r for r in recs if r["status"] == status]
    elif not include_closed:
        recs = [r for r in recs if r["status"] not in CLOSED]
    if severity:
        recs = [r for r in recs if r["severity"] == severity]
    recs.sort(key=lambda r: (_SEVERITY_ORDER[r["severity"]], -r["updated"]))
    return recs


def summary(domain: str) -> dict[str, Any]:
    recs = list(replay(domain).values())
    by_status = {s: 0 for s in STATUSES}
    open_by_severity = {s: 0 for s in SEVERITIES}
    for r in recs:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
        if r["status"] in ("open", "accepted"):
            open_by_severity[r["severity"]] += 1
    open_recs = [r for r in recs if r["status"] in ("open", "accepted")]
    return {
        "domain": domain,
        "store": str(_path(domain)),
        "total": len(recs),
        "by_status": by_status,
        "actionable": len(open_recs),
        "actionable_by_severity": open_by_severity,
        "auto_fixable_open": sum(1 for r in open_recs if r["auto_fixable"]),
    }


def history(domain: str, rec_id: str) -> list[dict[str, Any]]:
    return [e for e in events(domain)
            if (e.get("rec") or {}).get("id") == rec_id
            or e.get("id") == rec_id]


def save_lint_results(domain: str, results: list[dict[str, Any]],
                      rules: list[dict[str, Any]]) -> dict[str, Any]:
    """Persist a seo_lint run: raise every finding, auto-resolve fixes.

    A previously-raised rule recommendation for a linted URL is marked
    `resolved` when its rule ran this time and no longer fires — but only
    among the rules that actually ran (partial/category runs never resolve
    what they didn't check).
    """
    patchable = {r["id"] for r in rules
                 if isinstance(r.get("fix"), dict) and r["fix"].get("patch")}
    rules_run = {r["id"] for r in rules}
    state = replay(domain)

    raised = reopened = 0
    present: dict[str, set[str]] = {}   # url -> set of rule ids firing now
    for result in results:
        url = result.get("url", "")
        seen = present.setdefault(url, set())
        for f in result.get("findings", []):
            seen.add(f["id"])
            rid = make_id(domain, url, f"rule:{f['id']}", f["id"])
            was_closed = (state.get(rid) or {}).get("status") in ("done",
                                                                  "resolved")
            raise_rec(domain, {
                "url": url,
                "source": f"rule:{f['id']}",
                "category": f.get("category", "general"),
                "severity": f.get("severity", "medium"),
                "confidence": f.get("confidence", "medium"),
                "finding": f["id"],
                "why": f.get("why", ""),
                "fix": f.get("fix", ""),
                "evidence": f.get("evidence"),
                "auto_fixable": f["id"] in patchable,
            })
            raised += 1
            if was_closed:
                reopened += 1

    resolved = 0
    linted_urls = {r.get("url", "") for r in results}
    for rec in list(state.values()):
        if not rec["source"].startswith("rule:"):
            continue
        if rec["url"] not in linted_urls:
            continue
        rule_id = rec["source"].split(":", 1)[1]
        if rule_id not in rules_run:
            continue
        if rule_id in present.get(rec["url"], set()):
            continue
        if rec["status"] in CLOSED:
            continue
        set_status(domain, rec["id"], "resolved",
                   note="no longer detected by seo_lint")
        resolved += 1

    if raised or resolved:
        event_log.log(domain, "lint_saved",
                      f"Lint saved: {raised} finding(s), {resolved} resolved",
                      {"raised": raised, "reopened": reopened,
                       "resolved": resolved,
                       "urls": len(linted_urls)})

    return {"domain": domain, "raised": raised, "reopened": reopened,
            "resolved": resolved,
            "open_total": summary(domain)["actionable"]}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="recommend_store",
        description="Per-domain recommendation store (status lifecycle)")
    parser.add_argument("action",
                        choices=["add", "list", "set", "get", "summary",
                                 "history", "domains"])
    parser.add_argument("--domain", help="domain the recommendations belong to")
    parser.add_argument("--file", help="JSON file of recommendations (add); "
                                       "omit for stdin")
    parser.add_argument("--id", help="recommendation id (set/get/history)")
    parser.add_argument("--status", help="new status (set) or filter (list)")
    parser.add_argument("--severity", help="severity filter (list)")
    parser.add_argument("--all", action="store_true",
                        help="include done/ignored/resolved (list)")
    parser.add_argument("--note", help="optional note recorded with set")
    args = parser.parse_args(argv)

    if args.action == "domains":
        print(json.dumps({"domains": domains()}, indent=2))
        return 0
    if not args.domain:
        print(json.dumps({"error": "--domain is required"}))
        return 1
    domain = args.domain.strip().lower()

    try:
        if args.action == "add":
            raw = Path(args.file).read_text(encoding="utf-8") \
                if args.file else sys.stdin.read()
            payload = json.loads(raw)
            recs = payload if isinstance(payload, list) else [payload]
            saved = [raise_rec(domain, r) for r in recs]
            print(json.dumps({"domain": domain, "added": len(saved),
                              "recommendations": saved},
                             indent=2, ensure_ascii=False))
            return 0
        if args.action == "list":
            recs = list_recs(domain, status=args.status,
                             severity=args.severity,
                             include_closed=args.all)
            print(json.dumps({"domain": domain, "count": len(recs),
                              "recommendations": recs},
                             indent=2, ensure_ascii=False))
            return 0
        if args.action == "summary":
            print(json.dumps(summary(domain), indent=2, ensure_ascii=False))
            return 0
        # set / get / history need --id
        if not args.id:
            print(json.dumps({"error": "--id is required"}))
            return 1
        if args.action == "set":
            if not args.status:
                print(json.dumps({"error": "--status is required"}))
                return 1
            updated = set_status(domain, args.id, args.status,
                                 note=args.note or "")
            if updated is None:
                print(json.dumps({"error": f"no recommendation {args.id}"}))
                return 1
            print(json.dumps(updated, indent=2, ensure_ascii=False))
            return 0
        if args.action == "get":
            rec = get(domain, args.id)
            if rec is None:
                print(json.dumps({"error": f"no recommendation {args.id}"}))
                return 1
            print(json.dumps(rec, indent=2, ensure_ascii=False))
            return 0
        # history
        print(json.dumps({"domain": domain, "id": args.id,
                          "events": history(domain, args.id)},
                         indent=2, ensure_ascii=False))
        return 0
    except (ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
