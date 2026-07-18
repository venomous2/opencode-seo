#!/usr/bin/env bash
# OpenCode SEO Suite - Unix/macOS installer
# Copies skills/agents/commands to ~/.config/opencode and scripts to
# ~/.config/opencode/seo-suite/scripts.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OC_CONFIG="$HOME/.config/opencode"
SUITE_DIR="$OC_CONFIG/seo-suite"

echo "OpenCode SEO Suite installer"
echo "============================"

for dir in .opencode/skills .opencode/agents .opencode/commands scripts; do
    if [ ! -d "$ROOT/$dir" ]; then
        echo "ERROR: $dir not found. Run this script from the suite root." >&2
        exit 1
    fi
done

if command -v python3 >/dev/null 2>&1; then
    PY=python3
elif command -v python >/dev/null 2>&1; then
    PY=python
else
    PY=""
    echo "WARNING: python not found. The data layer scripts need Python 3.10+."
fi
[ -n "$PY" ] && echo "Python: $($PY --version 2>&1)"

for pair in ".opencode/skills:skills" ".opencode/agents:agents" ".opencode/commands:commands"; do
    src="$ROOT/${pair%%:*}"
    dst="$OC_CONFIG/${pair##*:}"
    mkdir -p "$dst"
    cp -R "$src/"* "$dst/"
    echo "Installed ${pair##*:} -> $dst"
done

mkdir -p "$SUITE_DIR/scripts"
cp -R "$ROOT/scripts/"* "$SUITE_DIR/scripts/"
echo "Installed scripts -> $SUITE_DIR/scripts"
if [ -d "$ROOT/rules" ]; then
    cp -R "$ROOT/rules" "$SUITE_DIR/"
    echo "Installed rules -> $SUITE_DIR/rules ($(find "$SUITE_DIR/rules" -name '*.yaml' | wc -l | tr -d ' ') rules)"
fi

if [ -n "$PY" ]; then
    if "$PY" -m pip install --user --quiet pyyaml 2>/dev/null; then
        echo "Python deps installed (user level): pyyaml"
    else
        echo "WARNING: could not install pyyaml; project_memory.py needs it."
        echo "         Run: $PY -m pip install --user pyyaml"
    fi
fi

CRED_FILE="$SUITE_DIR/credentials.json"
if [ ! -f "$CRED_FILE" ]; then
    echo
    read -r -p "Enter DataForSEO credentials now? [y/N] " answer
    if [[ "$answer" =~ ^[yY] ]]; then
        read -r -p "DataForSEO login (email): " login
        read -r -s -p "DataForSEO API password: " pass
        echo
        printf '{\n  "DATAFORSEO_LOGIN": "%s",\n  "DATAFORSEO_PASSWORD": "%s"\n}\n' \
            "$login" "$pass" > "$CRED_FILE"
        chmod 600 "$CRED_FILE"
        echo "Credentials written to $CRED_FILE (mode 600)"
    else
        echo "Skipped. Add credentials later via environment variables,"
        echo "a project .env file, or $CRED_FILE - see docs/DATAFORSEO-SETUP.md"
    fi
fi

echo
echo "Done. Restart OpenCode to load the new skills, then try:"
echo "  /site-audit https://example.com"
echo "  /keyword-research best espresso beans"
echo
echo "Verify with: python3 scripts/seo_config.py status"
