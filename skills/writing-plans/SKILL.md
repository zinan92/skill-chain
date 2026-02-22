---
name: writing-plans
description: Use when you have a spec or requirements for a multi-step task, before touching code
---

# Writing Plans

## Overview

Write comprehensive implementation plans assuming the engineer has zero context for our codebase and questionable taste. Document everything they need to know: which files to touch for each task, code, testing, docs they might need to check, how to test it. Give them the whole plan as bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume they are a skilled developer, but know almost nothing about our toolset or problem domain. Assume they don't know good test design very well.

**Announce at start:** "I'm using the writing-plans skill to create the implementation plan."

**Context:** This should be run in a dedicated worktree (created by brainstorming skill).

**Save plans to:** `docs/plans/YYYY-MM-DD-<feature-name>.md`

## Bite-Sized Task Granularity

**Each step is one action (2-5 minutes):**
- "Write the failing test" - step
- "Run it to make sure it fails" - step
- "Implement the minimal code to make the test pass" - step
- "Run the tests and make sure they pass" - step
- "Commit" - step

## Plan Document Header

**Every plan MUST start with this header:**

```markdown
# [Feature Name] Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

## Task Structure

````markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

**Step 1: Write the failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

**Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## Remember
- Exact file paths always
- Complete code in plan (not "add validation")
- Exact commands with expected output
- Reference relevant skills with @ syntax
- DRY, YAGNI, TDD, frequent commits

## Plan = Single Source of Truth

Once a plan is written and approved:
- All implementation follows the plan exactly
- Changes to scope require plan amendment (not ad-hoc decisions)
- Review checks implementation against the plan (not against reviewer's preferences)
- The plan is the contract between developer and reviewer

**If reality diverges from the plan:** update the plan first, get approval, then continue. Never silently deviate.

## Large Plan Mode (Heavy Tasks)

For Heavy tasks, structure the plan hierarchically:

### Epics
High-level capabilities (1-3 per plan). Each epic contains:

### Stories
User-facing increments within an epic. Each story contains:

### Tasks
Technical work items within a story. Each task contains:

### Steps
Atomic actions within a task (the familiar 5-step TDD cycle).

Example:
- Epic: "User Authentication System"
  - Story: "Email/Password Login"
    - Task: "Create login endpoint"
      - Step 1: Write failing test for POST /auth/login
      - Step 2: Run test → verify FAIL
      - Step 3: Write minimal implementation
      - Step 4: Run test → verify PASS
      - Step 5: Commit

## Red Flags — STOP

- Skipping writing-plans for a Medium or Heavy task
- Plan that contains no test steps (every task must have red-green verification)
- Plan that references vague paths ("somewhere in src/") instead of exact file paths
- Plan with no success criteria per task
- Modifying scope during execution without amending the plan first

**ALL of these mean: STOP and fix the process.**

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Planning slows me down" | Unplanned Medium/Heavy tasks take 2-3x longer due to rework. The plan saves time. |
| "I'll figure it out as I go" | That's called hacking, not engineering. Plans exist to prevent dead ends. |
| "The plan is in my head" | If it's not written down, it can't be reviewed, followed, or verified against. Write it down. |
| "This task is too fluid for a plan" | Then it's a Spike (from Triage). Spikes have plans too — they just plan what to investigate. |

**Process failure = stop and fix process.** Do not work around a broken process — fix it.

## Execution Handoff

After saving the plan, offer execution choice:

**"Plan complete and saved to `docs/plans/<filename>.md`. Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?"**

**If Subagent-Driven chosen:**
- **REQUIRED SUB-SKILL:** Use superpowers:subagent-driven-development
- Stay in this session
- Fresh subagent per task + code review

**If Parallel Session chosen:**
- Guide them to open new session in worktree
- **REQUIRED SUB-SKILL:** New session uses superpowers:executing-plans
