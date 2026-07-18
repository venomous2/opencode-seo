"""Citation readiness scorer for the OpenCode SEO Suite.

Deterministic, model-agnostic scoring of how ready a page is to be cited by
LLM-based search (Google AI Overviews/AI Mode, ChatGPT search, Perplexity,
Gemini). Zero model calls: every criterion is computed from page data
extracted by the suite's parser. Identical results under any LLM.

Honest framing: this scores the controllable inputs (structure, sourcing,
citability). It cannot and does not guarantee citation.

Usage:
    python scripts/citation_score.py --url https://example.com/guide
    python scripts/citation_score.py --file page.html --format text

Scoring: weighted criteria summing to 100, with hard gates (noindex or
non-200 page => capped score). Each criterion reports pass/partial/fail
plus a concrete recommendation when not fully met.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

import seo_lint  # noqa: E402
from site_crawler import fetch  # noqa: E402

QUESTION_STARTERS = ("how", "what", "why", "when", "which", "who", "where",
                     "can", "does", "do", "is", "are", "should")

GRADE_BANDS = [
    (80, "Strong citation candidate"),
    (60, "Citation-ready with gaps"),
    (40, "Weak — significant work needed"),
    (0, "Not ready"),
]


def grade(score: int) -> str:
    for floor, label in GRADE_BANDS:
        if score >= floor:
            return label
    return GRADE_BANDS[-1][1]


def _criterion(name: str, points: float, max_points: float,
               reason: str, recommendation: str = "") -> dict[str, Any]:
    status = "pass" if points >= max_points else ("partial" if points > 0 else "fail")
    return {
        "criterion": name,
        "status": status,
        "points": round(points, 1),
        "max_points": max_points,
        "reason": reason,
        **({"recommendation": recommendation} if status != "pass" and recommendation else {}),
    }


def score_page(page: dict[str, Any]) -> dict[str, Any]:
    criteria: list[dict[str, Any]] = []

    # --- hard gates ---------------------------------------------------------
    if page.get("status") and page["status"] != 200:
        return {"score": 0, "grade": grade(0), "gate": f"HTTP {page['status']}",
                "criteria": [], "url": page.get("url", "")}
    if page.get("noindex"):
        return {"score": 0, "grade": grade(0),
                "gate": "noindex — AI features grounded in search cannot cite "
                        "pages that are excluded from the index",
                "criteria": [], "url": page.get("url", "")}

    # --- 1. answer block (20) ----------------------------------------------
    words = page.get("first_h2_para_words") or 0
    if 40 <= words <= 170:
        pts, reason, rec = 20, f"Self-contained answer block after the first H2 ({words} words).", ""
    elif words > 170:
        pts, reason, rec = 12, f"Answer block present but long ({words} words; 40-170 is the quotable range).", \
            "Tighten the paragraph after the first H2 to a self-contained 40-170 words."
    elif words > 0:
        pts, reason, rec = 8, f"Answer block is thin ({words} words).", \
            "Expand the first-H2 paragraph to a complete 40-170 word answer that stands alone."
    else:
        pts, reason, rec = 0, "No paragraph after the first H2 to quote.", \
            "Write a 40-170 word self-contained answer directly under the first H2."
    criteria.append(_criterion("Answer block", pts, 20, reason, rec))

    # --- 2. question-form headings (10) -------------------------------------
    h2s = [h for h in (page.get("h2") or []) if h.strip()]
    question_h2 = [
        h for h in h2s
        if h.rstrip().endswith("?")
        or (h.split() and h.split()[0].lower() in QUESTION_STARTERS)
    ]
    if question_h2:
        pts, reason, rec = 10, f"{len(question_h2)} question-form H2(s), e.g. \"{question_h2[0]}\".", ""
    else:
        pts, reason, rec = 0, "No question-form H2 headings.", \
            "Rewrite at least one H2 as the literal question the page answers (searchers and AI both match on questions)."
    criteria.append(_criterion("Question-form headings", pts, 10, reason, rec))

    # --- 3. author signal (10) ----------------------------------------------
    has_author = bool(page.get("meta_author") or page.get("has_rel_author")
                      or "Person" in (page.get("schema_types") or []))
    if has_author:
        pts, reason, rec = 10, "Named author detectable (meta, rel=author, or Person schema).", ""
    else:
        pts, reason, rec = 0, "No author signal found.", \
            "Add a named author with a byline and Person schema (or author property on Article) — unattributed content is harder to trust and cite."
    criteria.append(_criterion("Author signal", pts, 10, reason, rec))

    # --- 4. date signal (10) -------------------------------------------------
    if page.get("jsonld_has_dates") or page.get("time_elements"):
        pts, reason, rec = 10, "Publication/modified dates present.", ""
    else:
        pts, reason, rec = 0, "No date signals (no datePublished/dateModified, no <time>).", \
            "Add datePublished and dateModified to the page's JSON-LD (and display a date). Freshness matters for citation."
    criteria.append(_criterion("Date signals", pts, 10, reason, rec))

    # --- 5. outbound sourcing (10) -------------------------------------------
    ext = page.get("external_link_count") or 0
    if ext >= 2:
        pts, reason, rec = 10, f"{ext} outbound citation links.", ""
    elif ext == 1:
        pts, reason, rec = 6, "One outbound citation.", \
            "Cite at least one more authoritative primary source where claims need support."
    else:
        pts, reason, rec = 0, "No outbound links — every claim stands on your word alone.", \
            "Link statistics and named claims to their primary sources (studies, official docs, data)."
    criteria.append(_criterion("Outbound sourcing", pts, 10, reason, rec))

    # --- 6. editorial schema (10) --------------------------------------------
    types = page.get("schema_types") or []
    if any(t in ("Article", "BlogPosting", "NewsArticle") for t in types):
        pts, reason, rec = 10, f"Editorial schema present ({', '.join(t for t in types if t in ('Article','BlogPosting','NewsArticle'))}).", ""
    elif types:
        pts, reason, rec = 4, f"Schema present but not editorial ({', '.join(types[:4])}).", \
            "Add Article (or BlogPosting) JSON-LD with headline, author, datePublished, dateModified."
    else:
        pts, reason, rec = 0, "No structured data at all.", \
            "Add Article JSON-LD via python scripts/schema_gen.py article --field ..."
    criteria.append(_criterion("Editorial schema", pts, 10, reason, rec))

    # --- 7. structure & scannability (10) ------------------------------------
    h2_count = page.get("h2_count") or 0
    lists = page.get("list_count") or 0
    pts = (6 if h2_count >= 3 else 3 if h2_count >= 1 else 0) + (4 if lists >= 1 else 0)
    reason = f"{h2_count} H2 sections, {lists} list(s)."
    rec = ""
    if h2_count < 3:
        rec += "Break the content into more descriptive H2 sections. "
    if lists < 1:
        rec += "Use at least one bulleted or numbered list where the content suits it (steps, options, criteria)."
    criteria.append(_criterion("Structure & scannability", pts, 10, reason, rec.strip()))

    # --- 8. content depth (10) -----------------------------------------------
    wc = page.get("word_count") or 0
    if wc >= 1500:
        pts, reason, rec = 10, f"{wc} words — comprehensive.", ""
    elif wc >= 800:
        pts, reason, rec = 7, f"{wc} words — reasonable depth.", \
            "Cover the missing subtopics competitors include; 1500+ words for competitive informational queries."
    elif wc >= 400:
        pts, reason, rec = 4, f"{wc} words — light coverage.", \
            "Expand towards comprehensive coverage of the question space (800-1500+ words where the SERP rewards it)."
    else:
        pts, reason, rec = 0, f"Only {wc} words.", \
            "Too little content to be a citation source; build the page out properly."
    criteria.append(_criterion("Content depth", pts, 10, reason, rec))

    # --- 9. factual density (5, low-confidence heuristic) --------------------
    density = page.get("number_density") or 0
    if density >= 8:
        pts, reason, rec = 5, f"~{density} numeric/statistical tokens per 1k words.", ""
    elif density >= 3:
        pts, reason, rec = 2.5, f"~{density} numeric tokens per 1k words.", \
            "Add concrete, sourced numbers (statistics, dates, quantities) — quotable facts get cited."
    else:
        pts, reason, rec = 0, f"~{density} numeric tokens per 1k words.", \
            "Add concrete, sourced numbers (statistics, dates, quantities) — quotable facts get cited."
    criteria.append(_criterion("Factual density (heuristic)", pts, 5, reason, rec))

    # --- 10. image accessibility (5) ------------------------------------------
    total = page.get("images_total") or 0
    missing = page.get("images_missing_alt") or 0
    if total == 0:
        pts, reason, rec = 5, "No images (nothing inaccessible).", ""
    elif missing == 0:
        pts, reason, rec = 5, f"All {total} images have alt text.", ""
    elif missing < total:
        pts, reason, rec = 2, f"{missing} of {total} images missing alt text.", \
            "Add descriptive alt text to the remaining images."
    else:
        pts, reason, rec = 0, f"None of {total} images have alt text.", \
            "Add descriptive alt text to every content image."
    criteria.append(_criterion("Image accessibility", pts, 5, reason, rec))

    # --- 11. indexation basics (5) --------------------------------------------
    pts = (2.5 if page.get("canonical") else 0) + (2.5 if not page.get("noindex") else 0)
    reason = ("Canonical present. " if page.get("canonical") else "No canonical. ") + "Indexable."
    rec = "" if pts == 5 else "Add a self-referencing canonical tag."
    criteria.append(_criterion("Indexation basics", pts, 5, reason, rec))

    total = round(sum(c["points"] for c in criteria))
    return {
        "score": total,
        "grade": grade(total),
        "gate": None,
        "criteria": criteria,
        "url": page.get("url", ""),
        "disclaimer": "Readiness scores the controllable inputs; it cannot guarantee citation.",
    }


def render_text(result: dict[str, Any]) -> str:
    lines = [f"\nCitation readiness: {result['url'] or '(inline page)'}",
             f"Score: {result['score']}/100 — {result['grade']}"]
    if result.get("gate"):
        lines.append(f"GATE: {result['gate']}")
        return "\n".join(lines)
    icon = {"pass": "[ok]", "partial": "[~~]", "fail": "[  ]"}
    for c in result["criteria"]:
        lines.append(f"  {icon[c['status']]} {c['criterion']} "
                     f"({c['points']:g}/{c['max_points']:g}) — {c['reason']}")
        if c.get("recommendation"):
            lines.append(f"       -> {c['recommendation']}")
    lines.append(result["disclaimer"])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="citation_score",
                                     description="Citation readiness scorer")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--url")
    source.add_argument("--file")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args(argv)

    if args.url:
        status, content_type, html_text = fetch(args.url, args.timeout)
        if status != 200 or "html" not in content_type.lower():
            print(json.dumps({"error": f"Fetch failed: HTTP {status}"}))
            return 1
        page = seo_lint.parse_html(html_text, args.url)
        page["status"] = status
    else:
        path = Path(args.file)
        if not path.is_file():
            print(json.dumps({"error": f"File not found: {path}"}))
            return 1
        page = seo_lint.parse_html(path.read_text(encoding="utf-8",
                                                  errors="replace"), str(path))

    result = score_page(page)
    if args.format == "text":
        print(render_text(result))
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
