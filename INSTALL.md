# Installation

## 1. Get the suite

```bash
git clone https://github.com/venomous2/opencode-seo.git
cd opencode-seo-suite
```

## 2. Run the installer

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy Bypass -File install.ps1
```

**macOS / Linux:**
```bash
bash install.sh
```

The installer:
1. Copies `skills/`, `agents/`, `commands/` into `~/.config/opencode/`
2. Copies the Python data layer to `~/.config/opencode/seo-suite/scripts/`
3. Creates an isolated Python venv and installs `pyyaml` + `requests`
4. Optionally stores your DataForSEO credentials (user-only permissions)

> **Prefer manual?** Copy the folders yourself — see the same destinations
> above. Skills are plain markdown; nothing is compiled.

## 3. Configure DataForSEO (mandatory)

Any one of these works (checked in this order):

1. **Environment variables** — `DATAFORSEO_LOGIN` / `DATAFORSEO_PASSWORD`
2. **`.env` in your project** — copy `.env.example` to `.env` and fill it in
3. **User credentials file** — `~/.config/opencode/seo-suite/credentials.json`
   (the installer can write this for you)

Get credentials at https://app.dataforseo.com/register → API access.

Verify:
```bash
python scripts/seo_config.py status
```
`DataForSEO status .... READY` means the suite's data layer is live.

## 4. (Optional) Google API tiers

See [docs/GOOGLE-APIS.md](docs/GOOGLE-APIS.md). The suite works fully
without them.

## 5. Restart OpenCode

Config and skills load at startup — quit and relaunch OpenCode, then:

```
/site-audit https://your-site.com
```

**Next:** [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md) walks your
first 15 minutes (first check, first audit, monitoring on), and
[docs/USER-GUIDE.md](docs/USER-GUIDE.md) is the full reference with tips.

## Validate the installation

```bash
python validate.py
```

## Update

```bash
git pull
bash install.sh        # or install.ps1 — re-copies everything
```

## Uninstall

```bash
bash uninstall.sh      # or uninstall.ps1 on Windows
```

Removes only the suite's own skills/agents/commands; asks before deleting
scripts and credentials.
