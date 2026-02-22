# MVU Escalation Prompt Template — Codex CLI

Use this template when an MVU has exceeded 2 roundtrips without resolution.

**Prerequisites:** Developer and Reviewer have gone back and forth twice. Issues remain unresolved. This is the escalation path.

## When to Escalate

- Roundtrip count > 2 (developer → reviewer → fix, twice)
- Tests still failing after 2 fix attempts
- Developer and Reviewer disagree on approach and can't converge

## Escalation via Codex CLI

```bash
codex --model o3 --full-auto \
  "Fix the following issues in [working directory].

## Task Spec
[FULL TEXT of the original task spec]

## Current State
[What the developer implemented — file paths, brief description]

## Unresolved Issues
[From reviewer's latest report — the specific issues that 2 roundtrips couldn't fix]

## Failed Tests
[Exact test output — command run + failure messages]

## Review History
Round 1: [Reviewer found X, Developer fixed Y but Z remained]
Round 2: [Reviewer found Z still present, Developer attempted W but failed]

## Your Job
1. Read the code and understand the actual problem
2. Fix the unresolved issues
3. Ensure all tests pass
4. Do not change the public API or break existing tests
5. Minimize changes — surgical fixes only
"
```

## After Codex CLI

1. Run tests: verify Codex's changes actually work
2. If tests pass → MVU Complete ✅
3. If tests fail → Human Escalation 🚨

## Human Escalation

If Codex CLI also fails:

```
Report to human:

## MVU Stuck: [task name]

**Spec:** [1-sentence summary]
**Developer attempts:** 2 roundtrips, issues: [list]
**Codex CLI attempt:** [what it tried, what failed]
**Current test status:** [exact output]

**Recommendation:**
- [ ] Fix manually (human has context developer/codex don't)
- [ ] Redesign the unit (spec may be flawed or ambiguous)
- [ ] Split into smaller units (this MVU may be too complex)
- [ ] Abandon (cost > value for this unit)
```

## Frequency Check

If escalation happens frequently (>20% of MVUs), the problem is upstream:
- Units too large → decompose further
- Specs too vague → improve Definition Phase
- Tests too brittle → improve test design
- Wrong tool for the job → reconsider approach

Track escalation rate as a meta-metric for the overall system health.
