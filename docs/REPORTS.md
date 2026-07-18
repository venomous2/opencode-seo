# White-label HTML Reports

Any suite markdown report (audit, brief, roadmap, quarterly review) can be
rendered into a branded, standalone HTML file — one file, no dependencies,
ready to email or print to PDF from the browser.

## Usage

```bash
python scripts/report_build.py SEO-AUDIT-example.com-2026-07-18.md
# -> SEO-AUDIT-example.com-2026-07-18.html
```

Options:

| Flag | Default | Purpose |
|---|---|---|
| `-o`, `--output` | `<input>.html` | Output path |
| `--brand` | `Lee Beirne` | Name in the header |
| `--title` | first H1 of the doc | Report title |
| `--accent` | `#1e3a5f` | Brand colour (hex) — headings, table headers, rules |
| `--footer` | suite attribution line | Footer text |

Example with full branding:

```bash
python scripts/report_build.py REPORT-acme-q3.md \
    --brand "Lee Beirne · AI SEO Consulting" \
    --title "Acme Ltd — Q3 SEO Review" \
    --accent "#0e7490"
```

## Print to PDF

Open the HTML in any browser → Print → "Save as PDF". The stylesheet
includes print rules (page-break control, no orphan headings), so the PDF
comes out clean without extra tools.

## Notes

- The converter covers the markdown the suite emits: headings, tables,
  bold/italic, code, lists, blockquotes, rules, links. It is intentionally
  small — no third-party packages.
- HTML reports are client-facing: check them before sending.
- `seo-report-writer` and `workflow-quarterly-review` call this
  automatically; you can also run it on any markdown file by hand.
