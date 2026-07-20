# DataForSEO Setup

DataForSEO is the suite's **mandatory** live-data backbone. Every keyword
volume, SERP result, ranking, and backlink number comes from a real API call.

## 1. Get credentials

1. Register at https://app.dataforseo.com/register
2. Your **login** is your account email; your **API password** is shown in
   the dashboard under API access (it is *not* your account password).
3. Add credit — most endpoints cost fractions of a cent to a few cents per
   call. A typical keyword research session costs well under $0.25.

## 2. Provide credentials (any one method)

Checked in priority order:

| Priority | Method | How |
|---|---|---|
| 1 | Environment variables | `DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD` |
| 2 | Project `.env` | Copy `.env.example` → `.env`, fill in values |
| 3 | User config file | `~/.config/opencode/seo-suite/credentials.json` |

Credentials file format:
```json
{
  "DATAFORSEO_LOGIN": "you@example.com",
  "DATAFORSEO_PASSWORD": "your_api_password"
}
```

Verify:
```bash
python scripts/seo_config.py status
```

## 3. Sandbox mode (free testing)

Every `dfs_client.py` command accepts `--sandbox`, which calls DataForSEO's
sandbox (fake data, no cost) — handy for trying the suite:

```bash
python scripts/dfs_client.py serp --keyword "coffee" --sandbox --pretty
```

## 4. What the suite uses

| CLI command | DataForSEO API | Typical cost* |
|---|---|---|
| `serp` | SERP API (Google organic, live) | ~$0.0006-0.002 |
| `volume` | Keywords Data (search volume) | ~$0.01/list |
| `ideas`, `related` | Labs (keyword ideas / related) | ~$0.01 |
| `ranked`, `competitors`, `intersection` | Labs (domain analytics) | ~$0.01-0.1 |
| `backlinks`, `refdomains`, `anchors` | Backlinks API | ~$0.02 |
| `onpage`, `lighthouse` | On-Page API | ~$0.001-0.01 |
| `content`, `mentions` | Content Analysis / AI endpoints | ~$0.01 |
| `business`, `amazon`, `whois` | Business Data / Merchant / Domain Analytics | ~$0.001-0.01 |

*Costs are indicative; check https://dataforseo.com/pricing for current rates.

## 5. Troubleshooting

- **"DataForSEO credentials not found"** — run
  `python scripts/seo_config.py status` to see which sources were checked.
- **401 / authentication errors** — you used your account password instead of
  the API password from the dashboard.
- **402 / payment errors** — top up your DataForSEO balance.
- **`task_errors: [40501 Invalid Field: 'location_name']`** — the location
  name isn't one DataForSEO recognises. Use full names: "United Kingdom",
  "United States". Common aliases (UK, USA, GB…) are auto-corrected.
- **Timeout on large pulls** — lower `--limit` (default 100).
- **`tasks_error: 1` with zero cost** — the request reached DataForSEO but a
  task parameter was rejected. Read `task_errors` in the output for the
  exact reason; it is NOT a credentials problem.
