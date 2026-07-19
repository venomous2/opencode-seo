"""PDF export for the OpenCode SEO Suite.

Renders an HTML report to PDF using the headless browser already on the
machine (Microsoft Edge on Windows, Chrome/Chromium elsewhere) — no
third-party packages, no wkhtmltopdf, no WeasyPrint.

Usage:
    python scripts/report_pdf.py report.html [-o report.pdf]
    python scripts/report_pdf.py report.md   # builds HTML first, then PDF
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

CANDIDATES = [
    # Windows — Edge ships with the OS
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    # macOS
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    # Linux
    "/usr/bin/microsoft-edge",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
]


class PdfError(RuntimeError):
    pass


def find_browser() -> str | None:
    for candidate in CANDIDATES:
        if Path(candidate).is_file():
            return candidate
    for name in ("msedge", "microsoft-edge", "google-chrome", "chromium",
                 "chromium-browser"):
        found = shutil.which(name)
        if found:
            return found
    return None


def html_to_pdf(html_path: Path, pdf_path: Path, browser: str) -> Path:
    url = "file:///" + str(html_path.resolve()).replace("\\", "/")
    command = [
        browser, "--headless", "--disable-gpu", "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path.resolve()}", url,
    ]
    result = subprocess.run(command, capture_output=True, text=True,
                            timeout=120)
    if result.returncode != 0 or not pdf_path.is_file():
        raise PdfError(f"Browser PDF export failed: "
                       f"{result.stderr.strip()[:300] or 'unknown error'}")
    return pdf_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="report_pdf",
                                     description="HTML report -> PDF via headless browser")
    parser.add_argument("input", help=".html report (or .md to build HTML first)")
    parser.add_argument("-o", "--output", help="output .pdf path")
    parser.add_argument("--browser", help="explicit browser executable path")
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    if not input_path.is_file():
        print(json.dumps({"error": f"File not found: {input_path}"}))
        return 1

    if input_path.suffix.lower() == ".md":
        try:
            import report_build
        except ImportError:
            sys.path.insert(0, str(Path(__file__).parent))
            import report_build
        html_path = report_build.build(
            input_path, input_path.with_suffix(".html"),
            brand="Lee Beirne", title=None,
            footer=report_build.DEFAULT_FOOTER)
    else:
        html_path = input_path

    browser = args.browser or find_browser()
    if not browser:
        print(json.dumps({
            "error": "No headless browser found. Install Microsoft Edge or "
                     "Chrome, or pass --browser <path-to-exe>."}))
        return 1

    pdf_path = Path(args.output) if args.output \
        else html_path.with_suffix(".pdf")
    try:
        result = html_to_pdf(html_path, pdf_path, browser)
    except (PdfError, subprocess.TimeoutExpired, OSError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1
    print(json.dumps({"written": str(result.resolve()),
                      "browser": browser,
                      "size_kb": result.stat().st_size // 1024}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
