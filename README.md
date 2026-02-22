# skill-chain

Portable development pipeline that chains Claude Code skills into a reproducible, guarded workflow.

## What

skill-chain packages a complete development pipeline:

```
/triage → /writing-plans → /mvu-execution → /requesting-code-review → /verification-before-completion → commit
```

Each step invokes a Claude Code skill, and **transition guards** enforce quality gates between steps. The pipeline won't proceed unless each step passes its guard.

## Why

- **Reproducible**: Same pipeline, same guards, any machine
- **Guarded**: JSON schema + Python guards at every transition
- **Portable**: Works on Claude Code and OpenClaw
- **Safe**: Namespaced install, never overwrites your config

## Quick Start

```bash
# Clone
git clone https://github.com/your-org/skill-chain.git ~/skill-chain
export SCO_HOME=~/skill-chain

# Check dependencies
bash $SCO_HOME/scripts/doctor.sh

# Install (preview first)
bash $SCO_HOME/scripts/install.sh --dry-run

# Install for real
bash $SCO_HOME/scripts/install.sh

# Run smoke test
lobster run $SCO_HOME/core/smoke-basic.lobster
```

## Supported Platforms

| Platform | Status | Adapter |
|----------|--------|---------|
| Claude Code | Full support | `adapters/claude-code/` |
| OpenClaw | Full support | `adapters/openclaw/` |

## Architecture

```
┌─────────────────────────────────────────┐
│              Pipeline Layer              │
│  dev-pipeline.lobster (orchestrator)     │
├─────────────────────────────────────────┤
│              Guard Layer                 │
│  guard.py / router.py (enforcement)     │
├─────────────────────────────────────────┤
│              Skill Layer                 │
│  /triage /writing-plans /mvu-execution  │
│  /requesting-code-review /verification  │
├─────────────────────────────────────────┤
│              Rules Layer                 │
│  coding-style / testing / security      │
└─────────────────────────────────────────┘
```

## Key Concepts

- **Pipeline** = the big SOP (Standard Operating Procedure)
- **Skill** = the small SOP (one concern, one job)
- **Guard** = enforcement at transitions (not advisory — code, not prompts)
- **Approval Gate** = human review required before commit

## Customization

- Replace any skill with your own version
- Add guards for custom quality checks
- Adjust pipeline steps in `core/dev-pipeline.lobster`
- See `docs/customization.md` for details

## Uninstall

```bash
bash $SCO_HOME/scripts/uninstall.sh
```

Only removes items tracked in the install manifest. Your existing config is never touched.

## License

MIT
