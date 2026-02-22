---
name: requesting-code-review
description: Use when completing tasks, implementing major features, or before merging to verify work meets requirements
---

<!-- Methodology: Adapted from obra/superpowers (MIT License)
     Local modifications: JSON output contract for guard.py compatibility,
     dual-stage review support, runtime integration with Lobster pipeline
     Last synced: superpowers v1.0 (2026-02) -->

# Requesting Code Review

Dispatch a code-reviewer subagent to catch issues before they cascade.

**Core principle:** Review early, review often.

## When to Request Review

**Mandatory:**
- After each task in subagent-driven development
- After completing major feature
- Before merge to main

**Optional but valuable:**
- When stuck (fresh perspective)
- Before refactoring (baseline check)
- After fixing complex bug

## How to Request

**1. Get git SHAs:**
```bash
BASE_SHA=$(git rev-parse HEAD~1)  # or origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

**2. Dispatch code-reviewer subagent:**

Use Task tool with code-reviewer subagent, fill template at `code-reviewer.md`

**Placeholders:**
- `{WHAT_WAS_IMPLEMENTED}` - What you just built
- `{PLAN_OR_REQUIREMENTS}` - What it should do
- `{BASE_SHA}` - Starting commit
- `{HEAD_SHA}` - Ending commit
- `{DESCRIPTION}` - Brief summary

**3. Act on feedback:**
- Fix Critical issues immediately
- Fix Important issues before proceeding
- Note Minor issues for later
- Push back if reviewer is wrong (with reasoning)

## Example

```
[Just completed Task 2: Add verification function]

You: Let me request code review before proceeding.

BASE_SHA=$(git log --oneline | grep "Task 1" | head -1 | awk '{print $1}')
HEAD_SHA=$(git rev-parse HEAD)

[Dispatch code-reviewer subagent]
  WHAT_WAS_IMPLEMENTED: Verification and repair functions for conversation index
  PLAN_OR_REQUIREMENTS: Task 2 from docs/plans/deployment-plan.md
  BASE_SHA: a7981ec
  HEAD_SHA: 3df7661
  DESCRIPTION: Added verifyIndex() and repairIndex() with 4 issue types

[Subagent returns]:
  Strengths: Clean architecture, real tests
  Issues:
    Important: Missing progress indicators
    Minor: Magic number (100) for reporting interval
  Assessment: Ready to proceed

You: [Fix progress indicators]
[Continue to Task 3]
```

## Integration with Workflows

**Subagent-Driven Development:**
- Review after EACH task
- Catch issues before they compound
- Fix before moving to next task

**Executing Plans:**
- Review after each batch (3 tasks)
- Get feedback, apply, continue

**Ad-Hoc Development:**
- Review before merge
- Review when stuck

## Red Flags — STOP

- Skipping review because the change is "simple" or "small"
- Not waiting for review to complete before proceeding to the next task
- Ignoring Critical or Important issues from the reviewer
- Merging without any review at all (self-review alone is not sufficient)

**ALL of these mean: STOP and fix the process.**

**If reviewer wrong:**
- Push back with technical reasoning
- Show code/tests that prove it works
- Request clarification

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "The tests pass so it's fine" | Tests verify behavior. Review verifies design, readability, and edge cases tests don't cover. Both are needed. |
| "It's just a refactor" | Refactors can introduce subtle bugs that tests miss. Review catches structural regressions. |
| "I'll get review on the next PR" | Compounding unreviewed changes makes every future review harder and less effective. Review now. |
| "Review takes too long, I'll lose momentum" | Shipping broken code costs more momentum than a 10-minute review. Slow is smooth, smooth is fast. |

**Process failure = stop and fix process.** Do not work around a broken process — fix it.

## Output Contract (guard.py)

The review step output must include these fields for `guard --check review` to pass:

**Legacy format (single-stage):**
```json
{
  "verdict": "approved|with_fixes|rejected",
  "summary": "string",
  "issues": [
    {"severity": "critical|high|medium|low", "file": "string", "line": "number", "description": "string"}
  ]
}
```

**Dual-stage format (v1.1+):**
```json
{
  "spec_review": {"verdict": "pass|fail", "issues": []},
  "quality_review": {"verdict": "pass|fail", "issues": []},
  "overall_verdict": "approved|with_fixes|rejected"
}
```

**Guard behavior:**
- Only `verdict == "approved"` (legacy) or `overall_verdict == "approved"` (dual-stage) passes
- `with_fixes` and `rejected` both block the pipeline
- Dual-stage: `spec_review.verdict == "fail"` + `overall_verdict == "approved"` → contradiction → blocked
- Guard auto-detects format (backward compatible)

See template at: requesting-code-review/code-reviewer.md
