#!/usr/bin/env bash
# doctor.sh — Verify skill-chain dependencies and installation health
# Usage: ./doctor.sh [--quiet]
set -euo pipefail

SCO_HOME="${SCO_HOME:-$(cd "$(dirname "$0")/.." && pwd)}"
QUIET=false
[[ "${1:-}" == "--quiet" ]] && QUIET=true

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

pass() { $QUIET || echo -e "  ${GREEN}✓${NC} $*"; }
fail() { echo -e "  ${RED}✗${NC} $*"; }
warn() { $QUIET || echo -e "  ${YELLOW}!${NC} $*"; }
info() { $QUIET || echo -e "${BLUE}[CHECK]${NC} $*"; }

ERRORS=0
WARNINGS=0

# ── Check: Required Commands ───────────────────────────────
check_cmd() {
    local cmd="$1" min_version="${2:-}" label="${3:-$1}"

    if command -v "$cmd" &>/dev/null; then
        local version
        version=$("$cmd" --version 2>&1 | head -1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -1 || echo "unknown")
        pass "${label}: ${version}"
    else
        fail "${label}: not found"
        ERRORS=$((ERRORS + 1))
    fi
}

check_optional_cmd() {
    local cmd="$1" label="${2:-$1}" purpose="${3:-}"

    if command -v "$cmd" &>/dev/null; then
        local version
        version=$("$cmd" --version 2>&1 | head -1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -1 || echo "unknown")
        pass "${label}: ${version}"
    else
        warn "${label}: not found (needed for: ${purpose})"
        WARNINGS=$((WARNINGS + 1))
    fi
}

$QUIET || echo ""
$QUIET || echo "╔══════════════════════════════════════════╗"
$QUIET || echo "║       skill-chain doctor v1.0.0          ║"
$QUIET || echo "╚══════════════════════════════════════════╝"
$QUIET || echo ""

# ── Required Dependencies ──────────────────────────────────
info "Required dependencies"
check_cmd "node" "18.0.0" "Node.js"
check_cmd "python3" "3.11.0" "Python"
check_cmd "git" "" "Git"
check_cmd "claude" "" "Claude CLI"

# ── Optional Dependencies ──────────────────────────────────
$QUIET || echo ""
info "Optional dependencies"
check_optional_cmd "lobster" "Lobster" "pipeline execution"
check_optional_cmd "openclaw" "OpenClaw" "openclaw adapter"
check_optional_cmd "codex" "Codex CLI" "cross-company AI review"

# ── Repo Structure ─────────────────────────────────────────
$QUIET || echo ""
info "Repo structure"

check_dir() {
    local dir="$1" label="$2"
    if [ -d "$dir" ]; then
        pass "${label}"
    else
        fail "${label}: missing"
        ERRORS=$((ERRORS + 1))
    fi
}

check_file() {
    local file="$1" label="$2" required="${3:-true}"
    if [ -f "$file" ]; then
        pass "${label}"
    elif [ "$required" = "true" ]; then
        fail "${label}: missing"
        ERRORS=$((ERRORS + 1))
    else
        warn "${label}: missing (optional)"
        WARNINGS=$((WARNINGS + 1))
    fi
}

check_dir "${SCO_HOME}/core" "core/"
check_dir "${SCO_HOME}/core/helpers" "core/helpers/"
check_dir "${SCO_HOME}/skills" "skills/"
check_dir "${SCO_HOME}/rules" "rules/"
check_dir "${SCO_HOME}/manifest" "manifest/"
check_dir "${SCO_HOME}/scripts" "scripts/"

check_file "${SCO_HOME}/core/dev-pipeline.lobster" "core/dev-pipeline.lobster"
check_file "${SCO_HOME}/core/helpers/guard.py" "core/helpers/guard.py"
check_file "${SCO_HOME}/core/helpers/router.py" "core/helpers/router.py"
check_file "${SCO_HOME}/manifest/skills-manifest.json" "manifest/skills-manifest.json"
check_file "${SCO_HOME}/manifest/package-manifest.json" "manifest/package-manifest.json"

# ── Skills Integrity ───────────────────────────────────────
$QUIET || echo ""
info "Skills integrity"

if [ -f "${SCO_HOME}/manifest/skills-manifest.json" ]; then
    SKILL_ISSUES=$(python3 -c "
import json, os, sys
m = json.load(open('${SCO_HOME}/manifest/skills-manifest.json'))
issues = 0
for cat_name, cat in m.get('categories', {}).items():
    for skill in cat.get('skills', []):
        skill_dir = os.path.join('${SCO_HOME}', 'skills', skill)
        if not os.path.isdir(skill_dir):
            print(f'MISSING: {skill} ({cat_name})')
            issues += 1
        elif not os.listdir(skill_dir):
            print(f'EMPTY: {skill} ({cat_name})')
            issues += 1
sys.exit(issues)
" 2>&1) || true

    if [ -z "$SKILL_ISSUES" ]; then
        SKILL_COUNT=$(python3 -c "
import json
m = json.load(open('${SCO_HOME}/manifest/skills-manifest.json'))
total = sum(len(c.get('skills',[])) for c in m.get('categories',{}).values())
print(total)
")
        pass "All ${SKILL_COUNT} manifest skills present"
    else
        echo "$SKILL_ISSUES" | while read -r line; do
            fail "$line"
        done
        ERRORS=$((ERRORS + $(echo "$SKILL_ISSUES" | wc -l | tr -d ' ')))
    fi
fi

# ── Audit Check ────────────────────────────────────────────
$QUIET || echo ""
info "Security audit"

AUDIT_OUTPUT=$(python3 "${SCO_HOME}/scripts/package-audit.py" 2>&1) || true
if echo "$AUDIT_OUTPUT" | grep -q "PASS:"; then
    pass "No hardcoded paths or secrets found"
else
    AUDIT_ISSUES=$(echo "$AUDIT_OUTPUT" | grep -c "POSSIBLE_SECRET" || echo "0")
    if [ "$AUDIT_ISSUES" -gt 0 ]; then
        fail "Found ${AUDIT_ISSUES} potential secrets!"
        ERRORS=$((ERRORS + 1))
    else
        HARDCODED=$(echo "$AUDIT_OUTPUT" | grep -c "HARDCODED_PATH" || echo "0")
        if [ "$HARDCODED" -gt 0 ]; then
            warn "Found ${HARDCODED} hardcoded paths (run package-audit.py for details)"
            WARNINGS=$((WARNINGS + 1))
        else
            pass "Audit clean"
        fi
    fi
fi

# ── Summary ────────────────────────────────────────────────
$QUIET || echo ""
if [ $ERRORS -eq 0 ]; then
    $QUIET || echo -e "${GREEN}All checks passed!${NC} (${WARNINGS} warnings)"
    exit 0
else
    echo -e "${RED}${ERRORS} errors, ${WARNINGS} warnings${NC}"
    exit 1
fi
