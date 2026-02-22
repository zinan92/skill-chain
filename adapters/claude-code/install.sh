#!/usr/bin/env bash
# adapters/claude-code/install.sh — Claude Code specific installation
# Called by main install.sh, not typically run directly
# Writes installed items to ADAPTER_MANIFEST (shared with main installer)
set -euo pipefail

SCO_HOME=""
DRY_RUN=false

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)    DRY_RUN=true; shift ;;
        --sco-home)   SCO_HOME="$2"; shift 2 ;;
        *) shift ;;
    esac
done

SCO_HOME="${SCO_HOME:-$(cd "$(dirname "$0")/../.." && pwd)}"
ADAPTER_MANIFEST="${ADAPTER_MANIFEST:-/dev/null}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
info() { echo -e "${BLUE}[INFO]${NC} $*"; }
dry()  { echo -e "${YELLOW}[DRY-RUN]${NC} $*"; }

# Record installed item to adapter manifest (for main installer to merge)
record_item() {
    local type="$1" src="$2" dst="$3"
    if [ "$ADAPTER_MANIFEST" != "/dev/null" ] && [ -f "$ADAPTER_MANIFEST" ]; then
        python3 -c "
import json
items = json.load(open('${ADAPTER_MANIFEST}'))
items.append({'type': '${type}', 'src': '${src}', 'dst': '${dst}'})
json.dump(items, open('${ADAPTER_MANIFEST}', 'w'))
"
    fi
}

info "Claude Code adapter install"

# ── Install rules ──────────────────────────────────────────
# Rules go into ~/.claude/rules/ — we use per-file symlinks to avoid conflicts
info "Installing rules..."

RULES_SRC="${SCO_HOME}/rules"
RULES_DST="${HOME}/.claude/rules"

for subdir in common python typescript; do
    src_dir="${RULES_SRC}/${subdir}"
    dst_dir="${RULES_DST}/${subdir}"
    [ -d "$src_dir" ] || continue

    for rule_file in "${src_dir}"/*.md; do
        [ -f "$rule_file" ] || continue
        fname=$(basename "$rule_file")
        dst="${dst_dir}/${fname}"

        if [ -L "$dst" ]; then
            existing=$(readlink "$dst")
            if [ "$existing" = "$rule_file" ]; then
                ok "Already linked: rules/${subdir}/${fname}"
                record_item "symlink" "$rule_file" "$dst"
            else
                warn "Conflict: ${dst} -> ${existing} (skipping)"
            fi
        elif [ -f "$dst" ]; then
            # File exists but isn't a symlink — check if content matches
            if diff -q "$rule_file" "$dst" &>/dev/null; then
                ok "Identical: rules/${subdir}/${fname}"
            else
                warn "Different content: rules/${subdir}/${fname} — skipping (user customized?)"
            fi
        else
            if $DRY_RUN; then
                dry "Would link: rules/${subdir}/${fname}"
            else
                mkdir -p "$dst_dir"
                ln -s "$rule_file" "$dst"
                ok "Linked: rules/${subdir}/${fname}"
            fi
            record_item "symlink" "$rule_file" "$dst"
        fi
    done
done

# ── Settings merge hint ────────────────────────────────────
info "Settings template available at:"
echo "  ${SCO_HOME}/adapters/claude-code/settings.json.tmpl"
echo ""
info "To merge into your settings (preview first):"
echo "  python3 ${SCO_HOME}/scripts/build-settings.py --dry-run"
echo ""
info "To generate merged settings file:"
echo "  python3 ${SCO_HOME}/scripts/build-settings.py --output /tmp/merged-settings.json"
echo ""
warn "Settings are NOT auto-merged to avoid overwriting your configuration."
