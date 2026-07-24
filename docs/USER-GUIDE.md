# User guide

Everything the suite does, and how to get the most out of it.

New here? Do [GETTING-STARTED.md](GETTING-STARTED.md) first — it takes 15
minutes and leaves you with monitoring switched on.

## The mental model

Three ideas explain the whole suite:

**1. The deterministic engine does everything checkable without taste.**
54 YAML rules, a citation scorer, the linter and the fix engine — pure
Python, zero model calls, identical answers no matter which LLM you run.
That is why the suite can honestly say "verified", not "the model thinks".

**2. The skills add the taste.** 87 markdown skills encode procedure and
judgement: audits, briefs, strategy, AI-search work. They never fabricate
metrics — live numbers come from DataForSEO, and they cite their source.

**3. The stores remember.** Five plain-JSON stores on your machine hold
your recommendation queue, activity timeline, health snapshots, spend
ledger and project context. Skills read and write them, so every session
starts where the last one ended instead of from scratch.

The loop that ties it together:

```
watch (scheduled) → stores → /briefing → you act → fixes auto-resolve
```

## Commands at a glance

Slash commands run inside OpenCode. Or just talk naturally — "audit my
site", "why don't I rank for X" — the `seo-suite` orchestrator routes you.

| Command | What it does | API spend |
|---|---|---|
| `/briefing <domain>` | Morning feed: health, changes, today's top actions | None |
| `/site-audit <domain>` | Full audit: 4 specialist agents, scorecard, branded report | ~£0.05–0.30 |
| `/keyword-research <seed>` | Live volumes, ideas, related keywords | Low |
| `/serp-analysis <keyword>` | Who ranks and why, SERP features | Low |
| `/keyword-gap <domain>` | Keywords competitors rank for and you don't | Low |
| `/new-post <topic>` | Research → publish-ready content brief | Low |
| `/content-refresh <domain>` | Triage decaying/thin/overlapping content | Medium |
| `/compare <domain> <rival>` | Side-by-side: authority, keywords, gaps, readiness | Low |
| `/cro <url>` | Conversion audit: deterministic checks + experiment plan | Low |
| `/citation-check <url>` | AI citation readiness score (+ mention baseline) | Low |
| `/schema <type>` | Generate JSON-LD structured data | None |

Typical DataForSEO spend for a full weekly monitoring run: a few pence.
Every billed call is ledgered — see the cost ledger below.

## The five stores

All under `~/.config/opencode/seo-suite/`. All plain JSON you can read.

### 1. Recommendation store — the queue (`recommendations/`)

Every finding from any source, with a status lifecycle:
`open → accepted → done`, plus `ignored` (never nagged about again) and
`resolved` (auto-detected as fixed). Re-finding a done issue reopens it as
a regression.

```
python scripts/recommend_store.py list --domain example.com
python scripts/recommend_store.py summary --domain example.com
python scripts/recommend_store.py set --domain example.com --id abc123 --status accepted
python scripts/recommend_store.py set --domain example.com --id abc123 --status ignored --note "client declined"
python scripts/recommend_store.py history --domain example.com --id abc123
```

**Tip:** the list is priority-ordered — impact × confidence, boosted for
auto-fixable items and persistent problems. Work top-down.

### 2. Event timeline (`events/`)

Chronological feed of everything the suite did: findings raised, statuses
changed, lint saves, snapshots, watch runs. Add your own notes so the
timeline tells the whole story:

```
python scripts/event_log.py log --domain example.com --type note --summary "Published espresso guide"
python scripts/event_log.py list --domain example.com --limit 20
```

### 3. Drift snapshots (`drift/`)

Dated rankings/scores/backlinks per domain. Audits and watch save them;
compare any two:

```
python scripts/drift_store.py compare --domain example.com
python scripts/drift_store.py chart --domain example.com    # ready-made chart blocks for reports
```

### 4. Cost ledger (`costs.jsonl`)

Every billed DataForSEO call, one JSON line each:

```
python scripts/cost_ledger.py report --by command
```

### 5. Project memory (`seo-project.yml` / `clients/*.yml`)

Your site's context: audience, brand voice, competitors, goals, entities.
Workflows load it automatically. `--client <name>` profiles for agencies.

## Working the queue

The intended weekly workflow:

1. **`/briefing`** each morning — the top actions, already prioritised.
2. **Act on one**: fix it yourself, or let the fix engine handle the
   mechanical findings: `python scripts/seo_fix.py --url <page>` previews
   the patches; add `--apply` to write them (with `.bak` backups and a
   re-lint to prove the score improved).
3. **Mark the decision**: `recommend_store.py set ... --status accepted`
   (or `ignored` with a note). The next audit sees the decision instead of
   re-raising the finding.
4. **Watch it close itself**: the next `seo_lint --save` or watch run
   auto-resolves fixed findings. They land in "Recent wins".

**Tip:** `seo-task-generator` turns the queue into tracker-ready tickets
(P1–P4, impact/effort, acceptance criteria) and marks accepted items back
in the store.

## Forecasting and proving impact

**Before the work — what's it worth?**

```
python scripts/seo_forecast.py --domain example.com --target-position 3
python scripts/seo_forecast.py --domain example.com --keywords "espresso grinder,burr grinder" --snapshot
```

Volume × position-CTR with low/expected/high bands. Every assumption —
the exact CTR curve, the discount factor, what is *not* modelled — prints
with the numbers. Scenario planning, honestly labelled.

**After the work — did it move anything?**

```
python scripts/impact_report.py --domain example.com --days 90
```

Joins each completed recommendation to the snapshots before and after it:
position movement for keyword fixes, URL-level movement for page fixes.
Verdicts come labelled "association, not causation" — use them in client
reports as evidence with integrity.

## Reports and dashboards

Every markdown report becomes client-facing with one command (branded
HTML + PDF + executive one-pager):

```
python scripts/report_publish.py SEO-AUDIT-example.com-2026-07-24.md
```

The always-current overview:

```
python scripts/project_dashboard.py --domain example.com
```

`DASHBOARD-<domain>-<date>.html`: health trend, action queue, wins,
activity timeline, 30-day spend. Regenerate any time; it reads the stores.

## Agency mode

```
python scripts/project_memory.py --client acme --init
python scripts/project_memory.py --list-clients
```

Per-client YAML profiles keep brands, competitors and goals separate. All
stores key by domain, so one install serves the whole portfolio; the cost
ledger shows spend per period for client billing.

## CI quality gate

```
python scripts/seo_lint.py --url https://staging.example.com --min-score 80
```

Exit code 1 below the threshold — drop it into your pipeline and no page
ships below your floor. For SPAs, `--render auto` renders JavaScript first
so you lint what Google sees.

## Tips and tricks

- **Start free.** `seo_lint --save`, `/schema` and the briefing cost
  nothing. Do those before any paid pulls.
- **The cache is your budget.** Repeat research within the TTL hits the
  disk cache, not the API. `--no-cache` exists for when you truly need
  fresh data.
- **Learn the API with `--sandbox`.** Most DataForSEO commands accept
  `--sandbox` — free fake data, real shapes.
- **Be specific in chat.** "Audit example.com for a Shopify migration next
  month" beats "audit example.com" — project memory plus a sentence of
  context changes the output noticeably.
- **Log your own work.** `event_log.py log --type note` for publishes,
  releases and campaigns. The impact report and dashboard get smarter.
- **Don't ignore silently.** Mark `ignored` with a note instead of leaving
  findings open forever — the queue stays honest and the note reminds
  future-you why.
- **One domain key everywhere.** Always use the bare domain
  (`example.com`, not `https://www.example.com`) so the stores line up.
- **Keep stores out of git.** They live in your home directory by design —
  commit `seo-project.yml`, not the stores.
- **British English is the default** in all analysis and reports. Ask for
  another variant if you need one; reports always end with the attribution
  footer.

## Troubleshooting

| Symptom | Likely fix |
|---|---|
| `DataForSEO status .... NOT READY` | Credentials — see [DATAFORSEO-SETUP.md](DATAFORSEO-SETUP.md); check env var names exactly |
| Skills missing after update | Restart OpenCode — skills load at startup |
| "Missing content" on a JS-heavy site | Re-lint with `--render auto` (renders first, then checks) |
| Shell errors about `head`/`grep`/`&&` | You used bashisms — OpenCode on Windows is PowerShell |
| Unexpected API spend | `cost_ledger.py report --by command`; shorten research loops, lean on the cache |
| Store looks wrong | Everything is JSONL — open the file, delete bad lines, re-run |

Deeper internals: [ARCHITECTURE.md](ARCHITECTURE.md) ·
[RULE-ENGINE.md](RULE-ENGINE.md) · [REPORTS.md](REPORTS.md) ·
[MCP.md](MCP.md)
