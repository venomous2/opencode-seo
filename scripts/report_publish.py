"""One-command client deliverables for the OpenCode SEO Suite.

Turns a suite markdown report into the full client-facing set:

    REPORT.md
    ├── REPORT.html            (branded, charts, TOC)
    ├── REPORT.pdf             (print-ready)
    ├── REPORT-onepager.html   (executive summary version)
    └── REPORT-onepager.pdf

Usage:
    python scripts/report_publish.py REPORT.md
    python scripts/report_publish.py REPORT.md --no-onepager
    python scripts/report_publish.py REPORT.md --html-only
    python scripts/report_publish.py REPORT.md --brand "Lee Beirne" --title "Q3 Review"

Every skill that writes a client report should finish with this command so
deliverables are always client-ready without extra steps.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import report_build  # noqa: E402
import report_pdf  # noqa: E402


def publish(md_path: Path, brand: str, title: str | None, footer: str,
            onepager: bool, html_only: bool) -> dict[str, object]:
    outputs: dict[str, object] = {"markdown": str(md_path.resolve())}
    if not md_path.is_file():
        return {"error": f"File not found: {md_path}"}

    html_path = report_build.build(md_path, md_path.with_suffix(".html"),
                                   brand=brand, title=title, footer=footer)
    outputs["html"] = str(html_path.resolve())

    if onepager:
        one_html = report_build.build(
            md_path,
            md_path.with_name(md_path.stem + "-onepager.html"),
            brand=brand, title=title, footer=footer, onepager=True)
        outputs["onepager_html"] = str(one_html.resolve())

    if html_only:
        outputs["pdf"] = "skipped (--html-only)"
        return outputs

    browser = report_pdf.find_browser()
    if not browser:
        outputs["pdf"] = ("skipped (no headless browser found — install Edge "
                          "or Chrome, or run scripts/report_pdf.py later)")
        return outputs

    try:
        pdf_path = report_pdf.html_to_pdf(html_path,
                                          html_path.with_suffix(".pdf"),
                                          browser)
        outputs["pdf"] = str(pdf_path.resolve())
        if onepager:
            one_html = Path(outputs["onepager_html"])
            one_pdf = report_pdf.html_to_pdf(
                one_html, one_html.with_suffix(".pdf"), browser)
            outputs["onepager_pdf"] = str(one_pdf.resolve())
    except (report_pdf.PdfError, OSError) as exc:
        outputs["pdf"] = f"failed ({exc})"
    return outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="report_publish",
        description="Markdown report -> branded HTML + PDF (+ one-pager)")
    parser.add_argument("input", help="markdown report file")
    parser.add_argument("--brand", default="Lee Beirne")
    parser.add_argument("--title", help="report title (default: first H1)")
    parser.add_argument("--footer", default=report_build.DEFAULT_FOOTER)
    parser.add_argument("--no-onepager", dest="onepager",
                        action="store_false",
                        help="skip the executive one-pager")
    parser.add_argument("--html-only", action="store_true",
                        help="skip PDF export")
    args = parser.parse_args(argv)

    outputs = publish(Path(args.input), args.brand, args.title, args.footer,
                      onepager=args.onepager, html_only=args.html_only)
    print(json.dumps(outputs, indent=2))
    return 1 if "error" in outputs else 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    sys.exit(main())
