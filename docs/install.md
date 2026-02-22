# Installation Guide

## Prerequisites

Run the doctor to check:
```bash
bash scripts/doctor.sh
```

### Required
- Node.js >= 18.0.0
- Python >= 3.11.0
- Git
- Claude CLI (`npm install -g @anthropic-ai/claude-code`)

### Optional
- Lobster (`npm install -g @openclaw/lobster`) — for pipeline execution
- OpenClaw — for OpenClaw adapter
- Codex CLI — for cross-company AI review

## Install

### 1. Clone
```bash
git clone https://github.com/your-org/skill-chain.git ~/skill-chain
export SCO_HOME=~/skill-chain
```

### 2. Preview
```bash
bash $SCO_HOME/scripts/install.sh --dry-run
```

### 3. Install
```bash
# Claude Code only (default)
bash $SCO_HOME/scripts/install.sh

# OpenClaw only
bash $SCO_HOME/scripts/install.sh --platform openclaw

# Both platforms
bash $SCO_HOME/scripts/install.sh --platform all
```

### 4. Add to shell profile
```bash
echo 'export SCO_HOME="$HOME/skill-chain"' >> ~/.zshrc
```

### 5. Verify
```bash
bash $SCO_HOME/scripts/doctor.sh
bash $SCO_HOME/adapters/claude-code/verify.sh
```

## What Gets Installed

| Asset | Location | Method |
|-------|----------|--------|
| Skills (required + transitive) | ~/.claude/skills/<name> | symlink |
| Commands (sc-prefixed) | ~/.claude/commands/sc-*.md | symlink |
| Agent (namespaced) | ~/.claude/agents/code-reviewer.skill-chain.md | symlink |
| Rules | ~/.claude/rules/{common,python,typescript}/ | symlink or skip |

**Settings are NOT auto-merged.** Use `build-settings.py` to preview and manually merge.

## Uninstall

```bash
bash $SCO_HOME/scripts/uninstall.sh

# Preview first
bash $SCO_HOME/scripts/uninstall.sh --dry-run
```

Only removes items in the install manifest. Never touches files it didn't create.

## Upgrade

```bash
cd $SCO_HOME
git pull
bash scripts/install.sh  # Re-run installer (idempotent)
```
