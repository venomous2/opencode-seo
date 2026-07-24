"""Honest SEO forecasting for the OpenCode SEO Suite.

Estimates monthly organic clicks for keywords at a target ranking position
using DataForSEO search volumes and a position-based CTR model. Deliberately
conservative and fully transparent: the CTR curve, the uncertainty band and
every assumption are printed in the output so clients can see exactly how
the numbers were produced. This is scenario planning, not a promise.

Model:
    clicks(month) = search_volume x CTR(position) x scale

    CTR curve (blended desktop, no SERP-feature adjustment):
        pos 1-10: per-position rates below; 11-20: 0.4%; 21-50: 0.1%
    Uncertainty band: low = 0.6x, high = 1.4x the expected estimate
    scale: flat discount for SERP features / brand effects (default 1.0)

Usage:
    python scripts/seo_forecast.py --domain example.com \
        --keywords "espresso grinder,best grinder" --target-position 3
    python scripts/seo_forecast.py --domain example.com --snapshot
        (keywords + volumes from the latest drift snapshot when present)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

import drift_store  # noqa: E402

SCRIPTS_DIR = Path(__file__).resolve().parent

CTR_CURVE = {1: 0.25, 2: 0.13, 3: 0.08, 4: 0.055, 5: 0.040,
             6: 0.030, 7: 0.023, 8: 0.018, 9: 0.014, 10: 0.010}
CTR_PAGE_TWO = 0.004
CTR_BEYOND = 0.001
BAND_LOW, BAND_HIGH = 0.6, 1.4

ASSUMPTIONS = {
    "model": "clicks = volume x CTR(position) x scale",
    "ctr_curve": {str(k): v for k, v in sorted(CTR_CURVE.items())},
    "ctr_11_to_20": CTR_PAGE_TWO,
    "ctr_21_plus": CTR_BEYOND,
    "uncertainty_band": {"low": BAND_LOW, "high": BAND_HIGH},
    "volumes": "DataForSEO estimates; real volumes vary with seasonality",
    "not_modelled": ["SERP features suppressing organic CTR",
                     "branded vs generic intent", "seasonality",
                     "conversion rate or revenue"],
    "honesty": "scenario planning with stated assumptions - not a promise "
               "of results",
}


def ctr(position: float) -> float:
    if position < 1:
        position = 1
    if position <= 10:
        return CTR_CURVE[int(round(position))]
    if position <= 20:
        return CTR_PAGE_TWO
    return CTR_BEYOND


def estimate(volume: float, position: float,
             scale: float = 1.0) -> dict[str, int]:
    expected = volume * ctr(position) * scale
    return {"low": round(expected * BAND_LOW),
            "expected": round(expected),
            "high": round(expected * BAND_HIGH)}


def _dfs(args: list[str], sandbox: bool = False,
         timeout: int = 120) -> dict[str, Any]:
    cmd = [sys.executable, str(SCRIPTS_DIR / "dfs_client.py"), *args]
    if sandbox:
        cmd.append("--sandbox")
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          timeout=timeout)
    if proc.returncode != 0:
        detail = (proc.stdout or proc.stderr).strip()[:300]
        raise RuntimeError(f"dfs_client failed: {detail}")
    return json.loads(proc.stdout)


def volume_lookup(keywords: list[str], location: str, language: str,
                  sandbox: bool = False) -> dict[str, float]:
    """Search volume per keyword via DataForSEO (billed, ledgered)."""
    payload = _dfs(["volume", "--keyword", ",".join(keywords),
                    "--location", location, "--language", language], sandbox)
    volumes: dict[str, float] = {}
    for result in payload.get("result") or []:
        for item in (result or {}).get("items") or []:
            keyword = item.get("keyword")
            volume = item.get("search_volume") \
                or (item.get("keyword_info") or {}).get("search_volume")
            if keyword and isinstance(volume, (int, float)):
                volumes[keyword] = volume
    return volumes


def forecast(domain: str, keywords: dict[str, float],
             current: dict[str, dict[str, Any]], target_position: int,
             scale: float) -> dict[str, Any]:
    """keywords: kw -> monthly volume; current: kw -> ranking entry."""
    rows = []
    total_now = total_target = 0
    for keyword, volume in sorted(keywords.items(),
                                  key=lambda kv: -kv[1]):
        entry = current.get(keyword)
        position = entry.get("position") if entry else None
        now_clicks = estimate(volume, position, scale) if position else None
        target_clicks = estimate(volume, target_position, scale)
        total_now += now_clicks["expected"] if now_clicks else 0
        total_target += target_clicks["expected"]
        rows.append({
            "keyword": keyword, "volume": int(volume),
            "current_position": position,
            "current_clicks": now_clicks,
            "target_position": target_position,
            "target_clicks": target_clicks,
            "uplift_expected": target_clicks["expected"]
            - (now_clicks["expected"] if now_clicks else 0),
        })
    return {
        "domain": domain,
        "target_position": target_position,
        "scale": scale,
        "keywords": rows,
        "totals": {
            "current_clicks_expected": total_now,
            "target_clicks_expected": total_target,
            "uplift_expected": total_target - total_now,
            "uplift_low": round(
                sum(r["target_clicks"]["low"] for r in rows)
                - total_now),
            "uplift_high": round(
                sum(r["target_clicks"]["high"] for r in rows)
                - total_now),
        },
        "assumptions": ASSUMPTIONS,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="seo_forecast",
        description="CTR-based click forecasting with stated assumptions")
    parser.add_argument("--domain", required=True)
    parser.add_argument("--keywords",
                        help="comma-separated keywords; default: the latest "
                             "drift snapshot's tracked keywords")
    parser.add_argument("--target-position", type=int, default=3)
    parser.add_argument("--scale", type=float, default=1.0,
                        help="flat CTR discount, e.g. 0.8 for feature-heavy "
                             "SERPs")
    parser.add_argument("--location", default="United States")
    parser.add_argument("--language", default="English")
    parser.add_argument("--snapshot", action="store_true",
                        help="append the forecast summary to the drift store")
    parser.add_argument("--sandbox", action="store_true")
    args = parser.parse_args(argv)

    domain = args.domain.strip().lower()

    current: dict[str, dict[str, Any]] = {}
    snapshot_volumes: dict[str, float] = {}
    snapshots = drift_store.list_snapshots(domain)
    if snapshots:
        latest = drift_store.load(domain, snapshots[-1])
        for entry in latest.get("rankings") or []:
            current[entry["keyword"]] = entry
            vol = entry.get("search_volume")
            if isinstance(vol, (int, float)):
                snapshot_volumes[entry["keyword"]] = vol

    if args.keywords:
        wanted = [k.strip() for k in args.keywords.split(",") if k.strip()]
        have = {k: v for k, v in snapshot_volumes.items() if k in wanted}
        need = [k for k in wanted if k not in have]
        try:
            fetched = volume_lookup(need, args.location, args.language,
                                    args.sandbox) if need else {}
        except (RuntimeError, json.JSONDecodeError) as exc:
            print(json.dumps({"error": str(exc)}))
            return 1
        volumes = {**fetched, **have}
        missing = [k for k in wanted if k not in volumes]
        if missing:
            print(json.dumps({"error": "no volume data for: "
                                       + ", ".join(missing)}))
            return 1
    else:
        if not snapshot_volumes:
            print(json.dumps({
                "error": "no keywords given and the latest drift snapshot "
                         "has no search volumes. Pass --keywords (a volume "
                         "pull will be billed) or run a watch/audit that "
                         "captures volumes first."}))
            return 1
        volumes = snapshot_volumes

    result = forecast(domain, volumes, current, args.target_position,
                      args.scale)

    if args.snapshot:
        drift_store.save(domain, {"forecast": {
            "target_position": args.target_position,
            "keywords": len(result["keywords"]),
            "current_clicks_expected":
                result["totals"]["current_clicks_expected"],
            "target_clicks_expected":
                result["totals"]["target_clicks_expected"],
            "uplift_expected": result["totals"]["uplift_expected"],
        }})
        result["snapshot_saved"] = True

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
