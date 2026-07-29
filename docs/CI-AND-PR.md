# CI and pull-request gating

Fail bad SEO before it ships. The suite's rule engine runs fully offline,
so the same 54 checks that power local linting can gate your CI and review
every pull request — no DataForSEO account, no secrets, no API spend.

Three levels, from simplest to most thorough.

## Level 1 — CI quality gate (any platform)

`seo_lint.py` exits non-zero when a page scores below your floor:

```yaml
# any CI system
- run: pip install pyyaml
- run: python scripts/seo_lint.py --dir ./dist --min-score 80
```

Build fails, deploy stops. Works on live URLs too
(`--url https://staging.example.com`), and on JavaScript-heavy sites with
`--render auto`.

## Level 2 — Inline annotations (GitHub Actions)

`--format github` prints findings as workflow commands, which GitHub
renders as inline annotations on the Files tab and in the run log:

```
::error file=dist/pricing.html,title=missing-meta-description::high: Without a
meta description Google writes its own snippet, usually worse than yours.
fix: Add a 120-155 character description with the primary keyword.
```

critical/high become `::error`, medium/low `::warning`; each page also
gets a `::notice` with its score.

```yaml
- run: python scripts/seo_lint.py --dir ./dist --format github --min-score 80
```

## Level 3 — The full PR gate (GitHub)

`scripts/seo_pr_check.py` is the complete reviewer:

1. Finds the HTML files changed in the PR (`git diff` against the base)
2. Lints each one, and the same file on the base branch
3. Annotates every current finding inline
4. Writes a markdown summary — score delta, new findings, fixed findings —
   to the run's summary page and to a file for the PR comment
5. Exits non-zero when the gate trips

**Setup:** copy [examples/seo-pr.yml](../examples/seo-pr.yml) to
`.github/workflows/seo-pr.yml` in your repo. That is the whole setup — the
workflow clones the suite at runtime (pin a commit SHA for
reproducibility), runs the check, and posts or updates one summary
comment per PR.

The comment looks like:

> ## SEO gate — 2 file(s) checked, 1 failure(s)
>
> | File | Before | After | Δ | New | Fixed |
> |---|---|---|---|---|---|
> | `src/pricing.html` | 82 | 71 | -11 | 2 | 1 |
>
> **FAIL** — src/pricing.html scored 71 (below --min-score 80)

### Tuning the gate

| Flag | Default | Meaning |
|---|---|---|
| (fail on new critical/high) | on | Any new critical or high finding fails the check; `--no-fail-new` disables |
| `--min-score N` | off | Every changed file must score at least N |
| `--max-drop N` | off | No file may drop more than N points vs the base branch |
| `--ext .html,.htm` | `.html,.htm` | File types to check |

### Notes and honest limits

- **Findings attach at file level.** The engine evaluates parsed page
  data, not source positions, so annotations point at the file rather
  than an exact line.
- **Markdown is excluded by default.** Raw `.md` is not renderable HTML —
  docs sites should lint the *built* output (e.g. `--dir ./dist` after
  your static site generator runs, in the same workflow).
- **Deleted files are skipped; new files are graded as-is** — every
  finding on a brand-new file counts as "new".
- **Local use works too:** `python scripts/seo_pr_check.py --base main
  --all-changed` reviews your branch before you push.

## What it deliberately does not check

Anything that needs live data — rankings, volumes, backlinks, competitor
movement. A pull request cannot tell you those. The PR gate answers one
question: *did this change break anything the 54 deterministic rules
verify?* The live-data side stays where it belongs: scheduled `watch`
runs and audits, feeding the recommendation store.
