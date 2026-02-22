#!/usr/bin/env bash
# build-review-preview.sh
# Formats quick-review results for Telegram.
# Reads env vars: CONTEXT, TEST_OUT, DIFF_OUT, REVIEW_OUT
set -euo pipefail

# Determine pass/fail
test_ok="FAIL"
[[ "${TEST_OUT:-}" == *"TEST_EXIT=0"* ]] && test_ok="PASS"

# Extract test summary
test_summary=$(echo "${TEST_OUT:-no test output}" | grep -v '^$' | grep -v 'TEST_EXIT=' | tail -5)

# Extract diff stats
diff_stats=$(echo "${DIFF_OUT:-}" | sed -n '/--- STATS ---/,/--- FILES ---/p' | grep -v '^---' | head -15)
diff_files=$(echo "${DIFF_OUT:-}" | sed -n '/--- FILES ---/,/--- DIFF ---/p' | grep -v '^---' | head -15)
file_count=$(echo "${diff_files}" | grep -c '.' 2>/dev/null || echo 0)

# Truncate review (max 2000 chars for review-only mode)
review="${REVIEW_OUT:-no review output}"
review_short="${review:0:2000}"
[[ ${#review} -gt 2000 ]] && review_short="${review_short}
...(truncated)"

# Build preview
cat <<PREVIEW
CODE REVIEW RESULTS
${CONTEXT:+
Context: ${CONTEXT}}

Tests: ${test_ok}
${test_summary}

Changes: ${file_count} files
${diff_stats}

AI Review (Codex/OpenAI):
${review_short}

No action taken. Use 'dev pipeline' to commit with approval, or commit manually.
PREVIEW
