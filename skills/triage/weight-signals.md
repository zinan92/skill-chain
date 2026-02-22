# Weight Signals Reference — Quick Assessment Guide

Use this as a cheat sheet when assessing task weight during triage.

## Hard Signals Decision Matrix

```
                    Light           Medium          Heavy
                    ─────           ──────          ─────
Lines changed       < 200           200-1000        1000+
Files touched       1-3             4-10            10+
Modules crossed     1               2-3             4+
New dependencies    0               1-2             3+
Test files needed   1               2-4             5+
```

**Rule: If ALL hard signals say Light → Light. If ANY says Heavy → Heavy. Else → Medium.**

## Common Patterns — Type × Weight Quick Reference

### Feature
```
"Add a new API endpoint following existing pattern"          → Light
"Add a new API endpoint with new data model"                 → Medium
"Add a new subsystem (new module, new routes, new models)"   → Heavy
```

### Bug Fix
```
"Fix wrong return value in one function"                     → Light
"Fix race condition across multiple services"                → Medium
"Fix data corruption requiring migration + schema change"    → Heavy
```

### Refactor
```
"Rename variable / extract helper function"                  → Light
"Restructure a module's internal organization"               → Medium
"Replace ORM / change database schema / rewrite layer"       → Heavy
```

### Integration
```
"Call an existing API from existing code"                     → Light
"Connect two internal services with new protocol"            → Medium
"Build bi-directional sync between two systems"              → Heavy
```

### Migration
```
"Bump a library version (no API changes)"                    → Light
"Upgrade framework with breaking changes"                    → Medium
"Switch database / rewrite data layer"                       → Heavy
```

### Spike / Config
```
Almost always Light. If a spike seems Medium, it's probably
actually a Feature with unclear requirements — reclassify.
```

## Parallelism Quick Check

```
Can parts run independently?
    │
    ├── No shared state (DB tables, config files, types) → ✅ Parallel
    │
    ├── Read-only shared state → ✅ Parallel (with caution)
    │
    ├── Write to same state → ❌ Sequential
    │
    └── Output of A feeds B → ❌ Sequential (A before B)
```

## P&A Decision

```
Weight = Light?  → No P&A. Direct implementation.
Weight = Medium? → P&A if crossing 2+ module boundaries.
Weight = Heavy?  → P&A required. Define Ports first.
```

## Example Triage Decisions

| Task | Type | Weight | P&A? | Route |
|------|------|--------|------|-------|
| Add cron job for daily data pull | Config | Light | No | MVU |
| New Twitter collector in data-pipeline | Feature | Medium | Yes (collector port) | Plan + MVUs |
| Build quant-qual bridge (Phase 1B) | Integration | Heavy | Yes (bridge ports) | P&A + Plan + MVUs |
| Fix AKShare API response parsing | Bug Fix | Light | No | MVU |
| Upgrade SQLAlchemy 1.x → 2.x | Migration | Medium | Yes (old→new) | Plan + MVUs |
| Research WebSocket vs SSE for live data | Spike | Light | No | MVU (output = document) |
| Split monolith into market modules | Refactor | Heavy | Yes (shared port) | P&A + Plan + MVUs |
