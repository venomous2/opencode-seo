#!/usr/bin/env bash
# OpenCode SEO Suite - Unix/macOS uninstaller
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OC_CONFIG="$HOME/.config/opencode"
SUITE_DIR="$OC_CONFIG/seo-suite"

for pair in ".opencode/skills:skills" ".opencode/agents:agents" ".opencode/commands:commands"; do
    src="$ROOT/${pair%%:*}"
    dst="$OC_CONFIG/${pair##*:}"
    [ -d "$src" ] || continue
    for item in "$src"/*; do
        name="$(basename "$item")"
        rm -rf "$dst/$name"
    done
    echo "Removed suite ${pair##*:} from $dst"
done

read -r -p "Also remove scripts, venv, and credentials in $SUITE_DIR ? [y/N] " answer
if [[ "$answer" =~ ^[yY] ]]; then
    rm -rf "$SUITE_DIR"
    echo "Removed $SUITE_DIR"
else
    echo "Kept $SUITE_DIR (scripts + credentials)."
fi
echo "Done. Restart OpenCode."
