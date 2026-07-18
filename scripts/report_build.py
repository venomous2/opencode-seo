"""White-label HTML report builder for the OpenCode SEO Suite.

Renders a suite markdown report (audit, brief, roadmap...) into a styled,
standalone HTML file with your branding — ready to send to a client or
print to PDF from the browser.

Usage:
    python scripts/report_build.py REPORT.md [-o report.html]
        [--brand "Lee Beirne"] [--title "SEO Audit — example.com"]
        [--accent "#1e3a5f"] [--footer "Custom footer line"]

The converter supports the markdown the suite actually emits: headings,
tables, bold/italic, inline code, fenced code blocks, lists, rules, links,
and blockquotes. No third-party dependencies.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

DEFAULT_FOOTER = ("Built by Lee Beirne · OpenCode SEO Suite — "
                  "inspired by AgriciDaniel/claude-seo")


# ---------------------------------------------------------------------------
# Minimal markdown -> HTML converter (suite-flavoured subset)
# ---------------------------------------------------------------------------

def _inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\w)\*([^*\n]+)\*(?!\w)", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def md_to_html(md: str) -> str:
    lines = md.splitlines()
    out: list[str] = []
    i = 0
    in_code = False
    code_lang = ""
    while i < len(lines):
        line = lines[i]

        # fenced code
        if line.strip().startswith("```"):
            if in_code:
                out.append("</code></pre>")
                in_code = False
            else:
                code_lang = line.strip()[3:]
                out.append(f'<pre class="code {html.escape(code_lang)}"><code>')
                in_code = True
            i += 1
            continue
        if in_code:
            out.append(html.escape(line) + "\n")
            i += 1
            continue

        stripped = line.strip()
        if not stripped:
            i += 1
            continue

        # table block
        if stripped.startswith("|") and i + 1 < len(lines) \
                and re.match(r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
            headers = [c.strip() for c in stripped.strip("|").split("|")]
            out.append("<table><thead><tr>"
                       + "".join(f"<th>{_inline(h)}</th>" for h in headers)
                       + "</tr></thead><tbody>")
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                out.append("<tr>" + "".join(f"<td>{_inline(c)}</td>"
                                            for c in cells) + "</tr>")
                i += 1
            out.append("</tbody></table>")
            continue

        # headings
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            level = len(m.group(1))
            out.append(f"<h{level}>{_inline(m.group(2))}</h{level}>")
            i += 1
            continue

        # horizontal rule
        if re.match(r"^(-{3,}|\*{3,})$", stripped):
            out.append("<hr>")
            i += 1
            continue

        # blockquote
        if stripped.startswith(">"):
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote_lines.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append("<blockquote>" + _inline(" ".join(quote_lines))
                       + "</blockquote>")
            continue

        # unordered list
        if re.match(r"^[-*]\s+", stripped):
            out.append("<ul>")
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i].strip()):
                item = re.sub(r"^[-*]\s+", "", lines[i].strip())
                out.append(f"<li>{_inline(item)}</li>")
                i += 1
            out.append("</ul>")
            continue

        # ordered list
        if re.match(r"^\d+[.)]\s+", stripped):
            out.append("<ol>")
            while i < len(lines) and re.match(r"^\d+[.)]\s+", lines[i].strip()):
                item = re.sub(r"^\d+[.)]\s+", "", lines[i].strip())
                out.append(f"<li>{_inline(item)}</li>")
                i += 1
            out.append("</ol>")
            continue

        # paragraph (merge following plain lines)
        para = [stripped]
        i += 1
        while i < len(lines) and lines[i].strip() \
                and not re.match(r"^(#{1,6}\s|[-*]\s|\d+[.)]\s|\||>|```|-{3,})",
                                 lines[i].strip()):
            para.append(lines[i].strip())
            i += 1
        out.append(f"<p>{_inline(' '.join(para))}</p>")

    return "\n".join(out)


# ---------------------------------------------------------------------------
# HTML shell
# ---------------------------------------------------------------------------

SHELL = """<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  :root {{ --accent: {accent}; --ink: #1e293b; --muted: #64748b; }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
         color: var(--ink); line-height: 1.6; max-width: 46rem;
         margin: 0 auto; padding: 2.5rem 1.5rem 4rem; }}
  .report-header {{ border-bottom: 4px solid var(--accent);
                   padding-bottom: 1rem; margin-bottom: 2rem; }}
  .report-header .brand {{ color: var(--accent); font-weight: 700;
                   letter-spacing: .12em; text-transform: uppercase;
                   font-size: .8rem; }}
  .report-header h1 {{ margin: .35rem 0 .2rem; font-size: 1.9rem;
                   line-height: 1.2; border: 0; }}
  .report-header .date {{ color: var(--muted); font-size: .85rem; }}
  h1, h2, h3, h4 {{ color: var(--accent); line-height: 1.3; }}
  h2 {{ border-bottom: 1px solid #e2e8f0; padding-bottom: .3rem;
       margin-top: 2.2rem; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1rem 0;
          font-size: .9rem; }}
  th, td {{ border: 1px solid #cbd5e1; padding: .45rem .6rem;
           text-align: left; vertical-align: top; }}
  th {{ background: var(--accent); color: #fff; }}
  tr:nth-child(even) td {{ background: #f1f5f9; }}
  code {{ background: #f1f5f9; padding: .1rem .3rem; border-radius: 4px;
         font-size: .85em; }}
  pre.code {{ background: #0f172a; color: #e2e8f0; padding: 1rem;
             border-radius: 8px; overflow-x: auto; font-size: .82rem; }}
  pre.code code {{ background: none; padding: 0; }}
  blockquote {{ border-left: 4px solid var(--accent); margin: 1rem 0;
               padding: .3rem 1rem; color: var(--muted);
               background: #f8fafc; }}
  hr {{ border: 0; border-top: 1px solid #e2e8f0; margin: 2rem 0; }}
  a {{ color: var(--accent); }}
  .report-footer {{ margin-top: 3rem; padding-top: 1rem;
                   border-top: 2px solid var(--accent);
                   color: var(--muted); font-size: .8rem; }}
  @media print {{
    body {{ max-width: none; padding: 0; }}
    h2 {{ page-break-after: avoid; }}
    table, pre {{ page-break-inside: avoid; }}
  }}
</style>
</head>
<body>
<header class="report-header">
  <div class="brand">{brand}</div>
  <h1>{title}</h1>
  <div class="date">{report_date}</div>
</header>
<main>
{body}
</main>
<footer class="report-footer">{footer}</footer>
</body>
</html>
"""


def build(md_path: Path, out_path: Path, brand: str, title: str | None,
          accent: str, footer: str) -> Path:
    markdown = md_path.read_text(encoding="utf-8")
    # use first H1 as title when --title is not given
    if not title:
        match = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
        title = match.group(1).strip() if match else md_path.stem
        # drop that H1 from the body to avoid duplication
        markdown = re.sub(r"^#\s+.+\n?", "", markdown, count=1)
    body = md_to_html(markdown)
    page = SHELL.format(
        title=html.escape(title), brand=html.escape(brand),
        report_date=date.today().strftime("%d %B %Y"),
        accent=accent, body=body, footer=html.escape(footer))
    out_path.write_text(page, encoding="utf-8")
    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="report_build",
                                     description="White-label HTML report builder")
    parser.add_argument("input", help="markdown report file")
    parser.add_argument("-o", "--output", help="output .html path")
    parser.add_argument("--brand", default="Lee Beirne")
    parser.add_argument("--title", help="report title (default: first H1)")
    parser.add_argument("--accent", default="#1e3a5f", help="brand colour, hex")
    parser.add_argument("--footer", default=DEFAULT_FOOTER)
    args = parser.parse_args(argv)

    md_path = Path(args.input)
    if not md_path.is_file():
        print(json.dumps({"error": f"File not found: {md_path}"}))
        return 1
    out_path = Path(args.output) if args.output \
        else md_path.with_suffix(".html")
    result = build(md_path, out_path, args.brand, args.title,
                   args.accent, args.footer)
    print(json.dumps({"written": str(result.resolve())}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
