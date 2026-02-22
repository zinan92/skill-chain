---
name: using-skill-chain
description: Bootstrap context for skill-chain — injected at session start
---

# Skill-Chain

Skill-chain is an opinionated software development pipeline that enforces quality gates at every stage. It orchestrates triage, planning, implementation, review, and verification as a structured skill chain.

## Commands

| Command | Purpose |
|---------|---------|
| `/sc-brainstorm` | Explore ideas and clarify intention before committing to a plan |
| `/sc-write-plan` | Decompose a triaged task into an executable plan document |
| `/sc-execute-plan` | Execute a plan through the full pipeline with guard enforcement |

## Pipeline

```
triage → plan → implement → review → verify → commit
```

Each stage has guards that enforce quality gates automatically. Guards block progression until their criteria are met — no skipping allowed.

## Key Principles

- Every task gets triaged before any code is written
- Plans are approved before execution begins
- Code review and verification happen before every commit
- Guards are code-enforced, not prompt-suggested

See `docs/` in the skill-chain repo for detailed documentation.
