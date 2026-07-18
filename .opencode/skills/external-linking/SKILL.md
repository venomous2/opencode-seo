---
name: external-linking
description: Outbound link practices — citing authoritative sources, when to link out, rel attribute usage (nofollow/sponsored/ugc), and link rot checking. Use when the user says external links, outbound links, or nofollow.
---

# External Linking

Audits the links a page sends OUT to other sites. Good outbound linking
is a quality and trust signal; bad outbound linking leaks users to dead
pages and undisclosed paid placements.

## Inputs

- Required: URL(s) to review, or pasted content containing links
- Optional: site policy notes (affiliate relationships, sponsored
  placements, editorial standards)

## Data pulls

- webfetch each page; extract every outbound link with its anchor text,
  destination, and rel attributes.
- webfetch each unique external destination to check status (link rot:
  404/410, parked domains, redirect chains to unrelated content).

## Process

1. **Inventory** — table of outbound links: destination | anchor | rel |
   status.
2. **Source quality** — factual claims, statistics, and quotes should
   cite authoritative primary sources (official docs, research,
   standards bodies, government data). Flag links to thin listicles or
   direct competitors where a stronger neutral source exists.
3. **rel attributes** —
   - `sponsored` for paid, affiliate, or any compensated placement.
   - `ugc` for user-generated content links (comments, forums).
   - `nofollow` for destinations you cannot vouch for.
   - No attribute needed for normal editorial citations — linking out
     to good sources is expected and healthy; never nofollow everything
     out of "link juice" fear.
4. **Link rot** — every dead or hijacked destination gets a proposed
   replacement (updated URL, archive link, or better source) or removal.
5. **When to link out** — data points, definitions, tools, original
   research, and anything the reader would want to verify. Avoid
   outbound links inside conversion-critical blocks (checkout CTAs,
   lead forms).
6. **Anchor text** — name the source or claim ("according to the 2024
   Census"), never raw URLs or "this link".

## Output

Findings table with per-link evidence (status, rel, anchor), then
recommendations ranked critical / high / medium / low — undisclosed paid
links and rot are critical; missing citations are high — each with a
one-line "why", then the single best next step. Multi-page audits go to
`EXTERNAL-LINKS-<domain>-<date>.md`; chat shows the critical rows.
