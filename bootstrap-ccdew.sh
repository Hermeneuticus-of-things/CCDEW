#!/usr/bin/env bash
# Bootstrap CCDEW pe Linux/macOS
# Usage:  ./bootstrap-ccdew.sh [target-folder]
# Default target: CCDEW

set -euo pipefail

echo "=== CCDEW bootstrap ==="

# 1. Prereq check
missing=()
for cmd in node npm git python3 claude; do
    command -v "$cmd" >/dev/null 2>&1 || missing+=("$cmd")
done
if [ ${#missing[@]} -gt 0 ]; then
    echo "MISSING: ${missing[*]}"
    echo "Install: Node>=18, Python 3, Git, Claude Code CLI (https://docs.claude.com/claude-code)"
    exit 1
fi

node_major=$(node -v | sed -E 's/^v([0-9]+).*/\1/')
if [ "$node_major" -lt 18 ]; then
    echo "Node prea vechi: $(node -v) (necesita >=18)"
    exit 1
fi
echo "Prereqs OK ($(node -v))"

# 2. Clone
target="${1:-CCDEW}"
if [ -d "$target" ]; then
    echo "Folder '$target' exista deja, sar peste clone."
else
    git clone https://github.com/Hermeneuticus-of-things/claude-code-eficient-workspace.git "$target"
fi
cd "$target"

# 3. Optional: codeburn global
read -rp "Instalez codeburn global pentru cost tracking? (y/N) " ans
if [ "${ans:-N}" = "y" ] || [ "${ans:-N}" = "Y" ]; then
    npm install -g codeburn
fi

# 4. Tests + audit
echo
echo "=== npm test ==="
npm test

echo
echo "=== npm run audit ==="
npm run audit

echo
echo "=== READY ==="
echo "Folder: $(pwd)"
echo "Pornire: claude"
