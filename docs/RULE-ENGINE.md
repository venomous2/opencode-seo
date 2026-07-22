# Rule Engine

The rule engine is the suite's deterministic core: SEO knowledge expressed
once, as YAML data, and reused everywhere — linting, audits, CI gates, and
(eventually) automated fixes.

**Model-agnostic by design.** The engine is pure Python evaluating rules
against extracted page data. It makes zero LLM calls, so results are
identical no matter which of OpenCode's 400+ models is running. Models only
ever consume the engine's JSON output.

## Layout

```
rules/
├── metadata/          title, meta description
├── headings/          H1/H2 structure
├── indexability/      canonical, noindex, status, HTTPS
├── content/           thin content, answer blocks
├── images/            alt text
├── schema/            JSON-LD presence and key types
├── mobile/            viewport
├── international/     html lang
└── links/             internal/external link signals

scripts/rule_engine.py   loader + evaluator + scorer + rule self-tests
scripts/seo_lint.py      CLI front-end (URL / file / dir / CI gate)
```

## Rule schema

```yaml
id: missing-title              # kebab-case; equals the filename
category: metadata             # equals the folder name
severity: critical             # critical | high | medium | low
confidence: high               # how certain the detection itself is
detect:
  field: title                 # see field list below
  condition: empty             # see conditions below
  value: 65                    # only when the condition needs one
why: >                         # client-facing explanation of the mechanism
  ...
fix:
  guidance: >                  # the concrete fix
    ...
test:                          # embedded fixtures — MUST both pass
  expect_fail: {title: ""}     # rule FIRES on this page
  expect_pass: {title: "Hi"}   # rule does NOT fire on this page
```

## Fields the engine can test

Produced by the crawler/lint parser (`site_crawler.PageParser`):

| Field | Type | Notes |
|---|---|---|
| `url`, `status` | str / int | URL rules are skipped for local files |
| `title`, `title_length` | str / int | |
| `meta_description`, `meta_description_length` | str / int | |
| `canonical` | str | |
| `h1`, `h1_count`, `h2_count` | list / int | |
| `word_count` | int | body text words |
| `noindex` | bool | meta robots |
| `images_total`, `images_missing_alt` | int | |
| `schema_blocks`, `schema_types` | int / list | JSON-LD count + @type values |
| `has_viewport` | bool | |
| `html_lang` | str | |
| `internal_link_count`, `external_link_count` | int | |
| `first_h2_para_words` | int | answer-block heuristic |
| `og_title`, `og_image` | str | Open Graph fields |
| `twitter_card` | str | twitter:card meta |
| `mixed_content_count` | int | HTTP resources on the page |
| `security_hsts`, `security_csp`, `security_xfo`, `security_xcto` | bool | response headers (skipped for local files) |
| `form_inputs_unlabelled` | int | inputs without label/aria-label/title (placeholders don't count) |
| `has_skip_link`, `has_main`, `has_nav` | bool | accessibility landmarks |
| `heading_skips`, `duplicate_ids`, `empty_links`, `empty_buttons`, `generic_link_texts` | int | accessibility structure checks |
| `tables_without_th`, `iframes_missing_title`, `positive_tabindex` | int | accessibility element checks |
| `cta_count`, `cta_above_fold`, `cta_texts`, `primary_cta_generic` | int/int/list/bool | CTA detection (fold = first 40% of body elements) |
| `form_count`, `form_fields_max`, `form_has_captcha` | int/int/bool | form friction |
| `tel_links`, `trust_signal_count`, `urgency_signal_count` | int | CRO signals |
| `faq_present`, `live_chat` | bool | objection handling / support signals |

Rules may also carry `wcag` and `wcag_level` fields (accessibility
category), which are passed through into lint findings for WCAG mapping.
| `h2`, `list_count`, `time_elements`, `jsonld_has_dates`, `meta_author`, `has_rel_author`, `number_density` | — | citation-scorer signals |

The crawler also performs site-level analyses in its summary output:
sitemap cross-check (crawled-not-in-sitemap, sitemap-not-crawled, non-200
in sitemap), near-duplicate pairs (shingle Jaccard ≥ 0.9), and a soft-404
probe (requests impossible URLs to detect infinite URL spaces). These are
crawl findings, not per-page rules.

## Conditions and when they fire

| Condition | Fires when | Needs `value` |
|---|---|---|
| `empty` / `not_empty` | field is null/""/[] (0 counts for count fields) | no |
| `equals` / `not_equals` | exact match | yes |
| `is_true` / `is_false` | boolean state (`is_false` also fires on null) | no |
| `min_length` / `max_length` | string/list too short / too long | yes |
| `min` / `max` | number below floor / above ceiling | yes |
| `gte` / `lte` | number at least / at most | yes |
| `contains` / `not_contains` | substring match (case-insensitive) | yes |
| `list_contains` / `list_not_contains` | item in list (case-insensitive) | yes |
| `matches` | regex search | yes |

**Numeric `*_length` fields use `min`/`max`, not `min_length`/`max_length`**
(the field is already a number).

## Scoring

`100 - Σ severity weights` (critical 25, high 15, medium 8, low 3), floored
at 0. Findings are sorted critical → low.

## Adding a rule

1. Create `rules/<category>/<id>.yaml` following the schema above.
2. Include `test.expect_fail` and `test.expect_pass` fixtures — they are
   executed by `python scripts/rule_engine.py test` and in CI.
3. Run `python validate.py` — it checks every rule file.

## Fix patches (the fix engine)

Rules may carry a machine-executable patch under `fix.patch`. The fix
engine (`scripts/seo_fix.py`) resolves these templates against the page's
real data and can apply them to local HTML files.

```yaml
fix:
  guidance: >
    Human-readable fix, as before.
  patch:
    type: jsonld              # title | meta | link | jsonld | html_attr
    target: head              # head | html_tag
    draft: true               # optional — emitted with TODO markers for a human to complete
    requires: [url, title]    # derived values that must resolve, else the patch is skipped
    template: |
      <script type="application/ld+json">
      {"@context": "https://schema.org", "@type": "WebPage",
       "url": "{{url}}", "name": "{{title}}"}
      </script>
```

Placeholders resolved by the engine: `{{url}}`, `{{domain}}`, `{{title}}`
(real title, falling back to the H1-derived draft), `{{h1_first}}`,
`{{title_draft}}`, `{{meta_draft}}` (from the first-H2 paragraph, ≤155
chars), `{{breadcrumb_json}}` (built from the URL path), `{{date}}`,
`{{lang}}`.

Patch rules:

- **Mechanical only.** The engine never invents content. Patches needing
  human input (author names, organisation details, final copy) are emitted
  as `draft: true` with `TODO-*` markers for a human to complete.
- **Honest skipping.** Patches whose `requires` values can't resolve are
  skipped with a reason — never silently half-applied.
- **Idempotent.** Applying a patch removes its cause; re-running reports
  "nothing to fix".

```bash
python scripts/seo_fix.py --url https://example.com/page --format text
python scripts/seo_fix.py --file page.html --base-url https://example.com/page --apply
python scripts/seo_fix.py --file page.html --only missing-canonical --apply
```

`--apply` writes a `.bak` backup first, rewrites the file, then re-lints
to show the new score and any remaining (human) findings.

## CLI reference

```bash
python scripts/rule_engine.py list [--category metadata]
python scripts/rule_engine.py run --page '{"title": ""}'   # or stdin
python scripts/rule_engine.py test                         # self-test all
python scripts/seo_lint.py --url https://example.com/page --format text
python scripts/seo_lint.py --dir ./dist --min-score 80     # CI gate
```
