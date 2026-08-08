"""Deterministic SXO baseline for the OpenCode SEO Suite.

SXO asks whether a landing page gives searchers the experience the live SERP
appears to reward. This module deliberately separates measured facts from
judgement: page type, CRO/accessibility baselines and SERP consensus are
deterministic; the workflow skill turns them into searcher segments and an
implementation blueprint.

Usage:
    python scripts/sxo_analyser.py --url https://example.com/page
    python scripts/sxo_analyser.py --url U --keyword "best espresso grinder" --save
    python scripts/sxo_analyser.py --file page.html --serp-file serp.json

`--keyword` performs one DataForSEO SERP pull. A title/H1-derived candidate
is shown when omitted, but is never spent automatically: confirm it first.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.parse
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

import recommend_store  # noqa: E402
import rule_engine  # noqa: E402
import seo_lint  # noqa: E402
from site_crawler import fetch  # noqa: E402

SCRIPTS_DIR = Path(__file__).resolve().parent
PAGE_TYPES = ("product", "comparison", "local", "tool", "service",
              "article", "landing", "hybrid", "unknown")


class SxoError(RuntimeError):
    pass


def _text(page: dict[str, Any]) -> str:
    h1 = page.get("h1") or []
    if isinstance(h1, str):
        h1 = [h1]
    h2 = page.get("h2") or []
    if isinstance(h2, str):
        h2 = [h2]
    return " ".join([page.get("url", ""), page.get("title", ""),
                     *h1, *h2]).lower()


def _schema(page: dict[str, Any], *names: str) -> bool:
    types = {str(t).lower() for t in page.get("schema_types") or []}
    return any(name.lower() in types for name in names)


def _add(scores: dict[str, int], evidence: dict[str, list[str]],
         page_type: str, points: int, reason: str) -> None:
    scores[page_type] += points
    evidence[page_type].append(reason)


def classify_page(page: dict[str, Any]) -> dict[str, Any]:
    """Classify a page from observable structural signals.

    This is not a business truth machine. It returns ranked candidates and
    evidence rather than forcing every page into one arbitrary type.
    """
    scores = {kind: 0 for kind in PAGE_TYPES if kind != "unknown"}
    evidence = {kind: [] for kind in scores}
    text = _text(page)
    url = str(page.get("url", "")).lower()

    if _schema(page, "Product", "Offer"):
        _add(scores, evidence, "product", 4, "Product or Offer schema")
    if re.search(r"/(product|products|shop|store|p)/", url):
        _add(scores, evidence, "product", 2, "product/shop URL pattern")
    if re.search(r"\b(buy|shop|sale|price)\b", text):
        _add(scores, evidence, "product", 1, "commercial product language")

    if re.search(r"\b(vs\.?|versus|alternatives?|compare|comparison|best\s+\w+)",
                 text):
        _add(scores, evidence, "comparison", 4,
             "comparison/alternatives language")
    if page.get("tables_total", 0):
        _add(scores, evidence, "comparison", 1, "comparison-capable table")

    if _schema(page, "LocalBusiness", "ProfessionalService"):
        _add(scores, evidence, "local", 4, "local business schema")
    if re.search(r"/(location|locations|near-me|contact)/", url):
        _add(scores, evidence, "local", 2, "location/contact URL pattern")
    if page.get("tel_links", 0):
        _add(scores, evidence, "local", 1, "tap-to-call contact link")

    if _schema(page, "WebApplication", "SoftwareApplication"):
        _add(scores, evidence, "tool", 4, "application schema")
    if re.search(r"\b(calculator|generator|checker|tool)\b", text):
        _add(scores, evidence, "tool", 3, "tool/calculator language")
    if page.get("form_count", 0):
        _add(scores, evidence, "tool", 1, "interactive form present")

    if _schema(page, "Service", "ProfessionalService"):
        _add(scores, evidence, "service", 4, "service schema")
    if re.search(r"\b(service|services|consulting|consultant|agency)\b", text):
        _add(scores, evidence, "service", 2, "service language")

    if _schema(page, "Article", "BlogPosting", "NewsArticle"):
        _add(scores, evidence, "article", 4, "article schema")
    if page.get("time_elements") or page.get("meta_author"):
        _add(scores, evidence, "article", 1, "author/date signal")
    if "/blog/" in url or "/article/" in url:
        _add(scores, evidence, "article", 2, "editorial URL pattern")

    if page.get("cta_count", 0) >= 2:
        _add(scores, evidence, "landing", 3, "multiple calls to action")
    if page.get("form_count", 0):
        _add(scores, evidence, "landing", 1, "lead/purchase form present")
    if 0 < page.get("word_count", 0) < 900:
        _add(scores, evidence, "landing", 1, "concise landing-page depth")

    if scores["article"] >= 3 and scores["landing"] >= 3:
        _add(scores, evidence, "hybrid", max(scores["article"],
                                               scores["landing"]) + 1,
             "strong editorial and conversion signals")

    ranked = sorted(((kind, value) for kind, value in scores.items() if value),
                    key=lambda pair: (-pair[1], pair[0]))
    if not ranked:
        return {"primary": "unknown", "secondary": None,
                "confidence": "low", "candidates": [], "evidence": []}

    primary, top = ranked[0]
    secondary = ranked[1][0] if len(ranked) > 1 else None
    gap = top - (ranked[1][1] if len(ranked) > 1 else 0)
    confidence = "high" if top >= 5 and gap >= 2 else \
        "medium" if top >= 3 else "low"
    return {
        "primary": primary,
        "secondary": secondary,
        "confidence": confidence,
        "candidates": [{"type": kind, "score": value,
                        "evidence": evidence[kind]} for kind, value in ranked],
        "evidence": evidence[primary],
    }


def keyword_candidate(page: dict[str, Any]) -> str | None:
    """Conservative candidate only; never use it for a paid pull automatically."""
    raw = " ".join((page.get("h1") or [])[:1]) or page.get("title", "")
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]*", raw.lower())
    stop = {"the", "a", "an", "and", "or", "for", "with", "to", "of", "in",
            "on", "your", "our", "best", "guide", "2025", "2026"}
    terms = [word for word in words if word not in stop]
    return " ".join(terms[:4]) or None


def _walk_serp(node: Any, found: list[dict[str, Any]]) -> None:
    if isinstance(node, dict):
        if isinstance(node.get("items"), list):
            found.extend(item for item in node["items"] if isinstance(item, dict))
        for key in ("result", "results", "tasks"):
            if key in node:
                _walk_serp(node[key], found)
    elif isinstance(node, list):
        for item in node:
            _walk_serp(item, found)


def serp_consensus(payload: dict[str, Any]) -> dict[str, Any]:
    """Classify organic results and calculate page-type consensus."""
    raw_items: list[dict[str, Any]] = []
    _walk_serp(payload, raw_items)
    seen: set[tuple[str, str]] = set()
    organic = []
    features: Counter[str] = Counter()
    for item in raw_items:
        kind = str(item.get("type", "organic")).lower()
        if kind != "organic":
            features[kind] += 1
            continue
        url = str(item.get("url", ""))
        title = str(item.get("title", item.get("title_tag", "")))
        if not url and not title:
            continue
        key = (url, title)
        if key in seen:
            continue
        seen.add(key)
        page = {"url": url, "title": title, "h1": [], "h2": [],
                "schema_types": [], "tables_total": 0, "cta_count": 0,
                "form_count": 0, "word_count": 0, "tel_links": 0}
        classification = classify_page(page)
        organic.append({"url": url, "title": title,
                        "page_type": classification})

    classified = [item for item in organic
                  if item["page_type"]["primary"] != "unknown"]
    counts = Counter(item["page_type"]["primary"] for item in classified)
    dominant, count = counts.most_common(1)[0] if counts else ("unknown", 0)
    share = round(count / len(classified), 2) if classified else 0.0
    confidence = "high" if len(classified) >= 5 and share >= 0.6 else \
        "medium" if len(classified) >= 3 and share >= 0.4 else "low"
    verdict = "strong_consensus" if share >= 0.6 else \
        "mixed" if share >= 0.4 else "fragmented"
    return {
        "organic_results": len(organic),
        "classified_results": len(classified),
        "types": dict(counts),
        "dominant_type": dominant,
        "dominant_share": share,
        "verdict": verdict,
        "confidence": confidence,
        "features": dict(features),
        "results": organic[:10],
    }


def alignment(target: dict[str, Any], consensus: dict[str, Any] | None) -> dict[str, Any]:
    if not consensus or consensus["dominant_type"] == "unknown":
        return {"status": "unavailable", "score": None,
                "confidence": "low", "why": "No classifiable organic SERP sample"}
    if consensus["verdict"] == "fragmented":
        return {"status": "mixed", "score": None,
                "confidence": consensus["confidence"],
                "why": "SERP is fragmented; differentiation may be viable"}
    dominant = consensus["dominant_type"]
    if target["primary"] == dominant:
        return {"status": "aligned", "score": 100,
                "confidence": consensus["confidence"],
                "why": f"Target primary type matches {dominant} SERP consensus"}
    if target.get("secondary") == dominant:
        return {"status": "partially_aligned", "score": 70,
                "confidence": consensus["confidence"],
                "why": f"Target secondary type matches {dominant} SERP consensus"}
    return {"status": "mismatch", "score": 35,
            "confidence": consensus["confidence"],
            "why": f"Target is {target['primary']}; live SERP favours {dominant}"}


def experience_baseline(page: dict[str, Any]) -> dict[str, Any]:
    """Reuse existing deterministic CRO and accessibility checks; no duplicates."""
    out = {}
    for category, label in (("cro", "conversion_readiness"),
                            ("accessibility", "accessibility_baseline")):
        rules = rule_engine.load_rules(category=category)
        result = rule_engine.run(page, rules)
        out[label] = {"score": result["score"], "findings": result["failed"],
                      "rules": result["rules_run"]}
    return out


def recommendation(domain: str, keyword: str | None, target: dict[str, Any],
                   consensus: dict[str, Any] | None,
                   fit: dict[str, Any]) -> dict[str, Any] | None:
    if not consensus or fit["status"] != "mismatch" \
            or consensus["confidence"] == "low":
        return None
    target_type = target["primary"]
    expected = consensus["dominant_type"]
    severity = "critical" if target_type == "article" and expected in {
        "product", "tool", "local"} else "high"
    return {
        "url": "",
        "source": "workflow:sxo",
        "key": f"page-type-{re.sub(r'[^a-z0-9]+', '-', (keyword or expected).lower()).strip('-')}",
        "category": "sxo",
        "severity": severity,
        "confidence": consensus["confidence"],
        "finding": f"Page-type mismatch: {target_type} page for {expected} SERP",
        "why": (f"{consensus['dominant_share']:.0%} of classified live SERP "
                f"results are {expected} pages; the target classifies as {target_type}."),
        "fix": (f"Validate the intent with first-party data, then build or "
                f"reshape the landing experience around a {expected} page model."),
        "evidence": {"keyword": keyword, "target_type": target_type,
                     "serp_type": expected, "serp_share": consensus["dominant_share"],
                     "classified_results": consensus["classified_results"]},
    }


def _fetch_page(url: str, render: str, timeout: int) -> tuple[dict[str, Any], str]:
    result = fetch(url, timeout)
    if result.status != 200 or "html" not in result.content_type.lower():
        raise SxoError(f"Fetch failed: HTTP {result.status}")
    html_text, engine = result.body, "raw"
    if render != "never":
        import spa_detect
        should_render = render == "always" or (
            render == "auto" and spa_detect.detect(result.body, url)["should_render"])
        if should_render:
            import render_page
            try:
                html_text, engine = render_page.render(url, engine="auto")
            except Exception:  # noqa: BLE001 - raw HTML is honest fallback
                engine = "raw-fallback"
    page = seo_lint.parse_html(html_text, url)
    return page, engine


def _fetch_serp(keyword: str, location: str, language: str,
                sandbox: bool) -> dict[str, Any]:
    cmd = [sys.executable, str(SCRIPTS_DIR / "dfs_client.py"), "serp",
           "--keyword", keyword, "--limit", "10", "--location", location,
           "--language", language]
    if sandbox:
        cmd.append("--sandbox")
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        raise SxoError((proc.stdout or proc.stderr).strip()[:300])
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise SxoError(f"DataForSEO returned non-JSON: {exc}") from exc


def analyse(page: dict[str, Any], keyword: str | None = None,
            serp: dict[str, Any] | None = None,
            render_engine: str = "file") -> dict[str, Any]:
    target = classify_page(page)
    consensus = serp_consensus(serp) if serp else None
    fit = alignment(target, consensus)
    return {
        "url": page.get("url", ""),
        "keyword": keyword,
        "keyword_candidate": keyword_candidate(page) if not keyword else None,
        "keyword_confirmation_required": bool(not keyword),
        "render_engine": render_engine,
        "page_type": target,
        "serp_consensus": consensus,
        "serp_fit": fit,
        "experience_baseline": experience_baseline(page),
        "evidence_coverage": {
            "page_rendered": render_engine not in ("raw", "file"),
            "serp_available": serp is not None,
            "first_party_outcomes": False,
            "note": ("First-party conversion/funnel evidence is unavailable "
                     "unless GA4 events or research are supplied."),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sxo_analyser",
        description="Deterministic SXO page-type and SERP-fit baseline")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--url", help="live page to analyse")
    source.add_argument("--file", help="local HTML file to analyse")
    serp_source = parser.add_mutually_exclusive_group()
    serp_source.add_argument("--keyword", help="confirmed keyword; performs one SERP pull")
    serp_source.add_argument("--serp-file", help="saved dfs_client.py serp JSON")
    parser.add_argument("--domain", help="domain for --save (default: URL host)")
    parser.add_argument("--save", action="store_true",
                        help="persist a high-confidence page-type mismatch")
    parser.add_argument("--render", choices=["auto", "always", "never"],
                        default="auto")
    parser.add_argument("--location", default="United States")
    parser.add_argument("--language", default="English")
    parser.add_argument("--sandbox", action="store_true")
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args(argv)

    try:
        if args.url:
            page, engine = _fetch_page(args.url, args.render, args.timeout)
        else:
            path = Path(args.file)
            if not path.is_file():
                raise SxoError(f"File not found: {path}")
            page, engine = seo_lint.parse_html(
                path.read_text(encoding="utf-8", errors="replace"), str(path)), "file"

        serp = (json.loads(Path(args.serp_file).read_text(encoding="utf-8"))
                if args.serp_file else
                _fetch_serp(args.keyword, args.location, args.language, args.sandbox)
                if args.keyword else None)
        output = analyse(page, args.keyword, serp, engine)

        if args.save:
            domain = args.domain or urllib.parse.urlparse(page.get("url", "")).netloc
            domain = domain.lower().removeprefix("www.") or "local"
            rec = recommendation(domain, args.keyword, output["page_type"],
                                 output["serp_consensus"], output["serp_fit"])
            if rec:
                rec["url"] = page.get("url", "")
                saved = recommend_store.raise_rec(domain, rec)
                output["recommendation_saved"] = {"id": saved["id"],
                                                   "status": saved["status"]}
            else:
                output["recommendation_saved"] = None
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return 0
    except (SxoError, json.JSONDecodeError, OSError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
