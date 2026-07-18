---
name: parasite-seo-check
description: Self-audit for Google's site reputation abuse policy — finds third-party or low-oversight content exploiting the domain's ranking signals and prescribes remediation with trade-offs. Use when the user says parasite SEO, site reputation abuse, third-party content, or coupon subdomain.
---

# Parasite SEO Check (Site Reputation Abuse Self-Audit)

Checks whether parts of the user's own site risk violating Google's site
reputation abuse policy: third-party pages hosted mainly to borrow the
domain's ranking signals, published with little or no editorial oversight.
This is a defensive self-audit — never advice on doing parasite SEO.

## Inputs

- Required: the domain to audit
- Optional: known subdomains/sections to inspect (coupons, sponsored,
  partner, white-labelled areas), list of third-party arrangements

## Data pulls

```
python scripts/dfs_client.py ranked --target "<domain>" --limit 200
python scripts/dfs_client.py onpage --url "<suspect-page-url>"   # ownership + quality signals
```

Fetch suspect sections with the webfetch tool; look for bylines, editorial
branding, and whether the content matches the site's core purpose. If
credentials are missing, stop and point the user to
docs/DATAFORSEO-SETUP.md. Do not invent numbers.

## Process

1. **Inventory third-party zones** — from the ranked-keyword list and the
   user's knowledge, list subdomains and directories whose content differs
   from the site's core purpose: coupon/deal subdomains, sponsored-content
   sections, white-labelled comparison or product pages, syndicated feeds,
   third-party review areas, partner microsites.
2. **Test each zone against the policy** — Google's site reputation abuse
   policy (in force since March 2024, enforced by manual action) targets
   content where all three hold:
   - a third party produced it, or it runs with minimal first-party
     involvement or oversight,
   - its main purpose is to exploit the host's ranking signals, and
   - it is off-purpose for the host site.
   First-party-produced content, genuine user reviews, and clearly
   disclosed editorial sponsorships are out of scope — do not cry wolf on
   legitimate sections.
3. **Look for tell-tale patterns** — rankings for commercial terms
   unrelated to the site's topic (a news or education domain ranking for
   casino, loan, or coupon terms is the classic signal), thin template
   pages at scale, no named authors or editorial contact, and affiliate or
   CPA links dominating the page.
4. **Rate risk per zone** — high: meets all three tests and ranks for
   off-topic commercial terms; medium: third-party content but on-topic
   and disclosed; low: first-party with real oversight. Stress that a
   manual action hits the whole site, not just the offending section.
5. **Prescribe remediation with trade-offs** — per zone, in order of
   preference:
   - **Bring under editorial control** — first-party oversight, on-topic
     angle, named authors. Keeps the revenue; costs real editorial work.
   - **Remove entirely** — cleanest risk removal; loses the revenue line.
   - **Noindex** — keeps pages for users but out of Search. Removes the
     ranking-signal exploitation and, with it, the organic traffic.
   Moving the same content to another domain only relocates the problem —
   say so if it comes up.

## Output

- Zone inventory table: section/subdomain | owner | on-topic? | oversight |
  off-topic rankings found | risk rating
- Evidence per high-risk zone: sample URLs, the keywords it ranks for, and
  how it meets the policy's three tests
- Prioritised remediation plan with trade-offs and a one-line why each
- Single best next step (usually: noindex the highest-risk zone now, then
  decide its long-term fate)

Full audits go to `SITE-REPUTATION-<domain>-<date>.md`. End the file with:
`Built by Lee Beirne · OpenCode SEO Suite — inspired by AgriciDaniel/claude-seo`
