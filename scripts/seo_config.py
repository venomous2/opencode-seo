"""Credential and configuration resolution for the OpenCode SEO Suite.

Resolution order (highest priority first):

DataForSEO (mandatory):
    1. Environment variables DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD
    2. A .env file in the current working directory (or any parent directory)
    3. ~/.config/opencode/seo-suite/credentials.json

Google APIs (optional, tiered):
    Tier 0 - GOOGLE_API_KEY                      (PageSpeed Insights, CrUX)
    Tier 1 - GOOGLE_SERVICE_ACCOUNT_JSON (path)  (+ Search Console, Indexing)
    Tier 2 - GA4_PROPERTY_ID                     (+ GA4 organic traffic)

Run ``python scripts/seo_config.py status`` to see what is configured.
"""

from __future__ import annotations

import json
import os
import stat
import sys
from pathlib import Path

SUITE_DIR = Path.home() / ".config" / "opencode" / "seo-suite"
CREDENTIALS_FILE = SUITE_DIR / "credentials.json"

ENV_DFS_LOGIN = "DATAFORSEO_LOGIN"
ENV_DFS_PASSWORD = "DATAFORSEO_PASSWORD"
ENV_GOOGLE_API_KEY = "GOOGLE_API_KEY"
ENV_GOOGLE_SA_JSON = "GOOGLE_SERVICE_ACCOUNT_JSON"
ENV_GA4_PROPERTY = "GA4_PROPERTY_ID"


class ConfigError(RuntimeError):
    """Raised when required configuration is missing."""


def _find_dotenv(start: Path | None = None) -> Path | None:
    """Walk upward from *start* looking for a .env file."""
    current = (start or Path.cwd()).resolve()
    for directory in (current, *current.parents):
        candidate = directory / ".env"
        if candidate.is_file():
            return candidate
    return None


def _load_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip().strip('"').strip("'")
        values[key.strip()] = value
    return values


def _load_credentials_file() -> dict[str, str]:
    if not CREDENTIALS_FILE.is_file():
        return {}
    try:
        data = json.loads(CREDENTIALS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ConfigError(f"Cannot parse {CREDENTIALS_FILE}: {exc}") from exc
    return {str(k): str(v) for k, v in data.items() if v is not None}


def _merged_env() -> dict[str, str]:
    """Merge the three credential sources in priority order."""
    merged: dict[str, str] = {}
    file_values = _load_credentials_file()
    merged.update(file_values)
    dotenv = _find_dotenv()
    if dotenv:
        for key, value in _load_dotenv(dotenv).items():
            merged[key] = value  # .env overrides credentials file
    for key in (
        ENV_DFS_LOGIN,
        ENV_DFS_PASSWORD,
        ENV_GOOGLE_API_KEY,
        ENV_GOOGLE_SA_JSON,
        ENV_GA4_PROPERTY,
    ):
        if os.environ.get(key):
            merged[key] = os.environ[key]  # real env wins overall
    return merged


def dataforseo_credentials() -> tuple[str, str]:
    """Return (login, password) for DataForSEO or raise a helpful error."""
    env = _merged_env()
    login = env.get(ENV_DFS_LOGIN)
    password = env.get(ENV_DFS_PASSWORD)
    if login and password:
        return login, password
    raise ConfigError(
        "DataForSEO credentials not found. Set them via one of:\n"
        f"  1. Environment variables: {ENV_DFS_LOGIN} / {ENV_DFS_PASSWORD}\n"
        "  2. A .env file in this project (see .env.example)\n"
        f"  3. {CREDENTIALS_FILE}  (created by install.ps1 / install.sh)\n"
        "Get credentials at https://app.dataforseo.com/register"
    )


def google_tier() -> dict[str, object]:
    """Describe which optional Google API tiers are available."""
    env = _merged_env()
    tier = -1
    api_key = env.get(ENV_GOOGLE_API_KEY)
    sa_json = env.get(ENV_GOOGLE_SA_JSON)
    ga4_property = env.get(ENV_GA4_PROPERTY)
    if api_key:
        tier = 0
    if sa_json and Path(sa_json).expanduser().is_file():
        tier = 1
    if tier >= 1 and ga4_property:
        tier = 2
    return {
        "tier": tier,
        "api_key": api_key,
        "service_account_json": sa_json,
        "ga4_property_id": ga4_property,
    }


def write_credentials_file(data: dict[str, str]) -> Path:
    """Persist credentials to the user-level config dir with tight permissions."""
    SUITE_DIR.mkdir(parents=True, exist_ok=True)
    CREDENTIALS_FILE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    try:
        CREDENTIALS_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 0o600 on POSIX
    except OSError:
        pass  # Windows ACLs are handled by the installer via icacls
    return CREDENTIALS_FILE


def status() -> int:
    """Print a human-readable credential status report."""
    env = _merged_env()
    print("OpenCode SEO Suite - credential status")
    print("=" * 45)

    def _masked(value: str | None) -> str:
        if not value:
            return "(not set)"
        return value[:3] + "*" * max(len(value) - 3, 3)

    dfs_ok = bool(env.get(ENV_DFS_LOGIN) and env.get(ENV_DFS_PASSWORD))
    print(f"DataForSEO login ..... {_masked(env.get(ENV_DFS_LOGIN))}")
    print(f"DataForSEO password .. {_masked(env.get(ENV_DFS_PASSWORD))}")
    print(f"DataForSEO status .... {'READY (mandatory layer active)' if dfs_ok else 'MISSING - suite data layer will fail'}")

    g = google_tier()
    names = {-1: "none (optional layer disabled)", 0: "Tier 0 - PSI + CrUX",
             1: "Tier 1 - + Search Console + Indexing", 2: "Tier 2 - + GA4"}
    print(f"Google API tier ...... {names[g['tier']]}")
    print(f"Google API key ....... {_masked(env.get(ENV_GOOGLE_API_KEY))}")
    print(f"Service account ...... {env.get(ENV_GOOGLE_SA_JSON) or '(not set)'}")
    print(f"GA4 property ......... {env.get(ENV_GA4_PROPERTY) or '(not set)'}")
    print()
    print(f"Credentials file ..... {CREDENTIALS_FILE}"
          f" ({'exists' if CREDENTIALS_FILE.is_file() else 'not created'})")
    dotenv = _find_dotenv()
    print(f".env file ............ {dotenv or '(not found)'}")
    return 0 if dfs_ok else 1


if __name__ == "__main__":
    sys.exit(status())
