---
name: triage
description: Use when you have a documented task with clear intention and need to classify it (type + weight) before any decomposition or coding — the CTO function that decides HOW to execute
---

<!-- Methodology: Adapted from obra/superpowers (MIT License)
     Local modifications: JSON output contract for guard.py compatibility,
     neutral wording, runtime integration with Lobster pipeline
     Last synced: superpowers v1.0 (2026-02) -->

# Triage — Task Classification & Execution Strategy

The CTO function. Before any code is written or any plan is made, every task must be triaged.

**Core principle:** Know what you're dealing with before you decide how to deal with it.

**Violating the letter of this rule is violating the spirit of this rule.**

## The Iron Law

```
NO DECOMPOSITION WITHOUT:
  1. Task type classified (Feature / Bug / Refactor / Integration / Migration / Spike / Config)
  2. Weight assessed with evidence (Light / Medium / Heavy)
  3. Human approval on the triage report
```

## What Is Triage

Triage is the bridge between "what do we want" (intention) and "how do we build it" (execution). It answers five questions:

| # | Question | Why It Matters |
|---|----------|----------------|
| 1 | **What type of task is this?** | Different types have different execution patterns |
| 2 | **How heavy is it?** | Determines decomposition depth and architecture needs |
| 3 | **What's the estimated effort?** | Sets expectations, prevents scope creep |
| 4 | **Parallel or sequential?** | Maximizes throughput when safe |
| 5 | **Does it need Ports & Adapters?** | Prevents coupling in multi-component work |

**Triage is NOT planning.** Triage decides the execution strategy. Planning (writing-plans) happens after, using the strategy triage defined.

## When to Use

```
Have a documented task with clear intention + success criteria?
    │
    ├── Yes → Use this skill (Triage)
    │
    └── No → Go back to clarify-intention first
              ⛔ No intention = no triage
```

**Use Triage before:**
- writing-plans (need weight to know decomposition depth)
- mvu-execution (need to confirm task IS an MVU)
- subagent-driven-development (need to know task count + parallelism)
- using-git-worktrees (need to know if isolation is warranted)

## The Protocol

### Step 1 — Classify Task Type

Read the task document. Match to exactly one type:

| Type | Signal | Typical Weight | Needs P&A? |
|------|--------|---------------|------------|
| **Feature** | New user-facing functionality | Medium-Heavy | Usually yes |
| **Bug Fix** | Correcting wrong behavior | Light | No |
| **Refactor** | Same behavior, better structure | Medium-Heavy | Depends on scope |
| **Integration** | Connecting two existing systems | Medium | Yes (adapter per side) |
| **Migration** | Upgrading deps, moving data, swapping infra | Medium-Heavy | Yes (old→new strategy) |
| **Spike** | Research / feasibility — output is a conclusion, not code | Light | No |
| **Config** | Settings, cron, deployment, env changes | Light | No |

**If unclear between two types:** pick the heavier one (conservative).

### Step 2 — Assess Weight

Use quantifiable signals, not gut feeling. Run the weight assessment checklist:

**Hard Signals (measure these):**

| Signal | How to Measure | Light | Medium | Heavy |
|--------|---------------|-------|--------|-------|
| Estimated lines changed | Count or estimate from spec | < 200 | 200-1000 | 1000+ |
| Files touched | List them | 1-3 | 4-10 | 10+ |
| Modules crossed | Check directory boundaries | 1 | 2-3 | 4+ |
| New dependencies | External libs, services, APIs | 0 | 1-2 | 3+ |
| Test files needed | Count from spec | 1 | 2-4 | 5+ |

**Soft Signals (consider these):**

| Signal | Light | Medium | Heavy |
|--------|-------|--------|-------|
| Pattern match | "Adding to existing pattern" | "New module, known pattern" | "New pattern / new domain" |
| Risk | Low — isolated change | Medium — touches shared code | High — changes contracts/schemas |
| Reversibility | Easy to revert | Needs migration | Breaking change |
| Prior art | Done this exact thing before | Similar task exists | First time |

**Scoring:**
- If ALL hard signals say Light → **Light**
- If ANY hard signal says Heavy → **Heavy**
- Otherwise → **Medium**
- **Soft signals can bump UP one level, never DOWN**

### Step 3 — Assess Parallelism

| Question | If Yes |
|----------|--------|
| Can this be split into independent parts? | Mark which parts can run in parallel |
| Do any parts share state (DB, config, types)? | Those parts must be sequential |
| Do any parts have data dependencies? | Sequential — output of A feeds B |
| Are there shared test fixtures? | Can parallel if fixtures are read-only |

**Output:** List of parallel groups and sequential chains.

### Step 4 — Architecture Decision

| Weight | Architecture | Rationale |
|--------|-------------|-----------|
| Light | Direct implementation | Too small for abstraction overhead |
| Medium | Optional P&A (if crossing modules) | P&A useful if 2+ modules involved |
| Heavy | Required P&A | Must define ports before any code |

**If P&A needed:** identify the Ports (interface contracts) before any decomposition.

### Step 5 — Produce Triage Report

Use the template in `./triage-report-template.md`. Fill every field.

### Step 6 — Human Approval

Present the triage report. Three possible outcomes:

| Outcome | What Happens |
|---------|-------------|
| **Approved** | Proceed to next phase (writing-plans for Medium/Heavy, mvu-execution for Light) |
| **Override** | Reviewer changes type/weight/strategy. Accept the override, update report. |
| **Rejected** | Task needs rethinking. Go back to clarify-intention. |

## Routing Table — After Triage

```
Triage Approved
    │
    ├── Light → Entire task = 1 MVU
    │     └── 🔧 mvu-execution (skip writing-plans)
    │
    ├── Medium → Decompose into 2-5 tasks
    │     ├── 🔧 writing-plans → create plan document
    │     └── Each task → 🔧 mvu-execution
    │
    └── Heavy → Decompose two layers + Ports & Adapters
          ├── Define Ports (interface contracts first)
          ├── 🔧 writing-plans → create plan document
          ├── Each Adapter can run in parallel
          └── Each MVU within Adapter → 🔧 mvu-execution
```

## Red Flags — STOP

- Starting to write code without completing triage
- Skipping triage because "it's obviously Light"
- Assessing weight by gut feeling without checking hard signals
- Classifying as Spike to avoid the rigor of Feature/Refactor
- Saying "Medium" for everything (the comfortable middle)
- Not presenting triage for human approval
- Decomposing before triage (putting cart before horse)
- Changing triage after decomposition starts without re-approval

**ALL of these mean: STOP and fix the process.**

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "It's obviously Light, skip triage" | 20-line changes have broken production. Triage takes 2 minutes. Do it. |
| "I already know how to build this" | Knowing HOW doesn't skip knowing WHAT TYPE and WHAT WEIGHT. Triage is about classification, not capability. |
| "Triage is overhead for small tasks" | Light triage IS small — 5 fields, 2 minutes. The routing decision alone justifies it. |
| "It's a bug fix, always Light" | Bug fixes that touch shared code, cross modules, or need schema changes are Medium. Classify, don't assume. |
| "Let's just start and see" | That's the definition of uncontrolled scope. Triage prevents exactly this. |
| "The reviewer will just approve anyway" | The approval step forces you to articulate your reasoning. That's the value. |

## Output Contract (guard.py)

The triage step output must include these fields for `guard --check triage` to pass:

**Required fields:**
```json
{
  "type": "Feature|Bug|Refactor|Integration|Migration|Spike|Config",
  "weight": "Light|Medium|Heavy",
  "summary": "string (5+ chars)",
  "routing": "mvu-execution|writing-plans"
}
```

**Recommended fields** (used by downstream steps):
```json
{
  "affected_areas": ["string"],
  "hard_signals": {
    "lines_changed": "number",
    "files_touched": "number",
    "modules_crossed": "number"
  }
}
```

**Guard behavior:**
- `weight` must be exactly one of `Light`, `Medium`, `Heavy` (case-sensitive)
- `summary` must be 5+ characters (no empty strings)
- Missing required fields → guard fails → pipeline stops

## Integration

**This skill is the gateway. Everything flows through it:**

- **Upstream:** 🔧 clarify-intention → produces the document that triage reads
- **Downstream (Light):** 🔧 mvu-execution → direct execution
- **Downstream (Medium):** 🔧 writing-plans → 🔧 subagent-driven-development or 🔧 executing-plans
- **Downstream (Heavy):** 🔧 writing-plans (with P&A) → 🔧 subagent-driven-development or 🔧 executing-plans

**This skill requires:**
- A documented task with intention + success criteria (from clarify-intention or equivalent)

**This skill produces:**
- Approved triage report with type, weight, strategy, and routing decision
- Ready for the next skill in the chain
