"""White-label HTML report builder for the OpenCode SEO Suite.

Renders a suite markdown report into a styled, standalone HTML file with
Lee Beirne's branding — charts, table of contents, severity badges, and a
print-to-PDF-friendly layout.

Usage:
    python scripts/report_build.py REPORT.md [-o report.html]
        [--brand "Lee Beirne"] [--title "SEO Audit — example.com"]
        [--footer "Custom footer line"]

Charts
------
Skills can embed fenced ```chart blocks containing one JSON spec per block:

    ```chart
    {"type": "donut", "title": "Overall SEO Health", "value": 64, "max": 100}

    {"type": "bar", "title": "Pillar scores",
     "data": [["Technical", 74], ["Content", 81]], "max": 100}

    {"type": "line", "title": "Organic clicks / month",
     "data": [["Mar", 120], ["Apr", 180], ["May", 260]]}

    {"type": "stats",
     "data": [["Referring domains", "312", "+18"], ["Top-10 keywords", "24", "-2"]]}
    ```

Everything renders as inline SVG/CSS — no JavaScript, no dependencies.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

DEFAULT_FOOTER = "Report built by Lee Beirne - https://leebeirne.com"

# Brand palette — Lee Beirne
NAVY = "#1E3A8A"
EMERALD = "#10B981"
ORANGE = "#C2410C"
DARK = "#0F172A"

# Keep legacy names for chart colours
CHART_COLOURS = [EMERALD, NAVY, ORANGE, "#F59E0B"]
SEVERITY_COLOURS = {
    "critical": ORANGE,
    "high": NAVY,
    "medium": "#F59E0B",
    "low": EMERALD,
}


def score_colour(value: float, max_value: float = 100) -> str:
    pct = 100 * value / max_value if max_value else 0
    if pct >= 70:
        return EMERALD
    if pct >= 40:
        return "#F59E0B"
    return ORANGE


# ---------------------------------------------------------------------------
# SVG charts
# ---------------------------------------------------------------------------

def svg_donut(spec: dict) -> str:
    title = html.escape(str(spec.get("title", "")))
    data = spec.get("data")
    if data:  # multi-segment donut with legend
        values = [float(v) for _, v in data] or [1]
        total = sum(values) or 1
        r, cx, cy = 54, 70, 70
        circ = 2 * 3.14159265 * r
        offset = 0.0
        segments = []
        legend = []
        for i, (label, value) in enumerate(data):
            value_f = float(value)
            length = circ * value_f / total
            colour = CHART_COLOURS[i % len(CHART_COLOURS)]
            segments.append(
                f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" '
                f'stroke="{colour}" stroke-width="16" '
                f'stroke-dasharray="{length:.1f} {circ - length:.1f}" '
                f'stroke-dashoffset="{-offset:.1f}" '
                f'transform="rotate(-90 {cx} {cy})"/>')
            legend.append(
                f'<span class="legend-item"><span class="sw" '
                f'style="background:{colour}"></span>{html.escape(str(label))} '
                f'({value_f:g})</span>')
            offset += length
        return f'''<figure class="chart donut">
<svg viewBox="0 0 140 140" width="150" height="150" role="img" aria-label="{title}">
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#e2e8f0" stroke-width="16"/>
  {''.join(segments)}
</svg>
<figcaption>{title}</figcaption>
<div class="legend">{''.join(legend)}</div>
</figure>'''

    value = float(spec.get("value", 0))
    max_value = float(spec.get("max", 100)) or 100
    pct = max(0.0, min(1.0, value / max_value))
    colour = score_colour(value, max_value)
    r, cx, cy = 54, 70, 70
    circ = 2 * 3.14159265 * r
    filled = circ * pct
    return f'''<figure class="chart donut">
<svg viewBox="0 0 140 140" width="150" height="150" role="img"
     aria-label="{title}: {value:g} out of {max_value:g}">
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#e2e8f0" stroke-width="14"/>
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{colour}" stroke-width="14"
          stroke-linecap="round" stroke-dasharray="{filled:.1f} {circ - filled:.1f}"
          transform="rotate(-90 {cx} {cy})"/>
  <text x="{cx}" y="{cy - 2}" text-anchor="middle" font-size="26"
        font-weight="700" fill="#111827">{value:g}</text>
  <text x="{cx}" y="{cy + 18}" text-anchor="middle" font-size="11"
        fill="#6b7280">/ {max_value:g}</text>
</svg>
<figcaption>{title}</figcaption>
</figure>'''


def svg_bar(spec: dict) -> str:
    data = spec.get("data") or []
    title = html.escape(str(spec.get("title", "")))
    unit = html.escape(str(spec.get("unit", "")))
    values = [float(v) for _, v in data] or [1]
    max_value = float(spec.get("max") or max(values)) or 1
    rows = []
    for i, (label, value) in enumerate(data):
        value_f = float(value)
        width = max(1.5, 100 * value_f / max_value)
        colour = (score_colour(value_f, max_value) if spec.get("max")
                  else CHART_COLOURS[i % len(CHART_COLOURS)])
        rows.append(f'''<div class="bar-row">
  <span class="bar-label">{html.escape(str(label))}</span>
  <span class="bar-track"><span class="bar-fill" style="width:{width:.1f}%;background:{colour}"></span></span>
  <span class="bar-value">{value_f:g}{unit}</span>
</div>''')
    return (f'<figure class="chart"><figcaption>{title}</figcaption>'
            + "".join(rows) + "</figure>")


def svg_compare(spec: dict) -> str:
    """Before/after grouped bars: data rows are [label, previous, current]."""
    data = spec.get("data") or []
    title = html.escape(str(spec.get("title", "")))
    flat = [float(v) for row in data for v in row[1:3]] or [1]
    max_value = float(spec.get("max") or max(flat)) or 1
    rows = []
    for i, entry in enumerate(data):
        label = html.escape(str(entry[0]))
        before, after = float(entry[1]), float(entry[2])
        delta = after - before
        before_w = max(1.5, 100 * before / max_value)
        after_w = max(1.5, 100 * after / max_value)
        after_colour = (score_colour(after, max_value) if spec.get("max")
                        else CHART_COLOURS[i % len(CHART_COLOURS)])
        delta_txt = f"+{delta:g}" if delta > 0 else f"{delta:g}"
        delta_colour = EMERALD if delta > 0 else (ORANGE if delta < 0 else "#6b7280")
        rows.append(f'''<div class="cmp-row">
  <span class="bar-label">{label}</span>
  <span class="cmp-track">
    <span class="cmp-before" style="width:{before_w:.1f}%"></span>
    <span class="cmp-after" style="width:{after_w:.1f}%;background:{after_colour}"></span>
  </span>
  <span class="bar-value">{before:g} → {after:g}</span>
  <span class="cmp-delta" style="color:{delta_colour}">{delta_txt}</span>
</div>''')
    legend = (f'<span class="cmp-legend">'
              f'<span class="sw" style="background:#94a3b8"></span>previous'
              f'<span class="sw" style="background:{EMERALD}"></span>current</span>')
    return (f'<figure class="chart"><figcaption>{title} {legend}</figcaption>'
            + "".join(rows) + "</figure>")


def svg_line(spec: dict) -> str:
    data = spec.get("data") or []
    title = html.escape(str(spec.get("title", "")))
    unit = html.escape(str(spec.get("unit", "")))
    if len(data) < 2:
        return ""
    values = [float(v) for _, v in data]
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1
    w, h, pad_x, pad_y = 640, 220, 40, 30
    step_x = (w - 2 * pad_x) / (len(data) - 1)

    def point(i: int, value: float) -> tuple[float, float]:
        x = pad_x + i * step_x
        y = h - pad_y - (h - 2 * pad_y) * (value - lo) / span
        return x, y

    points = [point(i, v) for i, v in enumerate(values)]
    polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    dots = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{EMERALD}" stroke="#fff" stroke-width="1.5"/>'
        for x, y in points)
    labels = "".join(
        f'<text x="{x:.1f}" y="{h - 8}" text-anchor="middle" font-size="10" fill="#6b7280">{html.escape(str(label))}</text>'
        for (label, _), (x, _) in zip(data, points))
    return f'''<figure class="chart line">
<figcaption>{title}</figcaption>
<svg viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="{title}">
  <line x1="{pad_x}" y1="{h - pad_y}" x2="{w - pad_x}" y2="{h - pad_y}" stroke="#cbd5e1"/>
  <text x="6" y="{pad_y + 4}" font-size="10" fill="#6b7280">{hi:g}{unit}</text>
  <text x="6" y="{h - pad_y}" font-size="10" fill="#6b7280">{lo:g}{unit}</text>
  <polyline points="{polyline}" fill="none" stroke="{EMERALD}" stroke-width="2.5"/>
  {dots}{labels}
</svg>
</figure>'''


def stat_cards(spec: dict) -> str:
    cards = []
    for entry in spec.get("data") or []:
        label, value = entry[0], entry[1]
        delta = str(entry[2]) if len(entry) > 2 else ""
        if delta:
            delta_colour = EMERALD if delta.startswith(("+", "↑")) else ORANGE
            delta_html = f'<span class="stat-delta" style="color:{delta_colour}">{html.escape(delta)}</span>'
        else:
            delta_html = ""
        cards.append(f'''<div class="stat-card">
  <div class="stat-label">{html.escape(str(label))}</div>
  <div class="stat-value">{html.escape(str(value))}</div>
  {delta_html}
</div>''')
    return '<div class="stat-strip">' + "".join(cards) + "</div>"


def normalise_spec(raw: str) -> dict | None:
    """Parse a chart block's spec, tolerating the shapes different models emit.

    Canonical form is JSON, but weaker models often write YAML or a bare
    list of label/value dicts — all are normalised to the same spec.
    """
    raw = raw.strip()
    # tolerate a bare chart-type word on the first line ("donut\n- label: ...")
    first_line, _, rest = raw.partition("\n")
    if first_line.strip() in ("donut", "bar", "line", "stats", "compare") and rest:
        raw = first_line.strip() + ":\n" + rest

    spec: Any = None
    try:
        spec = json.loads(raw)
    except json.JSONDecodeError:
        try:
            import yaml  # type: ignore
            spec = yaml.safe_load(raw)
        except Exception:  # noqa: BLE001 - any parse failure -> fallback
            return None
    if not isinstance(spec, (dict, list)):
        return None

    # unwrap {"donut": [...]} single-key form
    if isinstance(spec, dict) and "type" not in spec and len(spec) == 1:
        key, value = next(iter(spec.items()))
        if key in ("donut", "bar", "line", "stats", "compare"):
            spec = {"type": key, "data": value}
    if isinstance(spec, list):  # bare list of pairs/dicts -> bar chart
        spec = {"type": "bar", "data": spec}
    if "type" not in spec:
        return None

    # normalise data rows: {label/name, value/score} dicts -> [label, value]
    data = spec.get("data")
    if isinstance(data, list):
        pairs = []
        for item in data:
            if isinstance(item, dict):
                label = item.get("label", item.get("name", ""))
                value = item.get("value", item.get("score", 0))
                pairs.append([label, value])
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                pairs.append(list(item))
        if pairs:
            spec["data"] = pairs
    return spec


def render_chart(block: str) -> str:
    spec = normalise_spec(block)
    if not spec:
        return ('<div class="chart-unparsed"><strong>Chart data '
                '(unparsed)</strong><pre class="code"><code>'
                + html.escape(block) + "</code></pre></div>")
    chart_type = spec.get("type")
    if chart_type == "donut":
        return svg_donut(spec)
    if chart_type == "bar":
        return svg_bar(spec)
    if chart_type == "compare":
        return svg_compare(spec)
    if chart_type == "line":
        return svg_line(spec)
    if chart_type == "stats":
        return stat_cards(spec)
    return ('<div class="chart-unparsed"><strong>Chart data (unparsed)</strong>'
            f'<pre class="code"><code>{html.escape(block)}</code></pre></div>')


# ---------------------------------------------------------------------------
# Markdown -> HTML (suite-flavoured subset, now with charts + TOC + badges)
# ---------------------------------------------------------------------------

def _inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\w)\*([^*\n]+)\*(?!\w)", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _severity_badge(cell_html: str, raw: str) -> str:
    word = raw.strip().lower().rstrip(".")
    if word in SEVERITY_COLOURS:
        colour = SEVERITY_COLOURS[word]
        return (f'<span class="badge" style="background:{colour}">'
                f'{html.escape(raw.strip())}</span>')
    return cell_html


def md_to_html(md: str) -> tuple[str, list[tuple[int, str, str]]]:
    """Return (body_html, toc_entries[(level, slug, text)])."""
    lines = md.splitlines()
    out: list[str] = []
    toc: list[tuple[int, str, str]] = []
    i = 0
    in_code = False
    code_lang = ""
    code_lines: list[str] = []
    while i < len(lines):
        line = lines[i]

        # fenced code / chart blocks
        if line.strip().startswith("```"):
            if in_code:
                if code_lang == "chart":
                    out.append(render_chart("\n".join(code_lines).strip()))
                else:
                    out.append(f'<pre class="code {html.escape(code_lang)}"><code>'
                               + html.escape("\n".join(code_lines)) + "\n</code></pre>")
                in_code = False
                code_lines = []
            else:
                code_lang = line.strip()[3:].strip()
                in_code = True
            i += 1
            continue
        if in_code:
            code_lines.append(line)
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
                rendered = []
                for cell in cells:
                    cell_html = _inline(cell)
                    rendered.append(f"<td>{_severity_badge(cell_html, cell)}</td>")
                out.append("<tr>" + "".join(rendered) + "</tr>")
                i += 1
            out.append("</tbody></table>")
            continue

        # headings (collected for the TOC)
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            level = len(m.group(1))
            text = m.group(2)
            slug = _slug(text)
            if level in (2, 3):
                toc.append((level, slug, re.sub(r"[*`]", "", text)))
            out.append(f'<h{level} id="{slug}">{_inline(text)}</h{level}>')
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

    return "\n".join(out), toc


# ---------------------------------------------------------------------------
# HTML shell
# ---------------------------------------------------------------------------

SHELL = """<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.bunny.net">
<link href="https://fonts.bunny.net/css?family=inter:400,500,600,700,800|space-grotesk:400,500,600,700,800" rel="stylesheet">
<style>
  :root {{ --navy: {navy}; --emerald: {emerald}; --orange: {orange};
           --dark: {dark}; --ink: #111827; --muted: #6b7280;
           --gray-50: #f9fafb; --gray-100: #f3f4f6; --gray-200: #e5e7eb; }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
         color: var(--ink); line-height: 1.6; max-width: 48rem;
         margin: 0 auto; padding: 0 1.5rem 4rem; }}
  .palette-strip {{ height: 6px; margin: 0 -1.5rem 2rem;
    background: linear-gradient(90deg, var(--emerald) 0 33%, var(--navy) 33% 66%, var(--orange) 66% 100%); }}
  .report-header {{ border-bottom: 3px solid var(--navy);
                   padding-bottom: 1.2rem; margin-bottom: 1.5rem; }}
  .report-header .brand {{ color: var(--emerald); font-weight: 700;
                   letter-spacing: .14em; text-transform: uppercase;
                   font-size: .8rem; }}
  .report-header h1 {{ margin: .35rem 0 .2rem; font-size: 2rem;
                   line-height: 1.2; border: 0; color: var(--ink); }}
  .report-header .date {{ color: var(--muted); font-size: .85rem; }}
  nav.toc {{ background: var(--gray-50); border: 1px solid var(--gray-200);
            border-left: 4px solid var(--emerald); border-radius: 8px;
            padding: 1rem 1.4rem; margin: 0 0 2rem; font-size: .92rem; }}
  nav.toc strong {{ color: var(--navy); text-transform: uppercase;
                   font-size: .75rem; letter-spacing: .1em; }}
  nav.toc ul {{ margin: .5rem 0 0; padding-left: 1.2rem; }}
  nav.toc li {{ margin: .15rem 0; }}
  nav.toc li.l3 {{ margin-left: 1.2rem; font-size: .88em; }}
  nav.toc a {{ color: var(--ink); text-decoration: none; }}
  nav.toc a:hover {{ color: var(--navy); }}
  h1, h2, h3, h4 {{ color: var(--navy); line-height: 1.3; }}
  h2 {{ border-bottom: 2px solid var(--emerald); padding-bottom: .3rem;
       margin-top: 2.4rem; }}
  h3 {{ color: var(--ink); }}
  table {{ border-collapse: collapse; width: 100%; margin: 1rem 0;
          font-size: .9rem; }}
  th, td {{ border: 1px solid var(--gray-200); padding: .45rem .6rem;
           text-align: left; vertical-align: top; }}
  th {{ background: var(--navy); color: #fff; }}
  tr:nth-child(even) td {{ background: var(--gray-50); }}
  .badge {{ color: #fff; font-weight: 700; font-size: .78rem;
           padding: .12rem .5rem; border-radius: 999px;
           text-transform: uppercase; letter-spacing: .04em; }}
  code {{ background: var(--gray-100); padding: .1rem .3rem; border-radius: 4px;
         font-size: .85em; }}
  pre.code {{ background: var(--dark); color: #e2e8f0; padding: 1rem;
             border-radius: 8px; overflow-x: auto; font-size: .82rem; }}
  pre.code code {{ background: none; padding: 0; }}
  blockquote {{ border-left: 4px solid var(--emerald); margin: 1rem 0;
               padding: .4rem 1rem; color: var(--ink);
               background: #ecfdf5; border-radius: 0 8px 8px 0; }}
  hr {{ border: 0; border-top: 1px solid var(--gray-200); margin: 2rem 0; }}
  a {{ color: var(--navy); }}
  .chart {{ margin: 1.4rem 0; }}
  .chart figcaption {{ font-weight: 600; color: var(--ink);
                      margin-bottom: .6rem; font-size: .95rem; }}
  .chart.donut {{ text-align: center; }}
  .legend {{ margin-top: .5rem; font-size: .82rem; color: var(--ink); }}
  .legend-item {{ display: inline-block; margin: 0 .9rem .2rem 0; }}
  .legend-item .sw {{ display: inline-block; width: 10px; height: 10px;
                     border-radius: 2px; margin-right: .3rem; }}
  .chart-unparsed {{ border: 1px dashed var(--orange); border-radius: 8px;
                    padding: .8rem; margin: 1.4rem 0; font-size: .85rem; }}
  .chart-unparsed strong {{ color: var(--orange); }}
  .bar-row {{ display: flex; align-items: center; gap: .7rem;
             margin: .35rem 0; font-size: .88rem; }}
  .bar-label {{ flex: 0 0 11rem; color: var(--ink); }}
  .bar-track {{ flex: 1; background: var(--gray-200); border-radius: 999px;
               height: 14px; overflow: hidden; }}
  .bar-fill {{ display: block; height: 100%; border-radius: 999px; }}
  .bar-value {{ flex: 0 0 5.5rem; text-align: right; font-weight: 600; }}
  .cmp-row {{ display: flex; align-items: center; gap: .7rem;
             margin: .35rem 0; font-size: .88rem; }}
  .cmp-track {{ flex: 1; position: relative; background: var(--gray-200);
               border-radius: 999px; height: 14px; }}
  .cmp-before {{ position: absolute; inset: 0 auto 0 0;
                background: #94a3b8; border-radius: 999px; opacity: .55; }}
  .cmp-after {{ position: absolute; inset: 0 auto 0 0;
               border-radius: 999px; height: 8px; margin-top: 3px; }}
  .cmp-delta {{ flex: 0 0 3rem; text-align: right; font-weight: 700; }}
  .cmp-legend {{ font-weight: 400; font-size: .78rem; color: var(--muted);
                margin-left: .5rem; }}
  .cmp-legend .sw {{ display: inline-block; width: 10px; height: 10px;
                    border-radius: 2px; margin: 0 .25rem 0 .6rem;
                    vertical-align: -1px; }}
  .stat-strip {{ display: flex; flex-wrap: wrap; gap: .8rem; margin: 1.4rem 0; }}
  .stat-card {{ flex: 1 1 9rem; border: 1px solid var(--gray-200);
               border-top: 4px solid var(--emerald); border-radius: 8px;
               padding: .8rem 1rem; background: #fff; }}
  .stat-card:nth-child(2n) {{ border-top-color: var(--navy); }}
  .stat-card:nth-child(3n) {{ border-top-color: var(--orange); }}
  .stat-card:nth-child(4n) {{ border-top-color: #F59E0B; }}
  .stat-label {{ color: var(--muted); font-size: .72rem;
                text-transform: uppercase; letter-spacing: .08em; }}
  .stat-value {{ font-size: 1.7rem; font-weight: 700; color: var(--ink); }}
  .stat-delta {{ font-size: .85rem; font-weight: 600; }}
  .report-footer {{ margin-top: 3rem; padding-top: 1rem;
                   border-top: 3px solid var(--navy);
                   color: var(--muted); font-size: .82rem; }}
  .report-footer a {{ color: var(--navy); }}
  @media print {{
    body {{ max-width: none; padding: 0 1rem; }}
    nav.toc {{ display: none; }}
    h2 {{ page-break-after: avoid; }}
    table, pre, .chart, .stat-strip {{ page-break-inside: avoid; }}
  }}
  /* one-pager: tighter rhythm so the summary genuinely fits a page */
  body.onepager {{ max-width: 44rem; }}
  body.onepager h2 {{ margin-top: 1.2rem; font-size: 1.15rem; }}
  body.onepager .chart {{ margin: .8rem 0; }}
  body.onepager .report-header {{ margin-bottom: 1rem; }}
  body.onepager table {{ font-size: .82rem; }}
</style>
</head>
<body{body_class}>
<div class="palette-strip"></div>
<header class="report-header">
  <div class="brand">{brand}</div>
  <h1>{title}</h1>
  <div class="date">{report_date}</div>
</header>
{toc}
<main>
{body}
</main>
<footer class="report-footer">{footer}</footer>
</body>
</html>
"""


def _linkify(text: str) -> str:
    return re.sub(r"(https?://[^\s<]+)", r'<a href="\1">\1</a>', text)


def extract_onepager(md: str) -> str:
    """Condense a full report into an executive one-pager.

    Keeps: the executive summary section, every chart block (deduplicated),
    and the first 5 rows of the recommendations/actions table. Drops
    everything else (findings detail, roadmap, appendix).
    """
    chart_blocks = re.findall(r"(?ms)^```chart\s*\n(.*?)^```\s*$", md)

    parts = re.split(r"(?m)^(##\s+.*)$", md)
    sections: list[tuple[str, str]] = []
    for j in range(1, len(parts), 2):
        sections.append((parts[j].strip(),
                         parts[j + 1] if j + 1 < len(parts) else ""))

    out: list[str] = []

    # 1. executive summary (charts stripped here; re-added once below)
    exec_pair = next(
        ((h, b) for h, b in sections if re.search(r"executive summary", h, re.I)),
        sections[0] if sections else None)
    if exec_pair:
        body_clean = re.sub(r"(?ms)^```chart\s*\n.*?^```\s*$", "", exec_pair[1])
        out.append(exec_pair[0] + "\n\n" + body_clean.strip())

    # 2. all charts, deduplicated
    seen: set[str] = set()
    for block in chart_blocks:
        key = block.strip()
        if key and key not in seen:
            seen.add(key)
            out.append("```chart\n" + key + "\n```")

    # 3. recommendations/actions table, top 5 data rows
    for heading, body in sections:
        if re.search(r"recommend|action", heading, re.I):
            table_lines = [l for l in body.strip().splitlines()
                           if l.strip().startswith("|")]
            if table_lines:
                out.append(heading + "\n\n"
                           + "\n".join(table_lines[:2 + 5]))
            break

    return "\n\n".join(out).strip() + "\n"


def build(md_path: Path, out_path: Path, brand: str, title: str | None,
          footer: str, onepager: bool = False) -> Path:
    markdown = md_path.read_text(encoding="utf-8")
    # use first H1 as title when --title is not given
    if not title:
        match = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
        title = match.group(1).strip() if match else md_path.stem
        markdown = re.sub(r"^#\s+.+\n?", "", markdown, count=1)
    if onepager:
        markdown = extract_onepager(markdown)
    body, toc_entries = md_to_html(markdown)
    if not onepager and len(toc_entries) >= 3:
        items = "".join(
            f'<li class="l{level}"><a href="#{slug}">{html.escape(text)}</a></li>'
            for level, slug, text in toc_entries)
        toc_html = (f'<nav class="toc"><strong>Contents</strong>'
                    f"<ul>{items}</ul></nav>")
    else:
        toc_html = ""
    page = SHELL.format(
        title=html.escape(title), brand=html.escape(brand),
        report_date=date.today().strftime("%d %B %Y"),
        navy=NAVY, emerald=EMERALD, orange=ORANGE, dark=DARK,
        toc=toc_html, body=body,
        footer=_linkify(html.escape(footer)),
        body_class=' class="onepager"' if onepager else "")
    out_path.write_text(page, encoding="utf-8")
    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="report_build",
                                     description="White-label HTML report builder")
    parser.add_argument("input", help="markdown report file")
    parser.add_argument("-o", "--output", help="output .html path")
    parser.add_argument("--brand", default="Lee Beirne")
    parser.add_argument("--title", help="report title (default: first H1)")
    parser.add_argument("--footer", default=DEFAULT_FOOTER)
    parser.add_argument("--onepager", action="store_true",
                        help="executive one-pager: summary + charts + top 5 actions")
    args = parser.parse_args(argv)

    md_path = Path(args.input)
    if not md_path.is_file():
        print(json.dumps({"error": f"File not found: {md_path}"}))
        return 1
    if args.output:
        out_path = Path(args.output)
    elif args.onepager:
        out_path = md_path.with_name(md_path.stem + "-onepager.html")
    else:
        out_path = md_path.with_suffix(".html")
    result = build(md_path, out_path, args.brand, args.title, args.footer,
                   onepager=args.onepager)
    print(json.dumps({"written": str(result.resolve())}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
