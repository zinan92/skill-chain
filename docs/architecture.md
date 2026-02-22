# Architecture

## Three-Layer Design

### 1. Control Flow Layer (Pipeline)
- `core/dev-pipeline.lobster` — orchestrates the full development cycle
- Lobster runtime executes steps serially
- Each step invokes a Claude Code skill via `claude -p`
- Step outputs piped through guards before next step

### 2. Execution Layer (Skills)
- Each skill is a self-contained prompt in `skills/<name>/SKILL.md`
- Skills receive context via stdin (previous step's structured output)
- Skills produce structured JSON output (--json-schema enforced)
- Skills are composable and replaceable

### 3. Guard Layer (Enforcement)
- `core/helpers/guard.py` — validates structured output at each transition
- Guards are **code, not prompts** — they cannot be talked out of
- Guard checks: schema validation, field presence, value ranges
- `core/helpers/router.py` — conditional routing (Light skips plan, Medium/Heavy plans)

## Pipeline Flow

```
init → triage → route → implement → review → verify → pre_commit → commit
  │       │        │         │          │        │         │          │
  └guard──┘  guard─┘   guard─┘    guard─┘  guard─┘   guard─┘    guard─┘
```

## Approval Gate

Between review and verify, the pipeline pauses for human approval.
This is the only manual intervention point in the entire pipeline.

## Schema + Guard + Approval: Triple Defense

1. **Schema**: JSON schema on claude --json-schema forces structured output
2. **Guard**: Python guard validates the structure meets transition requirements
3. **Approval**: Human reviews the code review verdict before proceeding

All three must pass. Any failure stops the pipeline.

## File Organization

```
core/
├── dev-pipeline.lobster    # Pipeline definition
├── smoke-basic.lobster     # Smoke test (no Claude CLI)
├── smoke-test.lobster      # Smoke test (with Claude CLI)
└── helpers/
    ├── guard.py            # Transition guard (THE enforcer)
    ├── router.py           # Conditional routing logic
    ├── commit.py           # Safe git commit helper
    ├── extract_structured.py  # Extract structured_output from Claude JSON
    └── extract_review.py   # Extract review data
```
