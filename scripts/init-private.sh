#!/usr/bin/env bash
# init-private.sh — Initialize the my/ private overlay directory
# Safe to run multiple times (idempotent)
set -euo pipefail

SCO_HOME="${SCO_HOME:-$(cd "$(dirname "$0")/.." && pwd)}"

echo "Initializing private overlay directory..."
echo "SCO_HOME: ${SCO_HOME}"

# Create my/ structure
mkdir -p "${SCO_HOME}/my/openclaw"
mkdir -p "${SCO_HOME}/my/claude-code"
mkdir -p "${SCO_HOME}/my/memory"

# Copy examples if not already present
for file in SOUL.md USER.md HEARTBEAT.md; do
    src="${SCO_HOME}/env/private.example/openclaw/${file}"
    dst="${SCO_HOME}/my/openclaw/${file}"
    if [ -f "$src" ] && [ ! -f "$dst" ]; then
        cp "$src" "$dst"
        echo "  Created: my/openclaw/${file}"
    else
        echo "  Skipped: my/openclaw/${file} (already exists or no template)"
    fi
done

# Copy claude-code example
src="${SCO_HOME}/env/private.example/claude-code/local-overrides.json"
dst="${SCO_HOME}/my/claude-code/local-overrides.json"
if [ -f "$src" ] && [ ! -f "$dst" ]; then
    cp "$src" "$dst"
    echo "  Created: my/claude-code/local-overrides.json"
else
    echo "  Skipped: my/claude-code/local-overrides.json (already exists or no template)"
fi

echo ""
echo "Private overlay initialized at: ${SCO_HOME}/my/"
echo "Edit files in my/ to customize for your environment."
echo "These files are gitignored and will not be committed."
