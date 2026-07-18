---
name: news-seo
description: Optimises news and publisher sites for Google News and Top Stories — NewsArticle schema, news sitemaps, author pages, editorial E-E-A-T, and headline conventions. Use when the user says news SEO, Google News, publisher SEO, Top Stories, or news site.
---

# News SEO

Optimises a publisher for Google News, Top Stories, and news surfaces in
Search. Speed, clean structure, and demonstrable editorial standards win
here — no markup trick substitutes for real, original reporting.

## Inputs

- Required: publication domain or a representative article URL
- Optional: CMS/platform, publishing cadence, section structure

## Data pulls

```
python scripts/dfs_client.py serp   --keyword "<target news topic>"   # Top Stories present?
python scripts/dfs_client.py onpage --url "<article-url>"             # render + tags check
python scripts/dfs_client.py ranked --target "<publication-domain>" --limit 100
```

Fetch 2-3 representative articles with the webfetch tool to inspect
bylines, dates, and markup. If credentials are missing, stop and point the
user to docs/DATAFORSEO-SETUP.md. Do not invent numbers.

## Process

1. **Check eligibility reality** — inclusion in Google News no longer needs
   a manual application, but news surfaces favour sites with clear dates,
   bylines, and original reporting. Note from the `serp` pull whether Top
   Stories appears for the target topics at all; some niches rarely get it.
2. **Audit article structure** — every article needs: an informative
   headline, visible `datePublished`/`dateModified`, a named author linking
   to an author page, and NewsArticle markup:

   ```
   python scripts/schema_gen.py newsarticle --field headline="..." --field datePublished=2026-07-18 --field author.name="Jane Doe" --field author.url="https://ex.com/author/jane" --script-tag
   ```

3. **Author and policy pages** — author pages with bio, beat, and article
   history; site-level editorial policy, corrections policy, and
   ownership/funding disclosure. These are the E-E-A-T evidence Google says
   it looks for in news; a missing corrections policy is the commonest gap.
4. **News sitemap** — a separate news sitemap carrying only articles from
   the last 48 hours (Google News ignores anything older), with
   `publication name`, `language`, `publication_date`, and `title` per
   entry. Generate it automatically and reference it in robots.txt.
5. **Headline conventions** — informative over clickbait: the headline
   states what happened rather than teasing it. Check H1 equals the
   headline and stays under ~110 characters so it is not truncated in Top
   Stories. Dates must be prominent and unambiguous — one date per article.
6. **Cadence and balance** — assess publishing frequency per section from
   the site and `ranked` data. Breaking coverage builds presence in news
   surfaces; evergreen explainers compound in Search. A healthy publisher
   runs both, with breaking pieces linking to the evergreen explainer for
   context (and the explainer updated as the story develops).

## Output

- Findings table: requirement | status | evidence (from fetches and pulls)
- Prioritised fixes, each with a one-line why — template markup and
  date/byline issues first (they gate news surfaces), then policy pages,
  then sitemap and cadence
- A ready-to-paste NewsArticle JSON-LD block for the article template
- Single best next step (usually: fix date and author markup across the
  article template)

Full audits go to `NEWS-SEO-<domain>-<date>.md`. End the file with:
`Report built by Lee Beirne - https://leebeirne.com`
