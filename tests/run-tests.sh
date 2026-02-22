#!/usr/bin/env bash
# run-tests.sh — Run all skill-chain runtime regression tests.
# Usage: ./tests/run-tests.sh [--verbose]
# Exit: 0 if all pass, 1 if any fail.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VERBOSE=false
[[ "${1:-}" == "--verbose" || "${1:-}" == "-v" ]] && VERBOSE=true

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS=0
FAIL=0
ERRORS=""

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║    skill-chain runtime tests             ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════╝${NC}"
echo ""

# Check pyyaml is available (needed for topology tests)
if ! python3 -c "import yaml" 2>/dev/null; then
    echo -e "${YELLOW}!${NC} PyYAML not installed. Installing..."
    pip3 install --quiet pyyaml
fi

run_test_file() {
    local test_file="$1"
    local label
    label=$(basename "$test_file" .py)

    echo -n "  Running ${label}... "

    local output
    if $VERBOSE; then
        output=$(python3 -m pytest "$test_file" -v 2>&1) || true
    else
        output=$(python3 -m unittest "$test_file" 2>&1) || true
    fi

    # Check the exit code by running again (unittest returns via exit code)
    if python3 -m unittest "$test_file" 2>/dev/null; then
        echo -e "${GREEN}PASS${NC}"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}FAIL${NC}"
        FAIL=$((FAIL + 1))
        ERRORS="${ERRORS}\n--- ${label} ---\n${output}\n"
    fi
}

# Discover and run all test files
for test_file in "${SCRIPT_DIR}"/runtime/test_*.py; do
    if [ -f "$test_file" ]; then
        run_test_file "$test_file"
    fi
done

# Summary
echo ""
TOTAL=$((PASS + FAIL))
if [ "$FAIL" -eq 0 ]; then
    echo -e "${GREEN}All ${TOTAL} test files passed!${NC}"
    exit 0
else
    echo -e "${RED}${FAIL}/${TOTAL} test files failed.${NC}"
    if [ -n "$ERRORS" ]; then
        echo ""
        echo -e "${RED}Failures:${NC}"
        echo -e "$ERRORS"
    fi
    exit 1
fi
