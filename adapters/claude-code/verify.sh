#!/usr/bin/env bash
# adapters/claude-code/verify.sh — Verify Claude Code installation
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

echo "Verifying Claude Code adapter installation..."
echo ""

# Check Claude CLI
if command -v claude &>/dev/null; then
    pass "Claude CLI available"
else
    fail "Claude CLI not found"
    ERRORS=$((ERRORS + 1))
fi

# Check skills are linked
echo ""
echo "Skills:"
SKILLS_MANIFEST="${SCO_HOME}/manifest/skills-manifest.json"
if [ -f "$SKILLS_MANIFEST" ]; then
    for category in required transitive; do
        skills=$(python3 -c "
import json
m = json.load(open('${SKILLS_MANIFEST}'))
cats = m.get('categories', {})
if '${category}' in cats:
    for s in cats['${category}'].get('skills', []):
        print(s)
" 2>/dev/null)
        while IFS= read -r skill; do
            [ -z "$skill" ] && continue
            dst="${HOME}/.claude/skills/${skill}"
            if [ -L "$dst" ] || [ -d "$dst" ]; then
                pass "skill: ${skill}"
            else
                fail "skill: ${skill} — not installed"
                ERRORS=$((ERRORS + 1))
            fi
        done <<< "$skills"
    done
fi

# Check commands
echo ""
echo "Commands:"
for cmd in sc-brainstorm sc-execute-plan sc-write-plan; do
    dst="${HOME}/.claude/commands/${cmd}.md"
    if [ -L "$dst" ] || [ -f "$dst" ]; then
        pass "command: ${cmd}"
    else
        fail "command: ${cmd} — not installed"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check agents
echo ""
echo "Agents:"
dst="${HOME}/.claude/agents/code-reviewer.skill-chain.md"
if [ -L "$dst" ] || [ -f "$dst" ]; then
    pass "agent: code-reviewer.skill-chain"
else
    fail "agent: code-reviewer.skill-chain — not installed"
    ERRORS=$((ERRORS + 1))
fi

# Check rules
echo ""
echo "Rules:"
for subdir in common python typescript; do
    rule_count=$(ls "${HOME}/.claude/rules/${subdir}/" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$rule_count" -gt 0 ]; then
        pass "rules/${subdir}/: ${rule_count} files"
    else
        warn "rules/${subdir}/: empty or missing"
    fi
done

echo ""
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}All Claude Code verifications passed!${NC}"
    exit 0
else
    echo -e "${RED}${ERRORS} verification errors found.${NC}"
    exit 1
fi
