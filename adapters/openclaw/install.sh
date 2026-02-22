#!/usr/bin/env bash
# adapters/openclaw/install.sh — OpenClaw specific installation
# Renders templates, applies overlays, validates output
set -euo pipefail

SCO_HOME=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)    DRY_RUN=true; shift ;;
        --sco-home)   SCO_HOME="$2"; shift 2 ;;
        *) shift ;;
    esac
done

SCO_HOME="${SCO_HOME:-$(cd "$(dirname "$0")/../.." && pwd)}"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
info() { echo -e "${BLUE}[INFO]${NC} $*"; }
err()  { echo -e "${RED}[ERROR]${NC} $*"; }
dry()  { echo -e "${YELLOW}[DRY-RUN]${NC} $*"; }

info "OpenClaw adapter install"
info "SCO_HOME: ${SCO_HOME}"

# Check openclaw is available
if ! command -v openclaw &>/dev/null; then
    warn "OpenClaw CLI not found. Templates will be rendered but not validated."
fi

# ── Step 1: Render templates ───────────────────────────────
info "Rendering OpenClaw templates..."
OUTPUT_DIR="${SCO_HOME}/my/openclaw/rendered"

if $DRY_RUN; then
    dry "Would render templates to: ${OUTPUT_DIR}"
    SCO_HOME="$SCO_HOME" python3 "${SCO_HOME}/scripts/render-openclaw-templates.py" --dry-run
else
    mkdir -p "$OUTPUT_DIR"
    SCO_HOME="$SCO_HOME" python3 "${SCO_HOME}/scripts/render-openclaw-templates.py" --output-dir "$OUTPUT_DIR"
    ok "Templates rendered to: ${OUTPUT_DIR}"
fi

# ── Step 2: Validate rendered files ────────────────────────
echo ""
info "Validating rendered files..."
REQUIRED_FILES=("AGENTS.md" "SOUL.md" "IDENTITY.md" "HEARTBEAT.md" "USER.md" "TOOLS.md")
ERRORS=0

for fname in "${REQUIRED_FILES[@]}"; do
    rendered="${OUTPUT_DIR}/${fname}"
    overlay="${SCO_HOME}/my/openclaw/${fname}"

    # Check either rendered or overlay exists
    if [ -f "$rendered" ] || [ -f "$overlay" ]; then
        ok "${fname}"
    elif $DRY_RUN; then
        dry "Would check: ${fname}"
    else
        err "Missing: ${fname}"
        ERRORS=$((ERRORS + 1))
    fi
done

# ── Step 3: Check for hardcoded paths in rendered output ───
if [ -d "$OUTPUT_DIR" ] && ! $DRY_RUN; then
    echo ""
    info "Scanning rendered files for hardcoded paths..."
    LEAKS=$(grep -rn '/Users/' "$OUTPUT_DIR" 2>/dev/null | grep -v '${' || true)
    if [ -z "$LEAKS" ]; then
        ok "No hardcoded paths in rendered output"
    else
        warn "Found hardcoded paths in rendered output:"
        echo "$LEAKS" | head -5
    fi
fi

echo ""
if [ $ERRORS -eq 0 ]; then
    ok "OpenClaw adapter install complete"
    echo ""
    info "Rendered files at: ${OUTPUT_DIR}"
    info "To use with OpenClaw, copy or symlink these files to your OpenClaw project."
else
    err "${ERRORS} errors found"
    exit 1
fi
