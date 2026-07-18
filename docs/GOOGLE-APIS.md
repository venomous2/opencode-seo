# Google APIs (optional enrichment)

The suite works fully with DataForSEO alone. Google APIs add **first-party
field data** when you have credentials. Four capabilities, three tiers:

| Tier | You add | Unlocks |
|---|---|---|
| 0 | `GOOGLE_API_KEY` | PageSpeed Insights, CrUX + CrUX History (real field CWV) |
| 1 | + service account JSON | Search Console (queries, URL inspection, sitemaps) |
| 2 | + `GA4_PROPERTY_ID` | GA4 organic traffic by landing page |

Check your current tier:
```bash
python scripts/seo_config.py status
```

## Tier 0 — API key (5 minutes)

1. Google Cloud Console → create a project (or reuse one).
2. Enable **PageSpeed Insights API** and **Chrome UX Report API**.
3. Create an API key (Credentials → Create credentials → API key).
4. Set `GOOGLE_API_KEY` in your `.env` or environment.

```bash
python scripts/google_client.py pagespeed --url https://example.com --pretty
python scripts/google_client.py crux --target https://example.com --origin --pretty
python scripts/google_client.py crux-history --target https://example.com --origin --pretty
```

## Tier 1 — Service account (Search Console)

1. Cloud Console → create a **service account**, download its JSON key.
2. Enable **Google Search Console API**.
3. In Search Console, add the service account's email as a **user** on your
   property (Settings → Users and permissions).
4. Set `GOOGLE_SERVICE_ACCOUNT_JSON` to the JSON file path.
5. Install the extra dependency: `pip install google-auth`.

```bash
python scripts/google_client.py gsc-queries --site sc-domain:example.com --pretty
python scripts/google_client.py gsc-inspect --url https://example.com/page --site sc-domain:example.com --pretty
python scripts/google_client.py gsc-sitemaps --site sc-domain:example.com --pretty
```

> For `https://example.com`-style URL-prefix properties, pass the full
> property URL as `--site` instead of the `sc-domain:` form.

## Tier 2 — GA4

1. Enable **Google Analytics Data API (GA4)** in the same project.
2. Add the service account email as a **Viewer** on your GA4 property.
3. Set `GA4_PROPERTY_ID` (Admin → Property settings → numeric ID).

```bash
python scripts/google_client.py ga4-organic --start 90daysAgo --pretty
```

## Privacy notes

- Credentials stay local: `.env` (gitignored) or
  `~/.config/opencode/seo-suite/credentials.json` with user-only permissions.
- The service account needs **read-only** scopes; never grant edit access.
- Nothing is sent anywhere except the official Google API endpoints.
