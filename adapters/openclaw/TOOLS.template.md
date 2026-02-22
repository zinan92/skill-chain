# Tools Configuration

## Available Tools

### File Operations
- Read: Read file contents
- Write: Create/overwrite files
- Edit: In-place file editing
- Glob: Pattern-based file search
- Grep: Content search with regex

### Execution
- Bash: Shell command execution (sandboxed)
- Task: Launch sub-agents for parallel work

### Communication
- message: Send notifications (requires accountId)

## Skill Chain Tools
- Pipeline executor: lobster
- Guard system: python3 ${SCO_HOME}/core/helpers/guard.py
- Router: python3 ${SCO_HOME}/core/helpers/router.py
- Structured output extractor: python3 ${SCO_HOME}/core/helpers/extract_structured.py

## Tool Policies
- Deny overrides allow (security layers)
- Each tool requires explicit permission
- Bash commands sandboxed to ${TARGET_REPO}
