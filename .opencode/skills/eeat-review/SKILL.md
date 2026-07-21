---
name: eeat-review
description: E-E-A-T audit covering first-hand experience signals, author expertise, external authoritativeness via live mention data, and trust elements like policies and contact info. Use when the user says E-E-A-T, EEAT, expertise signals, or trust signals.
---

# E-E-A-T Review

Audits the four trust dimensions — Experience, Expertise, Authoritativeness,
Trust — with evidence, not vibes. Every finding cites what is present or
missing on the page or site.

## Inputs

- Required: domain or page URL
- Optional: author name, niche (YMYL niches get a stricter bar)

## Data pulls

```
python scripts/dfs_client.py mentions   --target "<domain-or-brand>" --limit 50
python scripts/dfs_client.py content    --url "<url>"
python scripts/dfs_client.py refdomains --target "<domain>" --limit 30
```

Fetch the page, its about page, and author pages with webfetch (parallel).
If credentials are missing, run the on-page audit from webfetch alone and
say external-mention data was unavailable.

## Process

1. **Experience** — look for first-hand evidence: original photos (not
   stock), data from the site's own tests, "we tried / we measured"
   language, specific details only a practitioner would know. Generic
   summaries of other sites' experience score zero here.
2. **Expertise** — named authors with credentials on-page; author pages
   listing qualifications; an about page that establishes topical focus.
   Flag anonymous content and credential claims with no supporting page.
3. **Authoritativeness** — from the data pulls: who mentions the brand
   and in what context, quality of referring domains, whether the site or
   its authors are cited by recognized publications. On-page: citations
   to primary sources rather than other blogs.
4. **Trust** — contact page with real address/phone, editorial and
   correction policies, clear ownership, HTTPS everywhere, dated content
   with update history, honest affiliate/disclosure statements. For YMYL:
   reviewer credits (medical/legal/financial) are mandatory.
5. **Score each dimension** 1-5 with quoted evidence; the lowest
   dimension sets the ceiling — E-E-A-T fails on its weakest leg.

## Output

Scorecard: dimension | score | evidence found | gaps. Then prioritized
fixes (critical / high / medium) with one-line whys — e.g. "Add named
author with linked credentials — anonymous YMYL content is the top
trust blocker." End with the single fastest credible win (usually author
pages or first-hand evidence in the top article). Write the full audit to
`EEAT-<domain>-<date>.md`.

## Output location

Save generated files to the SEO reports directory - `%SEO_REPORTS_DIR%\<name>\` on Windows, `$SEO_REPORTS_DIR/<name>/` on macOS/Linux - when the `SEO_REPORTS_DIR` environment variable is set; otherwise the current working directory. Create the subfolder if it doesn't exist.

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
