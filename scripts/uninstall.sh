#!/usr/bin/env bash
# uninstall.sh — Remove skill-chain installed items
# Only removes items tracked in install-manifest.json
# Usage: ./uninstall.sh [--dry-run]
set -euo pipefail

SCO_HOME="${SCO_HOME:-$(cd "$(dirname "$0")/.." && pwd)}"
MANIFEST_FILE="${SCO_HOME}/manifest/install-manifest.json"
DRY_RUN=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()   { echo -e "${RED}[ERROR]${NC} $*"; }
dry()   { echo -e "${YELLOW}[DRY-RUN]${NC} $*"; }

[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║     skill-chain uninstaller v1.0.0       ║"
echo "╚══════════════════════════════════════════╝"
echo ""

if [ ! -f "$MANIFEST_FILE" ]; then
    err "No install manifest found at: ${MANIFEST_FILE}"
    err "Nothing to uninstall (was skill-chain installed?)."
    exit 1
fi

# Parse manifest
ITEMS=$(python3 -c "
import json, sys
m = json.load(open('${MANIFEST_FILE}'))
for item in m.get('items', []):
    print(f\"{item['type']}|{item['dst']}\")
")

REMOVED=0
SKIPPED=0

while IFS='|' read -r item_type dst; do
    [ -z "$dst" ] && continue

    case "$item_type" in
        symlink)
            if [ -L "$dst" ]; then
                if $DRY_RUN; then
                    dry "Would remove symlink: $dst"
                else
                    rm "$dst"
                    ok "Removed symlink: $dst"
                fi
                REMOVED=$((REMOVED + 1))
            elif [ -e "$dst" ]; then
                warn "Not a symlink (not ours?): $dst — skipping"
                SKIPPED=$((SKIPPED + 1))
            else
                info "Already gone: $dst"
            fi
            ;;
        copy)
            if [ -f "$dst" ]; then
                if $DRY_RUN; then
                    dry "Would remove copied file: $dst"
                else
                    rm "$dst"
                    ok "Removed: $dst"
                fi
                REMOVED=$((REMOVED + 1))
            else
                info "Already gone: $dst"
            fi
            ;;
        *)
            warn "Unknown item type: $item_type for $dst"
            SKIPPED=$((SKIPPED + 1))
            ;;
    esac
done <<< "$ITEMS"

# Reset manifest
if ! $DRY_RUN; then
    cat > "$MANIFEST_FILE" << 'MANIFEST_EOF'
{
  "version": "1.0.0",
  "installed_at": null,
  "platform": null,
  "items": []
}
MANIFEST_EOF
    ok "Install manifest reset"
fi

echo ""
echo "╔══════════════════════════════════════════╗"
if $DRY_RUN; then
echo "║   Dry run complete (no changes made)     ║"
else
echo "║      Uninstall complete!                 ║"
fi
echo "╚══════════════════════════════════════════╝"
echo ""
info "Removed: ${REMOVED} items"
[ $SKIPPED -gt 0 ] && warn "Skipped: ${SKIPPED} items (not managed by skill-chain)"
echo ""
info "Note: The skill-chain repo at ${SCO_HOME} was NOT deleted."
info "To fully remove: rm -rf ${SCO_HOME}"
