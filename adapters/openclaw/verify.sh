#!/usr/bin/env bash
# adapters/openclaw/verify.sh — Verify OpenClaw installation
set -euo pipefail

SCO_HOME="${SCO_HOME:-$(cd "$(dirname "$0")/../.." && pwd)}"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "  ${GREEN}✓${NC} $*"; }
fail() { echo -e "  ${RED}✗${NC} $*"; }
warn() { echo -e "  ${YELLOW}!${NC} $*"; }

ERRORS=0

echo "Verifying OpenClaw adapter installation..."
echo ""

# Check OpenClaw CLI
if command -v openclaw &>/dev/null; then
    version=$(openclaw --version 2>&1 | head -1 || echo "unknown")
    pass "OpenClaw CLI: ${version}"
else
    fail "OpenClaw CLI not found"
    ERRORS=$((ERRORS + 1))
fi

# Check templates exist
echo ""
echo "Templates:"
for tmpl in AGENTS SOUL IDENTITY HEARTBEAT USER TOOLS; do
    src="${SCO_HOME}/adapters/openclaw/${tmpl}.template.md"
    if [ -f "$src" ]; then
        pass "template: ${tmpl}.template.md"
    else
        fail "template: ${tmpl}.template.md — missing"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check rendered output
echo ""
echo "Rendered files:"
RENDERED_DIR="${SCO_HOME}/my/openclaw/rendered"
if [ -d "$RENDERED_DIR" ]; then
    for fname in AGENTS.md SOUL.md IDENTITY.md HEARTBEAT.md USER.md TOOLS.md; do
        if [ -f "${RENDERED_DIR}/${fname}" ]; then
            pass "rendered: ${fname}"
        else
            warn "rendered: ${fname} — not yet rendered"
        fi
    done
else
    warn "Rendered directory not found. Run install first."
fi

# Check overlay support
echo ""
echo "Private overlays:"
OVERLAY_DIR="${SCO_HOME}/my/openclaw"
for fname in SOUL.md USER.md HEARTBEAT.md; do
    if [ -f "${OVERLAY_DIR}/${fname}" ]; then
        pass "overlay: ${fname} (will override template)"
    else
        warn "overlay: ${fname} — using template default"
    fi
done

# Check render script
echo ""
echo "Scripts:"
if [ -f "${SCO_HOME}/scripts/render-openclaw-templates.py" ]; then
    pass "render-openclaw-templates.py"
else
    fail "render-openclaw-templates.py — missing"
    ERRORS=$((ERRORS + 1))
fi

echo ""
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}All OpenClaw verifications passed!${NC}"
    exit 0
else
    echo -e "${RED}${ERRORS} verification errors found.${NC}"
    exit 1
fi
