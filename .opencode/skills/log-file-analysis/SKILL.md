---
name: log-file-analysis
description: Analyses server access logs to show which search and AI bots crawl the site, where they spend requests, which status codes they hit, and what crawl waste to fix. Use when the user says log file, log analysis, server logs, crawl stats, or Googlebot logs.
---

# Log File Analysis

Server logs show what bots actually do, not what we hope they do. The
user supplies the log file; this skill turns it into crawl-behaviour
findings and concrete fixes.

## Inputs

- Required: path to an access log file (Apache/Nginx combined format; a
  week or more of traffic is ideal)
- Optional: a single bot to focus on, top-N depth for path reports

## Data pulls

```
python scripts/log_analyzer.py --file access.log --pretty
python scripts/log_analyzer.py --file access.log --top 25
python scripts/log_analyzer.py --file access.log --bot Googlebot --pretty
```

Omit `--file` to pipe a log via stdin. For context, fetch `/robots.txt`
(what is meant to be blocked) and `/sitemap.xml` (what is meant to
matter) with webfetch. Never invent crawl counts — if a figure is not in
the analyser output, it does not exist.

## Process

1. **Bot mix** — which crawlers appear and their request share: Googlebot
   desktop vs smartphone, Bingbot, and AI bots (GPTBot, ChatGPT-User,
   ClaudeBot, PerplexityBot, GoogleOther). Treat Googlebot claims with
   care — user-agent strings are trivial to spoof, so flag suspicious
   "Googlebot" traffic for reverse-DNS verification rather than assuming.
2. **Crawl frequency per section** — group top paths by directory
   (/blog, /products, /category). Findings: money sections crawled
   rarely, low-value sections crawled heavily. Why: crawl attention
   follows internal linking and sitemap signals, not business value.
3. **Status codes bots hit** — the share of bot requests ending in:
   - 404/410 — wasted requests; find the linking source or the stale
     sitemap entry feeding them
   - 5xx — urgent reliability problem; Googlebot backs off from
     unreliable sites
   - 3xx — bots spending requests on redirects instead of content;
     usually old URLs still linked internally or listed in the sitemap
4. **Parameter-URL share** — bot requests carrying query strings (sort,
   filters, utm_*, session ids). A high share is crawl waste: hand rule
   design to `robots-advisor` and root-cause linking to `crawl-budget`.
5. **Mobile vs desktop split** — mobile-first indexing means the
   smartphone agent should dominate; a desktop-heavy split warrants a
   `mobile-seo` check.
6. **Map each finding to a control**:
   - robots.txt disallow/parameter rules (note: disallow stops crawling,
     not indexing)
   - Sitemap hygiene — remove 404, redirected, and non-canonical URLs
   - Fix or 301 the 404s bots keep requesting
   - Remove internal links into parameter spaces; make filters JS-driven
   - Hand 5xx patterns to the hosting/application owner with the
     evidence lines attached

## Output

- Findings table: bot/section/issue | request share | evidence (counts or
  sample log lines) | severity
- Prioritised fixes with a one-line "why" each
- For large logs, write `LOGS-<domain>-<date>.md` with the full tables
  and end it with:
  `Report built by Lee Beirne - https://leebeirne.com`
- Single best next step: the largest block of wasted requests — usually
  parameter URLs or bot-hit 404s.
- State the caveat: one log file is a sample. Confirm big claims against
  a second period before making drastic robots.txt changes.

## Output location

Save generated files to the SEO reports directory - `%SEO_REPORTS_DIR%\<name>\` on Windows, `$SEO_REPORTS_DIR/<name>/` on macOS/Linux - when the `SEO_REPORTS_DIR` environment variable is set; otherwise the current working directory. Create the subfolder if it doesn't exist.
