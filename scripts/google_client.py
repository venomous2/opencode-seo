"""Optional Google API client CLI for the OpenCode SEO Suite.

This layer is OPTIONAL. The suite works with DataForSEO alone; Google APIs
add first-party field data when credentials are available.

Tiers (see seo_config.google_tier):
    Tier 0  GOOGLE_API_KEY             -> pagespeed, crux, crux-history
    Tier 1  + service account JSON     -> gsc-queries, gsc-inspect, gsc-sitemaps
    Tier 2  + GA4 property ID          -> ga4-organic

Usage:
    python scripts/google_client.py <command> [options]

Commands:
    pagespeed      PageSpeed Insights lab + field data for a URL
    crux           CrUX field data (origin or URL) - real Core Web Vitals
    crux-history   CrUX 25-week history (origin or URL)
    gsc-queries    Search Analytics: top queries/pages with clicks, CTR, position
    gsc-inspect    URL Inspection: index status of a URL
    gsc-sitemaps   List submitted sitemaps and their status
    ga4-organic    GA4 organic sessions by landing page
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

try:
    from seo_config import google_tier
except ImportError:
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
    from seo_config import google_tier

PSI_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
CRUX_URL = "https://chromeuxreport.googleapis.com/v1/records:queryRecord"
CRUX_HISTORY_URL = "https://chromeuxreport.googleapis.com/v1/records:queryHistoryRecord"
GSC_SEARCHANALYTICS = "https://www.googleapis.com/webmasters/v3/sites/{site}/searchAnalytics/query"
GSC_INSPECT = "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect"
GSC_SITEMAPS = "https://www.googleapis.com/webmasters/v3/sites/{site}/sitemaps"
GA4_RUN = "https://analyticsdata.googleapis.com/v1beta/properties/{prop}:runReport"

SCOPES = [
    "https://www.googleapis.com/auth/webmasters.readonly",
    "https://www.googleapis.com/auth/analytics.readonly",
]


class GoogleError(RuntimeError):
    pass


def _get(url: str, params: dict[str, str]) -> dict[str, Any]:
    full = url + "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(full, timeout=60) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        raise GoogleError(f"HTTP {exc.code}: {exc.read().decode(errors='replace')[:400]}") from exc


def _post(url: str, body: dict[str, Any], *, key: str | None = None,
          token: str | None = None) -> dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if key:
        url += ("&" if "?" in url else "?") + "key=" + key
    request = urllib.request.Request(url, data=json.dumps(body).encode(),
                                     headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        raise GoogleError(f"HTTP {exc.code}: {exc.read().decode(errors='replace')[:400]}") from exc


def _service_account_token(sa_path: str) -> str:
    """Mint an OAuth access token from a service account JSON key.

    Uses google-auth if installed; otherwise fails with guidance.
    """
    try:
        from google.oauth2 import service_account  # type: ignore
        from google.auth.transport.requests import Request  # type: ignore
    except ImportError as exc:
        raise GoogleError(
            "Tier 1/2 Google APIs need google-auth: pip install google-auth"
        ) from exc
    credentials = service_account.Credentials.from_service_account_file(
        sa_path, scopes=SCOPES)
    credentials.refresh(Request())
    return credentials.token


def _require_key(tier: dict[str, Any]) -> str:
    key = tier.get("api_key")
    if not key:
        raise GoogleError("GOOGLE_API_KEY not set (Tier 0). See docs/GOOGLE-APIS.md")
    return str(key)


def _require_tier(tier: dict[str, Any], level: int) -> None:
    if int(tier.get("tier", -1)) < level:
        raise GoogleError(
            f"This command needs Google tier {level}; current tier is "
            f"{tier.get('tier')}. See docs/GOOGLE-APIS.md for setup.")


def run(command: str, args: argparse.Namespace) -> dict[str, Any]:
    tier = google_tier()

    if command == "pagespeed":
        key = _require_key(tier)
        # One category per request keeps the URL simple; the default PSI
        # category set already includes performance + seo signals.
        return _get(PSI_URL, {
            "url": args.url, "key": key, "strategy": args.strategy,
        })

    if command == "crux":
        key = _require_key(tier)
        body: dict[str, Any] = {"formFactor": args.form_factor}
        body["origin" if args.origin else "url"] = args.target
        return _post(CRUX_URL, body, key=key)

    if command == "crux-history":
        key = _require_key(tier)
        body = {"formFactor": args.form_factor}
        body["origin" if args.origin else "url"] = args.target
        return _post(CRUX_HISTORY_URL, body, key=key)

    if command == "gsc-queries":
        _require_tier(tier, 1)
        token = _service_account_token(str(tier["service_account_json"]))
        site = urllib.parse.quote(args.site, safe="")
        return _post(GSC_SEARCHANALYTICS.format(site=site), {
            "startDate": args.start, "endDate": args.end,
            "dimensions": ["query", "page"],
            "rowLimit": args.limit,
        }, token=token)

    if command == "gsc-inspect":
        _require_tier(tier, 1)
        token = _service_account_token(str(tier["service_account_json"]))
        return _post(GSC_INSPECT, {
            "inspectionUrl": args.url, "siteUrl": args.site,
        }, token=token)

    if command == "gsc-sitemaps":
        _require_tier(tier, 1)
        token = _service_account_token(str(tier["service_account_json"]))
        site = urllib.parse.quote(args.site, safe="")
        url = GSC_SITEMAPS.format(site=site)
        headers = {"Authorization": f"Bearer {token}"}
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers),
                                        timeout=60) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            raise GoogleError(f"HTTP {exc.code}: {exc.read().decode(errors='replace')[:400]}") from exc

    if command == "ga4-organic":
        _require_tier(tier, 2)
        token = _service_account_token(str(tier["service_account_json"]))
        url = GA4_RUN.format(prop=tier["ga4_property_id"])
        return _post(url, {
            "dateRanges": [{"startDate": args.start, "endDate": args.end}],
            "dimensions": [{"name": "landingPagePlusQueryString"}],
            "metrics": [{"name": "sessions"}, {"name": "engagedSessions"},
                        {"name": "conversions"}],
            "dimensionFilter": {
                "filter": {"fieldName": "sessionDefaultChannelGroup",
                           "stringFilter": {"value": "Organic Search"}}
            },
            "limit": args.limit,
        }, token=token)

    raise GoogleError(f"Unknown command: {command}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="google_client",
                                     description="Optional Google API client CLI")
    parser.add_argument("command", choices=[
        "pagespeed", "crux", "crux-history",
        "gsc-queries", "gsc-inspect", "gsc-sitemaps", "ga4-organic"])
    parser.add_argument("--url", help="full URL")
    parser.add_argument("--target", help="URL or origin for CrUX")
    parser.add_argument("--origin", action="store_true",
                        help="treat --target as an origin (CrUX)")
    parser.add_argument("--site", help="GSC property, e.g. sc-domain:example.com")
    parser.add_argument("--strategy", choices=["mobile", "desktop"], default="mobile")
    parser.add_argument("--form-factor", dest="form_factor",
                        choices=["PHONE", "DESKTOP", "TABLET"], default="PHONE")
    parser.add_argument("--start", default="28daysAgo")
    parser.add_argument("--end", default="today")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    try:
        result = run(args.command, args)
    except GoogleError as exc:
        print(json.dumps({"error": str(exc)}))
        return 1
    print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
