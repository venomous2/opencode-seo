# White-label HTML Reports

Any suite markdown report (audit, brief, roadmap, quarterly review) can be
rendered into a branded, standalone HTML file — one file, no JavaScript, no
dependencies, ready to email or print to PDF from the browser.

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
| `--footer` | `Report built by Lee Beirne - https://leebeirne.com` | Footer line (URLs auto-link) |

## What you get

- **Brand palette** — teal `#00E0BA`, purple `#91008D`, pink `#FF3483`,
  yellow `#FFCF00`, with the four-colour strip at the top
- **Table of contents** — auto-generated from H2/H3 headings (3+ sections)
- **Severity badges** — Critical / High / Medium / Low cells in tables
  render as coloured pills (pink / purple / amber / teal)
- **Charts** — see below
- **Print CSS** — page-break control for clean PDF export

## Charts

Skills embed fenced ```` ```chart ```` blocks with one JSON object; the
builder renders them as inline SVG/CSS graphs. Never chart numbers you
don't have data for.

**Donut** (scores / gauges — colour follows the score: ≥70 teal, ≥40 amber, below pink):

    ```chart
    {"type": "donut", "title": "Overall SEO Health", "value": 64, "max": 100}
    ```

**Bar** (comparisons — pillar scores, keyword movers):

    ```chart
    {"type": "bar", "title": "Pillar scores",
     "data": [["Technical", 74], ["Content", 81], ["Authority", 42]], "max": 100}
    ```

**Line** (trends — clicks, rankings over time):

    ```chart
    {"type": "line", "title": "Organic clicks / month",
     "data": [["Mar", 120], ["Apr", 180], ["May", 260]]}
    ```

**Stats** (headline KPI cards, right after the executive summary):

    ```chart
    {"type": "stats", "data": [["Referring domains", "312", "+18"],
     ["Top-10 keywords", "24", "-2"], ["Indexed pages", "186", "+12"]]}
    ```

Deltas starting with `+`/`↑` render teal, others pink.

## Print to PDF

Open the HTML in any browser → Print → "Save as PDF". The print stylesheet
hides the TOC and controls page breaks, so the PDF comes out clean.

## Notes

- The converter covers the markdown the suite emits: headings, tables,
  bold/italic, code, lists, blockquotes, rules, links, and `chart` blocks.
- HTML reports are client-facing: check them before sending.
- `seo-report-writer` and `workflow-quarterly-review` call this
  automatically; you can also run it on any markdown file by hand.
