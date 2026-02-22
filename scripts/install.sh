#!/usr/bin/env bash
# install.sh — Main installer for skill-chain
# Usage: ./install.sh [OPTIONS]
#
# Options:
#   --dry-run              Show what would be installed without making changes
#   --platform TYPE        Install for: claude-code | openclaw | all (default: claude-code)
#   --skills-dir PATH      Override skills install target (default: ~/.claude/skills)
#   --install-deps         Auto-install missing dependencies
#   --skip-doctor          Skip dependency version check
#   -h, --help             Show this help
set -euo pipefail

# ── Configuration ───────────────────────────────────────────
SCO_HOME="${SCO_HOME:-$(cd "$(dirname "$0")/.." && pwd)}"
PLATFORM="claude-code"
DRY_RUN=false
INSTALL_DEPS=false
SKIP_DOCTOR=false
SKILLS_PREFIX="${HOME}/.claude/skills"
MANIFEST_FILE="${SCO_HOME}/manifest/install-manifest.json"

# ── Colors ──────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()   { echo -e "${RED}[ERROR]${NC} $*"; }
dry()   { echo -e "${YELLOW}[DRY-RUN]${NC} $*"; }

# ── Argument Parsing ────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)       DRY_RUN=true; shift ;;
        --platform)      PLATFORM="$2"; shift 2 ;;
        --skills-dir)    SKILLS_PREFIX="$2"; shift 2 ;;
        --install-deps)  INSTALL_DEPS=true; shift ;;
        --skip-doctor)   SKIP_DOCTOR=true; shift ;;
        -h|--help)
            head -12 "$0" | tail -10
            exit 0
            ;;
        *) err "Unknown option: $1"; exit 1 ;;
    esac
done

# Validate platform
case "$PLATFORM" in
    claude-code|openclaw|all) ;;
    *) err "Invalid platform: $PLATFORM (expected: claude-code | openclaw | all)"; exit 1 ;;
esac

# ── Manifest Management ────────────────────────────────────
MANIFEST_ITEMS=()

manifest_add() {
    local type="$1" src="$2" dst="$3"
    MANIFEST_ITEMS+=("{\"type\":\"${type}\",\"src\":\"${src}\",\"dst\":\"${dst}\"}")
}

manifest_write() {
    local items_json
    items_json=$(printf '%s\n' "${MANIFEST_ITEMS[@]}" | paste -sd, -)
    cat > "$MANIFEST_FILE" << MANIFEST_EOF
{
  "version": "1.0.0",
  "installed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "platform": "${PLATFORM}",
  "sco_home": "${SCO_HOME}",
  "items": [${items_json}]
}
MANIFEST_EOF
}

# ── Safe Operations ─────────────────────────────────────────
safe_symlink() {
    local src="$1" dst="$2" label="${3:-}"

    if [ -L "$dst" ]; then
        local existing
        existing=$(readlink "$dst")
        if [ "$existing" = "$src" ]; then
            ok "Already linked: ${label:-$dst}"
            manifest_add "symlink" "$src" "$dst"
            return 0
        else
            warn "Conflict: $dst -> $existing (not ours, skipping)"
            return 0
        fi
    elif [ -e "$dst" ]; then
        warn "Exists (not symlink): $dst — skipping to avoid overwrite"
        return 0
    fi

    if $DRY_RUN; then
        dry "Would link: $dst -> $src"
    else
        mkdir -p "$(dirname "$dst")"
        ln -s "$src" "$dst"
        ok "Linked: ${label:-$dst}"
    fi
    manifest_add "symlink" "$src" "$dst"
}

safe_copy() {
    local src="$1" dst="$2" label="${3:-}"

    if [ -f "$dst" ]; then
        warn "Exists: $dst — skipping to avoid overwrite"
        return 0
    fi

    if $DRY_RUN; then
        dry "Would copy: $src -> $dst"
    else
        mkdir -p "$(dirname "$dst")"
        cp "$src" "$dst"
        ok "Copied: ${label:-$dst}"
    fi
    manifest_add "copy" "$src" "$dst"
}

# ── Banner ──────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║       skill-chain installer v1.0.0       ║"
echo "╚══════════════════════════════════════════╝"
echo ""
info "SCO_HOME:  ${SCO_HOME}"
info "Platform:  ${PLATFORM}"
info "Dry run:   ${DRY_RUN}"
echo ""

# ── Step 1: Doctor Check ───────────────────────────────────
if ! $SKIP_DOCTOR; then
    info "Running dependency check..."
    if $DRY_RUN; then
        dry "Would run: ${SCO_HOME}/scripts/doctor.sh --quiet"
    else
        if ! bash "${SCO_HOME}/scripts/doctor.sh" --quiet; then
            if $INSTALL_DEPS; then
                warn "Some dependencies missing. --install-deps not yet implemented."
                warn "Please install manually and re-run."
                exit 1
            else
                err "Dependency check failed. Fix issues above or use --skip-doctor."
                exit 1
            fi
        fi
    fi
    echo ""
fi

# ── Step 2: Initialize private overlay ─────────────────────
info "Initializing private overlay..."
if $DRY_RUN; then
    dry "Would run: ${SCO_HOME}/scripts/init-private.sh"
else
    bash "${SCO_HOME}/scripts/init-private.sh"
fi
echo ""

# ── Step 3: Install skills ─────────────────────────────────
info "Installing skills..."
SKILLS_MANIFEST="${SCO_HOME}/manifest/skills-manifest.json"
SKILLS_DIR="${SCO_HOME}/skills"
TARGET_SKILLS_DIR="${SKILLS_PREFIX}"

if [ -f "$SKILLS_MANIFEST" ]; then
    # Install required + transitive skills
    for category in required transitive; do
        skills=$(python3 -c "
import json, sys
m = json.load(open('${SKILLS_MANIFEST}'))
cats = m.get('categories', {})
if '${category}' in cats:
    for s in cats['${category}'].get('skills', []):
        print(s)
")
        while IFS= read -r skill; do
            [ -z "$skill" ] && continue
            src="${SKILLS_DIR}/${skill}"
            dst="${TARGET_SKILLS_DIR}/${skill}"
            if [ -d "$src" ]; then
                safe_symlink "$src" "$dst" "skill: ${skill}"
            else
                warn "Skill directory not found: ${src}"
            fi
        done <<< "$skills"
    done
else
    warn "skills-manifest.json not found, skipping skills install"
fi
echo ""

# ── Step 4: Install commands ───────────────────────────────
info "Installing commands..."
TARGET_COMMANDS_DIR="${HOME}/.claude/commands"
for cmd_file in "${SCO_HOME}/commands/"*.md; do
    [ -f "$cmd_file" ] || continue
    fname=$(basename "$cmd_file")
    safe_symlink "$cmd_file" "${TARGET_COMMANDS_DIR}/${fname}" "command: ${fname}"
done
echo ""

# ── Step 5: Install agent definitions ──────────────────────
info "Installing agents..."
TARGET_AGENTS_DIR="${HOME}/.claude/agents"
for agent_file in "${SCO_HOME}/agents/"*.md; do
    [ -f "$agent_file" ] || continue
    fname=$(basename "$agent_file")
    # Use namespaced name to avoid conflicts
    dst_name="${fname%.md}.skill-chain.md"
    safe_symlink "$agent_file" "${TARGET_AGENTS_DIR}/${dst_name}" "agent: ${dst_name}"
done
echo ""

# ── Step 6: Platform-specific install ──────────────────────
# Adapter manifest sidecar — adapters append here, main installer merges
ADAPTER_MANIFEST="${SCO_HOME}/manifest/.adapter-manifest-tmp.json"
echo '[]' > "$ADAPTER_MANIFEST"
export ADAPTER_MANIFEST

if [[ "$PLATFORM" == "claude-code" || "$PLATFORM" == "all" ]]; then
    info "Running Claude Code adapter install..."
    adapter="${SCO_HOME}/adapters/claude-code/install.sh"
    if [ -f "$adapter" ]; then
        if $DRY_RUN; then
            bash "$adapter" --dry-run --sco-home "$SCO_HOME"
        else
            bash "$adapter" --sco-home "$SCO_HOME"
        fi
    else
        warn "Claude Code adapter not found: ${adapter}"
    fi
    echo ""
fi

if [[ "$PLATFORM" == "openclaw" || "$PLATFORM" == "all" ]]; then
    info "Running OpenClaw adapter install..."
    adapter="${SCO_HOME}/adapters/openclaw/install.sh"
    if [ -f "$adapter" ]; then
        if $DRY_RUN; then
            bash "$adapter" --dry-run --sco-home "$SCO_HOME"
        else
            bash "$adapter" --sco-home "$SCO_HOME"
        fi
    else
        warn "OpenClaw adapter not found: ${adapter}"
    fi
    echo ""
fi

# ── Step 7: Merge adapter manifest and write ───────────────
# Merge adapter items into main manifest
if [ -f "$ADAPTER_MANIFEST" ]; then
    adapter_items=$(cat "$ADAPTER_MANIFEST")
    if [ "$adapter_items" != "[]" ]; then
        # Parse adapter manifest items and add to MANIFEST_ITEMS
        while IFS= read -r item; do
            [ -z "$item" ] && continue
            MANIFEST_ITEMS+=("$item")
        done < <(python3 -c "
import json, sys
items = json.load(open('${ADAPTER_MANIFEST}'))
for item in items:
    print(json.dumps(item))
")
    fi
    rm -f "$ADAPTER_MANIFEST"
fi

if ! $DRY_RUN; then
    manifest_write
    ok "Install manifest written: ${MANIFEST_FILE}"
fi

# ── Summary ─────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════╗"
if $DRY_RUN; then
echo "║    Dry run complete (no changes made)    ║"
else
echo "║      Installation complete!              ║"
fi
echo "╚══════════════════════════════════════════╝"
echo ""
info "Next steps:"
echo "  1. Add to your shell profile:"
echo "     export SCO_HOME=\"${SCO_HOME}\""
echo "  2. Verify installation:"
echo "     bash ${SCO_HOME}/scripts/doctor.sh"
echo "  3. Run smoke test:"
echo "     lobster run ${SCO_HOME}/core/smoke-basic.lobster"
echo ""
