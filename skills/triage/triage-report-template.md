# Triage Report Template

Use this template when producing the triage output. Fill every field — no field is optional.

```
Task tool (general-purpose):
  description: "Triage: [brief task name]"
  prompt: |
    You are the triage agent for this task.

    ## Task Document

    [FULL TEXT of the task document — intention, success criteria, constraints]

    ## Your Job: Classify & Route

    Read the document carefully. Produce a triage report following the format below.

    Before you classify:
    1. Read the task document completely
    2. Identify the codebase context (check directory structure, existing modules)
    3. Count affected files and modules by reading the code
    4. Do NOT guess — measure where possible

    ## Triage Report Format

    ```markdown
    ## Triage Report: [task name]

    **Date:** YYYY-MM-DD
    **Task document:** [path or link]

    ### 1. Task Type

    **Classification:** [Feature / Bug Fix / Refactor / Integration / Migration / Spike / Config]
    **Reasoning:** [1-2 sentences why this type, not another]

    ### 2. Weight Assessment

    **Classification:** [Light / Medium / Heavy]

    **Hard Signals:**

    | Signal | Value | Classification |
    |--------|-------|---------------|
    | Estimated lines changed | [number] | [L/M/H] |
    | Files touched | [list or count] | [L/M/H] |
    | Modules crossed | [list or count] | [L/M/H] |
    | New dependencies | [list or count] | [L/M/H] |
    | Test files needed | [list or count] | [L/M/H] |

    **Soft Signals:**

    | Signal | Assessment | Classification |
    |--------|-----------|---------------|
    | Pattern match | [description] | [L/M/H] |
    | Risk level | [Low/Medium/High + reason] | [L/M/H] |
    | Reversibility | [Easy/Needs migration/Breaking] | [L/M/H] |
    | Prior art | [Done before/Similar exists/First time] | [L/M/H] |

    **Final Weight:** [Light / Medium / Heavy]
    **Scoring justification:** [which signals drove the decision]

    ### 3. Effort Estimate

    **MVU count:** [how many MVUs this decomposes into]
    **Estimated roundtrips:** [total developer→reviewer cycles]
    **Calendar time:** [rough duration at current pace]

    ### 4. Parallelism

    **Can parallelize:** [Yes / No / Partial]

    [If yes/partial:]
    - Parallel group A: [task list]
    - Parallel group B: [task list]
    - Sequential chain: [A must finish before B because...]

    ### 5. Architecture

    **Needs Ports & Adapters:** [Yes / No]

    [If yes:]
    - Port 1: [interface name + what it abstracts]
    - Port 2: [interface name + what it abstracts]
    - Adapters: [list of concrete implementations needed]

    [If no:]
    - **Approach:** Direct implementation
    - **Reason:** [why P&A is unnecessary]

    ### 6. Routing Decision

    **Route:** [Light → MVU / Medium → Plan + MVUs / Heavy → P&A + Plan + MVUs]
    **Next skill:** 🔧 [mvu-execution / writing-plans]
    **Needs worktree:** [Yes / No]

    ### 7. Risks & Concerns

    [Anything the reviewer should know before approving — edge cases, unknowns, blockers]
    ```

    ## Rules

    - Fill EVERY field. "N/A" is acceptable only for parallelism on Light tasks.
    - Hard signals override soft signals (soft can bump up, never down).
    - If unclear between two weights, pick the heavier one.
    - If you can't measure a hard signal, say "estimated" and explain why.
    - Do NOT start decomposing or planning. Triage only.
```
