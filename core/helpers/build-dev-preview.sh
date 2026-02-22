#!/usr/bin/env bash
# build-dev-preview.sh
# Assembles the approval preview for dev-pipeline.
# Reads env vars: TASK, BRANCH, TEST_OUT, LINT_OUT, DIFF_OUT, REVIEW_OUT
set -euo pipefail

# Determine pass/fail
test_ok="FAIL"
[[ "${TEST_OUT:-}" == *"TEST_EXIT=0"* ]] && test_ok="PASS"

lint_ok="FAIL"
[[ "${LINT_OUT:-}" == *"LINT_EXIT=0"* ]] && lint_ok="PASS"

# Extract test summary (last 5 meaningful lines before exit code)
test_summary=$(echo "${TEST_OUT:-no test output}" | grep -v '^$' | grep -v 'TEST_EXIT=' | tail -5)

# Extract diff stats
diff_stats=$(echo "${DIFF_OUT:-}" | sed -n '/--- STATS ---/,/--- FILES ---/p' | grep -v '^---' | head -20)
diff_files=$(echo "${DIFF_OUT:-}" | sed -n '/--- FILES ---/,/--- END ---/p' | grep -v '^---' | head -15)
file_count=$(echo "${diff_files}" | grep -c '.' 2>/dev/null || echo 0)

# Truncate review for Telegram (max 1500 chars)
review="${REVIEW_OUT:-no review output}"
review_short="${review:0:1500}"
[[ ${#review} -gt 1500 ]] && review_short="${review_short}
...(truncated)"

# Truncate lint output
lint_detail=""
if [[ "$lint_ok" == "FAIL" ]]; then
  lint_raw=$(echo "${LINT_OUT:-}" | grep -v 'LINT_EXIT=' | head -10)
  lint_detail="
${lint_raw:0:500}"
fi

# Build preview (target: <3800 chars for Telegram)
cat <<PREVIEW
DEV PIPELINE RESULT

Task: ${TASK:-unknown}
Branch: ${BRANCH:-unknown}

Tests: ${test_ok}
${test_summary}

Lint: ${lint_ok}${lint_detail}

Changes: ${file_count} files
${diff_stats}

AI Review (Codex/OpenAI):
${review_short}

Approve to commit?
PREVIEW
