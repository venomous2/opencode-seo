"""JSON-LD structured data generator CLI for the OpenCode SEO Suite.

Generates valid Schema.org JSON-LD blocks ready to paste into a page.
Pass fields as --field key=value pairs; nested keys use dot notation
(address.city=Springfield, geo.lat=40.7). Repeatable properties accept
comma-separated values (sameAs=https://a,https://b).

Usage:
    python scripts/schema_gen.py article --field headline="My Post" \
        --field author.name="Jane Doe" --field datePublished=2026-07-17

Types:
    organization website webpage article blogposting newsarticle
    product offer review aggregaterating breadcrumblist
    localbusiness person event jobposting course faqpage video
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

TYPE_MAP = {
    "organization": "Organization",
    "website": "WebSite",
    "webpage": "WebPage",
    "article": "Article",
    "blogposting": "BlogPosting",
    "newsarticle": "NewsArticle",
    "product": "Product",
    "offer": "Offer",
    "review": "Review",
    "aggregaterating": "AggregateRating",
    "breadcrumblist": "BreadcrumbList",
    "localbusiness": "LocalBusiness",
    "person": "Person",
    "event": "Event",
    "jobposting": "JobPosting",
    "course": "Course",
    "faqpage": "FAQPage",
    "video": "VideoObject",
}

# Minimal recommended properties per type (advisory warnings, not hard rules).
RECOMMENDED = {
    "Organization": ["name", "url", "logo"],
    "WebSite": ["name", "url"],
    "WebPage": ["name", "url"],
    "Article": ["headline", "author", "datePublished", "image"],
    "BlogPosting": ["headline", "author", "datePublished", "image"],
    "NewsArticle": ["headline", "author", "datePublished", "image"],
    "Product": ["name", "image", "description", "offers"],
    "Offer": ["price", "priceCurrency", "availability"],
    "Review": ["reviewRating", "author", "itemReviewed"],
    "AggregateRating": ["ratingValue", "reviewCount"],
    "BreadcrumbList": ["itemListElement"],
    "LocalBusiness": ["name", "address", "telephone", "openingHours"],
    "Person": ["name"],
    "Event": ["name", "startDate", "location"],
    "JobPosting": ["title", "description", "hiringOrganization", "jobLocation"],
    "Course": ["name", "description", "provider"],
    "FAQPage": ["mainEntity"],
    "VideoObject": ["name", "description", "thumbnailUrl", "uploadDate"],
}


def _coerce(value: str) -> Any:
    """Best-effort coercion of CLI strings to JSON-native scalars."""
    if "," in value:
        return [_coerce(part) for part in value.split(",")]
    lowered = value.lower()
    if lowered in ("true", "false"):
        return lowered == "true"
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def _assign(target: dict[str, Any], dotted_key: str, value: Any) -> None:
    parts = dotted_key.split(".")
    node = target
    for part in parts[:-1]:
        node = node.setdefault(part, {})
        if not isinstance(node, dict):
            raise ValueError(f"Cannot nest under scalar property '{part}'")
    node[parts[-1]] = value


def build(schema_type: str, fields: list[str]) -> dict[str, Any]:
    type_name = TYPE_MAP[schema_type]
    node: dict[str, Any] = {"@context": "https://schema.org", "@type": type_name}
    for pair in fields:
        if "=" not in pair:
            raise ValueError(f"--field must be key=value, got: {pair}")
        key, _, value = pair.partition("=")
        _assign(node, key.strip(), _coerce(value.strip()))
    return node


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="schema_gen",
                                     description="JSON-LD schema generator")
    parser.add_argument("type", choices=sorted(TYPE_MAP))
    parser.add_argument("--field", action="append", default=[],
                        help="key=value; dot notation nests, commas make arrays")
    parser.add_argument("--script-tag", action="store_true",
                        help="wrap output in a <script type=application/ld+json> tag")
    args = parser.parse_args(argv)

    try:
        node = build(args.type, args.field)
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}))
        return 1

    type_name = node["@type"]
    missing = [p for p in RECOMMENDED.get(type_name, []) if p not in node]
    payload = json.dumps(node, indent=2, ensure_ascii=False)
    if args.script_tag:
        payload = ('<script type="application/ld+json">\n' + payload + "\n</script>")
    print(payload)
    if missing:
        print("\n<!-- Advisory: recommended properties not set: "
              + ", ".join(missing) + " -->", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
