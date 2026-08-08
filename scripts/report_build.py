"""White-label HTML report builder for the OpenCode SEO Suite.

Renders a suite markdown report into a styled, standalone HTML file with
Lee Beirne's branded template — dark header with LB monogram, score circle,
findings tables, recommendations grid, roadmap columns, and a print-to-PDF-
friendly layout.

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
  <span class="bar-value">{before:g} \u2192 {after:g}</span>
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
            delta_colour = EMERALD if delta.startswith(("+", "\u2191")) else ORANGE
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
    list of label/value dicts — all normalised to the same spec.
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
# Markdown -> HTML (branded template sections)
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
        return (f'<span class="badge" style="background:{colour};color:#fff">'
                f'{html.escape(raw.strip())}</span>')
    return cell_html


def _extract_score(markdown: str) -> tuple[float | None, str]:
    """Extract overall score and summary from markdown content."""
    # Look for patterns like "59/100", "Score: 59", "Overall: 59"
    patterns = [
        r"(?:overall|total|score|rating)[:\s]*(\d{1,3}(?:\.\d+)?)\s*(?:/\s*100|out of 100)?",
        r"(?<![\d.])(\d{1,3}(?:\.\d+)?)\s*/\s*100",
        r"(?<![\d.])(\d{1,3}(?:\.\d+)?)\s*out of\s*100",
    ]
    for pattern in patterns:
        m = re.search(pattern, markdown, re.I)
        if m:
            score = float(m.group(1))
            if 0 <= score <= 100:
                score = int(score) if score.is_integer() else score
                # Try to extract summary from first paragraph after score.
                # Skip markdown syntax lines (headings, tables, fences,
                # lists) so structural markup can't bleed into the summary.
                summary = ""
                after = markdown[m.end():m.end() + 500]
                para_match = re.search(r"\n\n([^#\n|`\-*>][^\n]{20,200})",
                                       after)
                if para_match:
                    summary = para_match.group(1).strip()
                return score, summary
    return None, ""


def _extract_severity_counts(markdown: str) -> dict[str, int]:
    """Count findings by severity from markdown content."""
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    # Look for severity badges/labels in tables and headings
    for severity in counts:
        # Match table cells with severity labels
        pattern = rf'\|\s*{severity}\s*\|'
        counts[severity] += len(re.findall(pattern, markdown, re.I))
        # Match severity in headings
        pattern = rf'#{1,6}\s+.*{severity}'
        counts[severity] += len(re.findall(pattern, markdown, re.I))
        # Match severity badges
        pattern = rf'class="[^"]*badge[^"]*"[^>]*>{severity}'
        counts[severity] += len(re.findall(pattern, markdown, re.I))
    return counts


def _extract_stats(markdown: str) -> list[tuple[str, str]]:
    """Extract key statistics from markdown content."""
    stats = []
    # Look for stat patterns like "X backlinks", "Y keywords", "Z words"
    patterns = [
        (r"(\d+)\s*(?:total\s+)?backlinks?", "Backlinks"),
        (r"(\d+)\s*(?:ranked\s+)?keywords?", "Ranked Keywords"),
        (r"(\d+)\s*words?\s*(?:on\s+)?(?:the\s+)?(?:home\s*page|main\s*page)", "Homepage Words"),
        (r"(?:home\s*page|main\s*page)\s*(?:is\s+|has\s+|contains\s+)?(\d+)\s*words?", "Homepage Words"),
        (r"(\d+)\s*pages?\s*(?:in\s+)?(?:the\s+)?sitemap", "Sitemap Pages"),
        (r"sitemap\s*(?:contains?\s+|has\s+)?(\d+)\s*pages?", "Sitemap Pages"),
        (r"(\d+)\s*(?:AI\s+)?crawlers?\s*(?:allowed|enabled)", "AI Crawlers"),
        (r"on[- ]page\s*(?:score|rating)[:\s]*(\d+)", "On-page Score"),
        (r"(?:domain\s+)?authority[:\s]*(\d+)", "Domain Authority"),
    ]
    for pattern, label in patterns:
        m = re.search(pattern, markdown, re.I)
        if m:
            stats.append((label, m.group(1)))
    return stats


def _classify_section(heading: str, body: str) -> str:
    """Classify a section by its heading and content to determine rendering style."""
    h = heading.lower()
    if any(w in h for w in ["critical", "high", "medium", "low", "finding"]):
        return "findings"
    if any(w in h for w in ["recommend", "action", "fix"]):
        return "recommendations"
    if any(w in h for w in ["roadmap", "timeline", "30", "60", "90", "phase"]):
        return "roadmap"
    if any(w in h for w in ["working", "strength", "positive", "pass"]):
        return "working"
    if any(w in h for w in ["executive", "summary", "overview"]):
        return "summary"
    if any(w in h for w in ["next step", "single best", "priority"]):
        return "next_step"
    return "default"


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
# HTML shell — branded Lee Beirne template
# ---------------------------------------------------------------------------

SHELL = """<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  :root {{ --navy: {navy}; --emerald: {emerald}; --orange: {orange};
           --dark: {dark}; --white: #FFFFFF; --gray-50: #F9FAFB;
           --gray-100: #F3F4F6; --gray-200: #E5E7EB; --gray-500: #6B7280;
           --gray-600: #4B5563; --gray-700: #374151; --gray-900: #111827; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: Arial, Helvetica, sans-serif;
         color: var(--gray-700); line-height: 1.6; background: var(--white); }}
  .container {{ max-width: 1000px; margin: 0 auto; padding: 0 40px; }}
  .report-header {{ background: linear-gradient(135deg, var(--dark) 0%, var(--navy) 100%);
                    padding: 60px 0; color: var(--white); }}
  .report-header .inner {{ display: flex; justify-content: space-between;
                           align-items: flex-start; }}
  .brand {{ display: flex; align-items: center; gap: 16px; }}
  .brand-logo {{ width: 56px; height: 56px; background: var(--navy);
                 border-radius: 10px; display: flex; align-items: center;
                 justify-content: center; font-size: 24px; font-weight: 800;
                 color: var(--white); border: 2px solid rgba(255,255,255,0.15); }}
   .brand-name {{ font-family: Arial, Helvetica, sans-serif; font-size: 22px;
                 font-weight: 700; }}
  .brand-role {{ font-size: 13px; color: rgba(255,255,255,0.6); }}
  .report-meta {{ text-align: right; }}
  .report-meta .label {{ font-size: 11px; text-transform: uppercase;
                         letter-spacing: 0.08em; color: var(--emerald);
                         font-weight: 600; margin-bottom: 4px; }}
  .report-meta .value {{ font-size: 14px; color: rgba(255,255,255,0.7); }}
  .score-section {{ background: var(--white); border: 1px solid var(--gray-200);
                    border-top: none; padding: 40px 0; }}
  .score-grid {{ display: grid; grid-template-columns: 200px 1fr;
                 gap: 40px; align-items: center; }}
  .score-circle {{ width: 160px; height: 160px; border-radius: 50%;
                   background: conic-gradient(var(--score-colour) 0deg,
                   var(--score-colour) var(--score-deg),
                   var(--orange) var(--score-deg),
                   var(--orange) var(--score-deg-plus),
                   var(--gray-200) var(--score-deg-plus));
                   display: flex; align-items: center; justify-content: center;
                   position: relative; }}
  .score-circle::after {{ content: ''; width: 130px; height: 130px;
                          background: var(--white); border-radius: 50%;
                          position: absolute; }}
   .score-value {{ position: relative; z-index: 1;
                   font-family: Arial, Helvetica, sans-serif; font-size: 48px;
                   font-weight: 800; color: var(--dark); }}
   .score-value span {{ font-size: 20px; color: var(--gray-500); }}
   .score-value.decimal {{ font-size: 38px; }}
   .score-value.decimal span {{ font-size: 16px; }}
   .score-summary h2 {{ font-family: Arial, Helvetica, sans-serif; font-size: 24px;
                       font-weight: 700; color: var(--dark); margin-bottom: 12px; }}
  .score-summary p {{ color: var(--gray-600); line-height: 1.7; }}
  .findings-count {{ display: flex; gap: 16px; margin-top: 16px; flex-wrap: wrap; }}
  .findings-count .tag {{ padding: 4px 12px; border-radius: 6px;
                          font-size: 12px; font-weight: 600; }}
  .tag-critical {{ background: #FEE2E2; color: #991B1B; }}
  .tag-high {{ background: #FEF3C7; color: #92400E; }}
  .tag-medium {{ background: #DBEAFE; color: #1E40AF; }}
  .tag-low {{ background: #D1FAE5; color: #065F46; }}
  .content {{ padding: 48px 0; }}
  .section {{ margin-bottom: 48px; }}
   .section-title {{ font-family: Arial, Helvetica, sans-serif; font-size: 20px;
                    font-weight: 700; color: var(--dark); padding-bottom: 12px;
                    border-bottom: 2px solid var(--dark); margin-bottom: 24px; }}
   h3 {{ font-family: Arial, Helvetica, sans-serif; font-size: 16px;
        font-weight: 600; color: var(--dark); margin-bottom: 12px; }}
  p {{ margin-bottom: 16px; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 24px; }}
  th {{ background: var(--gray-50); text-align: left; padding: 10px 16px;
        font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em;
        color: var(--gray-500); font-weight: 600;
        border-bottom: 1px solid var(--gray-200); }}
  td {{ padding: 12px 16px; font-size: 14px; border-bottom: 1px solid var(--gray-100);
        vertical-align: top; }}
  tr:last-child td {{ border-bottom: none; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px;
            font-size: 11px; font-weight: 700; text-transform: uppercase;
            letter-spacing: 0.05em; }}
  .status-critical {{ background: #FEE2E2; color: #991B1B; }}
  .status-high {{ background: #FEE2E2; color: #991B1B; }}
  .status-medium {{ background: #FEF3C7; color: #92400E; }}
  .status-low {{ background: #DBEAFE; color: #1E40AF; }}
  .status-pass {{ background: #D1FAE5; color: #065F46; }}
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
  .rec-grid {{ display: grid; gap: 12px; }}
  .rec-card {{ display: grid; grid-template-columns: 80px 1fr; gap: 16px;
               align-items: center; padding: 16px;
               border: 1px solid var(--gray-200); border-radius: 8px;
               background: var(--white); }}
  .rec-card:hover {{ border-color: var(--navy); }}
  .rec-why {{ font-size: 13px; color: var(--gray-500); }}
  .working-list {{ list-style: none; }}
  .working-list li {{ padding: 10px 0; border-bottom: 1px solid var(--gray-100);
                      display: flex; align-items: flex-start; gap: 12px;
                      font-size: 14px; }}
  .working-list li::before {{ content: '\\2713'; display: inline-block;
                              width: 20px; height: 20px; background: var(--emerald);
                              color: var(--white); border-radius: 50%;
                              text-align: center; line-height: 20px; font-size: 12px;
                              font-weight: 700; flex-shrink: 0; }}
  .next-step {{ background: linear-gradient(135deg, var(--dark) 0%, var(--navy) 100%);
                border-radius: 12px; padding: 32px; color: var(--white); margin: 32px 0; }}
  .next-step h3 {{ color: var(--emerald); margin-bottom: 8px;
                   font-family: Arial, Helvetica, sans-serif; }}
  .next-step p {{ color: rgba(255,255,255,0.8); margin-bottom: 0; }}
  .stats-row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
                gap: 16px; margin-bottom: 48px; }}
  .stat-card {{ background: var(--white); border: 1px solid var(--gray-200);
                border-radius: 8px; padding: 20px; text-align: center;
                border-top: 4px solid var(--emerald); }}
  .stat-card:nth-child(2) {{ border-top-color: var(--navy); }}
  .stat-card:nth-child(3) {{ border-top-color: var(--orange); }}
  .stat-card:nth-child(4) {{ border-top-color: var(--emerald); }}
  .stat-card:nth-child(5) {{ border-top-color: var(--navy); }}
  .stat-card:nth-child(6) {{ border-top-color: var(--orange); }}
   .stat-value {{ font-family: Arial, Helvetica, sans-serif; font-size: 28px;
                 font-weight: 800; color: var(--dark); }}
  .stat-label {{ font-size: 11px; text-transform: uppercase;
                 letter-spacing: 0.08em; color: var(--gray-500); margin-top: 4px; }}
  .stat-delta {{ font-size: .85rem; font-weight: 600; }}
  .roadmap-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }}
  .roadmap-col {{ background: var(--white); border: 1px solid var(--gray-200);
                  border-radius: 8px; padding: 24px;
                  border-top: 4px solid var(--emerald); }}
  .roadmap-col:nth-child(2) {{ border-top-color: var(--navy); }}
  .roadmap-col:nth-child(3) {{ border-top-color: var(--orange); }}
   .roadmap-col h4 {{ font-family: Arial, Helvetica, sans-serif; font-size: 14px;
                     font-weight: 700; color: var(--dark); margin-bottom: 16px;
                     text-transform: uppercase; letter-spacing: 0.05em; }}
  .roadmap-col ol {{ padding-left: 20px; font-size: 13px; color: var(--gray-600);
                     line-height: 1.8; }}
  .chart {{ margin: 1.4rem 0; }}
  .chart figcaption {{ font-weight: 600; color: var(--dark);
                       margin-bottom: .6rem; font-size: .95rem; }}
  .chart.donut {{ text-align: center; }}
  .legend {{ margin-top: .5rem; font-size: .82rem; color: var(--gray-900); }}
  .legend-item {{ display: inline-block; margin: 0 .9rem .2rem 0; }}
  .legend-item .sw {{ display: inline-block; width: 10px; height: 10px;
                      border-radius: 2px; margin-right: .3rem; }}
  .chart-unparsed {{ border: 1px dashed var(--orange); border-radius: 8px;
                     padding: .8rem; margin: 1.4rem 0; font-size: .85rem; }}
  .chart-unparsed strong {{ color: var(--orange); }}
  .bar-row {{ display: flex; align-items: center; gap: .7rem;
              margin: .35rem 0; font-size: .88rem; }}
  .bar-label {{ flex: 0 0 11rem; color: var(--gray-900); }}
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
  .cmp-legend {{ font-weight: 400; font-size: .78rem; color: var(--gray-500);
                 margin-left: .5rem; }}
  .cmp-legend .sw {{ display: inline-block; width: 10px; height: 10px;
                     border-radius: 2px; margin: 0 .25rem 0 .6rem;
                     vertical-align: -1px; }}
  .stat-strip {{ display: flex; flex-wrap: wrap; gap: .8rem; margin: 1.4rem 0; }}
  .report-footer {{ background: var(--dark); padding: 32px 0;
                    text-align: center; color: rgba(255,255,255,0.4);
                    font-size: 13px; }}
  .report-footer a {{ color: var(--emerald); text-decoration: none; }}
  nav.toc {{ background: var(--gray-50); border: 1px solid var(--gray-200);
             border-left: 4px solid var(--emerald); border-radius: 8px;
             padding: 1rem 1.4rem; margin: 0 0 2rem; font-size: .92rem; }}
  nav.toc strong {{ color: var(--navy); text-transform: uppercase;
                    font-size: .75rem; letter-spacing: .1em; }}
  nav.toc ul {{ margin: .5rem 0 0; padding-left: 1.2rem; }}
  nav.toc li {{ margin: .15rem 0; }}
  nav.toc li.l3 {{ margin-left: 1.2rem; font-size: .88em; }}
  nav.toc a {{ color: var(--gray-900); text-decoration: none; }}
  nav.toc a:hover {{ color: var(--navy); }}
  body.onepager .score-section {{ padding: 24px 0; }}
  body.onepager .score-grid {{ gap: 24px; }}
  body.onepager .score-circle {{ width: 100px; height: 100px; }}
  body.onepager .score-circle::after {{ width: 80px; height: 80px; }}
   body.onepager .score-value {{ font-size: 32px; }}
   body.onepager .score-value.decimal {{ font-size: 27px; }}
   body.onepager .score-value.decimal span {{ font-size: 12px; }}
  body.onepager .section {{ margin-bottom: 24px; }}
  body.onepager .stats-row {{ margin-bottom: 24px; }}
  body.onepager .roadmap-grid {{ gap: 12px; }}
  body.onepager .roadmap-col {{ padding: 16px; }}
  body.onepager .next-step {{ padding: 20px; margin: 20px 0; }}
  @media print {{
    body {{ font-size: 11px; }}
    .container {{ padding: 0 20px; }}
    .report-header {{ padding: 30px 0; }}
    .score-section, .content {{ padding: 20px 0; }}
    .section {{ page-break-inside: avoid; }}
    .roadmap-grid {{ grid-template-columns: 1fr; }}
    nav.toc {{ display: none; }}
  }}
  @media (max-width: 768px) {{
    .score-grid {{ grid-template-columns: 1fr; }}
    .report-header .inner {{ flex-direction: column; gap: 24px; }}
    .report-meta {{ text-align: left; }}
    .roadmap-grid {{ grid-template-columns: 1fr; }}
    .stats-row {{ grid-template-columns: repeat(2, 1fr); }}
  }}
</style>
</head>
<body{body_class}>
<div class="report-header">
  <div class="container">
    <div class="inner">
      <div class="brand">
        <div class="brand-logo">LB</div>
        <div>
          <div class="brand-name">{brand}</div>
          <div class="brand-role">AI SEO Consultant</div>
        </div>
      </div>
      <div class="report-meta">
        <div class="label">{report_type}</div>
        <div class="value">{site_domain}</div>
        <div class="value">{report_date}</div>
      </div>
    </div>
  </div>
</div>
{score_section}
<div class="content">
  <div class="container">
    {stats_row}
    {toc}
    {body}
  </div>
</div>
<div class="report-footer">
  <div class="container"><p>{footer}</p></div>
</div>
</body>
</html>
"""


def _linkify(text: str) -> str:
    return re.sub(r"(https?://[^\s<]+)", r'<a href="\1">\1</a>', text)


def _extract_domain(title: str) -> str:
    """Extract domain from title like 'SEO Audit — leebeirne.com'."""
    m = re.search(r"([a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z]{2,})", title)
    return m.group(1) if m else ""


def _build_score_section(score: float | None, summary: str,
                         severity_counts: dict[str, int]) -> str:
    """Build the score section HTML."""
    if score is None:
        return ""

    score_colour = EMERALD if score >= 70 else (ORANGE if score >= 40 else "#F59E0B")
    score_deg = score * 3.6
    score_deg_plus = min(score_deg + 53, 360)
    score_display = f"{score:g}"
    score_class = "score-value decimal" if isinstance(score, float) \
        and not score.is_integer() else "score-value"

    summary_html = html.escape(summary) if summary else ""

    tags = []
    for severity, count in severity_counts.items():
        if count > 0:
            tags.append(f'<span class="tag tag-{severity}">{count} '
                        f'{severity.title()}</span>')
    tags_html = "".join(tags) if tags else ""

    return f'''<div class="score-section">
  <div class="container">
    <div class="score-grid">
      <div class="score-circle" style="--score-colour:{score_colour};
           --score-deg:{score_deg}deg; --score-deg-plus:{score_deg_plus}deg;">
        <div class="{score_class}">{score_display}<span>/100</span></div>
      </div>
      <div class="score-summary">
        <h2>Overall Score: {score_display}/100</h2>
        <p>{summary_html}</p>
        <div class="findings-count">{tags_html}</div>
      </div>
    </div>
  </div>
</div>'''


def _build_stats_row(stats: list[tuple[str, str]]) -> str:
    """Build the stats row HTML."""
    if not stats:
        return ""
    cards = []
    for label, value in stats:
        cards.append(f'''<div class="stat-card">
  <div class="stat-value">{html.escape(value)}</div>
  <div class="stat-label">{html.escape(label)}</div>
</div>''')
    return '<div class="stats-row">' + "".join(cards) + '</div>'


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

    # Extract metadata for branded template
    score, summary = _extract_score(markdown)
    severity_counts = _extract_severity_counts(markdown)
    stats = _extract_stats(markdown)
    domain = _extract_domain(title or "")

    body, toc_entries = md_to_html(markdown)
    if not onepager and len(toc_entries) >= 3:
        items = "".join(
            f'<li class="l{level}"><a href="#{slug}">{html.escape(text)}</a></li>'
            for level, slug, text in toc_entries)
        toc_html = (f'<nav class="toc"><strong>Contents</strong>'
                    f"<ul>{items}</ul></nav>")
    else:
        toc_html = ""

    score_section = _build_score_section(score, summary, severity_counts)
    stats_row = _build_stats_row(stats)

    # Determine report type from title
    report_type = "Complete Site Audit"
    if title:
        t = title.lower()
        if "technical" in t:
            report_type = "Technical SEO Audit"
        elif "on-page" in t or "onpage" in t:
            report_type = "On-Page SEO Audit"
        elif "content" in t:
            report_type = "Content Audit"
        elif "competitor" in t:
            report_type = "Competitor Analysis"
        elif "backlink" in t:
            report_type = "Backlink Audit"
        elif "local" in t:
            report_type = "Local SEO Audit"

    page = SHELL.format(
        title=html.escape(title or ""), brand=html.escape(brand),
        report_date=date.today().strftime("%d %B %Y"),
        navy=NAVY, emerald=EMERALD, orange=ORANGE, dark=DARK,
        toc=toc_html, body=body,
        footer=_linkify(html.escape(footer)),
        body_class=' class="onepager"' if onepager else "",
        score_section=score_section, stats_row=stats_row,
        report_type=report_type, site_domain=domain)
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
