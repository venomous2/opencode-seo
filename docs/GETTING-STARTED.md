# Getting started

From download to a genuinely useful SEO answer in about 15 minutes.

This guide assumes you have never used the suite before. By the end you
will have run your first check, your first audit, and set up monitoring so
the suite keeps working between sessions.

## 1. What you need

| Thing | Why | Cost |
|---|---|---|
| **OpenCode** | The suite runs inside it | Free |
| **Python 3.10+** | The data layer | Free |
| **DataForSEO account** | Live volumes, rankings, backlinks — the suite never guesses these | Pay-as-you-go; pennies per audit |

Google APIs (Search Console, GA4, PageSpeed) are optional enrichment — the
suite works fully without them. Add them later if you want them
([GOOGLE-APIS.md](GOOGLE-APIS.md)).

## 2. Install (2 minutes)

**Windows (PowerShell):**

```powershell
git clone https://github.com/venomous2/opencode-seo.git
powershell -ExecutionPolicy Bypass -File opencode-seo\install.ps1
```

**macOS / Linux:**

```bash
git clone https://github.com/venomous2/opencode-seo.git
bash opencode-seo/install.sh
```

The installer copies the skills, agents and commands into OpenCode's
config, sets up an isolated Python environment, and offers to store your
DataForSEO credentials (get them at
<https://app.dataforseo.com/register> → API access).

**Restart OpenCode afterwards** — skills load at startup.

Verify the data layer is live:

```
python scripts/seo_config.py status
```

You want `DataForSEO status .... READY`. If not,
[DATAFORSEO-SETUP.md](DATAFORSEO-SETUP.md) walks through it.

## 3. Prove it works — free, 30 seconds

Before spending a penny on API calls, run the deterministic engine against
your homepage. This costs nothing and takes seconds:

```
python scripts/seo_lint.py --url https://your-site.com --save --domain your-site.com
```

You just did two things: linted the page against 54 self-testing rules,
and saved the findings into your **recommendation store** — the suite's
memory of what needs fixing.

Look at your queue:

```
python scripts/recommend_store.py list --domain your-site.com
```

Every finding has a severity, a plain-English "why", fix guidance, and a
priority score. This is the moment the suite starts working for you.

## 4. Your first briefing

In OpenCode, type:

```
/briefing your-site.com
```

Thirty seconds, no API spend: health, what needs attention, and today's
top actions — read straight from the stores you just populated. This is
the command you will use every morning.

## 5. Your first full audit

```
/site-audit your-site.com
```

About 10–15 minutes. The workflow pulls live rankings, competitors,
backlinks and on-page data from DataForSEO, dispatches four specialist
analysts in parallel (technical, content, competitive, AI-search), and
synthesises a 0–100 scorecard. You get:

- A prioritised action plan in chat (top 10, with the "why" attached)
- `SEO-AUDIT-<domain>-<date>.md` plus branded **HTML, PDF and an executive
  one-pager** — ready to send a client as-is
- A drift snapshot saved, so the next audit can show what changed
- Every finding persisted in the recommendation store

**Tip:** run the audit from a folder you own (e.g. your client's project
folder), and set `SEO_REPORTS_DIR` so reports file themselves neatly:

```powershell
# Windows (permanent, user-level)
[Environment]::SetEnvironmentVariable("SEO_REPORTS_DIR", "C:\SEO-Reports", "User")
```

```bash
# macOS / Linux — add to your shell profile
export SEO_REPORTS_DIR="$HOME/seo-reports"
```

Reports then land in `$SEO_REPORTS_DIR/<domain>/` instead of your current
directory.

## 6. Tell the suite about your site

```
python scripts/project_memory.py --init
```

This creates `seo-project.yml`: your audience, brand voice, competitors,
goals and key entities. Every workflow reads it, so briefs sound like your
brand and competitive checks know who your rivals are — without you
repeating yourself. Fill in what you know; every field is optional.

Agency? Use per-client profiles instead:
`python scripts/project_memory.py --client acme --init`.

## 7. Turn on monitoring

This is the step that turns a tool into a system:

```
python scripts/watch.py schedule --domain your-site.com --profile weekly
```

It prints the exact Windows Task Scheduler (`schtasks`) or cron line for
your machine — paste it, and every week the suite will automatically:

- Re-lint your key pages (fixed findings resolve themselves; regressions
  reopen)
- Diff your rankings (losses become recommendations with click estimates;
  recoveries close themselves)
- Snapshot backlinks and competitor keyword growth
- Log it all to your timeline

Nothing runs in the background from us — your operating system does the
scheduling, and every run reports its own API cost.

## 8. Your rhythm from now on

```
Each morning     /briefing                     # 30 seconds: what changed, what to do
Monday (auto)    watch runs                    # fresh rankings, lint, competitors
When you act     fix something → it resolves itself on the next lint run
Monthly          python scripts/project_dashboard.py --domain your-site.com
Any time         ask OpenCode anything — "why has traffic dropped?",
                 "what should we publish next?", "compare me to rival.com"
```

## 9. Where everything lives

| What | Where |
|---|---|
| Your recommendation queue | `~/.config/opencode/seo-suite/recommendations/` |
| Your activity timeline | `~/.config/opencode/seo-suite/events/` |
| Ranking/health snapshots | `~/.config/opencode/seo-suite/drift/` |
| API spend ledger | `~/.config/opencode/seo-suite/costs.jsonl` |
| Generated reports | `$SEO_REPORTS_DIR/<domain>/` |
| Project context | `seo-project.yml` in your project folder |

All plain JSON/JSONL files on your machine. Yours to read, back up, or
delete — no cloud account, no lock-in.

## Next: the full reference

**[USER-GUIDE.md](USER-GUIDE.md)** — every command, the five stores
explained, queue workflow, forecasting, proving impact, agency mode, CI
gates, and a page of tips.
