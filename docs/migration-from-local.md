# Migration from Local Environment

One-time guide for extracting assets from your existing Claude Code setup into skill-chain.

## What Was Already Migrated (V1)

The initial skill-chain repo was created by copying from:

| Source | Destination | Notes |
|--------|-------------|-------|
| ~/.claude/workflows/dev-pipeline.lobster | core/dev-pipeline.lobster | Templatized (no hardcoded paths) |
| ~/.claude/workflows/helpers/* | core/helpers/* | All 5 helper scripts |
| ~/.claude/workflows/smoke-*.lobster | core/smoke-*.lobster | Templatized |
| ~/.claude/skills/* | skills/* | 24 skills (symlinks resolved) |
| ~/.claude/rules/{common,python,typescript}/* | rules/* | 18 rule files |
| ~/.claude/agents/code-reviewer.md | agents/code-reviewer.md | As-is |
| ~/.claude/commands/*.md | commands/sc-*.md | Renamed with sc- prefix |
| ~/clawd/scripts/build-*-preview.sh | core/helpers/ | Pipeline support scripts |

## What Was NOT Migrated (Intentional)

- **Personal rules**: `~/.claude/rules/message-tool-accountid.md` (Telegram-specific)
- **Settings.json**: Too personal, provided as template instead
- **Hooks**: Provided as template in settings.json.tmpl
- **Memory files**: Personal, stays in my/memory/
- **Knowledge base**: Personal, not part of skill-chain
- **Notion scripts**: Personal data export tools
- **Watchdog/cron scripts**: Infrastructure-specific

## V1.1 — Superpowers Methodology Adoption (2026-02)

Replaced skill methodology layer with content adapted from [obra/superpowers](https://github.com/obra/superpowers) (MIT License).

**What changed:**
- Core 5 skills adopted superpowers methodology (discipline, red flags, rationalizations)
- Each skill gained an explicit Output Contract section documenting guard-compatible JSON fields
- All `superpowers:` skill references normalized to local references
- Personal references neutralized to generic wording
- Attribution headers added to all adapted skills
- Transitive skills (6 files) also cleaned of upstream references

**What did NOT change (runtime invariants preserved):**
1. `core/dev-pipeline.lobster` — unchanged
2. `core/helpers/guard.py` — unchanged (v1.1 dual-stage review from prior commit)
3. `core/helpers/router.py` — unchanged
4. All 8 runtime invariants verified via `tests/run-tests.sh`
5. `doctor.sh`, `install.sh`, `uninstall.sh` — unchanged
6. Manifest integrity — 25/25 skills consistent

**Architecture model (post-migration):**
```
┌─────────────────────────────────────────┐
│  Cognitive Layer (superpowers skills)    │
│  HOW to think about development         │
├─────────────────────────────────────────┤
│  Control Layer (Lobster pipeline)        │
│  WHEN to execute each step              │
├─────────────────────────────────────────┤
│  Enforcement Layer (guards + approvals)  │
│  WHAT must be true to proceed           │
└─────────────────────────────────────────┘
```

## How to Add Your Own Assets

1. Copy the asset into the appropriate directory
2. Remove hardcoded paths (use ${SCO_HOME}, ${TARGET_REPO})
3. Run `python3 scripts/package-audit.py` to verify
4. Update manifests if adding skills
5. Re-run install
