"""Interactive setup wizard for the OpenCode SEO Suite.

Walks through: DataForSEO credentials (with a live account check), optional
Google API tiers, and creating a first project/client memory file.

Usage:
    python scripts/setup_wizard.py
"""

from __future__ import annotations

import base64
import json
import sys
import urllib.error
import urllib.request

from seo_config import SUITE_DIR, google_tier, write_credentials_file

USER_DATA_URL = "https://api.dataforseo.com/v3/appendix/user_data"


def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value or default


def ask_yn(prompt: str, default: bool = False) -> bool:
    hint = "Y/n" if default else "y/N"
    value = input(f"{prompt} [{hint}] ").strip().lower()
    if not value:
        return default
    return value.startswith("y")


def check_dataforseo(login: str, password: str) -> dict | None:
    """Call the account-info endpoint to verify credentials work."""
    token = base64.b64encode(f"{login}:{password}".encode()).decode()
    request = urllib.request.Request(
        USER_DATA_URL, headers={"Authorization": f"Basic {token}"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode())
            result = (body.get("tasks") or [{}])[0].get("result") or []
            return result[0] if result else {}
    except (urllib.error.URLError, json.JSONDecodeError):
        return None


def main() -> int:
    print("OpenCode SEO Suite - setup wizard")
    print("=" * 40)
    print(f"Credentials are stored in: {SUITE_DIR}\n")

    # --- DataForSEO ---------------------------------------------------------
    print("STEP 1 - DataForSEO (mandatory data layer)")
    print("Get credentials at https://app.dataforseo.com/register")
    print("(the API password is in the dashboard, NOT your account password)\n")
    login = ask("DataForSEO login (email)")
    password = ask("DataForSEO API password")
    if login and password:
        print("Checking credentials against the API...", end=" ")
        account = check_dataforseo(login, password)
        if account is None:
            print("FAILED")
            print("Could not authenticate. Check the login/password and try again.")
            if not ask_yn("Save anyway?"):
                return 1
        else:
            balance = account.get("money", {}).get("balance")
            print(f"OK (balance: ${balance})")
        path = write_credentials_file({
            "DATAFORSEO_LOGIN": login,
            "DATAFORSEO_PASSWORD": password,
        })
        print(f"Saved to {path}\n")
    else:
        print("Skipped - the suite's data layer will fail until you add these.\n")

    # --- Google tiers -------------------------------------------------------
    print("STEP 2 - Google APIs (optional enrichment)")
    if ask_yn("Configure a Google API key now? (Tier 0: PageSpeed + CrUX)"):
        api_key = ask("GOOGLE_API_KEY")
        extra: dict[str, str] = {}
        if api_key:
            extra["GOOGLE_API_KEY"] = api_key
        if ask_yn("Add a Search Console service account? (Tier 1)"):
            sa = ask("Path to service-account JSON")
            if sa:
                extra["GOOGLE_SERVICE_ACCOUNT_JSON"] = sa
        if ask_yn("Add a GA4 property? (Tier 2)"):
            prop = ask("GA4_PROPERTY_ID")
            if prop:
                extra["GA4_PROPERTY_ID"] = prop
        if extra:
            creds = {"DATAFORSEO_LOGIN": login,
                     "DATAFORSEO_PASSWORD": password, **extra}
            write_credentials_file(creds)
            print("Saved.\n")
    else:
        print("Skipped - see docs/GOOGLE-APIS.md when you're ready.\n")

    # --- Project memory -----------------------------------------------------
    print("STEP 3 - Project memory")
    if ask_yn("Create a client profile now? (clients/<name>.yml)"):
        name = ask("Client name (e.g. acme)")
        if name:
            import subprocess
            subprocess.run([sys.executable, "scripts/project_memory.py",
                            "--client", name, "--init"], check=False)
    else:
        print("Skipped - create one any time with:")
        print("  python scripts/project_memory.py --client <name> --init\n")

    print("=" * 40)
    print("Setup complete. Verify with: python scripts/seo_config.py status")
    tier = google_tier()["tier"]
    print(f"Google tier detected: {tier if tier >= 0 else 'none (optional)'}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(130)
